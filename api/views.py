# views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from api.models import Class, CustomUser, QuestionBank, Quiz, QuizAttempt
from api.serializers import ClassSerializer, CustomUserSerializer, QuestionBankSerializer, QuizAttemptSerializer, QuizSerializer, EmailTokenObtainPairSerializer
from rest_framework.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import logout

class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        """
        Override to allow registration without authentication
        """
        if self.action == 'create':  # registration endpoint
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        if self.action == 'list' and not self.request.user.is_staff:
            return CustomUser.objects.filter(id=self.request.user.id)
        return self.queryset

    def create(self, request, *args, **kwargs):
        """
        Custom create method to handle user registration
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'User registered successfully',
                'user': CustomUserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            # Handle profile picture removal
            if request.data.get('remove_profile_picture') == 'true':
                user.profile_picture = 'profile_pictures/profile.png'
                user.save()

            # Save the updated user data
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not user.check_password(old_password):
            return Response(
                {'old_password': ['Wrong password.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set and validate the new password
        try:
            validate_password(new_password, user)
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password updated successfully'})
        except ValidationError as e:
            return Response(
                {'new_password': list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['delete'], permission_classes=[IsAuthenticated])
    def delete_account(self, request):
        """
        Permanently delete the user's account
        """
        user = request.user
        try:
            # Delete the user
            user.delete()
            # Force logout
            logout(request)
            return Response(
                {'message': 'Account deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response(
                {'error': 'Failed to delete account'},
                status=status.HTTP_400_BAD_REQUEST
            )

class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_teacher:
            return Class.objects.filter(teacher=user)
        return Class.objects.filter(students=user)

    def perform_create(self, serializer):
        if not self.request.user.is_teacher:
            return Response(
                {'error': 'Only teachers can create classes'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save(teacher=self.request.user)

    @action(detail=False, methods=['post'])  # Changed from detail=True to detail=False
    def join(self, request):  # Removed pk=None parameter
        if request.user.is_teacher:
            return Response(
                {'error': 'Teachers cannot join classes'},
                status=status.HTTP_403_FORBIDDEN
            )

        join_code = request.data.get('join_code')
        try:
            class_obj = Class.objects.get(join_code=join_code)
            if request.user in class_obj.students.all():
                return Response(
                    {'error': 'Already a member of this class'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            class_obj.students.add(request.user)
            return Response({'message': 'Successfully joined class'})
        except Class.DoesNotExist:
            return Response(
                {'error': 'Invalid join code'},
                status=status.HTTP_404_NOT_FOUND
            )

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Quiz.objects.all()  # Or filter as needed for public view

        user = self.request.user
        if user.is_teacher:
            return Quiz.objects.filter(teacher=user)
        return Quiz.objects.filter(classes__students=user)

    def perform_create(self, serializer):
        if not self.request.user.is_teacher:
            return Response(
                {'error': 'Only teachers can create quizzes'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save(
            teacher=self.request.user,
            question_ids=self.request.data.get('questions', [])
        )

    @action(detail=True, methods=['post'])
    def take_quiz(self, request, pk=None):
        quiz = self.get_object()

        if not quiz.is_active():
            return Response(
                {'error': 'Quiz is not currently available'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if QuizAttempt.objects.filter(quiz=quiz, student=request.user).exists():
            return Response(
                {'error': 'You have already attempted this quiz'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process answers
        answers = request.data.get('answers', {})
        questions = quiz.questions.all()
        correct_count = 0
        total_points = 0
        max_points = sum(question.points for question in questions)
        results = []

        for question in questions:
            answer = str(answers.get(str(question.id)))

            # Handle multiple choice answers
            if question.question_type == 'MC':
                # Check if answer is the option text rather than index
                if answer in [question.option_a, question.option_b, question.option_c, question.option_d]:
                    # Convert option text to index
                    options = [question.option_a, question.option_b, question.option_c, question.option_d]
                    answer = str(options.index(answer))

            is_correct = answer.lower() == question.correct_answer.lower()
            if is_correct:
                correct_count += 1
                total_points += question.points

            # Get display answer for results
            display_answer = answer
            if question.question_type == 'MC':
                options = {
                    '0': question.option_a,
                    '1': question.option_b,
                    '2': question.option_c,
                    '3': question.option_d
                }
                display_answer = options.get(answer, answer)
                correct_display = options.get(question.correct_answer, question.correct_answer)
            else:
                correct_display = question.correct_answer

            results.append({
                'question_id': question.id,
                'correct': is_correct,
                'user_answer': display_answer,
                'correct_answer': correct_display if quiz.show_correct_answers else None,
                'points': question.points if is_correct else 0,
                'max_points': question.points
            })

        # Calculate percentage score based on points
        score = (total_points / max_points) * 100 if max_points > 0 else 0

        # Create attempt
        attempt = QuizAttempt.objects.create(
            student=request.user,
            quiz=quiz,
            score=score,
            total_questions=len(questions),
            correct_questions=correct_count,
            total_points=total_points,
            max_points=max_points
        )

        return Response({
            'score': score,
            'correct_questions': correct_count,
            'total_questions': len(questions),
            'total_points': total_points,
            'max_points': max_points,
            'results': results
        })

class QuestionBankViewSet(viewsets.ModelViewSet):
    queryset = QuestionBank.objects.all()
    serializer_class = QuestionBankSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_teacher:
            return QuestionBank.objects.filter(teacher=self.request.user)
        return QuestionBank.objects.none()

    def perform_create(self, serializer):
        if not self.request.user.is_teacher:
            return Response(
                {'error': 'Only teachers can create questions'},
                status=status.HTTP_403_FORBIDDEN
            )
        # Update points handling
        points = self.request.data.get('points')
        try:
            points = int(points) if points else 1
            if points < 1:
                points = 1
        except (ValueError, TypeError):
            points = 1

        serializer.save(teacher=self.request.user, points=points)

class QuizAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = QuizAttempt.objects.all()
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = QuizAttempt.objects.all()

        # Apply user filter
        if user.is_teacher:
            queryset = queryset.filter(quiz__teacher=user)
        else:
            queryset = queryset.filter(student=user)

        # Apply quiz filter if provided
        quiz_id = self.request.query_params.get('quiz', None)
        if quiz_id is not None:
            queryset = queryset.filter(quiz_id=quiz_id)

        return queryset
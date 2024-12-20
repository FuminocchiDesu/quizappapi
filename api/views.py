# views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from api.models import Class, CustomUser, QuestionBank, Quiz, QuizAttempt
from api.serializers import ClassSerializer, CustomUserSerializer, QuestionBankSerializer, QuizAttemptSerializer, QuizSerializer

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.action == 'list' and not self.request.user.is_staff:
            return CustomUser.objects.filter(id=self.request.user.id)
        return self.queryset

    @action(detail=False, methods=['get'])
    def profile(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
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
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
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
        serializer.save(teacher=self.request.user)

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
        results = []

        for question in questions:
            answer = answers.get(str(question.id))
            is_correct = answer == question.correct_answer
            if is_correct:
                correct_count += 1
            results.append({
                'question_id': question.id,
                'correct': is_correct,
                'user_answer': answer,
                'correct_answer': question.correct_answer if quiz.show_correct_answers else None
            })

        # Create attempt
        score = (correct_count / len(questions)) * 100 if questions else 0
        attempt = QuizAttempt.objects.create(
            student=request.user,
            quiz=quiz,
            score=score,
            total_questions=len(questions),
            correct_questions=correct_count
        )

        return Response({
            'score': score,
            'correct_questions': correct_count,
            'total_questions': len(questions),
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
        serializer.save(teacher=self.request.user)

class QuizAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = QuizAttempt.objects.all()
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_teacher:
            return QuizAttempt.objects.filter(quiz__teacher=user)
        return QuizAttempt.objects.filter(student=user)
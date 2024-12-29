# serializers.py
from rest_framework import serializers
from .models import CustomUser, Class, Quiz, QuestionBank, QuizAttempt
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
import os

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    profile_picture = serializers.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'password', 'first_name',
                 'last_name', 'is_teacher', 'profile_picture')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_teacher=validated_data.get('is_teacher', False),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)

        # Handle profile picture removal
        if validated_data.get('remove_profile_picture'):
            instance.profile_picture = 'profile_pictures/profile.png'
            validated_data.pop('remove_profile_picture')

        # Handle profile picture update
        if 'profile_picture' in validated_data:
            profile_picture = validated_data['profile_picture']
            if profile_picture:
                # Get file extension
                ext = os.path.splitext(profile_picture.name)[1].lower()
                # Create new filename
                filename = f"{instance.username}{ext}"
                # Set correct path
                profile_picture.name = filename

        return super().update(instance, validated_data)

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Get the username and password from the request
        username = attrs.get('username')
        password = attrs.get('password')

        try:
            # Try to fetch the user by username or email
            user = CustomUser.objects.get(Q(username=username) | Q(email=username))

            # Update the username in attrs to the actual username
            # This is necessary because the parent class expects username
            attrs['username'] = user.username

            # Now authenticate with the actual username
            credentials = {
                'username': user.username,
                'password': password
            }

            user = authenticate(**credentials)

            if user is None:
                raise serializers.ValidationError('Invalid password')

            if not user.is_active:
                raise serializers.ValidationError('User is inactive')

            # If we get here, authentication was successful
            return super().validate(attrs)

        except CustomUser.DoesNotExist:
            raise serializers.ValidationError('No account found with the given credentials')

class ClassSerializer(serializers.ModelSerializer):
    teacher = CustomUserSerializer(read_only=True)
    students = CustomUserSerializer(many=True, read_only=True)

    class Meta:
        model = Class
        fields = ('id', 'name', 'section', 'teacher', 'join_code', 'students')

class QuestionBankSerializer(serializers.ModelSerializer):
    teacher = CustomUserSerializer(read_only=True)
    display_answer = serializers.SerializerMethodField()

    class Meta:
        model = QuestionBank
        fields = ['id', 'teacher', 'question_text', 'question_type', 'correct_answer',
                 'option_a', 'option_b', 'option_c', 'option_d', 'points', 'display_answer']

    def get_display_answer(self, obj):
        if obj.question_type == 'MC':
            options = {
                '0': obj.option_a,
                '1': obj.option_b,
                '2': obj.option_c,
                '3': obj.option_d
            }
            return options.get(obj.correct_answer, obj.correct_answer)
        elif obj.question_type == 'TF':
            return 'True' if obj.correct_answer.lower() == 'true' else 'False'
        return obj.correct_answer

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Replace correct_answer with display_answer for the response
        representation['correct_answer'] = representation.pop('display_answer')
        return representation

class QuizSerializer(serializers.ModelSerializer):
    teacher = CustomUserSerializer(read_only=True)
    questions = QuestionBankSerializer(many=True, read_only=True)
    question_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Quiz
        fields = ('id', 'title', 'teacher', 'classes', 'start_datetime',
                 'end_datetime', 'time_limit_minutes', 'questions',
                 'show_correct_answers', 'question_ids')

    def create(self, validated_data):
        question_ids = validated_data.pop('question_ids', [])
        quiz = super().create(validated_data)
        if question_ids:
            questions = QuestionBank.objects.filter(id__in=question_ids)
            quiz.questions.set(questions)
        return quiz

class QuizAttemptSerializer(serializers.ModelSerializer):
    student = CustomUserSerializer(read_only=True)
    quiz = QuizSerializer(read_only=True)

    class Meta:
        model = QuizAttempt
        fields = ('id', 'student', 'quiz', 'score', 'total_questions',
                 'correct_questions', 'total_points', 'max_points', 'attempt_datetime')
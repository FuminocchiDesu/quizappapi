# serializers.py
from rest_framework import serializers
from .models import CustomUser, Class, Quiz, QuestionBank, QuizAttempt

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'is_teacher', 'profile_picture')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user

class ClassSerializer(serializers.ModelSerializer):
    teacher = CustomUserSerializer(read_only=True)
    students = CustomUserSerializer(many=True, read_only=True)
    
    class Meta:
        model = Class
        fields = ('id', 'name', 'teacher', 'join_code', 'students')

class QuestionBankSerializer(serializers.ModelSerializer):
    teacher = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = QuestionBank
        fields = ('id', 'teacher', 'question_text', 'question_type',
                 'correct_answer', 'option_a', 'option_b', 'option_c', 'option_d')

class QuizSerializer(serializers.ModelSerializer):
    teacher = CustomUserSerializer(read_only=True)
    questions = QuestionBankSerializer(many=True, read_only=True)
    
    class Meta:
        model = Quiz
        fields = ('id', 'title', 'teacher', 'classes', 'start_datetime',
                 'end_datetime', 'time_limit_minutes', 'questions', 
                 'show_correct_answers')

class QuizAttemptSerializer(serializers.ModelSerializer):
    student = CustomUserSerializer(read_only=True)
    quiz = QuizSerializer(read_only=True)
    
    class Meta:
        model = QuizAttempt
        fields = ('id', 'student', 'quiz', 'score', 'total_questions',
                 'correct_questions', 'attempt_datetime')
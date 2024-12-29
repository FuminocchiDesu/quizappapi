from django.contrib import admin
from .models import CustomUser, Class, QuestionBank, Quiz, QuizAttempt

# Custom admin for CustomUser
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_teacher', 'date_joined', 'last_login')
    list_filter = ('is_teacher', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

# Admin for Class
@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'join_code')
    search_fields = ('name', 'join_code', 'teacher__username')
    filter_horizontal = ('students',)

# Admin for QuestionBank
@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'question_text', 'question_type')
    list_filter = ('question_type',)
    search_fields = ('teacher__username', 'question_text')

# Admin for Quiz
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'start_datetime', 'end_datetime', 'time_limit_minutes')
    list_filter = ('start_datetime', 'end_datetime')
    search_fields = ('title', 'teacher__username')
    filter_horizontal = ('classes', 'questions')

# Admin for QuizAttempt
@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score', 'correct_questions', 'attempt_datetime')
    list_filter = ('attempt_datetime',)
    search_fields = ('student__username', 'quiz__title')

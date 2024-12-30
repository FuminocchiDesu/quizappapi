# models.py
import os
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import MinLengthValidator, EmailValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    email = models.EmailField(_('email address'), unique=True, validators=[EmailValidator()])
    is_teacher = models.BooleanField(default=False)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        verbose_name="Profile Picture",
        default='profile_pictures/profile.png'
    )

    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="customuser_set",
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="customuser_set",
        related_query_name="customuser",
    )

    def save(self, *args, **kwargs):
        if not self.email:
            self.email = f"{self.username}@example.com"

        if not self.password:
            self.set_password(self.username)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_full_name() or self.username

class Class(models.Model):
    name = models.CharField(max_length=100)
    section = models.CharField(max_length=50, blank=True)  # Added section field
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_classes')
    join_code = models.CharField(max_length=8, unique=True)
    students = models.ManyToManyField(CustomUser, related_name='enrolled_classes', blank=True)

    def __str__(self):
        if self.section:
            return f"{self.name} {self.section}"
        return self.name

class QuestionBank(models.Model):
    QUESTION_TYPES = [
        ('MC', 'Multiple Choice'),
        ('TF', 'True/False'),
        ('ID', 'Identification')
    ]
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    question_text = models.TextField()
    question_type = models.CharField(max_length=2, choices=QUESTION_TYPES)
    correct_answer = models.TextField()
    option_a = models.CharField(max_length=200, blank=True, null=True)
    option_b = models.CharField(max_length=200, blank=True, null=True)
    option_c = models.CharField(max_length=200, blank=True, null=True)
    option_d = models.CharField(max_length=200, blank=True, null=True)
    points = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.question_type}: {self.question_text[:50]}"

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    classes = models.ManyToManyField(Class, related_name='quizzes')  # Change this line
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    time_limit_minutes = models.IntegerField(default=30)
    questions = models.ManyToManyField(QuestionBank)
    show_correct_answers = models.BooleanField(default=False)

    def is_active(self):
        now = timezone.now()
        return self.start_datetime <= now <= self.end_datetime

    def __str__(self):
        return self.title

class QuizAttempt(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.FloatField(default=0)
    total_questions = models.IntegerField()
    correct_questions = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    max_points = models.IntegerField(default=0)
    attempt_datetime = models.DateTimeField(auto_now_add=True)
    results = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title}"
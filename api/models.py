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
    # Use 'related_query_name' to avoid clash
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
        # Ensure email is set
        if not self.email:
            self.email = f"{self.username}@example.com"
        
        # Ensure a password is set
        if not self.password:
            self.set_password(self.username)
        
        # Rename profile picture to username if it exists
        if self.profile_picture and not self.profile_picture.name.endswith('profile.png'):
            ext = os.path.splitext(self.profile_picture.name)[1]
            self.profile_picture.name = f'profile_pictures/{self.username}{ext}'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_full_name() or self.username

class Class(models.Model):
    """
    Represents a class created by a teacher
    """
    name = models.CharField(max_length=100)
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_classes')
    join_code = models.CharField(max_length=8, unique=True)
    students = models.ManyToManyField(CustomUser, related_name='enrolled_classes', blank=True)
    
    def __str__(self):
        return self.name

class QuestionBank(models.Model):
    """
    Data banking system for storing questions
    """
    QUESTION_TYPES = [
        ('MC', 'Multiple Choice'),
        ('TF', 'True/False'),
        ('ID', 'Identification')
    ]

    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    question_text = models.TextField()
    question_type = models.CharField(max_length=2, choices=QUESTION_TYPES)
    correct_answer = models.TextField()
    
    # For multiple choice
    option_a = models.CharField(max_length=200, blank=True, null=True)
    option_b = models.CharField(max_length=200, blank=True, null=True)
    option_c = models.CharField(max_length=200, blank=True, null=True)
    option_d = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.question_type}: {self.question_text[:50]}"

class Quiz(models.Model):
    """
    Represents a quiz created by a teacher
    """
    title = models.CharField(max_length=200)
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    classes = models.ManyToManyField(Class, related_name='quizzes')  # Change this line

    # Quiz scheduling and timer
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    time_limit_minutes = models.IntegerField(default=30)

    # Quiz configuration
    questions = models.ManyToManyField(QuestionBank)
    show_correct_answers = models.BooleanField(default=False)

    def is_active(self):
        """Check if quiz is currently available"""
        now = timezone.now()
        return self.start_datetime <= now <= self.end_datetime 

    def __str__(self):
        return self.title

class QuizAttempt(models.Model):
    """
    Tracks student attempts at a quiz
    """
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.FloatField(default=0)
    total_questions = models.IntegerField()
    correct_questions = models.IntegerField(default=0)
    
    attempt_datetime = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.username} - {self.quiz.title}"
# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import ClassViewSet, CustomUserViewSet, QuestionBankViewSet, QuizAttemptViewSet, QuizViewSet

router = DefaultRouter()
router.register(r'users', CustomUserViewSet)
router.register(r'classes', ClassViewSet)
router.register(r'quizzes', QuizViewSet)
router.register(r'questions', QuestionBankViewSet)
router.register(r'attempts', QuizAttemptViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
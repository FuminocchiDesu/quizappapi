# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import ClassViewSet, CustomUserViewSet, QuestionBankViewSet, QuizAttemptViewSet, QuizViewSet, EmailTokenObtainPairView

router = DefaultRouter()
router.register(r'users', CustomUserViewSet)
router.register(r'classes', ClassViewSet)
router.register(r'quizzes', QuizViewSet)
router.register(r'questions', QuestionBankViewSet)
router.register(r'attempts', QuizAttemptViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/change_password/', CustomUserViewSet.as_view({'post': 'change_password'}), name='change_password'),
    path('users/delete_account/', CustomUserViewSet.as_view({'delete': 'delete_account'}), name='delete_account'),
]
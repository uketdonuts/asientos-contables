from django.urls import path
from users import views
from .views import (
    CustomPasswordResetView, 
    password_reset_complete_view,
    OTPVerificationView,
    SetNewPasswordView,
    PerfilUsuarioView,
    EditarPerfilUsuarioView
)

app_name = 'users'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset-complete/', password_reset_complete_view, name='password_reset_complete'),
    path('verify-otp/', OTPVerificationView.as_view(), name='verify_otp'),
    path('set-new-password/', SetNewPasswordView.as_view(), name='set_new_password'),
    path('perfil/', PerfilUsuarioView.as_view(), name='perfil'),
    path('editar-perfil/', EditarPerfilUsuarioView.as_view(), name='editar_perfil'),
]
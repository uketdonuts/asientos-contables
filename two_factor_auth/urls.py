from django.urls import path
from . import views

app_name = 'two_factor_auth'

urlpatterns = [
    path('', views.TwoFactorAuthView.as_view(), name='two_factor_auth'),
    path('setup/', views.TwoFactorAuthSetupView.as_view(), name='setup'),
    path('verify/', views.TwoFactorAuthVerifyView.as_view(), name='verify'),
    path('disable/', views.TwoFactorAuthDisableView.as_view(), name='disable'),
    path('setup-complete/', views.TwoFactorAuthSetupCompleteView.as_view(), name='setup_complete'),
    path('transition/', views.TwoFactorAuthTransitionView.as_view(), name='transition'),
    path('recovery/', views.TwoFactorAuthRecoveryView.as_view(), name='recovery'),
]

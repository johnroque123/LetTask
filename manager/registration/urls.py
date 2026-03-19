from django.urls import path
from .views import (
    register,
    login_view,
    verify_otp_view,
    logout_view,
    chatbot,
    change_password_view,
    forgot_password_view,
    verify_reset_otp_view,
    reset_password_view,
    edit_profile_view,
)

urlpatterns = [
    path('', register, name='register'),
    path('login/', login_view, name='login'),
    path('verify-otp/', verify_otp_view, name='verify_otp'),
    path('logout/', logout_view, name='logout'),
    path('chatbot/', chatbot, name='chatbot'),
    path('change-password/', change_password_view, name='change_password'),
    path('forgot-password/', forgot_password_view, name='forgot_password'),
    path('forgot-password/verify/', verify_reset_otp_view, name='verify_reset_otp'),
    path('forgot-password/reset/', reset_password_view, name='reset_password'),
    path('profile/edit/', edit_profile_view, name='edit_profile'),
]
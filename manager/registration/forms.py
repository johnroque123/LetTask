from django import forms
from .models import User
from django.contrib.auth.password_validation import validate_password
import re

INPUT_CLASS = "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"


def validate_strong_password(password):
    """
    Enforces strong password requirements:
    - At least 8 characters
    - At least 1 uppercase letter
    - At least 1 number
    - At least 1 special character
    """
    errors = []

    if len(password) < 8:
        errors.append("at least 8 characters")
    if not re.search(r'[A-Z]', password):
        errors.append("at least 1 uppercase letter")
    if not re.search(r'[0-9]', password):
        errors.append("at least 1 number")
    if not re.search(r'[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;\'`~/]', password):
        errors.append("at least 1 special character (!@#$%...)")

    if errors:
        raise forms.ValidationError(
            "Password must contain: " + ", ".join(errors) + "."
        )


# ─── Registration ──────────────────────────────────────────────────────────────

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}),
        label="Password"
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}),
        label="Confirm Password"
    )

    class Meta:
        model  = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'username':   forms.TextInput(attrs={'class': INPUT_CLASS}),
            'first_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'last_name':  forms.TextInput(attrs={'class': INPUT_CLASS}),
            'email':      forms.EmailInput(attrs={'class': INPUT_CLASS}),
        }

    def clean_password(self):
        password = self.cleaned_data.get('password')
        validate_strong_password(password)
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password  = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')
        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists.")
        return username


# ─── Change Password (logged-in user) ─────────────────────────────────────────

class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}),
        label="Current Password"
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}),
        label="New Password"
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}),
        label="Confirm New Password"
    )

    def clean_new_password(self):
        password = self.cleaned_data.get('new_password')
        validate_strong_password(password)
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password')
        p2 = cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("New passwords do not match.")
        return cleaned_data


# ─── Forgot Password ───────────────────────────────────────────────────────────

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Enter your email',
        }),
        label="Email"
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email, is_active=True).exists():
            raise forms.ValidationError("No active account found with that email.")
        return email


# ─── Reset Password (after OTP verified) ──────────────────────────────────────

class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}),
        label="New Password"
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}),
        label="Confirm New Password"
    )

    def clean_new_password(self):
        password = self.cleaned_data.get('new_password')
        validate_strong_password(password)
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password')
        p2 = cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


# ─── Edit Profile ──────────────────────────────────────────────────────────────

class EditProfileForm(forms.Form):
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'First name',
        })
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Last name',
        })
    )
    bio = forms.CharField(
        required=False,
        max_length=300,
        widget=forms.Textarea(attrs={
            'class': INPUT_CLASS,
            'rows': 3,
            'placeholder': 'Tell us a little about yourself...',
        })
    )
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'accept': 'image/*',
            'id': 'avatar-input',
            'class': INPUT_CLASS,
        })
    )
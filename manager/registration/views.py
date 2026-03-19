from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.core.cache import cache
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.conf import settings
import os
import time
import json
from datetime import date
from google import genai

from .models import OTPToken, Profile
from todo.models import Task
from .forms import (
    UserRegisterForm,
    ChangePasswordForm,
    ForgotPasswordForm,
    ResetPasswordForm,
    EditProfileForm,
)

User = get_user_model()


# ─── Brute-force helpers ───────────────────────────────────────────────────────

MAX_ATTEMPTS = 3
LOCKOUT_TIME = 30  # seconds


def get_client_ip(request):
    """
    Returns the real client IP, respecting a configurable number of trusted
    reverse proxies via TRUSTED_PROXY_COUNT in settings.
    """
    trusted = getattr(settings, 'TRUSTED_PROXY_COUNT', 0)
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if trusted > 0 and x_forwarded:
        ips = [ip.strip() for ip in x_forwarded.split(',')]
        # The real client IP is trusted_count hops from the right
        index = max(len(ips) - trusted, 0)
        return ips[index]
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def get_cache_keys(ip, username):
    return (
        f'login_attempts_{ip}',
        f'lockout_{ip}_{username}',
        f'lockout_time_{ip}_{username}',
    )


def is_locked_out(ip, username):
    _, lockout_key, _ = get_cache_keys(ip, username)
    return cache.get(lockout_key) is not None


def get_lockout_remaining(ip, username):
    _, _, lockout_time_key = get_cache_keys(ip, username)
    locked_at = cache.get(lockout_time_key)
    if locked_at is None:
        return 0
    return max(LOCKOUT_TIME - int(time.time() - locked_at), 0)


def record_failed_attempt(ip, username):
    attempts_key, lockout_key, lockout_time_key = get_cache_keys(ip, username)
    attempts = cache.get(attempts_key, 0) + 1
    cache.set(attempts_key, attempts, LOCKOUT_TIME)
    if attempts >= MAX_ATTEMPTS:
        cache.set(lockout_key, True, LOCKOUT_TIME)
        cache.set(lockout_time_key, time.time(), LOCKOUT_TIME)
    return attempts


def clear_attempts(ip, username):
    attempts_key, lockout_key, lockout_time_key = get_cache_keys(ip, username)
    cache.delete(attempts_key)
    cache.delete(lockout_key)
    cache.delete(lockout_time_key)


# ─── OTP helpers ───────────────────────────────────────────────────────────────

OTP_MAX_ATTEMPTS = 3


def _mask_email(email):
    if '@' not in email:
        return '***'
    local, domain = email.split('@', 1)
    return local[0] + '***@' + domain


# ─── Registration ──────────────────────────────────────────────────────────────

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_active = False
            user.save()

            code = OTPToken.generate_code()
            OTPToken.objects.create(user=user, code=code)

            try:
                send_mail(
                    subject='Verify your Tasklify account',
                    message=(
                        f'Hi {user.username},\n\n'
                        f'Your verification code is: {code}\n\n'
                        f'This code expires in 5 minutes. '
                        f'Do not share it with anyone.'
                    ),
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception:
                pass

            request.session['otp_user_id']      = user.pk
            request.session['otp_masked_email'] = _mask_email(user.email)
            return redirect('verify_otp')
    else:
        form = UserRegisterForm()

    return render(request, 'register/register.html', {'form': form})


# ─── OTP Verification (account activation) ────────────────────────────────────

def verify_otp_view(request):
    user_id = request.session.get('otp_user_id')
    if not user_id:
        return redirect('register')

    masked_email     = request.session.get('otp_masked_email', '***')
    otp_attempts_key = f'otp_attempts_{user_id}'

    if request.method == 'POST':
        entered_code = request.POST.get('otp', '').strip()
        attempts     = cache.get(otp_attempts_key, 0) + 1
        cache.set(otp_attempts_key, attempts, 300)

        if attempts > OTP_MAX_ATTEMPTS:
            try:
                User.objects.get(pk=user_id, is_active=False).delete()
            except User.DoesNotExist:
                pass
            request.session.pop('otp_user_id', None)
            request.session.pop('otp_masked_email', None)
            cache.delete(otp_attempts_key)
            messages.error(request, "Too many invalid attempts. Please register again.")
            return redirect('register')

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return redirect('register')

        token = OTPToken.objects.filter(
            user=user, code=entered_code, is_used=False
        ).last()

        if token and token.is_valid():
            token.is_used = True
            token.save()
            user.is_active = True
            user.save()
            Profile.objects.get_or_create(user=user)
            cache.delete(otp_attempts_key)
            request.session.pop('otp_user_id', None)
            request.session.pop('otp_masked_email', None)
            messages.success(request, "Account verified! You can now log in.")
            return redirect('login')

        elif token and not token.is_valid():
            # OTP expired — invalidate it but do NOT delete the user account.
            # Redirect back to register so they can request a fresh code.
            token.is_used = True
            token.save()
            request.session.pop('otp_user_id', None)
            request.session.pop('otp_masked_email', None)
            cache.delete(otp_attempts_key)
            messages.error(request, "OTP expired. Please register again.")
            return redirect('register')

        else:
            remaining = OTP_MAX_ATTEMPTS - attempts
            return render(request, 'register/verify_otp.html', {
                'error':        f"Invalid code. {max(remaining, 0)} attempt{'s' if remaining != 1 else ''} remaining.",
                'masked_email': masked_email,
            })

    return render(request, 'register/verify_otp.html', {'masked_email': masked_email})


# ─── Login ─────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        ip       = get_client_ip(request)

        if is_locked_out(ip, username):
            remaining      = get_lockout_remaining(ip, username)
            lockout_until  = int((time.time() + remaining) * 1000)
            request.session['login_error']       = "Too many failed attempts. Please wait before trying again."
            request.session['login_locked']      = True
            request.session['lockout_seconds']   = remaining
            request.session['lockout_until_ms']  = lockout_until
            request.session['login_next']        = request.POST.get('next', '')
            return redirect('login')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            clear_attempts(ip, username)
            auth_login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'
            return redirect(next_url)

        attempts           = record_failed_attempt(ip, username)
        remaining_attempts = MAX_ATTEMPTS - attempts

        if remaining_attempts <= 0:
            remaining     = get_lockout_remaining(ip, username)
            lockout_until = int((time.time() + remaining) * 1000)
            request.session['login_error']      = "Too many failed attempts. Please wait before trying again."
            request.session['login_locked']     = True
            request.session['lockout_seconds']  = remaining
            request.session['lockout_until_ms'] = lockout_until
        elif remaining_attempts <= 2:
            request.session['login_error']  = (
                f"Invalid username or password. "
                f"{remaining_attempts} attempt{'s' if remaining_attempts > 1 else ''} remaining."
            )
            request.session['login_locked'] = False
        else:
            request.session['login_error']  = "Invalid username or password."
            request.session['login_locked'] = False

        request.session['login_next'] = request.POST.get('next', '')
        return redirect('login')

    # GET — consume session flash data (PRG pattern)
    error            = request.session.pop('login_error',     None)
    locked           = request.session.pop('login_locked',    False)
    lockout_seconds  = request.session.pop('lockout_seconds', 0)
    lockout_until_ms = request.session.pop('lockout_until_ms', 0)
    next_url         = request.session.pop('login_next', request.GET.get('next', ''))

    return render(request, 'register/login.html', {
        'error':            error,
        'locked':           locked,
        'lockout_seconds':  lockout_seconds,
        'lockout_until_ms': lockout_until_ms,
        'next':             next_url,
        'messages':         messages.get_messages(request),
    })


# ─── Logout ────────────────────────────────────────────────────────────────────

@require_POST
def logout_view(request):
    auth_logout(request)
    messages.success(request, "You've been logged out successfully.")
    return redirect('login')


# ─── Change Password ───────────────────────────────────────────────────────────

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            user = request.user
            if not user.check_password(form.cleaned_data['current_password']):
                form.add_error('current_password', 'Current password is incorrect.')
            else:
                user.set_password(form.cleaned_data['new_password'])
                user.save()
                updated_user = authenticate(
                    request,
                    username=user.username,
                    password=form.cleaned_data['new_password'],
                )
                auth_login(request, updated_user)
                messages.success(request, "Password changed successfully.")
                return redirect('dashboard')
    else:
        form = ChangePasswordForm()

    return render(request, 'register/change_password.html', {'form': form})


# ─── Forgot Password ───────────────────────────────────────────────────────────

def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user  = User.objects.get(email=email, is_active=True)

            OTPToken.objects.filter(
                user=user, purpose=OTPToken.PURPOSE_RESET, is_used=False
            ).update(is_used=True)

            code = OTPToken.generate_code()
            OTPToken.objects.create(user=user, code=code, purpose=OTPToken.PURPOSE_RESET)

            try:
                send_mail(
                    subject='Reset your Tasklify password',
                    message=(
                        f'Hi {user.username},\n\n'
                        f'Your password reset code is: {code}\n\n'
                        f'This code expires in 5 minutes. '
                        f'Do not share it with anyone.\n\n'
                        f'If you did not request this, ignore this email.'
                    ),
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception:
                pass

            request.session['reset_user_id']      = user.pk
            request.session['reset_masked_email'] = _mask_email(user.email)
            return redirect('verify_reset_otp')
    else:
        form = ForgotPasswordForm()

    return render(request, 'register/forgot_password.html', {'form': form})


# ─── Verify Reset OTP ──────────────────────────────────────────────────────────

def verify_reset_otp_view(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('forgot_password')

    masked_email     = request.session.get('reset_masked_email', '***')
    otp_attempts_key = f'reset_otp_attempts_{user_id}'

    if request.method == 'POST':
        entered_code = request.POST.get('otp', '').strip()
        attempts     = cache.get(otp_attempts_key, 0) + 1
        cache.set(otp_attempts_key, attempts, 300)

        if attempts > OTP_MAX_ATTEMPTS:
            request.session.pop('reset_user_id', None)
            request.session.pop('reset_masked_email', None)
            cache.delete(otp_attempts_key)
            messages.error(request, "Too many invalid attempts. Please try again.")
            return redirect('forgot_password')

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return redirect('forgot_password')

        token = OTPToken.objects.filter(
            user=user,
            code=entered_code,
            is_used=False,
            purpose=OTPToken.PURPOSE_RESET,
        ).last()

        if token and token.is_valid():
            token.is_used = True
            token.save()
            cache.delete(otp_attempts_key)
            request.session['reset_verified_user_id'] = user.pk
            request.session.pop('reset_user_id', None)
            request.session.pop('reset_masked_email', None)
            return redirect('reset_password')

        elif token and not token.is_valid():
            token.is_used = True
            token.save()
            request.session.pop('reset_user_id', None)
            request.session.pop('reset_masked_email', None)
            cache.delete(otp_attempts_key)
            messages.error(request, "OTP expired. Please try again.")
            return redirect('forgot_password')

        else:
            remaining = OTP_MAX_ATTEMPTS - attempts
            return render(request, 'register/verify_reset_otp.html', {
                'error':        f"Invalid code. {max(remaining, 0)} attempt{'s' if remaining != 1 else ''} remaining.",
                'masked_email': masked_email,
            })

    return render(request, 'register/verify_reset_otp.html', {'masked_email': masked_email})


# ─── Reset Password ────────────────────────────────────────────────────────────

def reset_password_view(request):
    user_id = request.session.get('reset_verified_user_id')
    if not user_id:
        return redirect('forgot_password')

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return redirect('forgot_password')

            user.set_password(form.cleaned_data['new_password'])
            user.save()
            request.session.pop('reset_verified_user_id', None)
            messages.success(request, "Password reset successfully. You can now log in.")
            return redirect('login')
    else:
        form = ResetPasswordForm()

    return render(request, 'register/reset_password.html', {'form': form})


# ─── Edit Profile ──────────────────────────────────────────────────────────────

@login_required
def edit_profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES)
        if form.is_valid():
            user            = request.user
            user.first_name = form.cleaned_data.get('first_name', '')
            user.last_name  = form.cleaned_data.get('last_name', '')
            user.save()

            profile.bio = form.cleaned_data.get('bio', '')

            avatar = form.cleaned_data.get('avatar')
            if avatar:
                if profile.avatar:
                    try:
                        if os.path.isfile(profile.avatar.path):
                            os.remove(profile.avatar.path)
                    except Exception:
                        pass
                profile.avatar = avatar

            profile.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('edit_profile')
    else:
        form = EditProfileForm(initial={
            'first_name': request.user.first_name,
            'last_name':  request.user.last_name,
            'bio':        profile.bio,
        })

    return render(request, 'registration/edit_profile.html', {
        'form':    form,
        'profile': profile,
    })


# ─── Chatbot ───────────────────────────────────────────────────────────────────

@login_required
@require_POST
def chatbot(request):
    try:
        data         = json.loads(request.body)
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({'reply': 'Please type a message.'})

        tasks = Task.objects.filter(user=request.user, is_completed=False)

        # Sanitise task titles to prevent prompt injection.
        # Truncate each title and strip any characters that could break the prompt.
        def sanitise(title):
            return title[:80].replace('\n', ' ').replace('\r', ' ')

        task_list = ", ".join([sanitise(t.title) for t in tasks]) or "none"

        client   = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=(
                f"You are a helpful task assistant for Tasklify. "
                f"The user's name is {request.user.username}. "
                f"Their pending tasks are: {task_list}. "
                f"Keep responses short, friendly, and helpful. "
                f"User says: {user_message}"
            ),
        )
        return JsonResponse({'reply': response.text})

    except Exception as e:
        err = str(e)
        if '429' in err:
            return JsonResponse({'reply': '⚠️ Too many requests. Please wait a moment.'})
        if '404' in err:
            return JsonResponse({'reply': '⚠️ AI model unavailable. Please try again later.'})
        return JsonResponse({'reply': f'⚠️ Error: {err}'})
import environ
import os
from pathlib import Path

# ─── Base ──────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / '.env')

# ─── Core ──────────────────────────────────────────────────────────────────────

SECRET_KEY = env('SECRET_KEY')
DEBUG      = env.bool('DEBUG')

ALLOWED_HOSTS        = env.list('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost'])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])
SECURE_SSL_REDIRECT  = env.bool('SECURE_SSL_REDIRECT', default=False)

# ─── Apps ──────────────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'registration',
    'todo',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'task.urls'
LOGIN_URL    = 'login'

WSGI_APPLICATION = 'task.wsgi.application'

# ─── Proxy / IP ────────────────────────────────────────────────────────────────
# Set to 1 if behind nginx/Cloudflare, 0 for direct/local deployment
TRUSTED_PROXY_COUNT = env.int('TRUSTED_PROXY_COUNT', default=0)

# ─── Templates ─────────────────────────────────────────────────────────────────

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ─── Database ──────────────────────────────────────────────────────────────────

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ─── Auth ──────────────────────────────────────────────────────────────────────

AUTH_USER_MODEL = 'registration.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── Email ─────────────────────────────────────────────────────────────────────

EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')

# ─── Cache ─────────────────────────────────────────────────────────────────────

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# ─── Security (production) ─────────────────────────────────────────────────────

SECURE_HSTS_SECONDS            = env.int('SECURE_HSTS_SECONDS', default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False)
SESSION_COOKIE_SECURE          = env.bool('SESSION_COOKIE_SECURE', default=False)
CSRF_COOKIE_SECURE             = env.bool('CSRF_COOKIE_SECURE', default=False)

# ─── Internationalisation ──────────────────────────────────────────────────────

LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'
USE_I18N      = True
USE_TZ        = True

# ─── Static & Media ────────────────────────────────────────────────────────────

STATIC_URL  = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL  = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ─── Third-party keys ──────────────────────────────────────────────────────────

GEMINI_API_KEY = env('GEMINI_API_KEY')
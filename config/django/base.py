

import os
from django.core.exceptions import ImproperlyConfigured
from config.env import BASE_DIR, env

env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DJANGO_DEBUG", default=True)

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    "admin_interface",
    "colorfield",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'center.apps.CenterConfig',
    'user.apps.UserConfig',
    'mathfilters',
    'testprogress.apps.TestprogressConfig',
    'inquiry_followup.apps.InquiryFollowupConfig',
    'registration.apps.RegistrationConfig',
    'accounts.apps.AccountsConfig',
    'reports.apps.ReportsConfig',
    'lesson.apps.LessonConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'user.middleware.ForcePasswordChangeMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'user.models.EmailOrPhoneBackend',
]

AUTH_USER_MODEL = 'user.BaseUser'


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE =  'Asia/Kolkata'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

STATICFILES_DIRS = [BASE_DIR / "static"]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240


def _read_text_file(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError as e:
        raise ImproperlyConfigured(f"Missing required file: {path}") from e


# ---- XPSolv Partner Login (mTLS + HS256 JWT) ----
# Store secrets/certs OUTSIDE the repo and load via env/.env.
# Recommended: XPSOLV_JWT_SECRET_FILE points to a file that contains the base64 secret.

XPSOLV_CLIENT_ID = env('XPSOLV_CLIENT_ID', default=None)
XPSOLV_SURFACE = env('XPSOLV_SURFACE', default='A')
XPSOLV_LOGIN_URL = env('XPSOLV_LOGIN_URL', default='https://partner-api.xpsolv.ai/partner/login/init')

_xpsolv_hosts = env('XPSOLV_REDIRECT_HOST_ALLOWLIST', default=None)
if _xpsolv_hosts:
    XPSOLV_REDIRECT_HOST_ALLOWLIST = [h.strip() for h in _xpsolv_hosts.split(',') if h.strip()]
else:
    XPSOLV_REDIRECT_HOST_ALLOWLIST = None

XPSOLV_CERT_PATH = env('XPSOLV_CERT_PATH', default=None)
XPSOLV_KEY_PATH = env('XPSOLV_KEY_PATH', default=None)

XPSOLV_JWT_SECRET_FILE = env('XPSOLV_JWT_SECRET_FILE', default=None)
XPSOLV_JWT_SECRET_B64 = env('XPSOLV_JWT_SECRET_B64', default=None)
if not XPSOLV_JWT_SECRET_B64 and XPSOLV_JWT_SECRET_FILE:
    XPSOLV_JWT_SECRET_B64 = _read_text_file(XPSOLV_JWT_SECRET_FILE)

# Fail fast in non-debug if partially configured.
if not DEBUG:
    any_xpsolv = any([
        XPSOLV_CLIENT_ID,
        XPSOLV_CERT_PATH,
        XPSOLV_KEY_PATH,
        XPSOLV_JWT_SECRET_B64,
    ])
    if any_xpsolv and not all([XPSOLV_CLIENT_ID, XPSOLV_CERT_PATH, XPSOLV_KEY_PATH, XPSOLV_JWT_SECRET_B64]):
        raise ImproperlyConfigured('XPSolv partner login is partially configured; set all required XPSOLV_* settings.')
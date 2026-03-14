from .base import *


from config.env import env

from .base import _read_text_file
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# Tell Django it's behind an HTTPS reverse proxy (nginx)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# Required in Django 4.0+ for HTTPS; derive from ALLOWED_HOSTS automatically
# You can also set CSRF_TRUSTED_ORIGINS explicitly in your .env file
_csrf_env = env.list("CSRF_TRUSTED_ORIGINS", default=[])
CSRF_TRUSTED_ORIGINS = _csrf_env if _csrf_env else [
    f'https://{host}' for host in ALLOWED_HOSTS if host not in ('*', 'localhost', '127.0.0.1')
]


XPSOLV_CLIENT_ID = os.environ.get("XPSOLV_CLIENT_ID", "1345")

XPSOLV_CERT_PATH = env("XPSOLV_CERT_PATH")
XPSOLV_KEY_PATH = env("XPSOLV_KEY_PATH")

XPSOLV_JWT_SECRET_FILE = env(
    "XPSOLV_JWT_SECRET_FILE",
    default=env("XPSOLV_JWT_SECRET_B64_PATH", default=None),
)
XPSOLV_JWT_SECRET_B64 = env("XPSOLV_JWT_SECRET_B64", default=None)
if not XPSOLV_JWT_SECRET_B64 and XPSOLV_JWT_SECRET_FILE:
    XPSOLV_JWT_SECRET_B64 = _read_text_file(XPSOLV_JWT_SECRET_FILE)

XPSOLV_AUD = env("XPSOLV_AUD")
XPSOLV_LOGIN_URL = env("XPSOLV_LOGIN_URL")


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': env("DATABASE_NAME"),
        'USER': env("DATABASE_USER"),
        'PASSWORD': env("DATABASE_PASSWORD"),
        'HOST': env("DATABASE_HOST"),
        'PORT': env.int("DATABASE_PORT", 5432),
    }
}
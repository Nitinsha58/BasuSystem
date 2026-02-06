from .base import *


from config.env import env
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])


XPSOLV_CLIENT_ID = os.environ.get("XPSOLV_CLIENT_ID", "1345")

XPSOLV_CERT_PATH = env("XPSOLV_CERT_PATH")
XPSOLV_KEY_PATH = env("XPSOLV_KEY_PATH")

XPSOLV_JWT_SECRET_FILE = env(
    "XPSOLV_JWT_SECRET_FILE",
    default=env("XPSOLV_JWT_SECRET_B64_PATH", default=None),
)
XPSOLV_JWT_SECRET_B64 = env("XPSOLV_JWT_SECRET_B64", default=None)

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
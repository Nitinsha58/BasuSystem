"""
WSGI config for App project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""
import os
from django.core.wsgi import get_wsgi_application
from config.env import env, BASE_DIR

# Read .env file
env.read_env(os.path.join(BASE_DIR, '.env'))


os.environ.setdefault('DJANGO_SETTINGS_MODULE', env("DJANGO_SETTINGS_MODULE"))

application = get_wsgi_application()

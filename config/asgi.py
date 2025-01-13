
import os
from django.core.asgi import get_asgi_application
from config.env import env, BASE_DIR

env.read_env(os.path.join(BASE_DIR, '.env'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', env("DJANGO_SETTINGS_MODULE"))

application = get_asgi_application()

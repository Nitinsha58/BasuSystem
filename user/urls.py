from django.urls import path
from .views import (
    login_user,
    logout_user,
    change_password,
)


urlpatterns = [
    path('login/', login_user, name="login"),
    path('logout/', logout_user, name="logout"),
    path('change_password/', change_password, name="change_password"),
]
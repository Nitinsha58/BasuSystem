from django.urls import path
from .views import (
    staff_login,
    staff_logout
)


urlpatterns = [
    path('login/', staff_login, name="staff_login"),
    path('logout/', staff_logout, name="staff_logout"),
]
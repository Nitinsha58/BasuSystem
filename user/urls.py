from django.urls import path
from .views import (
    staff_login, 
)


urlpatterns = [
    path('login/', staff_login, name="staff_login"),
]
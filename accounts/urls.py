from django.urls import path
from .views import (
    installments
)

urlpatterns = [
    path("installments", installments, name="installments"),
]
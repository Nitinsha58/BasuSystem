from django.urls import path
from . import api_views

urlpatterns = [
    path('paper/<str:token>/', api_views.PaperDetailAPI.as_view()),
    path('start/<str:token>/', api_views.StartAttemptAPI.as_view()),
    path('submit/<str:token>/', api_views.SubmitAttemptAPI.as_view()),
]

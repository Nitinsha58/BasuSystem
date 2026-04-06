from django.urls import path
from . import api_views

urlpatterns = [
    path('paper/<str:token>/', api_views.PaperDetailAPI.as_view()),
    path('start/<str:token>/', api_views.StartAttemptAPI.as_view()),
    path('submit/<str:token>/', api_views.SubmitAttemptAPI.as_view()),
    path('question/<str:token>/<int:index>/', api_views.QuestionDetailAPI.as_view()),
    path('answer/<str:token>/', api_views.SaveAnswerAPI.as_view()),
    path('log-event/<str:token>/', api_views.LogEventAPI.as_view()),
]

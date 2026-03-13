from django.urls import path
from . import views
from . import api_views

app_name = 'sat'

urlpatterns = [
    # Paper management
    path('papers/', views.paper_list, name='paper_list'),
    path('papers/create/', views.paper_create, name='paper_create'),
    path('papers/<int:pk>/', views.paper_detail, name='paper_detail'),
    path('papers/<int:pk>/delete/', views.paper_delete, name='paper_delete'),

    # Assignment management
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/create/', views.assignment_create, name='assignment_create'),
    path('assignments/<int:pk>/', views.assignment_detail, name='assignment_detail'),
    path('assignments/<int:pk>/reset/', views.assignment_reset, name='assignment_reset'),

    # Result management
    path('results/', views.result_list, name='result_list'),
    path('results/<int:pk>/', views.result_detail, name='result_detail'),

    # Report (public shareable link)
    path('report/<str:report_token>/', views.report_view, name='report'),

    # DRF API
    path('api/paper/<str:token>/', api_views.PaperDetailAPI.as_view(), name='api_paper'),
    path('api/start/<str:token>/', api_views.StartAttemptAPI.as_view(), name='api_start'),
    path('api/submit/<str:token>/', api_views.SubmitAttemptAPI.as_view(), name='api_submit'),
]

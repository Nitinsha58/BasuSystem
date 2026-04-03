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
    path('papers/<int:pk>/reevaluate/', views.paper_reevaluate, name='paper_reevaluate'),

    # Assignment management
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/create/', views.assignment_create, name='assignment_create'),
    path('assignments/<int:pk>/', views.assignment_detail, name='assignment_detail'),
    path('assignments/<int:pk>/reset/', views.assignment_reset, name='assignment_reset'),

    # Result management
    path('results/', views.result_list, name='result_list'),
    path('results/<int:pk>/', views.result_detail, name='result_detail'),
    path('results/<int:pk>/delete/', views.result_delete, name='result_delete'),

    # Report (public shareable link)
    path('report/<str:report_token>/', views.report_view, name='report'),

    # School session management
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/create/', views.session_create, name='session_create'),
    path('sessions/<int:pk>/', views.session_detail, name='session_detail'),
    path('sessions/<int:pk>/toggle/', views.session_toggle, name='session_toggle'),
    path('sessions/<int:pk>/delete/', views.session_delete, name='session_delete'),

    # School kiosk (public self-registration for school visits)
    path('school/<str:session_code>/', views.school_kiosk, name='school_kiosk'),

    # DRF API
    path('api/paper/<str:token>/', api_views.PaperDetailAPI.as_view(), name='api_paper'),
    path('api/start/<str:token>/', api_views.StartAttemptAPI.as_view(), name='api_start'),
    path('api/submit/<str:token>/', api_views.SubmitAttemptAPI.as_view(), name='api_submit'),
]

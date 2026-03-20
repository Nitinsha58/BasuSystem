from django.urls import path
from . import views

app_name = 'marketing'

urlpatterns = [
    path('campaigns/', views.campaign_list, name='campaign_list'),
    path('campaigns/new/', views.campaign_create, name='campaign_create'),
    path('campaigns/<int:campaign_id>/', views.campaign_detail, name='campaign_detail'),
    path('campaigns/<int:campaign_id>/edit/', views.campaign_edit, name='campaign_edit'),
    path('campaigns/<int:campaign_id>/bulk-inquiries/', views.bulk_create_inquiries, name='bulk_create_inquiries'),
]

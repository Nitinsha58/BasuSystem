from django.urls import path
from .views import (
    create_inquiry, 
    inquiries,
    inquiry, 
    update_followup, 
    create_followup, 
    delete_followup, 
    delete_inquiry, 
    search_inquiries,
    create_referral_inquiry,
)

urlpatterns = [
    path('search-inquiries/', search_inquiries, name='search_inquiries'),
    path('inquiry', create_inquiry, name='create_inquiry'),
    path('partner/referral', create_referral_inquiry, name='create_referral_inquiry'),
    path('inquiries', inquiries, name='inquiries'),
    path('inquiries/<int:inquiry_id>', inquiry, name='inquiry'),
    path('create-followup/<int:inquiry_id>/', create_followup, name='create_followup'),
    path('update-followup/<int:inquiry_id>/<int:followup_id>', update_followup, name='update_followup'),
    path('delete-followup/<int:inquiry_id>/<int:followup_id>', delete_followup, name='delete_followup'),
    path('delete-inquiry/<int:inquiry_id>/', delete_inquiry, name='delete_inquiry'),
]
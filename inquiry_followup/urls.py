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
    check_inquiry_phone,
    create_referral_inquiry,
    stationary_partner_inquiries,
    inquiry_stats,
    bulk_assign_campaign,
    add_leads,
    quick_update_inquiry,
)

urlpatterns = [
    path('search-inquiries/', search_inquiries, name='search_inquiries'),
    path('check-inquiry-phone/', check_inquiry_phone, name='check_inquiry_phone'),
    path('inquiry', create_inquiry, name='create_inquiry'),
    path('partner/referral', create_referral_inquiry, name='create_referral_inquiry'),
    path('inquiries', inquiries, name='inquiries'),
    path('inquiries/stats', inquiry_stats, name='inquiry_stats'),
    path('inquiries/<int:inquiry_id>', inquiry, name='inquiry'),
    path('create-followup/<int:inquiry_id>/', create_followup, name='create_followup'),
    path('update-followup/<int:inquiry_id>/<int:followup_id>', update_followup, name='update_followup'),
    path('delete-followup/<int:inquiry_id>/<int:followup_id>', delete_followup, name='delete_followup'),
    path('delete-inquiry/<int:inquiry_id>/', delete_inquiry, name='delete_inquiry'),

    path('partner-inquiries/<int:partner_id>/', stationary_partner_inquiries, name='partner_inquiry'),
    path('inquiries/bulk-assign-campaign', bulk_assign_campaign, name='bulk_assign_campaign'),
    path('inquiries/add-leads/', add_leads, name='add_leads'),
    path('inquiries/<int:inquiry_id>/quick-update/', quick_update_inquiry, name='quick_update_inquiry'),
]
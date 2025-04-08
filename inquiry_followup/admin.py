from django.contrib import admin
from .forms import AdmissionCounselorForm, StationaryPartnerForm
from .models import AdmissionCounselor, Inquiry, FollowUpStatus, FollowUp, Referral, StationaryPartner

class AdmissionCounselorAdmin(admin.ModelAdmin):
    form = AdmissionCounselorForm
    list_display = ['user', 'center', 'created_at', 'updated_at']

class StationaryPartnerAdmin(admin.ModelAdmin):
    form = StationaryPartnerForm
    list_display = ['name', 'user__first_name', 'user__phone', 'address', 'created_at']

admin.site.register(AdmissionCounselor, AdmissionCounselorAdmin)
admin.site.register(StationaryPartner, StationaryPartnerAdmin)
admin.site.register(Inquiry)
admin.site.register(FollowUpStatus)
admin.site.register(FollowUp)
admin.site.register(Referral)
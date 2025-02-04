from django.contrib import admin
from .forms import AdmissionCounselorForm
from .models import AdmissionCounselor, Inquiry, FollowUpStatus, FollowUp, Referral

class AdmissionCounselorAdmin(admin.ModelAdmin):
    form = AdmissionCounselorForm
    list_display = ['user', 'center', 'created_at', 'updated_at']

admin.site.register(AdmissionCounselor, AdmissionCounselorAdmin)
admin.site.register(Inquiry)
admin.site.register(FollowUpStatus)
admin.site.register(FollowUp)
admin.site.register(Referral)
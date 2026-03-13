from django.contrib import admin
from .forms import AdmissionCounselorForm, StationaryPartnerForm
from .models import AdmissionCounselor, Inquiry, FollowUpStatus, FollowUp, Referral, StationaryPartner


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = [
        'student_name',
        'phone',
        'school',
        'lead_type',
        'existing_member',
        'session',
        'referral',
        'stationary_partner',
        'get_classes',
        'get_subjects',
        'created_at',
        'updated_at',
    ]
    list_filter = [
        'lead_type',
        'existing_member',
        ('session', admin.RelatedOnlyFieldListFilter),
        ('referral', admin.RelatedOnlyFieldListFilter),
        ('stationary_partner', admin.RelatedOnlyFieldListFilter),
        ('classes', admin.RelatedOnlyFieldListFilter),
        ('subjects', admin.RelatedOnlyFieldListFilter),
        ('created_at', admin.DateFieldListFilter),
        ('updated_at', admin.DateFieldListFilter),
    ]
    search_fields = [
        'student_name',
        'phone',
        'school',
        'address',
        'referral__name',
        'stationary_partner__name',
        'stationary_partner__user__first_name',
        'stationary_partner__user__last_name',
        'stationary_partner__user__phone',
        'session__name',
        'classes__name',
        'subjects__name',
    ]
    list_select_related = ['referral', 'stationary_partner', 'session']
    filter_horizontal = ['classes', 'subjects']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 50

    @admin.display(description='Classes')
    def get_classes(self, obj):
        return ', '.join(obj.classes.values_list('name', flat=True))

    @admin.display(description='Subjects')
    def get_subjects(self, obj):
        return ', '.join(obj.subjects.values_list('name', flat=True))

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('classes', 'subjects')

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        # Search includes M2M fields (classes/subjects), so we need DISTINCT.
        return queryset.distinct(), True

class AdmissionCounselorAdmin(admin.ModelAdmin):
    form = AdmissionCounselorForm
    list_display = ['user', 'center', 'created_at', 'updated_at']

class StationaryPartnerAdmin(admin.ModelAdmin):
    form = StationaryPartnerForm
    list_display = ['name', 'get_user_name', 'get_user_phone', 'center', 'is_active', 'address', 'created_at', 'updated_at']
    list_filter = ['is_active', ('center', admin.RelatedOnlyFieldListFilter), ('created_at', admin.DateFieldListFilter)]
    search_fields = ['name', 'address', 'user__first_name', 'user__last_name', 'user__phone', 'center__name']
    list_select_related = ['user', 'center']

    @admin.display(description='User')
    def get_user_name(self, obj):
        full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        return full_name or obj.user.phone

    @admin.display(description='Phone')
    def get_user_phone(self, obj):
        return obj.user.phone

admin.site.register(AdmissionCounselor, AdmissionCounselorAdmin)
admin.site.register(StationaryPartner, StationaryPartnerAdmin)
admin.site.register(FollowUpStatus)
admin.site.register(FollowUp)
admin.site.register(Referral)
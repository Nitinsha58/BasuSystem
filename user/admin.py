from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Q
from .models import BaseUser

class CustomUserAdmin(UserAdmin):
    model = BaseUser
    list_display = ['first_name', 'last_name', 'phone', 'is_staff', 'is_active']
    ordering = ['phone']
    search_fields = ['phone', 'first_name', 'last_name']

    fieldsets = (
        (None, {'fields': ('first_name', 'last_name', 'phone', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),  # Removed 'date_joined'
    )

    readonly_fields = ('date_joined', 'last_login')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'phone', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        queryset |= self.model.objects.filter(Q(phone__icontains=search_term))
        return queryset, use_distinct

admin.site.register(BaseUser, CustomUserAdmin)

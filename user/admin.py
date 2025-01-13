from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from .models import BaseUser

class CustomUserAdmin(UserAdmin):
    model = BaseUser
    list_display = ['first_name','last_name', 'phone', 'is_staff', 'is_active']
    ordering=['phone']
    fieldsets = (
        (None, {'fields': ('first_name','last_name','phone', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name','last_name', 'phone', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

admin.site.register(BaseUser, CustomUserAdmin)
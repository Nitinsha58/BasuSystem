from django.contrib import admin
from .models import Student, ParentDetails, FeeDetails, Installment, TransportDetails, Batch, Teacher, Attendance, Homework
from .forms import TeacherForm
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError

class TeacherAdmin(admin.ModelAdmin):
    form = TeacherForm
    list_display = ['user', 'created_at', 'updated_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__phone', 'batch__class_name__name',
        'batch__section__name',
        'batch__subject__name']

class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'batch', 'is_present', 'created_at']
    search_fields = [
        'student__user__first_name', 
        'student__user__last_name', 
        'student__user__phone', 
        'batch__class_name__name',
        'batch__section__name',
        'batch__subject__name'
    ]

class StudentAdmin(admin.ModelAdmin):
    list_display = ['user__first_name', 'user__last_name', 'created_at', 'updated_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__phone', 'batches__class_name__name',
        'batches__section__name',
        'batches__subject__name']
    list_filter = ['batches__class_name', 'batches__section', 'batches__subject']
    ordering = ['user__first_name', 'user__last_name']

admin.site.register(Student, StudentAdmin)
admin.site.register(ParentDetails)
admin.site.register(FeeDetails)
admin.site.register(Installment)
admin.site.register(TransportDetails)
admin.site.register(Batch)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(Homework)
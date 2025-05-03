from django.contrib import admin
from .models import (
    Student, 
    ParentDetails, 
    FeeDetails, 
    Installment, 
    TransportDetails, 
    Batch, 
    Teacher, 
    Attendance, 
    Homework, 
    Chapter,
    Test,
    TestQuestion,
    Remark,
    RemarkCount,
    Day,
    Mentor,
    Mentorship,
    MentorReview,
    )
from .forms import TeacherForm, MentorForm

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

class ChapterAdmin(admin.ModelAdmin):
    list_display = ['chapter_name', 'subject', 'class_name', 'created_at', 'updated_at']
    search_fields = ['chapter_name', 'chapter_no' 'subject__name', 'class_name']
    list_filter = ['subject', 'class_name']
    ordering = ['created_at']

class HomeworkAdmin(admin.ModelAdmin):
    list_display = ['student__user__first_name', 'batch', 'status', 'created_at', 'updated_at']
    search_fields = ['batch__class_name__name', 'batch__section__name', 'batch__subject__name',]
    list_filter = ['batch', 'status']
    ordering = ['created_at']

class BatchAdmin(admin.ModelAdmin):
    def days_display(self, obj):
        return ", ".join([day.name for day in obj.days.all()])
    days_display.short_description = 'Days'

    def combined_time(self, obj):
        return f"{obj.start_time} - {obj.end_time}"
    combined_time.short_description = 'Time'

    list_display = ['class_name', 'section', 'subject', 'combined_time', 'days_display']
    search_fields = ['class_name__name', 'section__name', 'subject__name']
    list_filter = ['class_name', 'section', 'subject']
    ordering = ['class_name__name', 'section__name', 'subject__name']

class MentorAdmin(admin.ModelAdmin):
    form = MentorForm
    list_display = ['user', 'user__first_name', 'user__last_name', 'created_at']


admin.site.register(Student, StudentAdmin)
admin.site.register(ParentDetails)
admin.site.register(FeeDetails)
admin.site.register(Installment)
admin.site.register(TransportDetails)
admin.site.register(Batch, BatchAdmin)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(Homework, HomeworkAdmin)
admin.site.register(Chapter, ChapterAdmin)
admin.site.register(Test)
admin.site.register(TestQuestion)
admin.site.register(Remark)
admin.site.register(RemarkCount)
admin.site.register(Day)
admin.site.register(Mentor, MentorAdmin)
admin.site.register(Mentorship)
admin.site.register(MentorReview)


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
    TransportMode,
    TransportPerson,
    ReportPeriod,

    MentorRemark,
    Action,
    ActionSuggested,
    TransportAttendance,

    Recommendation,
    ReportNegative,
    ReportPositive,
    StudentBatchLink,
    StudentTestRemark,
    StudentRemark,
    AcademicSession,
    StudentEnrollment,
    )
from .forms import TeacherForm, MentorForm
import csv
from django.http import HttpResponse

class TeacherAdmin(admin.ModelAdmin):
    form = TeacherForm
    list_display = ['user', 'created_at', 'updated_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__phone', 'batch__class_name__name',
        'batch__section__name',
        'batch__subject__name']

class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'batch', 'is_present', 'date', 'created_at']
    search_fields = [
        'student__user__first_name', 
        'student__user__last_name', 
        'student__user__phone', 
        'batch__class_name__name',
        'batch__section__name',
        'batch__subject__name'
    ]
    list_filter = ['batch', 'is_present', 'type']
    

class StudentAdmin(admin.ModelAdmin):
    list_display = [
        'user_full_name', 'email', 'user__phone', 'gender', 'dob', 'doj', 'school_name',
        'class_enrolled', 'course', 'program_duration', 'marksheet_submitted', 'sat_score',
        'active', 'created_at', 'updated_at'
    ]
    search_fields = [
        'user__first_name', 'user__last_name', 'user__phone', 'email',
        'school_name', 'aadhar_card_number'
    ]
    list_filter = [
        'gender', 'course', 'program_duration', 'class_enrolled',
        'marksheet_submitted', 'active', 'created_at'
    ]
    ordering = ['user__first_name', 'user__last_name']
    actions = ['export_students_csv']
    list_per_page = 500

    def user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    user_full_name.short_description = "Name"

    def export_students_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="students_by_class.csv"'
        writer = csv.writer(response)
        
        # Write header
        writer.writerow(['Student Name', 'Phone', 'Mother', 'Father'])

        for student in queryset.select_related('user').prefetch_related('batches__class_name'):
            writer.writerow([
            f"{student.user.first_name} {student.user.last_name}",
            student.user.phone or '',
            student.parent_details.mother_contact or '', 
            student.parent_details.father_contact or '',
            ])

        return response
    
    def export_students_with_subject_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="students_with_subjects.csv"'
        writer = csv.writer(response)

        # Write header
        writer.writerow(['Student Name', 'Phone', 'Mother', 'Father', 'Subjects'])

        for student in queryset.select_related('user').prefetch_related('batches__subject'):
            subjects = set()
            for batch in student.batches.all():
                if batch.subject and batch.subject.name:
                    subjects.add(batch.subject.name)
            writer.writerow([
                f"{student.user.first_name} {student.user.last_name}",
                student.user.phone or '',
                student.parent_details.mother_contact or '', 
                student.parent_details.father_contact or '',
                ",".join(subjects)
            ])

        return response

    def export_students_with_section_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="students_with_sections.csv"'
        writer = csv.writer(response)

        # Write header
        writer.writerow(['Student Name', 'Phone', 'Mother', 'Father', 'Classes', 'Sections (Section - Subject)'])

        for student in queryset.select_related('user').prefetch_related('batches__class_name', 'batches__section', 'batches__subject'):
            classes = set()
            sections = set()
            for batch in student.batches.all():
                # Collect class names
                if batch.class_name and batch.class_name.name:
                    classes.add(batch.class_name.name)
                # Collect section-subject combinations
                section_name = batch.section.name if batch.section and batch.section.name else ''
                subject_name = batch.subject.name if batch.subject and batch.subject.name else ''
                if section_name or subject_name:
                    combined = f"{section_name} - {subject_name}" if section_name and subject_name else section_name or subject_name
                    sections.add(combined)
            writer.writerow([
                f"{student.user.first_name} {student.user.last_name}",
                student.user.phone or '',
                student.parent_details.mother_contact or '',
                student.parent_details.father_contact or '',
                ",".join(classes),
                ",".join(sections)
            ])

        return response

    def export_mentor_students(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="mentor_students.csv"'
        writer = csv.writer(response)

        # Write header
        writer.writerow(['Mentor Name', 'Student Name', 'Phone'])

        for student in queryset.select_related('user', 'parent_details').prefetch_related('mentorships__mentor__user'):
            for mentorship in student.mentorships.filter(active=True):
                mentor = mentorship.mentor
                if mentor:
                    writer.writerow([
                        f"{mentor.user.first_name} {mentor.user.last_name}",
                        f"{student.user.first_name} {student.user.last_name}",
                        student.parent_details.mother_contact or student.parent_details.father_contact or student.user.phone or ''
                    ])

        return response
    
    def export_students_in_detail(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="students_detailed.csv"'
        writer = csv.writer(response)

        # Write header
        writer.writerow(['Student Name', 'Class', 'Batch', 'Subject', 'School Name', 'Phone', 'Mother Phone', 'Father Phone', 'Status'])

        for student in queryset.select_related('user').prefetch_related('batches__class_name', 'batches__subject'):
            batches_info = []
            for batch in student.batches.all():
                subject_name = batch.subject.name + "-" + batch.section.name if batch.subject else ''
                batches_info.append(f"{subject_name}")
            writer.writerow([
                f"{student.user.first_name} {student.user.last_name}",
                ", ".join(set(batch.class_name.name for batch in student.batches.all() if batch.class_name)),
                ", ".join(batches_info),
                ", ".join(set(batch.subject.name for batch in student.batches.all() if batch.subject)),
                student.school_name or '',
                student.user.phone or '',
                student.parent_details.mother_contact or '',
                student.parent_details.father_contact or '',
                'Active' if student.active else 'Inactive'
            ])

        return response
    
    export_mentor_students.short_description = "Export mentor-student as CSV"
    actions.append('export_mentor_students')

    export_students_in_detail.short_description = "Export students in detail as CSV"
    actions.append('export_students_in_detail')

    export_students_with_section_csv.short_description = "Export students with classes and sections (Section - Subject) as CSV"
    actions.append('export_students_with_section_csv')

    export_students_with_subject_csv.short_description = "Export students with subjects as CSV"
    actions.append('export_students_with_subject_csv')

    export_students_csv.short_description = "Export students as CSV"

class ChapterAdmin(admin.ModelAdmin):
    list_display = ['chapter_name', 'subject', 'class_name', 'created_at', 'updated_at']
    search_fields = ['chapter_name', 'chapter_no' 'subject__name', 'class_name']
    list_filter = ['subject', 'class_name']
    ordering = ['created_at']

class HomeworkAdmin(admin.ModelAdmin):
    list_display = ['student__user__first_name', 'batch', 'status', 'date', 'created_at', 'updated_at']
    search_fields = ['batch__class_name__name', 'batch__section__name', 'batch__subject__name', 'student__user__first_name', 'student__user__last_name', 'student__user__phone']
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


class ReportPeriodAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date']
    search_fields = ['name']
    ordering = ['start_date']

class MentorRemarkAdmin(admin.ModelAdmin):
    list_display = ['mentor', 'student', 'mentor_remark', 'created_at']
    search_fields = ['mentor__user__first_name', 'mentor__user__last_name', 'student__user__first_name', 'student__user__last_name']
    list_filter = ['mentor', 'student']
    ordering = ['created_at']

class StudentRemarkAdmin(admin.ModelAdmin):
    list_display = ['student', 'added_by', 'remark', 'created_at']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'added_by__first_name', 'added_by__last_name']
    list_filter = ['student', 'added_by']
    ordering = ['created_at']

class ActionAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['created_at']

class ActionSuggestedAdmin(admin.ModelAdmin):
    list_display = ['student', 'batch', 'created_at']
    list_filter = ['action']
    ordering = ['created_at']


class ReportNegativeAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['created_at']

class ReportPositiveAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['created_at']

class MentorshipAdmin(admin.ModelAdmin):
    list_display = ['mentor_name', 'student_name', 'active', 'created_at', 'updated_at']
    list_filter = ['active', 'mentor', 'student']
    search_fields = [
        'mentor__user__first_name', 'mentor__user__last_name',
        'student__user__first_name', 'student__user__last_name'
    ]
    ordering = ['-created_at', '-updated_at']

    def mentor_name(self, obj):
        return f"{obj.mentor.user.first_name} {obj.mentor.user.last_name}"
    mentor_name.short_description = "Mentor"

    def student_name(self, obj):
        return f"{obj.student.user.first_name} {obj.student.user.last_name}"
    student_name.short_description = "Student"

class TransportAttendanceAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'is_present', 'date', 'time', 'action', 'created_at', 'updated_at']
    search_fields = [
        'student__user__first_name',
        'student__user__last_name',
        'student__user__phone'
    ]
    list_filter = ['is_present', 'date', 'time', 'action']
    ordering = ['-date', '-created_at']

    def student_name(self, obj):
        return f"{obj.student.user.first_name} {obj.student.user.last_name}"
    student_name.short_description = "Student"

class StudentBatchLinkAdmin(admin.ModelAdmin):
    list_display = ['student', 'batch', 'active', 'joined_at']
    search_fields = [
        'student__user__first_name',
        'student__user__last_name',
        'batch__class_name__name',
        'batch__section__name',
        'batch__subject__name'
    ]
    list_filter = ['active', 'batch']
    ordering = ['-joined_at']


class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "is_active")
    list_filter = ("is_active",)
    ordering = ("-start_date",)

    actions = ["make_active"]

    def make_active(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(
                request,
                "Please select exactly one session.",
                level="error"
            )
            return
        session = queryset.first()
        session.activate()

    make_active.short_description = "Mark selected session as active"


class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "session",
        "class_name",
        "course",
        "active"
    )
    list_filter = ("session", "active", "class_name")
    search_fields = ("student__user__first_name", "student__user__phone")


admin.site.register(StudentEnrollment, StudentEnrollmentAdmin)
admin.site.register(AcademicSession, AcademicSessionAdmin)
admin.site.register(StudentTestRemark)
admin.site.register(Recommendation)
admin.site.register(TransportAttendance, TransportAttendanceAdmin)
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
admin.site.register(Mentorship, MentorshipAdmin)
admin.site.register(TransportMode)
admin.site.register(TransportPerson)
admin.site.register(ReportPeriod, ReportPeriodAdmin)

admin.site.register(MentorRemark, MentorRemarkAdmin)
admin.site.register(Action, ActionAdmin)
admin.site.register(ActionSuggested, ActionSuggestedAdmin)

admin.site.register(ReportNegative, ReportNegativeAdmin)
admin.site.register(ReportPositive, ReportPositiveAdmin)

admin.site.register(StudentBatchLink, StudentBatchLinkAdmin)
admin.site.register(StudentRemark, StudentRemarkAdmin)
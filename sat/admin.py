from django.contrib import admin
from django.utils.html import format_html
from .models import TestPaper, Question, TestAssignment, TestAttempt, QuestionResponse, TestResult, SchoolTestSession


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ('order', 'text', 'option_a', 'option_b', 'option_c', 'option_d',
               'correct_answer', 'difficulty', 'subject_tag')


@admin.register(TestPaper)
class TestPaperAdmin(admin.ModelAdmin):
    list_display = ('title', 'class_name', 'time_limit', 'marks_per_correct', 'created_at')
    inlines = [QuestionInline]


@admin.register(SchoolTestSession)
class SchoolTestSessionAdmin(admin.ModelAdmin):
    list_display = ('school_name', 'paper', 'campaign', 'date', 'session_code', 'is_active', 'created_at')
    list_filter = ('is_active', 'campaign')
    readonly_fields = ('session_code',)
    ordering = ('-date',)


@admin.register(TestAssignment)
class TestAssignmentAdmin(admin.ModelAdmin):
    list_display = ('inquiry', 'paper', 'school_session', 'token', 'deadline', 'auto_release', 'created_at')
    readonly_fields = ('token',)


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = (
        'assignment', 'started_at', 'submitted_at',
        'integrity_badge', 'tab_switch_count', 'fullscreen_exit_count',
        'auto_submitted', 'late_by_seconds',
    )
    readonly_fields = (
        'started_at', 'tab_switch_count', 'fullscreen_exit_count',
        'auto_submitted', 'late_by_seconds', 'question_order',
    )
    list_filter = ('auto_submitted',)

    @admin.display(description='Integrity')
    def integrity_badge(self, obj):
        badges = []
        if obj.auto_submitted:
            badges.append('<span style="background:#f97316;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">Auto-submitted</span>')
        if obj.late_by_seconds is not None and obj.late_by_seconds > 0:
            badges.append(f'<span style="background:#ef4444;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">Late +{obj.late_by_seconds}s</span>')
        if obj.tab_switch_count > 0 or obj.fullscreen_exit_count > 0:
            badges.append('<span style="background:#eab308;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">Suspicious</span>')
        if not badges:
            return format_html('<span style="color:#6b7280;font-size:11px;">Clean</span>')
        return format_html(' '.join(badges))


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'total_marks', 'max_marks', 'visibility', 'report_token', 'created_at')
    readonly_fields = ('report_token',)

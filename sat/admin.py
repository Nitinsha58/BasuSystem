from django.contrib import admin
from .models import TestPaper, Question, TestAssignment, TestAttempt, QuestionResponse, TestResult


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ('order', 'text', 'option_a', 'option_b', 'option_c', 'option_d',
               'correct_answer', 'difficulty', 'subject_tag')


@admin.register(TestPaper)
class TestPaperAdmin(admin.ModelAdmin):
    list_display = ('title', 'class_name', 'time_limit', 'marks_per_correct', 'created_at')
    inlines = [QuestionInline]


@admin.register(TestAssignment)
class TestAssignmentAdmin(admin.ModelAdmin):
    list_display = ('inquiry', 'paper', 'token', 'deadline', 'auto_release', 'created_at')
    readonly_fields = ('token',)


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'total_marks', 'max_marks', 'visibility', 'report_token', 'created_at')
    readonly_fields = ('report_token',)

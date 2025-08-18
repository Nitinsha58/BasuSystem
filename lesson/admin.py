from django.contrib import admin
from .models import ChapterSequence, Lesson, Holiday, Lecture, LectureMismatch, LectureDate

@admin.register(LectureMismatch)
class LectureMismatchAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'reason', 'date', 'created_at')
    list_filter = ('reason', 'date')
    search_fields = ('lesson__topic', 'reason')
    ordering = ('-date',)

@admin.register(LectureDate)
class LectureDateAdmin(admin.ModelAdmin):
    list_display = ('batch', 'date')
    list_filter = ('batch__class_name', 'batch__subject', 'batch__section')
    search_fields = ('batch__name',)
    ordering = ('batch', 'date')

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'date')
    search_fields = ('name',)
    ordering = ('date',)

@admin.register(ChapterSequence)
class ChapterSequenceAdmin(admin.ModelAdmin):
    list_display = ('batch', 'chapter_no', 'sequence')
    list_filter = ('batch__class_name', 'batch__subject', 'batch__section')
    search_fields = ('batch__name', 'chapter_name')
    ordering = ('batch', 'sequence')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('batch')
        
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('chapter_sequence', 'sequence', 'topic')
    list_filter = ('chapter_sequence__batch',)
    search_fields = ('topic', 'chapter_sequence__batch__name', 'chapter_sequence__chapter_name')
    ordering = ('chapter_sequence__sequence', 'sequence')


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_diaplay = ('lesson', 'date', 'status')
    list_filter = ('lesson', 'status')
    search_fields = ('lesson__topic', 'lesson__chapter_sequence__chapter_name')


from django.db import models
from registration.models import Batch, Chapter, Teacher
from django.db.models import Q

class ChapterSequence(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='chapter_sequences')

    chapter_no = models.IntegerField(null=True, blank=True)
    chapter_name = models.CharField(max_length=255, null=True, blank=True)

    sequence = models.PositiveIntegerField()

    class Meta:
        ordering = ['batch', 'sequence']

    def __str__(self):
        return f"{self.batch} - {self.chapter_no} -  {self.chapter_name} (Sequence: {self.sequence})"

class Lesson(models.Model):
    chapter_sequence = models.ForeignKey(ChapterSequence, on_delete=models.CASCADE, related_name='lessons')
    sequence = models.PositiveIntegerField()
    topic = models.CharField(max_length=255)
    homework = models.TextField(null=True, blank=True)
    classwork = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['chapter_sequence__sequence', 'sequence']

    def next(self):
        return Lesson.objects.filter(
            chapter_sequence__batch=self.chapter_sequence.batch,
            chapter_sequence__sequence__gte=self.chapter_sequence.sequence,
        ).filter(
            Q(chapter_sequence__sequence__gt=self.chapter_sequence.sequence) |
            Q(sequence__gt=self.sequence)
        ).order_by(
            'chapter_sequence__sequence',
            'sequence'
        ).first()

    def __str__(self):
        return f"{self.chapter_sequence.chapter_no}. {self.chapter_sequence.chapter_name} - {self.topic}"

class Lecture(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='lectures')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    class Meta:
        ordering = ['-date', 'lesson__chapter_sequence__sequence', 'lesson__sequence']

    def __str__(self):
        return f"Lecture for {self.lesson.topic} on {self.date} ({self.status})"

class Holiday(models.Model):
    name = models.CharField(max_length=255,null=True, blank=True)
    date = models.DateField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.date}"


class LectureDate(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='lecture_dates')
    date = models.DateField()
    
    class Meta:
        unique_together = ('batch', 'date')
        ordering = ['batch', 'date']

    def __str__(self):
        return f"{self.batch} - {self.date}"

class LectureMismatch(models.Model):
    REASON_CHOICES = [
        ('Cancelled', 'Cancelled'), 
        ('Substitute', 'Substitute'),
        ('Extra Class', 'Extra Class'),
        ('Other', 'Other'),
    ]

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='mismatches')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    remark = models.TextField(null=True, blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
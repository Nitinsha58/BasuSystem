from django.db import models
from registration.models import Batch, Chapter

class ChapterSequence(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='chapter_sequences')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='chapter_sequences')
    sequence = models.PositiveIntegerField()

    class Meta:
        unique_together = ('batch', 'chapter', 'sequence')
        ordering = ['batch', 'sequence']

    def __str__(self):
        return f"{self.batch} - {self.chapter} (Sequence: {self.sequence})"

class Lesson(models.Model):
    chapter_sequence = models.ForeignKey(ChapterSequence, on_delete=models.CASCADE, related_name='lessons')
    sequence = models.PositiveIntegerField()
    topic = models.CharField(max_length=255)
    homework = models.TextField(null=True, blank=True)
    classwork = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['chapter_sequence__sequence', 'sequence']
    

class Holiday(models.Model):
    name = models.CharField(max_length=255,null=True, blank=True)
    date = models.DateField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.date}"

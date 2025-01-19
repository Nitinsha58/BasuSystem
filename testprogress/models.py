from django.db import models
from colorfield.fields import ColorField

class TestStatus(models.Model):
    """
    Model to store possible statuses for a test.
    Example statuses: 'Scheduled', 'Completed', 'Postponed', etc.
    """
    name = models.CharField(max_length=50, unique=True, help_text="Status name (e.g., Scheduled, Completed)")
    description = models.TextField(blank=True, help_text="Optional description of the status")
    color = ColorField(null=True, blank=True, verbose_name='Color')
    def __str__(self):
        return self.name


class Test(models.Model):
    """
    Model to store test details, including its status and date.
    """
    name = models.CharField(max_length=100, help_text="Name of the test")
    status = models.ForeignKey(
        TestStatus,
        on_delete=models.SET_NULL,
        null=True,
        related_name="tests",
        help_text="Current status of the test"
    )
    date = models.DateField(help_text="Date of the test (can include future dates)")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the test was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the test was last updated")

    def __str__(self):
        return f"{self.name} ({self.date})"

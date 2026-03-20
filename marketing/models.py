from django.db import models
from colorfield.fields import ColorField


class Campaign(models.Model):
    CHANNEL_CHOICES = [
        ('google_ads', 'Google Ads'),
        ('meta', 'Meta (FB/IG)'),
        ('youtube', 'YouTube'),
        ('offline', 'Offline'),
        ('whatsapp', 'WhatsApp Broadcast'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=255)
    channel = models.CharField(max_length=50, choices=CHANNEL_CHOICES)
    session = models.ForeignKey(
        'registration.AcademicSession',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campaigns',
    )
    utm_source = models.CharField(max_length=100, blank=True)
    color = ColorField(default='#6c757d', blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_channel_display()})"

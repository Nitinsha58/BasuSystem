from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Inquiry, FollowUpStatus, FollowUp


@receiver(post_save, sender=Inquiry)
def create_initial_followup(sender, instance, created, **kwargs):
    if created:
        default_status = FollowUpStatus.objects.order_by('order').first()
        FollowUp.objects.create(
            inquiry=instance,
            status=default_status,
            description=""
        )

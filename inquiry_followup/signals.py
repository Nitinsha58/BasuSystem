from django.db.models.signals import post_save, post_delete
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import Inquiry, FollowUpStatus, FollowUp


def _sync_current_status(inquiry):
    """Update the denormalized current_status on an Inquiry from its latest FollowUp."""
    latest = (
        inquiry.followup
        .select_related('status')
        .order_by('-created_at')
        .first()
    )
    new_status = latest.status if latest else None
    new_status_id = new_status.id if new_status else None
    if inquiry.current_status_id != new_status_id:
        Inquiry.objects.filter(pk=inquiry.pk).update(current_status=new_status)


@receiver(post_save, sender=FollowUp)
def followup_saved(sender, instance, **kwargs):
    _sync_current_status(instance.inquiry)


@receiver(post_delete, sender=FollowUp)
def followup_deleted(sender, instance, **kwargs):
    _sync_current_status(instance.inquiry)


@receiver(m2m_changed, sender=Inquiry.subjects.through)
def create_initial_followup(sender, instance, action, **kwargs):
    if action in ['post_add']:  # Ensures that M2M data is saved first
        default_status = FollowUpStatus.objects.order_by('order').first()
        
        classes = ", ".join([cls.name for cls in instance.classes.all()])
        subjects = ", ".join([subject.name for subject in instance.subjects.all()])

        desc = f"Inquiry for {instance.student_name} in {classes} for {subjects}, from {instance.address}"
        
        FollowUp.objects.create(
            inquiry=instance,
            status=default_status,
            description=desc
        )


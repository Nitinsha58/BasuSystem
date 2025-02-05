from django.db.models.signals import post_save
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import Inquiry, FollowUpStatus, FollowUp


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


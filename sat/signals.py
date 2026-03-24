from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


@receiver(post_save, sender='sat.TestResult')
def create_post_test_followup(sender, instance, created, **kwargs):
    if not created:
        return

    from inquiry_followup.models import FollowUp, FollowUpStatus

    try:
        inquiry = instance.attempt.assignment.inquiry
    except Exception:
        return

    post_test_status = FollowUpStatus.objects.filter(name='Post-Test').first()
    if post_test_status is None:
        return

    FollowUp.objects.create(
        inquiry=inquiry,
        status=post_test_status,
        admission_counsellor=inquiry.assigned_counsellor,
        description=(
            f"Test completed – {instance.grade_band} "
            f"({instance.percentage}%). Review result and proceed."
        ),
        followup_date=timezone.now().date(),
    )

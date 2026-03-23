from django.core.management.base import BaseCommand
from inquiry_followup.models import Inquiry


class Command(BaseCommand):
    help = 'Backfill current_status on all Inquiry records from their latest FollowUp'

    def handle(self, *args, **options):
        inquiries = Inquiry.objects.prefetch_related('followup__status')
        updated = 0
        for inq in inquiries:
            latest = inq.followup.order_by('-created_at').first()
            new_status = latest.status if latest else None
            new_status_id = new_status.id if new_status else None
            if inq.current_status_id != new_status_id:
                Inquiry.objects.filter(pk=inq.pk).update(current_status=new_status)
                updated += 1
        self.stdout.write(self.style.SUCCESS(f'Done. Updated {updated} of {inquiries.count()} inquiries.'))

"""
Data migration: seed ReferralSource from existing Referral rows, then
populate Inquiry.referral_source for every inquiry that has a referral.

Category mapping heuristic (case-insensitive name matching):
  digital   → google, youtube, instagram, website, whatsapp, facebook, online, fb, ig
  offline   → banner, pamphlet, school, event, flyer, newspaper
  representative → representative, rep, agent
  word_of_mouth  → everything else (friends, family, reference, etc.)
"""

from django.db import migrations

DIGITAL_KEYWORDS = {'google', 'youtube', 'instagram', 'website', 'whatsapp', 'facebook', 'online', 'fb', 'ig'}
OFFLINE_KEYWORDS = {'banner', 'pamphlet', 'school', 'event', 'flyer', 'newspaper', 'hoarding'}
REPRESENTATIVE_KEYWORDS = {'representative', 'rep', 'agent'}


def _guess_category(name: str) -> str:
    lower = name.lower()
    for kw in DIGITAL_KEYWORDS:
        if kw in lower:
            return 'digital'
    for kw in OFFLINE_KEYWORDS:
        if kw in lower:
            return 'offline'
    for kw in REPRESENTATIVE_KEYWORDS:
        if kw in lower:
            return 'representative'
    return 'word_of_mouth'


def migrate_forward(apps, schema_editor):
    Referral = apps.get_model('inquiry_followup', 'Referral')
    ReferralSource = apps.get_model('inquiry_followup', 'ReferralSource')
    Inquiry = apps.get_model('inquiry_followup', 'Inquiry')

    # Build a mapping from old Referral.id → new ReferralSource instance
    old_to_new = {}
    for referral in Referral.objects.all():
        category = _guess_category(referral.name)
        source, _ = ReferralSource.objects.get_or_create(
            name=referral.name,
            category=category,
            defaults={'is_active': True},
        )
        old_to_new[referral.id] = source

    # Bulk-update inquiries in batches to avoid loading all rows into memory
    batch_size = 500
    inquiries_to_update = []
    for inquiry in Inquiry.objects.filter(referral__isnull=False).select_related('referral').iterator(chunk_size=batch_size):
        new_source = old_to_new.get(inquiry.referral_id)
        if new_source:
            inquiry.referral_source = new_source
            inquiries_to_update.append(inquiry)
        if len(inquiries_to_update) >= batch_size:
            Inquiry.objects.bulk_update(inquiries_to_update, ['referral_source'])
            inquiries_to_update = []

    if inquiries_to_update:
        Inquiry.objects.bulk_update(inquiries_to_update, ['referral_source'])


def migrate_backward(apps, schema_editor):
    # Reverse: clear referral_source (old referral FK is still intact)
    Inquiry = apps.get_model('inquiry_followup', 'Inquiry')
    Inquiry.objects.update(referral_source=None)


class Migration(migrations.Migration):

    dependencies = [
        ('inquiry_followup', '0016_inquiry_campaign_inquiry_intent_inquiry_lead_quality_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_forward, migrate_backward),
    ]

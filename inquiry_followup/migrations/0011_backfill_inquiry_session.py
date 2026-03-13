from django.db import migrations


def backfill_sessions(apps, schema_editor):
    Inquiry = apps.get_model('inquiry_followup', 'Inquiry')
    AcademicSession = apps.get_model('registration', 'AcademicSession')

    sessions = list(AcademicSession.objects.order_by('start_date'))
    if not sessions:
        return

    db_alias = schema_editor.connection.alias

    for session in sessions:
        # One UPDATE per session — no Python-level iteration over inquiries
        Inquiry.objects.using(db_alias).filter(
            session__isnull=True,
            created_at__date__gte=session.start_date,
            created_at__date__lte=session.end_date,
        ).update(session=session)


class Migration(migrations.Migration):

    dependencies = [
        ('inquiry_followup', '0010_inquiry_session'),
        ('registration', '0102_alter_feedetails_student'),
    ]

    operations = [
        migrations.RunPython(backfill_sessions, migrations.RunPython.noop),
    ]

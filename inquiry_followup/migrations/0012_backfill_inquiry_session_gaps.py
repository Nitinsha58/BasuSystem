from django.db import migrations


def backfill_sessions_for_gaps(apps, schema_editor):
    """Assign session for inquiries that don't fall inside any session range.

    Rules (date-based, ignores is_active):
    1) If inquiry.created_at is before the earliest session.start_date => assign earliest session.
    2) If inquiry.created_at is after a session.end_date but before the next session.start_date
       => assign the next upcoming session.

    Note: If an inquiry is after the last known session.end_date, there is no "next" session,
    so it is left unchanged (session remains NULL) until a future session is created.
    """

    Inquiry = apps.get_model('inquiry_followup', 'Inquiry')
    AcademicSession = apps.get_model('registration', 'AcademicSession')

    db_alias = schema_editor.connection.alias

    sessions = list(AcademicSession.objects.using(db_alias).order_by('start_date').values('id', 'start_date', 'end_date'))
    if not sessions:
        return

    first = sessions[0]

    # Before the first session => assign the first (upcoming) session
    Inquiry.objects.using(db_alias).filter(
        session__isnull=True,
        created_at__date__lt=first['start_date'],
    ).update(session_id=first['id'])

    # Between sessions (gaps) => assign the next upcoming session
    for prev_session, next_session in zip(sessions, sessions[1:]):
        Inquiry.objects.using(db_alias).filter(
            session__isnull=True,
            created_at__date__gt=prev_session['end_date'],
            created_at__date__lt=next_session['start_date'],
        ).update(session_id=next_session['id'])


class Migration(migrations.Migration):

    dependencies = [
        ('inquiry_followup', '0011_backfill_inquiry_session'),
    ]

    operations = [
        migrations.RunPython(backfill_sessions_for_gaps, migrations.RunPython.noop),
    ]

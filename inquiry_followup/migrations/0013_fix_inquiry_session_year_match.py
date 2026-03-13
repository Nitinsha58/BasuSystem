from django.db import migrations


def clear_sessions_with_year_mismatch(apps, schema_editor):
    """Clear Inquiry.session where inquiry.created_at.year != session.start_date.year."""

    Inquiry = apps.get_model('inquiry_followup', 'Inquiry')

    db_alias = schema_editor.connection.alias

    from django.db.models import F
    from django.db.models.functions import ExtractYear

    (
        Inquiry.objects.using(db_alias)
        .filter(session__isnull=False)
        .annotate(
            inquiry_year=ExtractYear('created_at'),
            session_year=ExtractYear('session__start_date'),
        )
        .exclude(inquiry_year=F('session_year'))
        .update(session_id=None)
    )


def backfill_sessions_with_year_match(apps, schema_editor):
    """Assign sessions for inquiries that are missing session, using year-match rule.

    This re-runs the intent of earlier backfills (`0011` and `0012`) but only associates
    a session when inquiry.created_at.year == session.start_date.year.

    Order:
    1) If inquiry date falls within a session's [start_date, end_date] AND years match => assign.
    2) If inquiry date is before the earliest session.start_date AND years match earliest => assign earliest.
    3) If inquiry date falls in a gap between sessions AND years match next session => assign next session.

    If inquiry is after the last session.end_date, it remains NULL.
    """

    Inquiry = apps.get_model('inquiry_followup', 'Inquiry')
    AcademicSession = apps.get_model('registration', 'AcademicSession')

    db_alias = schema_editor.connection.alias

    sessions = list(
        AcademicSession.objects.using(db_alias)
        .order_by('start_date')
        .values('id', 'start_date', 'end_date')
    )
    if not sessions:
        return

    # 1) Within session range (inclusive) with year match
    for session in sessions:
        start_date = session['start_date']
        end_date = session['end_date']
        if start_date is None or end_date is None:
            continue

        Inquiry.objects.using(db_alias).filter(
            session__isnull=True,
            created_at__year=start_date.year,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        ).update(session_id=session['id'])

    first = sessions[0]
    first_start = first['start_date']
    if first_start is None:
        return

    # 2) Before the first session => assign first session only if year matches
    Inquiry.objects.using(db_alias).filter(
        session__isnull=True,
        created_at__year=first_start.year,
        created_at__date__lt=first_start,
    ).update(session_id=first['id'])

    # 3) Between sessions (gaps) => assign the next upcoming session only if year matches
    for prev_session, next_session in zip(sessions, sessions[1:]):
        prev_end = prev_session['end_date']
        next_start = next_session['start_date']
        if prev_end is None or next_start is None:
            continue

        Inquiry.objects.using(db_alias).filter(
            session__isnull=True,
            created_at__year=next_start.year,
            created_at__date__gt=prev_end,
            created_at__date__lt=next_start,
        ).update(session_id=next_session['id'])


class Migration(migrations.Migration):

    dependencies = [
        ('inquiry_followup', '0012_backfill_inquiry_session_gaps'),
    ]

    operations = [
        migrations.RunPython(clear_sessions_with_year_mismatch, migrations.RunPython.noop),
        migrations.RunPython(backfill_sessions_with_year_match, migrations.RunPython.noop),
    ]

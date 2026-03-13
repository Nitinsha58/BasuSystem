from django.db import migrations


def fill_inquiry_session_with_fallback(apps, schema_editor):
    """Ensure Inquiry.session is not NULL (when sessions exist).

    Priority:
    1) Year-match session (session.start_date.year == inquiry.created_at.year) using range/gap rules.
    2) Active session
    3) Nearest session overall (date-based) as a last resort.
    """

    Inquiry = apps.get_model('inquiry_followup', 'Inquiry')
    AcademicSession = apps.get_model('registration', 'AcademicSession')

    db_alias = schema_editor.connection.alias

    sessions = list(
        AcademicSession.objects.using(db_alias)
        .order_by('start_date')
        .values('id', 'start_date', 'end_date', 'is_active')
    )
    if not sessions:
        return

    # 1) Year-match assignments (range + before-first + gaps)
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
    if first_start is not None:
        Inquiry.objects.using(db_alias).filter(
            session__isnull=True,
            created_at__year=first_start.year,
            created_at__date__lt=first_start,
        ).update(session_id=first['id'])

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

    # 2) Active session fallback
    active_session = next((s for s in sessions if s.get('is_active')), None)
    if active_session:
        Inquiry.objects.using(db_alias).filter(session__isnull=True).update(session_id=active_session['id'])
        return

    # 3) Nearest overall fallback (date-based)
    first_start = sessions[0]['start_date']
    last_end = sessions[-1]['end_date']

    if first_start is not None:
        Inquiry.objects.using(db_alias).filter(
            session__isnull=True,
            created_at__date__lt=first_start,
        ).update(session_id=sessions[0]['id'])

    for prev_session, next_session in zip(sessions, sessions[1:]):
        prev_end = prev_session['end_date']
        next_start = next_session['start_date']
        if prev_end is None or next_start is None:
            continue

        Inquiry.objects.using(db_alias).filter(
            session__isnull=True,
            created_at__date__gt=prev_end,
            created_at__date__lt=next_start,
        ).update(session_id=next_session['id'])

    if last_end is not None:
        Inquiry.objects.using(db_alias).filter(
            session__isnull=True,
            created_at__date__gt=last_end,
        ).update(session_id=sessions[-1]['id'])


class Migration(migrations.Migration):

    dependencies = [
        ('inquiry_followup', '0013_fix_inquiry_session_year_match'),
    ]

    operations = [
        migrations.RunPython(fill_inquiry_session_with_fallback, migrations.RunPython.noop),
    ]

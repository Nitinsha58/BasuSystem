from django.db import migrations


def backfill_enrollment_links(apps, schema_editor):
    Student = apps.get_model('registration', 'Student')
    StudentEnrollment = apps.get_model('registration', 'StudentEnrollment')
    EnrollmentBatch = apps.get_model('registration', 'EnrollmentBatch')
    StudentBatchLink = apps.get_model('registration', 'StudentBatchLink')
    AcademicSession = apps.get_model('registration', 'AcademicSession')

    active_session = AcademicSession.objects.filter(is_active=True).first()

    def get_or_create_enrollment(student, session, fallback_class_name=None):
        if not session:
            return None

        defaults = {
            'class_name': fallback_class_name or getattr(student, 'class_enrolled', None),
            'course': getattr(student, 'course', None),
            'program_duration': getattr(student, 'program_duration', None) or '1 Year',
            'active': getattr(student, 'active', True),
        }

        # If we still couldn't resolve class_name, we cannot create an enrollment.
        if not defaults['class_name']:
            return None

        enrollment, created = StudentEnrollment.objects.get_or_create(
            student=student,
            session=session,
            defaults=defaults,
        )

        # Only set subjects when creating, or when enrollment has none.
        try:
            if created:
                enrollment.subjects.set(student.subjects.all())
            else:
                if enrollment.subjects.count() == 0 and student.subjects.count() > 0:
                    enrollment.subjects.set(student.subjects.all())
        except Exception:
            # Be fail-safe in data migrations (e.g. historical schema differences)
            pass

        return enrollment

    # 1) Ensure an enrollment exists for the active session (when available)
    if active_session:
        for student in Student.objects.all().iterator():
            get_or_create_enrollment(student, active_session)

    # 2) Backfill EnrollmentBatch from Student.batches (while the legacy M2M exists)
    #    We prefer the batch.session when available.
    for student in Student.objects.all().iterator():
        try:
            batches = student.batches.all()
        except Exception:
            batches = []

        for batch in batches:
            session = getattr(batch, 'session', None) or active_session
            enrollment = get_or_create_enrollment(student, session, fallback_class_name=getattr(batch, 'class_name', None))
            if not enrollment:
                continue
            EnrollmentBatch.objects.get_or_create(enrollment=enrollment, batch=batch)

    # 3) Backfill StudentBatchLink.enrollment (and mirror into EnrollmentBatch)
    #    If enrollment is missing, we derive it from batch.session (or active session).
    for link in StudentBatchLink.objects.select_related('student', 'batch').filter(enrollment__isnull=True).iterator():
        session = getattr(link.batch, 'session', None) or active_session
        enrollment = get_or_create_enrollment(link.student, session, fallback_class_name=getattr(link.batch, 'class_name', None))
        if not enrollment:
            continue

        # Avoid unique_together collisions by de-duplicating.
        duplicate_exists = StudentBatchLink.objects.filter(
            student_id=link.student_id,
            batch_id=link.batch_id,
            enrollment_id=enrollment.id,
        ).exclude(id=link.id).exists()

        if duplicate_exists:
            link.delete()
            continue

        link.enrollment_id = enrollment.id
        link.save(update_fields=['enrollment'])

        EnrollmentBatch.objects.get_or_create(enrollment=enrollment, batch=link.batch)


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0097_alter_studentbatchlink_unique_together_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_enrollment_links, migrations.RunPython.noop),
    ]

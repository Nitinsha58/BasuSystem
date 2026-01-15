from django.db import migrations


def create_student_enrollments(apps, schema_editor):
    Student = apps.get_model('registration', 'Student')
    StudentEnrollment = apps.get_model('registration', 'StudentEnrollment')
    AcademicSession = apps.get_model('registration', 'AcademicSession')

    active_session = AcademicSession.objects.filter(is_active=True).first()

    if not active_session:
        return  # fail-safe, do nothing

    for student in Student.objects.all():
        enrollment, created = StudentEnrollment.objects.get_or_create(
            student=student,
            session=active_session,
            defaults={
                'class_name': student.class_enrolled,
                'course': student.course,
                'program_duration': student.program_duration,
            }
        )

        if created:
            enrollment.subjects.set(student.subjects.all())


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0061_studentenrollment'),
    ]

    operations = [
        migrations.RunPython(create_student_enrollments, migrations.RunPython.noop),
    ]

from django.db import migrations

def migrate_existing_batch_links(apps, schema_editor):
    Student = apps.get_model('registration', 'Student')
    StudentBatchLink = apps.get_model('registration', 'StudentBatchLink')

    for student in Student.objects.prefetch_related('batches').all():
        for batch in student.batches.all():
            StudentBatchLink.objects.get_or_create(
                student=student,
                batch=batch,
                defaults={'active': True}
            )

class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0045_studentbatchlink'),  # update this with your actual latest migration
    ]

    operations = [
        migrations.RunPython(migrate_existing_batch_links),
    ]

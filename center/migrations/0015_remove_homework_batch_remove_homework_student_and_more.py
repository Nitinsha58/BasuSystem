# Generated by Django 5.1.4 on 2025-04-01 08:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('center', '0014_test_no_of_questions_test_total_max_marks_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='homework',
            name='batch',
        ),
        migrations.RemoveField(
            model_name='homework',
            name='student',
        ),
        migrations.DeleteModel(
            name='Attendance',
        ),
        migrations.DeleteModel(
            name='Homework',
        ),
    ]

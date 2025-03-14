# Generated by Django 5.1.4 on 2025-01-11 13:47

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('center', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='student', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='questionresponse',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='question_response', to='center.student'),
        ),
        migrations.AddField(
            model_name='homework',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='homework', to='center.student'),
        ),
        migrations.AddField(
            model_name='attendance',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance', to='center.student'),
        ),
        migrations.AddField(
            model_name='batch',
            name='subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='batch', to='center.subject'),
        ),
        migrations.AddField(
            model_name='test',
            name='batch',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test', to='center.batch'),
        ),
        migrations.AddField(
            model_name='questionresponse',
            name='test',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='response', to='center.test'),
        ),
        migrations.AddField(
            model_name='testquestion',
            name='test',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='question', to='center.test'),
        ),
        migrations.AddField(
            model_name='questionresponse',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='response', to='center.testquestion'),
        ),
        migrations.AlterUniqueTogether(
            name='attendance',
            unique_together={('student', 'batch', 'date')},
        ),
        migrations.AlterUniqueTogether(
            name='batch',
            unique_together={('class_name', 'section', 'subject')},
        ),
        migrations.AlterUniqueTogether(
            name='testquestion',
            unique_together={('test', 'question_number')},
        ),
        migrations.AlterUniqueTogether(
            name='questionresponse',
            unique_together={('question', 'student')},
        ),
    ]

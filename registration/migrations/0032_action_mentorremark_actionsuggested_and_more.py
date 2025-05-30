# Generated by Django 5.1.4 on 2025-05-27 05:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0031_reportperiod'),
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Actions',
            },
        ),
        migrations.CreateModel(
            name='MentorRemark',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mentor_remark', models.TextField()),
                ('parent_remark', models.TextField(blank=True, null=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('mentor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='remarks', to='registration.mentor')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mentor_remarks', to='registration.student')),
            ],
            options={
                'unique_together': {('mentor', 'student', 'start_date', 'end_date')},
            },
        ),
        migrations.CreateModel(
            name='ActionSuggested',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('action', models.ManyToManyField(related_name='action_suggestions', to='registration.action')),
                ('batch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='action_suggestions', to='registration.batch')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='action_suggestions', to='registration.student')),
                ('mentor_remark', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='action_suggestions', to='registration.mentorremark')),
            ],
            options={
                'unique_together': {('student', 'batch', 'mentor_remark')},
            },
        ),
        migrations.DeleteModel(
            name='MentorReview',
        ),
    ]

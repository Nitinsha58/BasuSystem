# Generated by Django 5.1.4 on 2025-02-04 09:21

import colorfield.fields
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('center', '0014_test_no_of_questions_test_total_max_marks_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FollowUpStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('order', models.IntegerField(unique=True)),
                ('color', colorfield.fields.ColorField(blank=True, default=None, image_field=None, max_length=25, null=True, samples=None, verbose_name='Color')),
            ],
        ),
        migrations.CreateModel(
            name='AdmissionCounselor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('center', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='admission_counsellor', to='center.center')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='admission_counsellor', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Inquiry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_name', models.CharField(max_length=255)),
                ('school', models.CharField(max_length=255)),
                ('address', models.TextField()),
                ('phone', models.CharField(max_length=15)),
                ('referral', models.CharField(blank=True, max_length=100, null=True)),
                ('classes', models.ManyToManyField(blank=True, to='center.classname')),
                ('subjects', models.ManyToManyField(blank=True, to='center.subject')),
            ],
        ),
        migrations.CreateModel(
            name='FollowUp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('admission_counsellor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='inquiry_followup.admissioncounselor')),
                ('status', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='followup', to='inquiry_followup.followupstatus')),
                ('inquiry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followup', to='inquiry_followup.inquiry')),
            ],
        ),
    ]

# Generated by Django 5.1.4 on 2025-04-25 09:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0018_chapter_created_at_chapter_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='testquestion',
            name='chapter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='registration.chapter'),
        ),
        migrations.AlterField(
            model_name='testquestion',
            name='chapter_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='testquestion',
            name='chapter_no',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]

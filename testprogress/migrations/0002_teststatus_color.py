# Generated by Django 5.1.4 on 2025-01-19 20:30

import colorfield.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('testprogress', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='teststatus',
            name='color',
            field=colorfield.fields.ColorField(blank=True, default=None, image_field=None, max_length=25, null=True, samples=None, verbose_name='Color'),
        ),
    ]

# Generated by Django 5.1.4 on 2025-03-17 07:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inquiry_followup', '0008_remove_inquiry_lead_quality_inquiry_lead_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='stationarypartner',
            name='lead_incentive',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]

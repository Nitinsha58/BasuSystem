# Generated by Django 5.1.4 on 2025-07-05 10:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0046_migrate_existing_batch_links'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentbatchlink',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]

# Generated by Django 5.1.4 on 2025-01-17 08:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('center', '0004_alter_testquestion_unique_together_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='testquestion',
            old_name='optionalQuestion',
            new_name='optional_question',
        ),
        migrations.AddField(
            model_name='testquestion',
            name='has_optional',
            field=models.BooleanField(default=False),
        ),
    ]

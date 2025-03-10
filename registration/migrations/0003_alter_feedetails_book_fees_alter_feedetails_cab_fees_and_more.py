# Generated by Django 5.1.4 on 2025-02-10 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0002_alter_student_class_enrolled_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feedetails',
            name='book_fees',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='feedetails',
            name='cab_fees',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='feedetails',
            name='remaining_balance',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='feedetails',
            name='uniform_fees',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
    ]

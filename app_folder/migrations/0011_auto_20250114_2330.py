# Generated by Django 2.1.5 on 2025-01-14 14:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_folder', '0010_auto_20250110_1852'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='paymentdetail',
            index=models.Index(fields=['purchase'], name='app_folder__purchas_f8e198_idx'),
        ),
    ]

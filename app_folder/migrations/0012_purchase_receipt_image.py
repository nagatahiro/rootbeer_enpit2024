# Generated by Django 2.1.5 on 2025-01-14 14:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_folder', '0011_auto_20250114_2330'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='receipt_image',
            field=models.ImageField(blank=True, null=True, upload_to='receipts/'),
        ),
    ]
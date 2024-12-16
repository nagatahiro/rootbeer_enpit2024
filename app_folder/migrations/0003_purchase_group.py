# Generated by Django 5.1.4 on 2024-12-16 00:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_folder', '0002_purchase'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='group',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='purchases', to='app_folder.customgroup'),
        ),
    ]

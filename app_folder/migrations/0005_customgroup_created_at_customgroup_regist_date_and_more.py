# Generated by Django 4.2.13 on 2025-01-07 04:40

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('app_folder', '0004_merge_0003_auto_20250102_1341_0003_purchase_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='customgroup',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default='2025-01-07 00:00:00'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='customgroup',
            name='regist_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='customgroup',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.DeleteModel(
            name='Purchase',
        ),
        
    ]

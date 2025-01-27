# Generated by Django 2.1.5 on 2025-01-10 09:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app_folder', '0009_alter_customgroup_invite_token'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentDetail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_paid', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
        migrations.AlterField(
            model_name='customgroup',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AddField(
            model_name='paymentdetail',
            name='purchase',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_details', to='app_folder.Purchase'),
        ),
        migrations.AddField(
            model_name='paymentdetail',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_details', to=settings.AUTH_USER_MODEL),
        ),
    ]

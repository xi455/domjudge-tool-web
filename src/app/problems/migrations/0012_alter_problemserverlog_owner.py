# Generated by Django 3.2.23 on 2024-02-13 12:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('problems', '0011_auto_20240213_2026'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problemserverlog',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='owner_log', to=settings.AUTH_USER_MODEL, verbose_name='使用者紀錄'),
        ),
    ]

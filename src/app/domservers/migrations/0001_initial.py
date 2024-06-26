# Generated by Django 3.2.19 on 2023-06-18 05:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DomServerClient',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_at', models.DateTimeField(auto_now_add=True, verbose_name='建立時間')),
                ('update_at', models.DateTimeField(auto_now=True, verbose_name='更新時間')),
                ('name', models.CharField(max_length=255, verbose_name='主機名稱')),
                ('host', models.URLField(help_text='https://domserver.example.com', verbose_name='Dom server URL')),
                ('username', models.CharField(help_text='必須要有 "API reader", "API writer" roles', max_length=128, verbose_name='帳號')),
                ('mask_password', models.CharField(editable=False, max_length=128, verbose_name='密碼')),
                ('disable_ssl', models.BooleanField(default=False)),
                ('timeout', models.BooleanField(default=False)),
                ('category_id', models.BigIntegerField(default=0, help_text='請輸入類型ID', verbose_name='類型ID')),
                ('affiliation_id', models.BigIntegerField(default=0, help_text='請輸入所屬關係ID', verbose_name='所屬關係ID')),
                ('affiliation_country', models.CharField(default='TWN', max_length=128, verbose_name='所屬國家')),
                ('version', models.CharField(default='7.3.2', max_length=16, verbose_name='Dom Server 版本')),
                ('api_version', models.CharField(default='v4', max_length=16, verbose_name='Dom Server API 版本')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dom_servers', to=settings.AUTH_USER_MODEL, verbose_name='擁有者')),
            ],
            options={
                'verbose_name': 'Dom Server 連線資訊',
                'verbose_name_plural': 'Dom Server 連線資訊',
            },
        ),
    ]

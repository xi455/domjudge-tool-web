# Generated by Django 3.2.23 on 2024-02-14 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domservers', '0005_rename_user_contestrecord_owner'),
    ]

    operations = [
        migrations.AlterField(
            model_name='domserverclient',
            name='name',
            field=models.CharField(max_length=255, unique=True, verbose_name='主機名稱'),
        ),
    ]

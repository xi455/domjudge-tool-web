# Generated by Django 3.2.23 on 2024-04-17 03:54

from django.db import migrations, models
import django.db.models.deletion
import utils.problems.validator


class Migration(migrations.Migration):

    dependencies = [
        ('domservers', '0009_alter_domservercontest_options'),
        ('problems', '0014_auto_20240401_1556'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='short_name',
            field=models.CharField(default='p01', help_text='ex: p01', max_length=50, validators=[utils.problems.validator.validation_zip_file_name], verbose_name='題目簡稱'),
        ),
        migrations.AlterField(
            model_name='problemserverlog',
            name='contest',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='contest_log', to='domservers.domservercontest', verbose_name='考區紀錄'),
        ),
        migrations.AlterField(
            model_name='problemserverlog',
            name='problem',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='problem_log', to='problems.problem', verbose_name='題目紀錄'),
        ),
        migrations.AlterField(
            model_name='problemserverlog',
            name='server_client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='server_log', to='domservers.domserverclient', verbose_name='伺服器紀錄'),
        ),
    ]

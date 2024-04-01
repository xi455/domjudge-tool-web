# Generated by Django 3.2.23 on 2024-04-01 07:56

import app.problems.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('domservers', '0008_auto_20240401_1556'),
        ('problems', '0013_auto_20240214_1650'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='problem',
            options={'ordering': ['-update_at', '-create_at'], 'verbose_name': '題目', 'verbose_name_plural': '題目'},
        ),
        migrations.RemoveField(
            model_name='problem',
            name='is_processed',
        ),
        migrations.RemoveField(
            model_name='problem',
            name='web_problem_id',
        ),
        migrations.RemoveField(
            model_name='problemserverlog',
            name='web_problem_contest_cid',
        ),
        migrations.AddField(
            model_name='problemserverlog',
            name='contest',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='contest_log', to='domservers.domservercontest', verbose_name='考區紀錄'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='name',
            field=models.CharField(max_length=255, unique=True, validators=[app.problems.models.validate_problem_name], verbose_name='題目名稱'),
        ),
        migrations.AlterField(
            model_name='problemserverlog',
            name='problem',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='problem_log', to='problems.problem', verbose_name='題目紀錄'),
        ),
        migrations.AlterField(
            model_name='problemserverlog',
            name='server_client',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='server_log', to='domservers.domserverclient', verbose_name='伺服器紀錄'),
        ),
    ]

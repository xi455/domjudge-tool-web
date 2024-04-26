# Generated by Django 3.2.23 on 2024-04-23 15:43

import app.problems.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import utils.problems.validator


class Migration(migrations.Migration):

    replaces = [('problems', '0003_problem_is_processed'), ('problems', '0004_problemserverlog'), ('problems', '0005_problem_web_problem_id'), ('problems', '0006_alter_problem_name'), ('problems', '0007_alter_problem_name'), ('problems', '0008_alter_problem_name'), ('problems', '0009_alter_problemserverlog_web_problem_contest'), ('problems', '0010_auto_20231118_1508'), ('problems', '0011_auto_20240213_2026'), ('problems', '0012_alter_problemserverlog_owner'), ('problems', '0013_auto_20240214_1650'), ('problems', '0014_auto_20240401_1556'), ('problems', '0015_auto_20240417_1154')]

    dependencies = [
        ('domservers', '0004_contestrecord'),
        ('domservers', '0005_rename_user_contestrecord_owner'),
        ('domservers', '0008_auto_20240401_1556'),
        ('domservers', '0002_alter_domserverclient_mask_password'),
        ('domservers', '0009_alter_domservercontest_options'),
        ('problems', '0002_auto_20211129_2240'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='is_processed',
            field=models.BooleanField(default=False, verbose_name='是否上傳'),
        ),
        migrations.AddField(
            model_name='problem',
            name='web_problem_id',
            field=models.CharField(blank=True, max_length=68, null=True, verbose_name='網站題目ID'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='name',
            field=models.CharField(max_length=255, null=True, verbose_name='題目名稱'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='name',
            field=models.CharField(max_length=255, verbose_name='題目名稱'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='name',
            field=models.CharField(max_length=255, validators=[app.problems.models.validate_problem_name], verbose_name='題目名稱'),
        ),
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
        migrations.AlterField(
            model_name='problem',
            name='name',
            field=models.CharField(max_length=255, unique=True, validators=[app.problems.models.validate_problem_name], verbose_name='題目名稱'),
        ),
        migrations.AddField(
            model_name='problem',
            name='short_name',
            field=models.CharField(default='p01', help_text='ex: p01', max_length=50, validators=[utils.problems.validator.validation_zip_file_name], verbose_name='題目簡稱'),
        ),
        migrations.CreateModel(
            name='ProblemServerLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('web_problem_id', models.CharField(max_length=68, verbose_name='網站題目ID')),
                ('problem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='problem_log', to='problems.problem', verbose_name='題目紀錄')),
                ('server_client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='server_log', to='domservers.domserverclient', verbose_name='伺服器紀錄')),
                ('web_problem_state', models.CharField(choices=[('新增', '新增'), ('移除', '移除')], default='新增', max_length=2, verbose_name='存放狀態')),
                ('owner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='owner_log', to=settings.AUTH_USER_MODEL, verbose_name='使用者紀錄')),
                ('contest', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='contest_log', to='domservers.domservercontest', verbose_name='考區紀錄')),
            ],
        ),
    ]

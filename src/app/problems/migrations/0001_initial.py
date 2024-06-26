# Generated by Django 3.1.7 on 2021-02-26 06:36

import app.problems.models
from django.conf import settings
import django.core.validators
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
            name='Problem',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_at', models.DateTimeField(auto_now_add=True, verbose_name='建立時間')),
                ('update_at', models.DateTimeField(auto_now=True, verbose_name='更新時間')),
                ('name', models.CharField(max_length=255, verbose_name='題目名稱')),                
                ('description_file', models.FileField(help_text='上傳題目說明 PDF', upload_to=app.problems.models.problem_file_path, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf'])], verbose_name='題目說明檔')),
                ('time_limit', models.FloatField(default=1.0, verbose_name='限制執行時間')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='problems', to=settings.AUTH_USER_MODEL, verbose_name='擁有者')),
            ],
            options={
                'verbose_name': '題目',
                'verbose_name_plural': '題目',
            },
        ),
        migrations.CreateModel(
            name='ProblemInOut',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('input_content', models.TextField(help_text='每行前後空白會被去除', verbose_name='輸入測資')),
                ('answer_content', models.TextField(help_text='每行前後空白會被去除', verbose_name='輸出答案')),
                ('problem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='int_out_data', to='problems.problem')),
            ],
            options={
                'verbose_name': '題目輸入輸出',
                'verbose_name_plural': '題目輸入輸出',
            },
        ),
    ]

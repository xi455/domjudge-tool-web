from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, ValidationError
from django.db import models

from app.domservers.models import DomServerClient, DomServerContest
from utils.models import BaseModel
from utils.problems.validator import validation_zip_file_name


def problem_file_path(instance, filename):
    _id = str(instance.id).replace("-", "")
    return f"problems/problem_{_id}/problem.pdf"


def validate_problem_name(value):
    if value[0].isdigit():
        raise ValidationError("題目名稱首字不可為數字")


class Problem(BaseModel):
    name = models.CharField("題目名稱", max_length=255, unique=True, validators=[validate_problem_name])
    short_name = models.CharField("題目簡稱", max_length=50, default="p01", help_text="ex: p01", validators=[validation_zip_file_name])
    description_file = models.FileField(
        "題目說明檔",
        upload_to=problem_file_path,
        help_text="上傳題目說明 PDF",
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )
    time_limit = models.FloatField("限制執行時間", default=1.0)
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="problems",
        verbose_name="擁有者",
    )

    def delete(self, using=None, keep_parents=False):
        pdf_path = self.description_file.path
        model = super().delete(using, keep_parents)
        default_storage.delete(pdf_path)
        return model

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "題目"
        verbose_name_plural = "題目"
        ordering = ["-update_at", "-create_at"]


def normalization_text(txt: str):
    contexts = []
    for index, line in enumerate(txt.splitlines()):
        s = line.strip()
        if s:
            contexts.append(s)
    return "\n".join(contexts)


class ProblemInOut(models.Model):
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name="int_out_data",
    )
    input_content = models.TextField("輸入測資", help_text="每行前後空白會被去除")
    answer_content = models.TextField("輸出答案", help_text="每行前後空白會被去除")
    is_sample = models.BooleanField("是否為範例測資", default=False)

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.input_content = normalization_text(self.input_content)
        self.answer_content = normalization_text(self.answer_content)
        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return f"{self.id}"

    class Meta:
        verbose_name = "題目輸入輸出"
        verbose_name_plural = "題目輸入輸出"


class ProblemServerLog(models.Model):
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="owner_log",
        verbose_name="使用者紀錄",
        null=True,
    )
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name="problem_log",
        verbose_name="題目紀錄",
    )
    server_client = models.ForeignKey(
        DomServerClient,
        on_delete=models.CASCADE,
        related_name="server_log",
        verbose_name="伺服器紀錄",
    )
    contest = models.ForeignKey(
        DomServerContest,
        on_delete=models.CASCADE,
        related_name="contest_log",
        verbose_name="考區紀錄",
        null=True,
    )
    web_problem_id = models.CharField("網站題目ID", max_length=68)

    class state(models.TextChoices):
        FIRST_STATE = "新增", "新增"
        SECOND_STATE = "移除", "移除"

    web_problem_state = models.CharField(
        verbose_name="存放狀態",
        max_length=2,
        choices=state.choices,
        default=state.FIRST_STATE,
    )

    def __str__(self):
        return f"{self.problem}"

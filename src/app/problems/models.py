from django.core.files.storage import default_storage
from django.core.validators import FileExtensionValidator
from django.db import models

from utils.models import BaseModel


def problem_file_path(instance, filename):
    _id = str(instance.id).replace("-", "")
    return f"problems/problem_{_id}/problem.pdf"


class Problem(BaseModel):
    name = models.CharField("題目名稱", max_length=255)
    short_name = models.CharField("題目代號", max_length=50, help_text="ex: p01")
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
    # problem_text_id = models.CharField("題目ID", max_length=10, blank=True)
    is_processed = models.BooleanField("是否上傳", default=False)
    # domserver_info = models.CharField("已上傳的 domserver", max_length=128, blank=True)
    # is_latest_inout = models.BooleanField("最新測資", default=False)

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
        ordering = ["short_name", "-update_at", "-create_at"]


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


class DomServer(models.Model):
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name="domserver",
    )
    server_name = models.CharField("Server 名稱", max_length=68)
    problem_web_id = models.CharField("網站題目ID", max_length=68)
    problem_web_contest = models.CharField("網站比賽區號", max_length=68)

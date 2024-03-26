from django.contrib.auth.models import AbstractUser
from django.db import models

from utils.models import BaseModel


class User(BaseModel, AbstractUser):
    first_name = models.CharField("名字", max_length=30, blank=True)
    last_name = models.CharField("姓氏", max_length=150, blank=True)

    REQUIRED_FIELDS: list = []

    @property
    def chinese_full_name(self):
        value = f"{self.last_name}{self.first_name}".strip()
        return value if value else "無法顯示姓名"

    def natural_key(self):
        return self.username

    def __str__(self):
        # return self.username
        return f"{self.chinese_full_name}"

    def save(self, *args, **kwargs):
        self.email = str(self.email).lower()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "使用者帳號"
        verbose_name_plural = "使用者帳號"

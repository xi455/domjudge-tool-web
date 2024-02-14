from functools import cached_property

from django.core.signing import Signer
from django.db import models
from django_cryptography.fields import encrypt

from utils.models import BaseModel


class DomServerClient(BaseModel):
    name = models.CharField("主機名稱", max_length=255)
    host = models.URLField(
        "Dom server URL",
        help_text="https://domserver.example.com",
    )
    username = models.CharField(
        "帳號",
        max_length=128,
        help_text='必須要有 "API reader", "API writer" roles',
    )
    mask_password = encrypt(
        models.CharField(
            "密碼",
            max_length=128,
            # editable=False,
        )
    )
    disable_ssl = models.BooleanField(default=False)
    timeout = models.BooleanField(default=False)
    category_id = models.BigIntegerField(
        default=0,
        verbose_name="類型ID",
        help_text="請輸入類型ID",
    )
    affiliation_id = models.BigIntegerField(
        default=0,
        verbose_name="所屬關係ID",
        help_text="請輸入所屬關係ID",
    )
    affiliation_country = models.CharField("所屬國家", max_length=128, default="TWN")
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="dom_servers",
        verbose_name="擁有者",
    )
    version = models.CharField(
        "Dom Server 版本",
        max_length=16,
        default="7.3.2",
    )
    api_version = models.CharField(
        "Dom Server API 版本",
        max_length=16,
        default="v4",
    )

    @cached_property
    def _signer(self):
        return Signer()

    @property
    def password(self):
        return self._signer.unsign(self.mask_password)

    @password.setter
    def password(self, value):
        self.mask_password = self._signer.sign(value)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "Dom Server 連線資訊"
        verbose_name_plural = "Dom Server 連線資訊"

class ContestRecord(BaseModel):
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="contest_records",
        verbose_name="使用者",
    )
    server_id = models.TextField(
        verbose_name="伺服器ID",
        help_text="請輸入伺服器ID",
        editable=False,
    )
    domjudge_contest_id = models.TextField(
        verbose_name="Domjudge考區ID",
        help_text="請輸入Domjudge考區ID",
        editable=False,
    )

    def __str__(self):
        return f"Contest Record - User: {self.owner}, Domjudge Contest Cid: {self.domjudge_contest_id}"

    class Meta:
        verbose_name = "Contest 紀錄"
        verbose_name_plural = "Contest 紀錄"
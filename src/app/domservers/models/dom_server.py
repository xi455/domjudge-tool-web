from functools import cached_property

from django.core.signing import Signer
from django.db import models
from django_cryptography.fields import encrypt

from utils.models import BaseModel


class DomServerClient(BaseModel):
    name = models.CharField("主機名稱", max_length=255, unique=True)
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


class DomServerContest(BaseModel):
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="contest_owner",
        verbose_name="使用者",
        default=1,
    )
    server_client = models.ForeignKey(
        DomServerClient,
        on_delete=models.CASCADE,
        related_name="contest_server_client",
        verbose_name="伺服器紀錄",
        default=1,
        # editable=False,
    )
    cid = models.CharField(
        "考區ID",
        max_length=255,
        # editable=False,
    )
    name = models.CharField("考區名稱", max_length=255)
    short_name = models.CharField(
        "考區簡稱",
        max_length=255,
    )
    start_time = models.CharField("開始時間", max_length=255)
    end_time = models.CharField("記分牌結束時間", max_length=255)
    activate_time = models.CharField("啟動時間", max_length=255)
    scoreboard_freeze_length = models.CharField(
        "凍結時間", max_length=255, blank=True, null=True
    )
    scoreboard_unfreeze_time = models.CharField(
        "記分牌解凍時間", max_length=255, blank=True, null=True
    )
    deactivate_time = models.CharField("停用時間", max_length=255, blank=True, null=True)
    start_time_enabled = models.BooleanField("是否啟用開始時間", default=False)
    process_balloons = models.BooleanField("是否啟用處理氣球", default=False)
    open_to_all_teams = models.BooleanField("是否向所有團隊開放", default=False)
    contest_visible_on_public_scoreboard = models.BooleanField(
        "是否比賽在公共計分板上可見", default=False
    )
    enabled = models.BooleanField("是否啟用", default=False)

    def __str__(self):
        return f"{self.short_name}"

    class Meta:
        verbose_name = "DomServer Contest 考場"
        verbose_name_plural = "DomServer Contest 考場"

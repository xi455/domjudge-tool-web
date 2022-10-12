from functools import cached_property

from django.db import models
from django.core.signing import Signer


from utils.models import BaseModel


class DomServerClient(BaseModel):
    name = models.CharField('主機名稱', max_length=255)
    host = models.URLField(
        'Dom server URL',
        help_text='https://domserver.example.com',
    )
    username = models.CharField(
        '帳號',
        max_length=128,
        help_text='必須要有 "API reader", "API writer" roles',
    )
    mask_password = models.CharField(
        '密碼',
        max_length=128,
        editable=False,
    )
    owner = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='dom_servers',
        verbose_name='擁有者',
    )
    api_version = models.CharField(
        'Dom Server API 版本',
        max_length=16,
        default='v4',
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
        return f'{self.name}'

    class Meta:
        verbose_name = 'Dom Server 連線資訊'
        verbose_name_plural = 'Dom Server 連線資訊'



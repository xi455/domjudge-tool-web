import uuid

from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(
        "ID",
        editable=False,
        primary_key=True,
        default=uuid.uuid4,
    )
    create_at = models.DateTimeField("建立時間", auto_now_add=True)
    update_at = models.DateTimeField("更新時間", auto_now=True)

    class Meta:
        abstract = True

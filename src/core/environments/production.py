import logging
import sys
import sentry_sdk

from core.settings import env

from sentry_sdk.integrations.django import DjangoIntegration

logging.basicConfig(stream=sys.stderr)

sentry_sdk.init(
    dsn=env('SENTRY_DSN'),
    environment=env('SENTRY_ENV'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.5,
    send_default_pii=True,
)

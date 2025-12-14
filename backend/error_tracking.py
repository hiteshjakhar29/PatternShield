"""Sentry integration for error tracking."""
from __future__ import annotations

import importlib.util


def init_sentry(config) -> None:
    if not config.SENTRY_DSN:
        return
    if not importlib.util.find_spec("sentry_sdk"):
        return
    import sentry_sdk  # type: ignore
    from sentry_sdk.integrations.flask import FlaskIntegration  # type: ignore

    sentry_sdk.init(dsn=config.SENTRY_DSN, integrations=[FlaskIntegration()], traces_sample_rate=0.1)


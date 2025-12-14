"""Security middleware including HTTP headers."""
import importlib.util
from flask import Flask


CONTENT_SECURITY_POLICY = {
    "default-src": "'self'",
}


def configure_talisman(app: Flask) -> None:
    if importlib.util.find_spec("flask_talisman"):
        from flask_talisman import Talisman  # type: ignore

        Talisman(
            app,
            content_security_policy=CONTENT_SECURITY_POLICY,
            force_https=False,
            frame_options="DENY",
            referrer_policy="no-referrer",
            x_xss_protection=True,
            session_cookie_secure=True,
        )


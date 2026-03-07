"""
PatternShield Backend — Central Configuration
All tunable constants and environment variable bindings live here.
"""
import os


class Config:
    # ── Flask ────────────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    PORT = int(os.getenv("PORT", 5000))

    # ── CORS ─────────────────────────────────────────────────────────
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

    # ── Rate Limiting ────────────────────────────────────────────────
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    RATE_LIMIT_PER_HOUR = os.getenv("RATE_LIMIT_PER_HOUR", "500")
    RATE_LIMIT_PER_MINUTE = os.getenv("RATE_LIMIT_PER_MINUTE", "60")

    # ── Authentication ───────────────────────────────────────────────
    API_KEY_REQUIRED = os.getenv("API_KEY_REQUIRED", "False").lower() == "true"
    API_KEY = os.getenv("API_KEY", None)

    # ── Logging ──────────────────────────────────────────────────────
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # ── Storage paths ────────────────────────────────────────────────
    FEEDBACK_FILE = os.getenv("FEEDBACK_FILE", "data/feedback.jsonl")
    TEMPORAL_FILE = os.getenv("TEMPORAL_FILE", "data/temporal.json")

    # ── Model flags ──────────────────────────────────────────────────
    TRANSFORMER_ENABLED = os.path.exists("models/distilbert_darkpattern/best_model")

    # ── Detection thresholds ─────────────────────────────────────────
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.30"))
    MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "2000"))
    MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "100"))
    MAX_TEMPORAL_PER_DOMAIN = int(os.getenv("MAX_TEMPORAL_PER_DOMAIN", "200"))
    MAX_ELEMENTS_TEMPORAL = int(os.getenv("MAX_ELEMENTS_TEMPORAL", "50"))

    # ── API versioning ───────────────────────────────────────────────
    API_VERSION = "2.1.0"

"""
PatternShield Backend — Central Configuration
All tunable constants and environment variable bindings live here.

Environment variables (see .env.example for a full reference):
  DATABASE_URL        — SQLAlchemy DSN (default: SQLite)
  ANTHROPIC_API_KEY   — enables LLM hybrid detection
  LLM_MODEL           — Claude model ID (default: claude-haiku-4-5-20251001)
  LLM_ENABLED         — toggle LLM layer without removing the key
  LLM_TIMEOUT         — max seconds to wait for LLM response
  LLM_TRIGGER_THRESHOLD — min rule-based confidence before LLM is called
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

    # ── Storage paths (legacy JSONL — still used for fast append) ────
    FEEDBACK_FILE = os.getenv("FEEDBACK_FILE", "data/feedback.jsonl")
    TEMPORAL_FILE = os.getenv("TEMPORAL_FILE", "data/temporal.json")

    # ── Database (SQLAlchemy) ─────────────────────────────────────────
    # Default: SQLite for zero-config local dev.
    # Set DATABASE_URL=postgresql://user:pass@host/dbname for production.
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/patternshield.db")
    DB_ECHO = os.getenv("DB_ECHO", "False").lower() == "true"

    # ── LLM integration (Anthropic Claude) ───────────────────────────
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", None)
    LLM_MODEL = os.getenv("LLM_MODEL", "claude-haiku-4-5-20251001")
    LLM_ENABLED = os.getenv("LLM_ENABLED", "True").lower() == "true"
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "15"))
    # Rule-based confidence must reach this level before LLM is called.
    # Keeps API cost proportional to actual detection signal.
    LLM_TRIGGER_THRESHOLD = float(os.getenv("LLM_TRIGGER_THRESHOLD", "0.25"))

    # ── Model flags ──────────────────────────────────────────────────
    TRANSFORMER_ENABLED = os.path.exists("models/distilbert_darkpattern/best_model")

    # ── Detection thresholds ─────────────────────────────────────────
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.30"))
    MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "2000"))
    MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "100"))
    MAX_TEMPORAL_PER_DOMAIN = int(os.getenv("MAX_TEMPORAL_PER_DOMAIN", "200"))
    MAX_ELEMENTS_TEMPORAL = int(os.getenv("MAX_ELEMENTS_TEMPORAL", "50"))

    # ── API versioning ───────────────────────────────────────────────
    API_VERSION = "3.0.0"

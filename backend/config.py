"""Environment-aware configuration management for PatternShield."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from typing import List, Type

from dotenv import load_dotenv

load_dotenv()


def _get_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _split_list(value: str | None) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass
class Config:
    """Base configuration shared across environments."""

    DEBUG: bool = _get_bool(os.getenv("DEBUG"), False)
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_hex(32))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///patternshield.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CORS_ORIGINS: List[str] = field(
        default_factory=lambda: _split_list(
            os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5000")
        )
    )
    API_RATE_LIMIT: str = os.getenv("RATE_LIMIT_PER_MINUTE", "100 per minute")
    RATE_LIMIT_ENABLED: bool = _get_bool(os.getenv("RATE_LIMIT_ENABLED"), True)
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    MODEL_PATH: str = os.getenv("MODEL_PATH", "/app/models")
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5000"))
    API_KEY_HEADER: str = os.getenv("API_KEY_HEADER", "X-API-Key")
    ALLOWED_API_KEYS: List[str] = field(
        default_factory=lambda: _split_list(os.getenv("ALLOWED_API_KEYS"))
    )
    JWT_SECRET: str = os.getenv("JWT_SECRET", "jwt-secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))
    ENABLE_METRICS: bool = _get_bool(os.getenv("ENABLE_METRICS"), True)
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")

    def validate(self) -> None:
        """Validate critical settings to avoid insecure deployments."""
        if self.SECRET_KEY in {"", "changeme", "change-me", "example-secret-key"}:
            raise ValueError("SECRET_KEY must be set to a non-default value")
        if not self.DEBUG and (self.DATABASE_URL.startswith("sqlite")):
            raise ValueError("Use a production-ready database when DEBUG is False")
        if not self.CORS_ORIGINS:
            raise ValueError("CORS_ORIGINS cannot be empty")
        if not self.DEBUG and any(origin == "*" for origin in self.CORS_ORIGINS):
            raise ValueError("CORS_ORIGINS cannot include '*' in production")
        if not self.JWT_SECRET:
            raise ValueError("JWT_SECRET must be configured")
        if not self.ALLOWED_API_KEYS and not self.DEBUG:
            raise ValueError("At least one API key must be configured")


class DevelopmentConfig(Config):
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"


class ProductionConfig(Config):
    DEBUG: bool = False


class TestingConfig(Config):
    DEBUG: bool = True
    DATABASE_URL: str = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


def get_config() -> Config:
    env = os.getenv("FLASK_ENV", os.getenv("APP_ENV", "development")).lower()
    config_class: Type[Config]
    if env.startswith("prod"):
        config_class = ProductionConfig
    elif env.startswith("test"):
        config_class = TestingConfig
    else:
        config_class = DevelopmentConfig
    config = config_class()
    if env.startswith("test"):
        config.ALLOWED_API_KEYS = ["test-key"]
        config.RATE_LIMIT_ENABLED = False
    if env.startswith("dev"):
        config.DEBUG = True
    config.validate()
    return config

"""
Database engine and session factory.

DATABASE_URL defaults to SQLite (file-based, zero-config for local dev).
Set DATABASE_URL=postgresql://user:pass@host/db for production PostgreSQL.

Design decision: SQLAlchemy ORM abstracts the DB engine so the rest of the
codebase never calls raw SQL — swapping SQLite → PostgreSQL only requires
changing the env var.
"""
import os
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

# ── Engine ────────────────────────────────────────────────────────────────────

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///data/patternshield.db",  # sensible local default
)

# SQLite needs special connect args for multi-threaded Flask
_connect_args = {}
_pool_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}
    # Use StaticPool only in tests (injected via env var)
    if os.getenv("TESTING", "false").lower() == "true":
        _pool_kwargs["poolclass"] = StaticPool

engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    echo=os.getenv("DB_ECHO", "false").lower() == "true",
    **_pool_kwargs,
)

# ── Session factory ───────────────────────────────────────────────────────────

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Declarative base ──────────────────────────────────────────────────────────

Base = declarative_base()


# ── Helpers ───────────────────────────────────────────────────────────────────

def init_db() -> None:
    """Create all tables if they don't exist. Safe to call on every startup."""
    # Import models so metadata is populated before create_all
    import models.site           # noqa: F401
    import models.scan           # noqa: F401
    import models.detected_pattern  # noqa: F401
    import models.trust_score_history  # noqa: F401
    import models.user_feedback  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info(f"✓ Database ready ({DATABASE_URL.split('://')[0]})")


def get_db():
    """
    Dependency-style session generator.
    Usage (Flask route):
        with get_db() as db:
            db.query(...)
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

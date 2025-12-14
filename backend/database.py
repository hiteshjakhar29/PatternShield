"""Database utilities with SQLAlchemy engine management."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine as sa_create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.models import Base


def create_db_engine(config):
    engine = sa_create_engine(config.DATABASE_URL, pool_size=config.DB_POOL_SIZE, pool_pre_ping=True, future=True)
    Base.metadata.create_all(engine)
    return engine


def create_session_factory(engine, pool_size: int = 5):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@contextmanager
def session_scope(SessionLocal) -> Iterator:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def health_check(engine) -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


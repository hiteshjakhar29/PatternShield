"""Database models for PatternShield."""

from __future__ import annotations

import datetime as dt
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SoftDeleteMixin:
    __abstract__ = True
    __allow_unmapped__ = True

    deleted = Column(Boolean, default=False, index=True)
    created_at = Column(
        DateTime, default=dt.datetime.utcnow, nullable=False, index=True
    )
    updated_at = Column(
        DateTime,
        default=dt.datetime.utcnow,
        onupdate=dt.datetime.utcnow,
        nullable=False,
    )


class PredictionLog(Base, SoftDeleteMixin):
    __tablename__ = "predictions"
    __table_args__ = (Index("ix_predictions_api_key_created", "api_key", "created_at"),)

    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    prediction = Column(String, nullable=False)
    confidence = Column(Float)
    model_version = Column(String)
    api_key = Column(String, index=True)
    ip_address = Column(String)
    response_time_ms = Column(Integer)
    metadata_json = Column(JSON)


class APIKey(Base, SoftDeleteMixin):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    key = Column(String, unique=True, nullable=False)


class User(Base, SoftDeleteMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)


class ModelVersion(Base, SoftDeleteMixin):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    checksum = Column(String)

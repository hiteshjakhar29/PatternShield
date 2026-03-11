"""
PatternShield — SQLAlchemy Models Package

Tables:
  sites                — deduplicated domain registry
  scans                — one row per page scan
  detected_patterns    — individual dark-pattern hits per scan
  trust_score_history  — time-series trust scores per domain
  user_feedback        — thumbs-up / thumbs-down corrections
"""
from models.base import Base, engine, SessionLocal, init_db

from models.site import Site
from models.scan import Scan
from models.detected_pattern import DetectedPattern
from models.trust_score_history import TrustScoreHistory
from models.user_feedback import UserFeedback

__all__ = [
    "Base", "engine", "SessionLocal", "init_db",
    "Site", "Scan", "DetectedPattern", "TrustScoreHistory", "UserFeedback",
]

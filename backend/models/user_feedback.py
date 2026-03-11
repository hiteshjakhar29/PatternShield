"""
UserFeedback model — DB-backed version of the JSONL feedback store.

Replaces the file-based FeedbackService for structured querying.
The JSONL store is kept as a fast append-log; this table is the
queryable, relational version.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from models.base import Base


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(Integer, nullable=True)  # denormalised for easy querying

    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    domain = Column(String(255), nullable=True, index=True)

    # What was detected
    element_text = Column(Text, nullable=True)
    detected_pattern = Column(String(100), nullable=False, index=True)

    # User correction
    is_correct = Column(Boolean, nullable=False)
    user_label = Column(String(100), nullable=True)  # user's suggested label if incorrect

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "site_id": self.site_id,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "domain": self.domain,
            "element_text": self.element_text,
            "detected_pattern": self.detected_pattern,
            "is_correct": self.is_correct,
            "user_label": self.user_label,
        }

"""
Site model — deduplicated domain registry.

One row per unique domain. Created the first time a domain is scanned.
Acts as the foreign-key anchor for scans and trust_score_history.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from models.base import Base


class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))
    notes = Column(Text, nullable=True)  # reserved for future analyst annotations

    # Relationships
    scans = relationship("Scan", back_populates="site", cascade="all, delete-orphan")
    trust_history = relationship(
        "TrustScoreHistory", back_populates="site", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Site domain={self.domain!r} id={self.id}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "domain": self.domain,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }

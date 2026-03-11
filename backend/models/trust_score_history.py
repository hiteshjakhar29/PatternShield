"""
TrustScoreHistory model — time-series trust scores per domain.

Enables:
  - Temporal trend analysis (is a site getting worse over time?)
  - Historical average trust score for a domain
  - Anomaly detection when score drops sharply between visits
"""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from models.base import Base


class TrustScoreHistory(Base):
    __tablename__ = "trust_score_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=True)

    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    score = Column(Float, nullable=False)         # 0–100
    grade = Column(String(2), nullable=False)     # A–F
    risk_level = Column(String(20), nullable=True)
    pattern_count = Column(Integer, default=0)   # # of dark patterns found

    # Relationships
    site = relationship("Site", back_populates="trust_history")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "site_id": self.site_id,
            "scan_id": self.scan_id,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "score": self.score,
            "grade": self.grade,
            "risk_level": self.risk_level,
            "pattern_count": self.pattern_count,
        }

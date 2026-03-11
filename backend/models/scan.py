"""
Scan model — one row per full-page analysis.

Records the raw page evidence, final trust score, and which detection method
was used. Linking detected_patterns here enables historical aggregation.
"""
import json
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from models.base import Base


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)

    # When
    scanned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Page-level evidence (summarised — not raw HTML)
    page_url = Column(Text, nullable=True)
    page_title = Column(String(512), nullable=True)
    element_count = Column(Integer, default=0)
    flagged_element_count = Column(Integer, default=0)

    # Trust score snapshot at scan time
    trust_score = Column(Float, nullable=True)       # 0–100
    trust_grade = Column(String(2), nullable=True)   # A–F
    risk_level = Column(String(20), nullable=True)   # low / medium / high / critical

    # Detection method(s) used
    method = Column(String(50), default="rule_based_v2")  # rule_based_v2 | llm_hybrid
    llm_used = Column(Integer, default=0)  # 0/1 flag (SQLite-compatible bool)

    # Serialised pattern breakdown (JSON string)
    _pattern_breakdown = Column("pattern_breakdown", Text, nullable=True)

    # Relationships
    site = relationship("Site", back_populates="scans")
    detected_patterns = relationship(
        "DetectedPattern", back_populates="scan", cascade="all, delete-orphan"
    )

    # ── Helpers ────────────────────────────────────────────────────────────────

    @property
    def pattern_breakdown(self) -> dict:
        if self._pattern_breakdown:
            try:
                return json.loads(self._pattern_breakdown)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    @pattern_breakdown.setter
    def pattern_breakdown(self, value: dict) -> None:
        self._pattern_breakdown = json.dumps(value) if value else None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "site_id": self.site_id,
            "scanned_at": self.scanned_at.isoformat() if self.scanned_at else None,
            "page_url": self.page_url,
            "element_count": self.element_count,
            "flagged_element_count": self.flagged_element_count,
            "trust_score": self.trust_score,
            "trust_grade": self.trust_grade,
            "risk_level": self.risk_level,
            "method": self.method,
            "llm_used": bool(self.llm_used),
            "pattern_breakdown": self.pattern_breakdown,
        }

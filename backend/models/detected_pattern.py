"""
DetectedPattern model — individual dark-pattern hit within a scan.

One row per detected pattern per element, enabling:
  - frequency analysis across scans
  - per-pattern trust contribution
  - LLM explanation storage alongside rule-based result
"""
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from models.base import Base


class DetectedPattern(Base):
    __tablename__ = "detected_patterns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False, index=True)

    # Element evidence
    element_text = Column(Text, nullable=True)       # first 500 chars
    element_type = Column(String(50), nullable=True)  # button, div, span, etc.

    # Detection result
    pattern_type = Column(String(100), nullable=False, index=True)
    confidence = Column(Float, nullable=False, default=0.0)
    severity = Column(String(20), nullable=True)      # critical/high/medium/low

    # Source of the detection
    detected_by = Column(String(30), default="rule")  # rule | llm | merged

    # Explanation (may come from rule or LLM)
    explanation = Column(Text, nullable=True)
    remediation = Column(Text, nullable=True)

    # Relationship
    scan = relationship("Scan", back_populates="detected_patterns")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "element_text": self.element_text,
            "element_type": self.element_type,
            "pattern_type": self.pattern_type,
            "confidence": self.confidence,
            "severity": self.severity,
            "detected_by": self.detected_by,
            "explanation": self.explanation,
            "remediation": self.remediation,
        }

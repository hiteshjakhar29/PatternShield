"""
PatternShield — Database Service Layer

High-level helpers used by API routes to read/write the DB without
importing SQLAlchemy internals directly into route handlers.

Design decision: Thin service layer keeps routes clean and makes the
persistence logic independently testable.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from models.base import SessionLocal, init_db
from models.site import Site
from models.scan import Scan
from models.detected_pattern import DetectedPattern
from models.trust_score_history import TrustScoreHistory
from models.user_feedback import UserFeedback

logger = logging.getLogger(__name__)


# ── Bootstrap ─────────────────────────────────────────────────────────────────

def setup_database() -> None:
    """Called once at app startup to create tables."""
    try:
        init_db()
    except Exception as e:
        logger.error(f"Database setup failed: {e}", exc_info=True)
        raise


# ── Site helpers ──────────────────────────────────────────────────────────────

def get_or_create_site(domain: str) -> Site:
    """Return existing Site row or insert a new one (upsert pattern)."""
    db = SessionLocal()
    try:
        site = db.query(Site).filter(Site.domain == domain).first()
        if not site:
            site = Site(domain=domain)
            db.add(site)
            db.flush()
        site.last_seen = datetime.now(timezone.utc)
        db.commit()
        db.refresh(site)
        return site
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Scan helpers ──────────────────────────────────────────────────────────────

def record_scan(
    domain: str,
    trust_score: float,
    trust_grade: str,
    risk_level: str,
    element_count: int,
    flagged_count: int,
    method: str,
    llm_used: bool,
    pattern_breakdown: Dict[str, Any],
    detections: List[Dict[str, Any]],
    page_url: Optional[str] = None,
) -> Scan:
    """
    Persist a full scan result.

    Creates/updates Site → creates Scan → creates DetectedPattern rows
    → creates TrustScoreHistory row. All in one transaction.
    """
    db = SessionLocal()
    try:
        # Upsert site
        site = db.query(Site).filter(Site.domain == domain).first()
        if not site:
            site = Site(domain=domain)
            db.add(site)
            db.flush()
        site.last_seen = datetime.now(timezone.utc)

        # Create scan
        scan = Scan(
            site_id=site.id,
            page_url=page_url,
            element_count=element_count,
            flagged_element_count=flagged_count,
            trust_score=trust_score,
            trust_grade=trust_grade,
            risk_level=risk_level,
            method=method,
            llm_used=int(llm_used),
        )
        scan.pattern_breakdown = pattern_breakdown
        db.add(scan)
        db.flush()

        # Create detected pattern rows
        for det in detections:
            primary = det.get("primary_pattern") or det.get("merged", {}).get("primary_pattern")
            if not primary:
                continue
            conf = det.get("confidence") or (
                det.get("merged", {}).get("confidence")
                or max(det.get("confidence_scores", {}).values(), default=0.0)
            )
            dp = DetectedPattern(
                scan_id=scan.id,
                element_text=(det.get("text") or "")[:500],
                element_type=det.get("element_type", "div"),
                pattern_type=primary,
                confidence=float(conf),
                severity=det.get("severity") or det.get("merged", {}).get("severity", "low"),
                detected_by="llm_hybrid" if det.get("llm") else "rule",
                explanation=(
                    det.get("explanation")
                    or det.get("merged", {}).get("explanation")
                    or (det.get("llm") or {}).get("explanation", "")
                    or ""
                ),
                remediation=(
                    det.get("remediation")
                    or det.get("merged", {}).get("remediation")
                    or (det.get("llm") or {}).get("remediation", "")
                    or ""
                ),
            )
            db.add(dp)

        # Trust score history
        tsh = TrustScoreHistory(
            site_id=site.id,
            scan_id=scan.id,
            score=trust_score,
            grade=trust_grade,
            risk_level=risk_level,
            pattern_count=flagged_count,
        )
        db.add(tsh)

        db.commit()
        db.refresh(scan)
        return scan
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Trust history helpers ─────────────────────────────────────────────────────

def get_trust_history(domain: str, limit: int = 30) -> List[Dict[str, Any]]:
    """Return recent trust score history for a domain (newest first)."""
    db = SessionLocal()
    try:
        site = db.query(Site).filter(Site.domain == domain).first()
        if not site:
            return []
        rows = (
            db.query(TrustScoreHistory)
            .filter(TrustScoreHistory.site_id == site.id)
            .order_by(TrustScoreHistory.recorded_at.desc())
            .limit(limit)
            .all()
        )
        return [r.to_dict() for r in rows]
    finally:
        db.close()


def get_historical_trust_summary(domain: str) -> Dict[str, Any]:
    """
    Compute aggregate trust metrics for a domain across all stored scans.

    Returns:
      avg_score, min_score, max_score, scan_count, trend (improving/stable/declining)
    """
    db = SessionLocal()
    try:
        site = db.query(Site).filter(Site.domain == domain).first()
        if not site:
            return {"scan_count": 0, "avg_score": None, "trend": "unknown"}

        rows = (
            db.query(TrustScoreHistory)
            .filter(TrustScoreHistory.site_id == site.id)
            .order_by(TrustScoreHistory.recorded_at.asc())
            .all()
        )
        if not rows:
            return {"scan_count": 0, "avg_score": None, "trend": "unknown"}

        scores = [r.score for r in rows]
        avg = round(sum(scores) / len(scores), 1)
        trend = _compute_trend(scores)

        return {
            "scan_count": len(scores),
            "avg_score": avg,
            "min_score": round(min(scores), 1),
            "max_score": round(max(scores), 1),
            "latest_score": round(scores[-1], 1),
            "trend": trend,
            "first_seen": rows[0].recorded_at.isoformat() if rows[0].recorded_at else None,
            "last_seen": rows[-1].recorded_at.isoformat() if rows[-1].recorded_at else None,
        }
    finally:
        db.close()


def _compute_trend(scores: List[float]) -> str:
    """Simple linear trend: compare first half average vs second half average."""
    if len(scores) < 3:
        return "insufficient_data"
    mid = len(scores) // 2
    first_half = sum(scores[:mid]) / mid
    second_half = sum(scores[mid:]) / (len(scores) - mid)
    delta = second_half - first_half
    if delta > 5:
        return "improving"
    if delta < -5:
        return "declining"
    return "stable"


# ── Feedback helpers ──────────────────────────────────────────────────────────

def record_feedback_db(
    element_text: str,
    detected_pattern: str,
    is_correct: bool,
    user_label: str = "",
    domain: str = "",
) -> UserFeedback:
    """Persist a feedback record to the DB."""
    db = SessionLocal()
    try:
        fb = UserFeedback(
            domain=domain or None,
            element_text=(element_text or "")[:500],
            detected_pattern=detected_pattern,
            is_correct=is_correct,
            user_label=user_label or None,
        )
        db.add(fb)
        db.commit()
        db.refresh(fb)
        return fb
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_feedback_stats() -> Dict[str, Any]:
    """Compute accuracy stats from the DB feedback table."""
    db = SessionLocal()
    try:
        all_fb = db.query(UserFeedback).all()
        total = len(all_fb)
        if total == 0:
            return {"total": 0, "correct": 0, "incorrect": 0, "accuracy": None}
        correct = sum(1 for f in all_fb if f.is_correct)
        by_pattern: Dict[str, Dict] = {}
        for f in all_fb:
            p = f.detected_pattern
            if p not in by_pattern:
                by_pattern[p] = {"total": 0, "correct": 0}
            by_pattern[p]["total"] += 1
            if f.is_correct:
                by_pattern[p]["correct"] += 1
        for p, stats in by_pattern.items():
            t = stats["total"]
            stats["accuracy"] = round(stats["correct"] / t, 3) if t else None
        return {
            "total": total,
            "correct": correct,
            "incorrect": total - correct,
            "accuracy": round(correct / total, 3),
            "by_pattern": by_pattern,
        }
    finally:
        db.close()

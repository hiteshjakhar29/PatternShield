"""
Feedback Service — persists user feedback to JSONL and provides query helpers.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List

from storage.json_store import JSONLStore

logger = logging.getLogger(__name__)


class FeedbackService:
    def __init__(self, feedback_file: str):
        self._store = JSONLStore(feedback_file)

    def record(
        self,
        text: str,
        detected_pattern: str,
        is_correct: bool,
        user_label: str = "",
        domain: str = "",
    ) -> Dict:
        entry = {
            "id": str(uuid.uuid4()),
            "text": text[:500],
            "detected_pattern": detected_pattern,
            "is_correct": bool(is_correct),
            "user_label": user_label or "",
            "domain": domain or "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            self._store.append(entry)
        except Exception as e:
            logger.warning(f"Could not persist feedback: {e}")
        return entry

    def all(self) -> List[Dict]:
        return self._store.read_all()

    def count(self) -> int:
        return self._store.count()

    def accuracy_stats(self) -> Dict:
        """Return simple accuracy statistics across all feedback."""
        records = self.all()
        if not records:
            return {"total": 0, "correct": 0, "incorrect": 0, "accuracy": None}
        correct = sum(1 for r in records if r.get("is_correct"))
        total = len(records)
        return {
            "total": total,
            "correct": correct,
            "incorrect": total - correct,
            "accuracy": round(correct / total, 4) if total > 0 else None,
        }

    def by_pattern(self) -> Dict[str, Dict]:
        """Group feedback by detected pattern type."""
        groups: Dict[str, Dict] = {}
        for r in self.all():
            pt = r.get("detected_pattern", "unknown")
            if pt not in groups:
                groups[pt] = {"total": 0, "correct": 0}
            groups[pt]["total"] += 1
            if r.get("is_correct"):
                groups[pt]["correct"] += 1
        for pt, g in groups.items():
            g["accuracy"] = round(g["correct"] / g["total"], 4) if g["total"] > 0 else None
        return groups

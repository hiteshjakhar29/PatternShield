"""
Temporal Service — persistent per-domain history for fake timer / persistent
urgency detection.

Data format (temporal.json):
{
  "domain.com": [
    {"text": "...", "pattern": "Urgency/Scarcity", "selector": "", "timestamp": "..."},
    ...
  ]
}
"""
import logging
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List

from storage.json_store import JSONStore

logger = logging.getLogger(__name__)

# Patterns that indicate countdown / timer language
_TIMER_PATTERNS = [
    re.compile(r"\d+\s*(left|remaining)", re.IGNORECASE),
    re.compile(r"(ends?|expires?)\s*in\s*\d+", re.IGNORECASE),
    re.compile(r"\btimer\b", re.IGNORECASE),
    re.compile(r"\bcountdown\b", re.IGNORECASE),
]


class TemporalService:
    def __init__(self, temporal_file: str, max_per_domain: int = 200):
        self._store = JSONStore(temporal_file, default={})
        self._max = max_per_domain

    # ── Write ──────────────────────────────────────────────────────────

    def record(self, domain: str, elements: List[Dict]) -> int:
        """Append elements for a domain; trim to max_per_domain."""
        now = datetime.now(timezone.utc).isoformat()

        def _update(data: dict) -> dict:
            bucket = data.get(domain, [])
            for elem in elements[:50]:
                bucket.append({
                    "text": (elem.get("text", "") or "")[:300],
                    "pattern": elem.get("pattern", ""),
                    "selector": elem.get("selector", ""),
                    "timestamp": now,
                })
            if len(bucket) > self._max:
                bucket = bucket[-self._max:]
            data[domain] = bucket
            return data

        try:
            data = self._store.update(_update)
            return len(data.get(domain, []))
        except Exception as e:
            logger.warning(f"Temporal record failed for {domain}: {e}")
            return 0

    # ── Read ───────────────────────────────────────────────────────────

    def history(self, domain: str) -> List[Dict]:
        data = self._store.read()
        return data.get(domain, [])

    def all_domains(self) -> List[str]:
        return list(self._store.read().keys())

    def domain_count(self) -> int:
        return len(self._store.read())

    # ── Analysis ───────────────────────────────────────────────────────

    def check(self, domain: str, current_elements: List[Dict]) -> List[Dict]:
        """
        Compare current page elements against stored history.
        Returns a list of flag dicts; 'type' field matches API docs.
        """
        history = self.history(domain)
        flags = []

        # Build index: normalized text → list of historical entries
        history_index = defaultdict(list)
        for h in history:
            key = (h.get("text") or "").lower().strip()
            if key:
                history_index[key].append(h)

        seen_timers: set = set()

        for elem in current_elements:
            text = (elem.get("text") or "").strip()
            text_lower = text.lower()

            # 1. Identical urgency text repeated across visits
            if text_lower in history_index:
                prev = history_index[text_lower]
                if len(prev) >= 2 and any(
                    p.get("pattern") == "Urgency/Scarcity" for p in prev
                ):
                    flags.append({
                        "type": "persistent_urgency",
                        "text": text,
                        "description": (
                            "This urgency message appeared identically across multiple visits, "
                            "suggesting it is static/fake rather than live."
                        ),
                        "occurrences": len(prev),
                        "first_seen": prev[0]["timestamp"],
                        "severity": "high",
                    })

            # 2. Timer / countdown language seen before (= timer resets)
            for pat in _TIMER_PATTERNS:
                if pat.search(text_lower):
                    similar = [
                        h for h in history
                        if pat.search((h.get("text") or "").lower())
                    ]
                    key = pat.pattern
                    if len(similar) >= 2 and key not in seen_timers:
                        seen_timers.add(key)
                        flags.append({
                            "type": "resetting_timer",
                            "text": text,
                            "description": (
                                "A countdown or timer appeared across multiple visits, "
                                "suggesting it resets between page loads (fake urgency)."
                            ),
                            "occurrences": len(similar),
                            "severity": "critical",
                        })
                    break

        return flags

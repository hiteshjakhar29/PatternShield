"""
PatternShield — Hybrid Detection Pipeline

Orchestrates the three-layer detection stack:

  Layer 1 — Rule-based (ml_detector.py)
    Fast, deterministic, always runs. 10-category keyword+regex engine
    with context-aware scoring, sentiment adjustment, and accessibility checks.

  Layer 2 — LLM semantic enrichment (services/llm_analyzer.py)
    Called ONLY when the rule layer shows sufficient signal
    (top confidence ≥ LLM_TRIGGER_THRESHOLD). This keeps API cost and
    latency proportional to actual detection activity — benign elements
    never trigger an LLM call.

  Layer 3 — Merge & verdict
    Combines both layers into a unified response that exposes all three
    result sets transparently. Merge strategy:
      - LLM wins on primary_pattern if confidence ≥ LLM_HIGH_CONFIDENCE
      - Both agree → confidence averaged (stronger signal)
      - LLM uncertain / unavailable → rule-based result used as-is

The response shape is designed to be interview-friendly:
  {
    "rule_based": { ... full rule result ... },
    "llm":        { ... LLM result or null ... },
    "merged":     { ... final verdict ... },
    // flat keys for backward-compat with existing extension code
    "primary_pattern": "...",
    "confidence": 0.0,
    ...
  }
"""
import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# LLM only triggered when rule-based top confidence meets this threshold
LLM_TRIGGER_THRESHOLD = float(__import__("os").getenv("LLM_TRIGGER_THRESHOLD", "0.25"))

# LLM is authoritative (overrides rule-based primary) above this threshold
LLM_HIGH_CONFIDENCE = 0.70


class PatternPipeline:
    """
    Hybrid detection pipeline: rule-based → LLM enrichment → merged verdict.

    Usage:
        pipeline = PatternPipeline(rule_detector, llm_analyzer)
        result = pipeline.analyze(text, element_type="button")
        # result["merged"]["primary_pattern"] — final verdict
        # result["llm"]                        — LLM details (or None)
        # result["rule_based"]                 — raw rule output
    """

    def __init__(self, rule_detector, llm_analyzer=None):
        self._rule = rule_detector
        self._llm = llm_analyzer

    # ── Public API ─────────────────────────────────────────────────────────────

    def analyze(
        self,
        text: str,
        element_type: str = "div",
        color: str = "#000000",
        use_sentiment: bool = True,
        use_enhanced: bool = True,
        font_size: Optional[Any] = None,
        opacity: Optional[Any] = None,
        position: Optional[Any] = None,
        parent_text: Optional[str] = None,
        enable_llm: bool = True,
    ) -> Dict[str, Any]:
        """
        Run the full pipeline on a single DOM element.

        Returns a dict with:
          - rule_based   : raw rule-based detection
          - llm          : LLM result (or None if skipped/failed)
          - merged       : authoritative final verdict
          - (flat keys)  : primary_pattern, confidence, severity, etc.
                           duplicated from merged for backward compatibility
          - llm_triggered: whether LLM was invoked
          - pipeline_latency_ms
        """
        t0 = time.time()

        # ── Layer 1: Rule-based ───────────────────────────────────────────────
        rule_result = self._rule.analyze_element(
            text=text,
            element_type=element_type,
            color=color,
            use_sentiment=use_sentiment,
            use_enhanced=use_enhanced,
            font_size=font_size,
            opacity=opacity,
            position=position,
            parent_text=parent_text,
        )

        # ── Layer 2: LLM (conditional) ────────────────────────────────────────
        llm_result = None
        llm_triggered = False
        rule_top_conf = max(
            rule_result.get("confidence_scores", {}).values(), default=0.0
        )

        llm_available = (
            enable_llm
            and self._llm is not None
            and getattr(self._llm, "is_enabled", False)
        )

        if llm_available and rule_top_conf >= LLM_TRIGGER_THRESHOLD:
            llm_triggered = True
            llm_result = self._llm.analyze(
                text=text,
                element_type=element_type,
                context=parent_text or "",
            )

        # ── Layer 3: Merge ────────────────────────────────────────────────────
        merged = self._merge(rule_result, llm_result)
        merged["pipeline_latency_ms"] = round((time.time() - t0) * 1000, 2)
        merged["llm_triggered"] = llm_triggered
        return merged

    def batch_analyze(
        self,
        elements: List[Dict],
        enable_llm: bool = False,
    ) -> List[Dict]:
        """
        Batch-analyze multiple DOM elements.

        LLM is disabled by default in batch mode to avoid cost/latency
        explosion on large pages. Set enable_llm=True for targeted batches.
        """
        results = []
        for elem in elements:
            if isinstance(elem, str):
                elem = {"text": elem}

            text = (elem.get("text") or "").strip()
            if not text:
                results.append(_empty_result())
                continue

            r = self.analyze(
                text=text,
                element_type=elem.get("element_type", "div"),
                color=elem.get("color", "#000000"),
                font_size=elem.get("font_size") or elem.get("fontSize"),
                opacity=elem.get("opacity"),
                enable_llm=enable_llm,
            )
            r["text"] = text[:200]
            results.append(r)
        return results

    # ── Merge logic ────────────────────────────────────────────────────────────

    def _merge(self, rule: Dict, llm) -> Dict[str, Any]:
        """
        Produce a unified verdict from rule-based + LLM layers.

        Merge strategy (see module docstring for rationale):
          1. LLM high confidence → LLM wins on primary_pattern
          2. Both agree → average confidence (stronger signal)
          3. LLM uncertain or absent → rule-based result stands
        """
        rule_primary = rule.get("primary_pattern")
        rule_scores = rule.get("confidence_scores", {})
        rule_conf = rule_scores.get(rule_primary or "", 0.0)

        llm_dict = None
        if llm is not None:
            llm_dict = llm.to_dict() if hasattr(llm, "to_dict") else {
                "pattern": llm.pattern,
                "confidence": llm.confidence,
                "explanation": llm.explanation,
                "affected_element": llm.affected_element,
                "remediation": llm.remediation,
                "model": llm.model,
                "latency_ms": llm.latency_ms,
            }

        # Determine merged primary_pattern and confidence
        if llm and llm.pattern and llm.confidence >= LLM_HIGH_CONFIDENCE:
            # LLM is highly confident — override rule-based category
            merged_primary = llm.pattern
            merged_conf = round(llm.confidence, 3)
            merged_explanation = llm.explanation
            merged_remediation = llm.remediation
            merge_strategy = "llm_override"

        elif llm and llm.pattern and rule_primary == llm.pattern:
            # Both detectors agree — average their confidence scores
            merged_primary = rule_primary
            merged_conf = round((rule_conf + llm.confidence) / 2, 3)
            merged_explanation = (
                llm.explanation
                or rule.get("explanations", {}).get(rule_primary, "")
            )
            merged_remediation = llm.remediation
            merge_strategy = "consensus"

        else:
            # Fall back to rule-based result
            merged_primary = rule_primary
            merged_conf = round(rule_conf, 3)
            merged_explanation = rule.get("explanations", {}).get(rule_primary or "", "")
            merged_remediation = ""
            merge_strategy = "rule_fallback"

        merged_block = {
            "primary_pattern": merged_primary,
            "confidence": merged_conf,
            "detected_patterns": rule.get("detected_patterns", []),
            "severity": rule.get("severity", "none"),
            "explanation": merged_explanation,
            "remediation": merged_remediation,
            "is_cookie_consent": rule.get("is_cookie_consent", False),
            "accessibility_issues": rule.get("accessibility_issues", []),
            "merge_strategy": merge_strategy,
        }

        result = {
            # Structured layers — full transparency for API consumers
            "rule_based": {
                "primary_pattern": rule_primary,
                "detected_patterns": rule.get("detected_patterns", []),
                "confidence_scores": rule_scores,
                "explanations": rule.get("explanations", {}),
                "severity": rule.get("severity", "none"),
                "sentiment": rule.get("sentiment", {}),
                "is_cookie_consent": rule.get("is_cookie_consent", False),
                "accessibility_issues": rule.get("accessibility_issues", []),
            },
            "llm": llm_dict,
            "merged": merged_block,

            # Flat keys for backward compatibility with Chrome extension
            "primary_pattern": merged_primary,
            "detected_patterns": rule.get("detected_patterns", []),
            "confidence_scores": rule_scores,
            "confidence": merged_conf,
            "severity": rule.get("severity", "none"),
            "explanation": merged_explanation,
            "explanations": rule.get("explanations", {}),
            "is_cookie_consent": rule.get("is_cookie_consent", False),
            "accessibility_issues": rule.get("accessibility_issues", []),
            "sentiment": rule.get("sentiment", {}),
        }
        return result


# ── Helpers ────────────────────────────────────────────────────────────────────

def _empty_result() -> Dict[str, Any]:
    return {
        "text": "",
        "primary_pattern": None,
        "detected_patterns": [],
        "confidence_scores": {},
        "confidence": 0.0,
        "severity": "none",
        "explanations": {},
        "explanation": "",
        "remediation": "",
        "is_cookie_consent": False,
        "accessibility_issues": [],
        "rule_based": {},
        "llm": None,
        "merged": {"primary_pattern": None, "confidence": 0.0},
        "llm_triggered": False,
        "pipeline_latency_ms": 0.0,
    }

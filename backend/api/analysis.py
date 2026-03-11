"""
Analysis endpoints — single element, batch, and transformer variants.

v3.0: All endpoints now route through PatternPipeline (rule-based + LLM hybrid).
Response shape is backward-compatible with v2.x (flat keys preserved) but
also includes structured `rule_based`, `llm`, and `merged` layers for
API consumers that want full transparency.
"""
import logging
import time

from flask import Blueprint, jsonify, request, current_app

from api.auth import require_api_key

logger = logging.getLogger(__name__)
bp = Blueprint("analysis", __name__)


def _get_pipeline():
    """Return the PatternPipeline if available."""
    return current_app.config.get("PIPELINE")


def _get_rule_detector():
    """Fallback to raw rule detector when pipeline not initialised."""
    return current_app.config.get("DETECTORS", {}).get("rule")


# ── Single element ─────────────────────────────────────────────────────────────

@bp.route("/analyze", methods=["POST"])
@require_api_key
def analyze():
    """
    Analyze a single DOM element for dark patterns.

    Request body:
      text            (str, required)  — element text content
      element_type    (str)            — HTML tag name, e.g. "button"
      color           (str)            — computed text colour hex
      use_sentiment   (bool)           — enable TextBlob sentiment boost
      use_enhanced    (bool)           — enable context-aware scoring
      font_size       (number)         — computed font size (px)
      opacity         (number)         — computed opacity (0–1)
      position        (str)            — "fixed" | "absolute" etc.
      parent_text     (str)            — surrounding text for context
      enable_llm      (bool)           — force-disable LLM for this call

    Response shape (v3.0 — backward-compatible):
      {
        // Flat keys (v2.x compat)
        "primary_pattern": "Urgency/Scarcity" | null,
        "detected_patterns": [...],
        "confidence_scores": {...},
        "confidence": 0.87,
        "severity": "high",
        "explanation": "...",
        "explanations": {...},
        "is_cookie_consent": false,
        "accessibility_issues": [],
        "sentiment": {...},

        // Structured layers (v3.0 new)
        "rule_based": { ... },
        "llm": { "pattern": ..., "confidence": ..., "explanation": ...,
                 "remediation": ..., "model": ..., "latency_ms": ... } | null,
        "merged": { "primary_pattern": ..., "confidence": ..., ... },

        // Metadata
        "method": "llm_hybrid" | "rule_based_v2",
        "llm_triggered": true | false,
        "pipeline_latency_ms": 42.1,
        "latency_ms": 42.1
      }
    """
    from config import Config

    pipeline = _get_pipeline()
    rule = _get_rule_detector()
    if not pipeline and not rule:
        return jsonify({"error": "Detection service not available"}), 503

    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"error": "Missing required field: text"}), 400

    text = data.get("text", "")
    if not text or not str(text).strip():
        return jsonify({"error": "Empty text"}), 400
    if len(str(text)) > Config.MAX_TEXT_LENGTH:
        return jsonify({
            "error": f"Text too long (max {Config.MAX_TEXT_LENGTH} chars)"
        }), 400

    try:
        t0 = time.time()
        enable_llm = data.get("enable_llm", True)

        if pipeline:
            result = pipeline.analyze(
                text=str(text),
                element_type=data.get("element_type", "div"),
                color=data.get("color", "#000000"),
                use_sentiment=data.get("use_sentiment", True),
                use_enhanced=data.get("use_enhanced", True),
                font_size=data.get("font_size"),
                opacity=data.get("opacity"),
                position=data.get("position"),
                parent_text=data.get("parent_text"),
                enable_llm=bool(enable_llm),
            )
            method = "llm_hybrid" if result.get("llm_triggered") else "rule_based_v2"
        else:
            # Fallback: raw rule detector (pipeline failed to init)
            result = rule.analyze_element(
                text=str(text),
                element_type=data.get("element_type", "div"),
                color=data.get("color", "#000000"),
                use_sentiment=data.get("use_sentiment", True),
                use_enhanced=data.get("use_enhanced", True),
                font_size=data.get("font_size"),
                opacity=data.get("opacity"),
                position=data.get("position"),
                parent_text=data.get("parent_text"),
            )
            result["rule_based"] = result.copy()
            result["llm"] = None
            result["merged"] = {"primary_pattern": result.get("primary_pattern")}
            result["llm_triggered"] = False
            method = "rule_based_v2"

        latency_ms = round((time.time() - t0) * 1000, 2)
        result["method"] = method
        result["latency_ms"] = latency_ms
        return jsonify(result)

    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        return jsonify({"error": "Analysis failed", "details": str(e)}), 500


# ── Transformer endpoint ────────────────────────────────────────────────────────

@bp.route("/analyze/transformer", methods=["POST"])
@require_api_key
def analyze_transformer():
    """Analyze with fine-tuned DistilBERT (requires models/ directory)."""
    detectors = current_app.config.get("DETECTORS", {})
    transformer = detectors.get("transformer")
    if not transformer:
        return jsonify({
            "error": "Transformer model not available",
            "message": "Use /analyze for LLM-hybrid or rule-based detection.",
        }), 503

    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"error": "Missing required field: text"}), 400

    try:
        t0 = time.time()
        result = transformer.predict(data["text"], return_probabilities=True)
        return jsonify({
            **result,
            "method": "transformer",
            "latency_ms": round((time.time() - t0) * 1000, 2),
        })
    except Exception as e:
        logger.error(f"Transformer error: {e}", exc_info=True)
        return jsonify({"error": "Analysis failed", "details": str(e)}), 500


# ── Batch endpoint ─────────────────────────────────────────────────────────────

@bp.route("/batch/analyze", methods=["POST"])
@require_api_key
def batch_analyze():
    """
    Batch-analyze up to MAX_BATCH_SIZE DOM elements.

    LLM is disabled by default in batch mode (enable_llm: true to override).
    Rule-based analysis is always applied to all elements.

    Request body:
      elements    (list, required) — array of element objects
      enable_llm  (bool)          — set true to enable LLM on flagged elements
                                    (slower, costs API calls, higher accuracy)

    Response:
      {
        "results": [ <per-element result> ],
        "count": N,
        "method": "rule_based_v2" | "llm_hybrid",
        "llm_enabled_for_batch": false,
        "latency_ms": 123.4
      }
    """
    from config import Config

    pipeline = _get_pipeline()
    rule = _get_rule_detector()
    if not pipeline and not rule:
        return jsonify({"error": "Detection service not available"}), 503

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No body provided"}), 400

    # Accept both {elements:[...]} and legacy {texts:[...]}
    if "elements" in data:
        elements = data["elements"]
    elif "texts" in data:
        elements = [{"text": t} for t in data["texts"]]
    else:
        return jsonify({"error": "Provide 'elements' list"}), 400

    if not isinstance(elements, list) or len(elements) == 0:
        return jsonify({"error": "elements must be a non-empty array"}), 400

    if len(elements) > Config.MAX_BATCH_SIZE:
        return jsonify({
            "error": f"Batch limited to {Config.MAX_BATCH_SIZE} elements"
        }), 400

    enable_llm = bool(data.get("enable_llm", False))

    try:
        t0 = time.time()
        results = []

        if pipeline:
            raw = pipeline.batch_analyze(elements, enable_llm=enable_llm)
            for r in raw:
                results.append({
                    "text": r.get("text", "")[:200],
                    "primary_pattern": r.get("primary_pattern"),
                    "detected_patterns": r.get("detected_patterns", []),
                    "confidence_scores": r.get("confidence_scores", {}),
                    "confidence": r.get("confidence", 0.0),
                    "severity": r.get("severity", "none"),
                    "explanation": r.get("explanation", ""),
                    "explanations": r.get("explanations", {}),
                    "is_cookie_consent": r.get("is_cookie_consent", False),
                    "accessibility_issues": r.get("accessibility_issues", []),
                    "llm": r.get("llm"),
                    "merged": r.get("merged", {}),
                    "llm_triggered": r.get("llm_triggered", False),
                })
        else:
            # Fallback: raw rule detector
            for elem in elements:
                if isinstance(elem, str):
                    elem = {"text": elem}
                text = (elem.get("text") or "").strip()
                if not text:
                    results.append({
                        "text": "", "primary_pattern": None,
                        "detected_patterns": [], "confidence_scores": {},
                        "confidence": 0.0, "severity": "none",
                        "explanations": {}, "explanation": "",
                        "is_cookie_consent": False, "llm": None,
                    })
                    continue
                r = rule.analyze_element(
                    text=text,
                    element_type=elem.get("element_type", "div"),
                    color=elem.get("color", "#000000"),
                    font_size=elem.get("font_size") or elem.get("fontSize"),
                    opacity=elem.get("opacity"),
                )
                results.append({
                    "text": text[:200],
                    "primary_pattern": r["primary_pattern"],
                    "detected_patterns": r["detected_patterns"],
                    "confidence_scores": r["confidence_scores"],
                    "confidence": max(r.get("confidence_scores", {}).values(), default=0.0),
                    "severity": r["severity"],
                    "explanations": r["explanations"],
                    "explanation": "",
                    "is_cookie_consent": r["is_cookie_consent"],
                    "accessibility_issues": r.get("accessibility_issues", []),
                    "llm": None,
                })

        any_llm = any(r.get("llm_triggered") for r in results)
        latency_ms = round((time.time() - t0) * 1000, 2)
        return jsonify({
            "results": results,
            "count": len(results),
            "method": "llm_hybrid" if any_llm else "rule_based_v2",
            "llm_enabled_for_batch": enable_llm,
            "latency_ms": latency_ms,
        })

    except Exception as e:
        logger.error(f"Batch error: {e}", exc_info=True)
        return jsonify({"error": "Batch analysis failed", "details": str(e)}), 500

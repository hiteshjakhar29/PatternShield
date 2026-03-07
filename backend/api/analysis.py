"""
Analysis endpoints — single element, batch, and transformer variants.
"""
import logging
import time

from flask import Blueprint, jsonify, request, current_app

from api.auth import require_api_key

logger = logging.getLogger(__name__)
bp = Blueprint("analysis", __name__)


def _get_rule_detector():
    return current_app.config.get("DETECTORS", {}).get("rule")


# ── Single element ─────────────────────────────────────────────────────────

@bp.route("/analyze", methods=["POST"])
@require_api_key
def analyze():
    """Analyze a single DOM element for dark patterns."""
    from config import Config
    rule = _get_rule_detector()
    if not rule:
        return jsonify({"error": "Detector not available"}), 503

    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"error": "Missing required field: text"}), 400

    text = data["text"]
    if not text or not text.strip():
        return jsonify({"error": "Empty text"}), 400
    if len(text) > Config.MAX_TEXT_LENGTH:
        return jsonify({"error": f"Text too long (max {Config.MAX_TEXT_LENGTH} chars)"}), 400

    try:
        t0 = time.time()
        result = rule.analyze_element(
            text=text,
            element_type=data.get("element_type", "div"),
            color=data.get("color", "#000000"),
            use_sentiment=data.get("use_sentiment", True),
            use_enhanced=data.get("use_enhanced", True),
            font_size=data.get("font_size"),
            opacity=data.get("opacity"),
            position=data.get("position"),
            parent_text=data.get("parent_text"),
        )
        latency_ms = round((time.time() - t0) * 1000, 2)
        return jsonify({**result, "method": "rule_based_v2", "latency_ms": latency_ms})
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        return jsonify({"error": "Analysis failed", "details": str(e)}), 500


# ── Transformer endpoint ────────────────────────────────────────────────────

@bp.route("/analyze/transformer", methods=["POST"])
@require_api_key
def analyze_transformer():
    """Analyze with fine-tuned transformer (requires models/ directory)."""
    detectors = current_app.config.get("DETECTORS", {})
    transformer = detectors.get("transformer")
    if not transformer:
        return jsonify({
            "error": "Transformer model not available",
            "message": "Use /analyze for rule-based detection.",
        }), 503

    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"error": "Missing required field: text"}), 400

    try:
        t0 = time.time()
        result = transformer.predict(data["text"], return_probabilities=True)
        return jsonify({**result, "method": "transformer", "latency_ms": round((time.time() - t0) * 1000, 2)})
    except Exception as e:
        logger.error(f"Transformer error: {e}", exc_info=True)
        return jsonify({"error": "Analysis failed", "details": str(e)}), 500


# ── Batch endpoint ──────────────────────────────────────────────────────────

@bp.route("/batch/analyze", methods=["POST"])
@require_api_key
def batch_analyze():
    """Batch-analyze up to MAX_BATCH_SIZE elements."""
    from config import Config
    rule = _get_rule_detector()
    if not rule:
        return jsonify({"error": "Detector not available"}), 503

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
        return jsonify({"error": f"Batch limited to {Config.MAX_BATCH_SIZE} elements"}), 400

    results = []
    try:
        t0 = time.time()
        for elem in elements:
            if isinstance(elem, str):
                elem = {"text": elem}
            text = (elem.get("text") or "").strip()
            if not text:
                results.append({
                    "text": "", "primary_pattern": None,
                    "detected_patterns": [], "confidence_scores": {},
                    "severity": "none", "explanations": {}, "is_cookie_consent": False,
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
                "severity": r["severity"],
                "explanations": r["explanations"],
                "is_cookie_consent": r["is_cookie_consent"],
                "accessibility_issues": r.get("accessibility_issues", []),
            })

        latency_ms = round((time.time() - t0) * 1000, 2)
        return jsonify({
            "results": results,
            "count": len(results),
            "method": "rule_based_v2",
            "latency_ms": latency_ms,
        })
    except Exception as e:
        logger.error(f"Batch error: {e}", exc_info=True)
        return jsonify({"error": "Batch analysis failed", "details": str(e)}), 500

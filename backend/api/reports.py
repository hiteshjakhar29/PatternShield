"""
Report endpoints — site scoring and offline rule export.
"""
import logging
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, current_app

from api.auth import require_api_key

logger = logging.getLogger(__name__)
bp = Blueprint("reports", __name__)


@bp.route("/site-score", methods=["POST"])
@require_api_key
def site_score():
    """Calculate a trust score (0-100 / A-F) for a full site scan."""
    from ml_detector import DarkPatternDetector
    data = request.get_json(silent=True)
    if not data or "detections" not in data:
        return jsonify({"error": "Missing 'detections'"}), 400

    try:
        score = DarkPatternDetector.calculate_site_score(data["detections"])
        score["domain"] = data.get("domain", "unknown")
        score["timestamp"] = datetime.now(timezone.utc).isoformat()
        return jsonify(score)
    except Exception as e:
        logger.error(f"Site score error: {e}", exc_info=True)
        return jsonify({"error": "Scoring failed", "details": str(e)}), 500


@bp.route("/offline-rules", methods=["GET"])
def offline_rules():
    """Export detection rules for client-side offline detection."""
    detectors = current_app.config.get("DETECTORS", {})
    rule = detectors.get("rule")
    if not rule:
        return jsonify({"error": "Detector not available"}), 503

    rules = {}
    for ptype, cfg in rule.PATTERNS.items():
        rules[ptype] = {
            "keywords": cfg.get("keywords", []),
            "patterns": cfg.get("patterns", []),
            "negative_keywords": cfg.get("negative_keywords", []),
            "severity_weight": cfg.get("severity_weight", 0.5),
            "description": cfg.get("description", ""),
        }

    from config import Config
    return jsonify({
        "rules": rules,
        "cookie_signals": rule.COOKIE_SIGNALS,
        "version": Config.API_VERSION,
        "total_categories": len(rules),
    })

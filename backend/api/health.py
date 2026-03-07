"""
Health, metrics, and pattern catalog endpoints.
"""
import logging
import time
from datetime import datetime, timezone

from flask import Blueprint, jsonify, current_app

logger = logging.getLogger(__name__)
bp = Blueprint("health", __name__)

# Module-level startup timestamp for uptime reporting
_START_TIME = time.time()


@bp.route("/", methods=["GET"])
def index():
    """Root — API overview."""
    from config import Config
    return jsonify({
        "name": "PatternShield API",
        "version": Config.API_VERSION,
        "status": "running",
        "endpoints": {
            "GET  /":                    "API overview (this response)",
            "GET  /health":              "Health check + service status",
            "GET  /metrics":             "Runtime metrics",
            "GET  /pattern-types":       "All 10 pattern categories",
            "GET  /offline-rules":       "Export rules for offline mode",
            "POST /analyze":             "Analyze single element",
            "POST /analyze/transformer": "Transformer-based analysis (if loaded)",
            "POST /batch/analyze":       "Batch analyze up to 100 elements",
            "POST /site-score":          "Site-level trust score (A-F)",
            "POST /feedback":            "Submit accuracy feedback",
            "GET  /report/feedback":     "Aggregated feedback accuracy report",
            "POST /temporal/record":     "Record elements for temporal tracking",
            "POST /temporal/check":      "Check for fake timers / persistent urgency",
        },
    })


@bp.route("/health", methods=["GET"])
def health():
    """Service health check."""
    from config import Config
    detectors = current_app.config.get("DETECTORS", {})
    feedback_svc = current_app.config.get("FEEDBACK_SERVICE")
    temporal_svc = current_app.config.get("TEMPORAL_SERVICE")

    uptime_s = round(time.time() - _START_TIME, 1)

    return jsonify({
        "status": "healthy",
        "version": Config.API_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_s,
        "models": {
            "rule_based":  detectors.get("rule") is not None,
            "transformer": detectors.get("transformer") is not None,
            "ensemble":    detectors.get("ensemble") is not None,
        },
        "services": {
            "feedback": feedback_svc is not None,
            "temporal": temporal_svc is not None,
        },
        "config": {
            "environment":   Config.FLASK_ENV,
            "rate_limiting": Config.RATE_LIMIT_ENABLED,
            "authentication": Config.API_KEY_REQUIRED,
            "confidence_threshold": Config.CONFIDENCE_THRESHOLD,
        },
        "pattern_categories": 10,
    })


@bp.route("/metrics", methods=["GET"])
def metrics():
    """Runtime metrics."""
    feedback_svc = current_app.config.get("FEEDBACK_SERVICE")
    temporal_svc = current_app.config.get("TEMPORAL_SERVICE")

    feedback_count   = feedback_svc.count() if feedback_svc else 0
    temporal_domains = temporal_svc.domain_count() if temporal_svc else 0
    accuracy_stats   = feedback_svc.accuracy_stats() if feedback_svc else {}

    return jsonify({
        "uptime_seconds":          round(time.time() - _START_TIME, 1),
        "feedback_total":          feedback_count,
        "feedback_accuracy":       accuracy_stats.get("accuracy"),
        "temporal_domains_tracked": temporal_domains,
        "pattern_categories":      10,
    })


@bp.route("/pattern-types", methods=["GET"])
def pattern_types():
    """Return all supported pattern types and metadata."""
    detectors = current_app.config.get("DETECTORS", {})
    rule = detectors.get("rule")
    if not rule:
        return jsonify({"error": "Detector not available"}), 503
    return jsonify({
        "pattern_types": rule.get_all_pattern_types(),
        "total": len(rule.PATTERNS),
    })

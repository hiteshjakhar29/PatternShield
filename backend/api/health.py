"""
Health, metrics, and pattern catalog endpoints.
v3.0: health check now reports LLM status and DB connectivity.
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
        "detection_pipeline": "rule_based + llm_hybrid",
        "endpoints": {
            "GET  /":                      "API overview (this response)",
            "GET  /health":                "Health check + service status",
            "GET  /metrics":               "Runtime metrics",
            "GET  /pattern-types":         "All 10 pattern categories",
            "GET  /offline-rules":         "Export rules for offline mode",
            "POST /analyze":               "Analyze single element (rule + LLM)",
            "POST /analyze/transformer":   "Transformer-based analysis (if loaded)",
            "POST /batch/analyze":         "Batch analyze up to 100 elements",
            "POST /site-score":            "Site-level trust score (A-F) + persist",
            "GET  /site-score/history":    "Historical trust score trend for domain",
            "POST /feedback":              "Submit accuracy feedback",
            "GET  /report/feedback":       "Aggregated feedback accuracy report",
            "POST /temporal/record":       "Record elements for temporal tracking",
            "POST /temporal/check":        "Check for fake timers / persistent urgency",
        },
    })


@bp.route("/health", methods=["GET"])
def health():
    """Service health check including LLM and DB status."""
    from config import Config
    detectors = current_app.config.get("DETECTORS", {})
    feedback_svc = current_app.config.get("FEEDBACK_SERVICE")
    temporal_svc = current_app.config.get("TEMPORAL_SERVICE")
    llm = current_app.config.get("LLM_ANALYZER")
    pipeline = current_app.config.get("PIPELINE")

    uptime_s = round(time.time() - _START_TIME, 1)

    return jsonify({
        "status": "healthy",
        "version": Config.API_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_s,
        "detection": {
            "rule_based":    detectors.get("rule") is not None,
            "transformer":   detectors.get("transformer") is not None,
            "ensemble":      detectors.get("ensemble") is not None,
            "llm":           getattr(llm, "is_enabled", False),
            "llm_model":     Config.LLM_MODEL if getattr(llm, "is_enabled", False) else None,
            "pipeline":      pipeline is not None,
        },
        "persistence": {
            "database":  current_app.config.get("DB_ENABLED", False),
            "db_engine": Config.DATABASE_URL.split("://")[0] if Config.DATABASE_URL else None,
            "feedback":  feedback_svc is not None,
            "temporal":  temporal_svc is not None,
        },
        "config": {
            "environment":          Config.FLASK_ENV,
            "rate_limiting":        Config.RATE_LIMIT_ENABLED,
            "authentication":       Config.API_KEY_REQUIRED,
            "confidence_threshold": Config.CONFIDENCE_THRESHOLD,
            "llm_trigger_threshold": Config.LLM_TRIGGER_THRESHOLD,
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

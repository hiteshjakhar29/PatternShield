"""
Report endpoints — site scoring and offline rule export.

v3.0: /site-score now persists results to the DB and returns historical
      trust trend alongside the current score. New /site-score/history
      endpoint exposes full time-series data for a domain.
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
    """
    Calculate a trust score for a full page scan and persist it.

    Request body:
      detections  (list, required) — output from /batch/analyze
      domain      (str)            — site domain for history tracking
      page_url    (str)            — full URL (optional)

    Response includes current score + historical context from the DB.
    """
    from ml_detector import DarkPatternDetector

    data = request.get_json(silent=True)
    if not data or "detections" not in data:
        return jsonify({"error": "Missing 'detections'"}), 400

    domain = data.get("domain", "unknown")
    page_url = data.get("page_url")
    detections = data["detections"]

    try:
        # Compute current trust score
        score_data = DarkPatternDetector.calculate_site_score(detections)
        score_data["domain"] = domain
        score_data["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Persist to DB (best-effort — never fails the response)
        persisted = False
        scan_id = None
        history = {}

        if current_app.config.get("DB_ENABLED"):
            try:
                from database import record_scan, get_historical_trust_summary

                llm_used = any(d.get("llm") for d in detections if isinstance(d, dict))
                method = "llm_hybrid" if llm_used else "rule_based_v2"

                scan = record_scan(
                    domain=domain,
                    trust_score=score_data["score"],
                    trust_grade=score_data["grade"],
                    risk_level=score_data["risk_level"],
                    element_count=score_data.get("total_elements", len(detections)),
                    flagged_count=score_data.get("flagged_elements", 0),
                    method=method,
                    llm_used=llm_used,
                    pattern_breakdown=score_data.get("pattern_breakdown", {}),
                    detections=detections,
                    page_url=page_url,
                )
                persisted = True
                scan_id = scan.id
                history = get_historical_trust_summary(domain)
            except Exception as db_err:
                logger.warning(f"DB persist failed (non-fatal): {db_err}")

        score_data["history"] = history
        score_data["persisted"] = persisted
        score_data["scan_id"] = scan_id
        return jsonify(score_data)

    except Exception as e:
        logger.error(f"Site score error: {e}", exc_info=True)
        return jsonify({"error": "Scoring failed", "details": str(e)}), 500


@bp.route("/site-score/history", methods=["GET"])
@require_api_key
def site_score_history():
    """
    Return historical trust score trend for a domain.

    Query params:
      domain  (str, required)
      limit   (int, default 30)
    """
    if not current_app.config.get("DB_ENABLED"):
        return jsonify({"error": "Database not available"}), 503

    domain = request.args.get("domain", "").strip()
    if not domain:
        return jsonify({"error": "Missing 'domain' query parameter"}), 400

    limit = min(int(request.args.get("limit", 30)), 100)

    try:
        from database import get_trust_history, get_historical_trust_summary
        history = get_trust_history(domain, limit=limit)
        summary = get_historical_trust_summary(domain)
        return jsonify({
            "domain": domain,
            "summary": summary,
            "history": history,
        })
    except Exception as e:
        logger.error(f"History fetch error: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch history", "details": str(e)}), 500


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

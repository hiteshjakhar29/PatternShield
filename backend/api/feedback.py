"""
Feedback endpoints — collect and report user corrections on detections.
"""
import logging
from flask import Blueprint, jsonify, request, current_app

logger = logging.getLogger(__name__)
bp = Blueprint("feedback", __name__)


@bp.route("/feedback", methods=["POST"])
def submit_feedback():
    """Record user feedback (thumbs up/down) on a detection."""
    svc = current_app.config.get("FEEDBACK_SERVICE")
    if not svc:
        return jsonify({"error": "Feedback service not available"}), 503

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No body provided"}), 400

    required = ["text", "detected_pattern", "is_correct"]
    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    entry = svc.record(
        text=data["text"],
        detected_pattern=data["detected_pattern"],
        is_correct=data["is_correct"],
        user_label=data.get("user_label", ""),
        domain=data.get("domain", ""),
    )
    return jsonify({
        "success": True,
        "entry": entry,
        "total_feedback": svc.count(),
    })


@bp.route("/report/feedback", methods=["GET"])
def feedback_report():
    """Aggregate accuracy report across all feedback."""
    svc = current_app.config.get("FEEDBACK_SERVICE")
    if not svc:
        return jsonify({"error": "Feedback service not available"}), 503

    return jsonify({
        "overall": svc.accuracy_stats(),
        "by_pattern": svc.by_pattern(),
    })

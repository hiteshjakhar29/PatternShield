"""
Temporal detection endpoints — record element snapshots and detect
fake timers / persistent urgency across visits.
"""
import logging

from flask import Blueprint, jsonify, request, current_app

from api.auth import require_api_key

logger = logging.getLogger(__name__)
bp = Blueprint("temporal", __name__)


@bp.route("/temporal/record", methods=["POST"])
@require_api_key
def temporal_record():
    """Store element snapshots for a domain visit."""
    svc = current_app.config.get("TEMPORAL_SERVICE")
    if not svc:
        return jsonify({"error": "Temporal service not available"}), 503

    data = request.get_json(silent=True)
    if not data or "domain" not in data or "elements" not in data:
        return jsonify({"error": "Missing 'domain' or 'elements'"}), 400

    stored = svc.record(data["domain"], data["elements"])
    return jsonify({"success": True, "domain": data["domain"], "stored": stored})


@bp.route("/temporal/check", methods=["POST"])
@require_api_key
def temporal_check():
    """Check current elements against historical snapshots for fraud signals."""
    svc = current_app.config.get("TEMPORAL_SERVICE")
    if not svc:
        return jsonify({"error": "Temporal service not available"}), 503

    data = request.get_json(silent=True)
    if not data or "domain" not in data:
        return jsonify({"error": "Missing 'domain'"}), 400

    flags = svc.check(data["domain"], data.get("elements", []))
    return jsonify({
        "domain": data["domain"],
        "flags": flags,
        "temporal_issues": len(flags),
        "history_size": len(svc.history(data["domain"])),
    })

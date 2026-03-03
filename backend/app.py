"""
PatternShield API Server v2.0 - Production
Flask API with enhanced dark pattern detection (10 categories),
feedback loop, site scoring, temporal tracking, and offline support.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import os
import logging
import time
import json
from functools import wraps
from datetime import datetime, timezone
from collections import defaultdict

from ml_detector import DarkPatternDetector

# ═══════════════════════════════════════════════════════════════════════════
# APP SETUP
# ═══════════════════════════════════════════════════════════════════════════

app = Flask(__name__)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    RATE_LIMIT_PER_HOUR = os.getenv("RATE_LIMIT_PER_HOUR", "500")
    RATE_LIMIT_PER_MINUTE = os.getenv("RATE_LIMIT_PER_MINUTE", "60")
    API_KEY_REQUIRED = os.getenv("API_KEY_REQUIRED", "False").lower() == "true"
    API_KEY = os.getenv("API_KEY", None)
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    TRANSFORMER_ENABLED = os.path.exists("models/distilbert_darkpattern/best_model")
    FEEDBACK_FILE = os.getenv("FEEDBACK_FILE", "data/feedback.jsonl")


app.config.from_object(Config)

# Logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("logs/app.log")],
)
logger = logging.getLogger(__name__)

# CORS
CORS(app, resources={
    r"/*": {
        "origins": Config.CORS_ORIGINS,
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-API-Key"],
        "expose_headers": ["X-Request-ID"],
        "supports_credentials": True,
    }
})

# Security headers (production only)
if not Config.DEBUG:
    Talisman(app,
             force_https=False,  # Let reverse proxy handle HTTPS
             strict_transport_security=True,
             session_cookie_secure=True,
             content_security_policy=None)  # Extension needs flexible CSP

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[f"{Config.RATE_LIMIT_PER_HOUR}/hour",
                    f"{Config.RATE_LIMIT_PER_MINUTE}/minute"],
    storage_uri="memory://",
    enabled=Config.RATE_LIMIT_ENABLED,
)

# ═══════════════════════════════════════════════════════════════════════════
# AUTH & MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════════


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not Config.API_KEY_REQUIRED:
            return f(*args, **kwargs)
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != Config.API_KEY:
            logger.warning(f"Unauthorized: {request.remote_addr}")
            return jsonify({"error": "Invalid or missing API key"}), 401
        return f(*args, **kwargs)
    return decorated


@app.before_request
def before_request():
    request.start_time = time.time()
    request.request_id = os.urandom(8).hex()
    if request.path not in ("/health", "/metrics"):
        logger.info(f"→ {request.method} {request.path} from {request.remote_addr}")


@app.after_request
def after_request(response):
    if hasattr(request, "start_time"):
        elapsed = time.time() - request.start_time
        response.headers["X-Request-ID"] = getattr(request, "request_id", "")
        response.headers["X-Response-Time"] = f"{elapsed:.3f}s"
        if request.path not in ("/health", "/metrics"):
            logger.info(f"← {response.status_code} in {elapsed:.3f}s")
    return response


# ═══════════════════════════════════════════════════════════════════════════
# INIT MODELS
# ═══════════════════════════════════════════════════════════════════════════

logger.info("Initializing PatternShield v2.0...")

rule_detector = None
try:
    rule_detector = DarkPatternDetector()
    logger.info("✓ Rule-based detector loaded (10 categories)")
except Exception as e:
    logger.error(f"✗ Failed to load detector: {e}")

transformer_detector = None
ensemble_detector = None
if Config.TRANSFORMER_ENABLED:
    try:
        from transformer_detector import TransformerDetector, EnsembleDetector
        transformer_detector = TransformerDetector()
        ensemble_detector = EnsembleDetector()
        logger.info("✓ Transformer model loaded")
    except Exception as e:
        logger.warning(f"Transformer not available: {e}")

# In-memory feedback and temporal stores
feedback_store = []
temporal_store = defaultdict(list)  # domain -> [{text, pattern, timestamp}, ...]

# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

# ── Health & Info ─────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    """Root endpoint — shows API info."""
    return jsonify({
        "name": "PatternShield API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "GET /health": "Health check",
            "GET /pattern-types": "List all 10 pattern categories",
            "GET /offline-rules": "Export rules for offline mode",
            "POST /analyze": "Analyze single element",
            "POST /batch/analyze": "Batch analyze (up to 100)",
            "POST /site-score": "Site-level dark pattern score",
            "POST /feedback": "Submit feedback on detection",
            "POST /temporal/record": "Record element for temporal tracking",
            "POST /temporal/check": "Check for persistent/resetting patterns",
        },
        "docs": "Send POST to /analyze with {\"text\": \"Only 3 left in stock!\"} to test",
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "models": {
            "rule_based": rule_detector is not None,
            "transformer": transformer_detector is not None,
            "ensemble": ensemble_detector is not None,
        },
        "config": {
            "environment": Config.FLASK_ENV,
            "rate_limiting": Config.RATE_LIMIT_ENABLED,
            "authentication": Config.API_KEY_REQUIRED,
        },
        "pattern_categories": 10,
    })


@app.route("/metrics", methods=["GET"])
def metrics():
    return jsonify({
        "feedback_count": len(feedback_store),
        "temporal_domains": len(temporal_store),
        "pattern_categories": 10,
    })


@app.route("/pattern-types", methods=["GET"])
def pattern_types():
    """Return all supported pattern types and their metadata."""
    if not rule_detector:
        return jsonify({"error": "Detector not available"}), 503
    return jsonify({
        "pattern_types": rule_detector.get_all_pattern_types(),
        "total": len(rule_detector.PATTERNS),
    })


# ── Core Analysis ─────────────────────────────────────────────────────────

@app.route("/analyze", methods=["POST"])
@limiter.limit(f"{Config.RATE_LIMIT_PER_MINUTE}/minute")
@require_api_key
def analyze():
    """Analyze text for dark patterns (enhanced v2)."""
    if not rule_detector:
        return jsonify({"error": "Detector not available"}), 503

    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400

    text = data["text"]
    if not text or not text.strip():
        return jsonify({"error": "Empty text provided"}), 400
    if len(text) > 2000:
        return jsonify({"error": "Text too long (max 2000 chars)"}), 400

    try:
        start = time.time()
        result = rule_detector.analyze_element(
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
        latency = time.time() - start

        return jsonify({
            "text": text,
            "primary_pattern": result["primary_pattern"],
            "detected_patterns": result["detected_patterns"],
            "confidence_scores": result["confidence_scores"],
            "sentiment": result["sentiment"],
            "explanations": result["explanations"],
            "severity": result["severity"],
            "is_cookie_consent": result["is_cookie_consent"],
            "accessibility_issues": result["accessibility_issues"],
            "method": "rule_based_v2",
            "latency_ms": round(latency * 1000, 2),
        })
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        return jsonify({"error": "Analysis failed", "details": str(e)}), 500


@app.route("/analyze/transformer", methods=["POST"])
@limiter.limit(f"{Config.RATE_LIMIT_PER_MINUTE}/minute")
@require_api_key
def analyze_transformer():
    """Analyze with transformer model."""
    if not transformer_detector:
        return jsonify({"error": "Transformer model not available",
                        "message": "Use /analyze for rule-based detection"}), 503

    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400

    try:
        start = time.time()
        result = transformer_detector.predict(data["text"], return_probabilities=True)
        latency = time.time() - start
        return jsonify({**result, "method": "transformer", "latency_ms": round(latency * 1000, 2)})
    except Exception as e:
        logger.error(f"Transformer error: {e}", exc_info=True)
        return jsonify({"error": "Analysis failed", "details": str(e)}), 500


# ── Batch Analysis ────────────────────────────────────────────────────────

@app.route("/batch/analyze", methods=["POST"])
@limiter.limit("500/hour")
@require_api_key
def batch_analyze():
    """Batch analyze multiple elements."""
    if not rule_detector:
        return jsonify({"error": "Detector not available"}), 503

    data = request.get_json()
    if not data or "elements" not in data:
        # Support legacy format: {"texts": [...]}
        if data and "texts" in data:
            elements = [{"text": t} for t in data["texts"]]
        else:
            return jsonify({"error": "No elements provided"}), 400
    else:
        elements = data["elements"]

    if len(elements) > 100:
        return jsonify({"error": "Batch limited to 100 elements"}), 400

    results = []
    try:
        for elem in elements:
            if isinstance(elem, str):
                elem = {"text": elem}

            text = elem.get("text", "")
            if not text:
                results.append({"text": "", "primary_pattern": None,
                                "detected_patterns": [], "confidence_scores": {},
                                "severity": "none"})
                continue

            r = rule_detector.analyze_element(
                text=text,
                element_type=elem.get("element_type", "div"),
                color=elem.get("color", "#000000"),
                font_size=elem.get("font_size"),
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
            })

        return jsonify({"results": results, "count": len(results), "method": "rule_based_v2"})
    except Exception as e:
        logger.error(f"Batch error: {e}", exc_info=True)
        return jsonify({"error": "Batch analysis failed", "details": str(e)}), 500


# ── Site Score ────────────────────────────────────────────────────────────

@app.route("/site-score", methods=["POST"])
@limiter.limit("50/hour")
@require_api_key
def site_score():
    """Calculate dark pattern score for a full site scan."""
    data = request.get_json()
    if not data or "detections" not in data:
        return jsonify({"error": "No detections provided"}), 400

    try:
        score = DarkPatternDetector.calculate_site_score(data["detections"])
        score["domain"] = data.get("domain", "unknown")
        score["timestamp"] = datetime.now(timezone.utc).isoformat()
        return jsonify(score)
    except Exception as e:
        logger.error(f"Site score error: {e}", exc_info=True)
        return jsonify({"error": "Scoring failed", "details": str(e)}), 500


# ── User Feedback ─────────────────────────────────────────────────────────

@app.route("/feedback", methods=["POST"])
@limiter.limit("50/hour")
def feedback():
    """Collect user feedback on detection accuracy."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required = ["text", "detected_pattern", "is_correct"]
    if not all(k in data for k in required):
        return jsonify({"error": f"Required fields: {required}"}), 400

    entry = {
        "text": data["text"][:500],
        "detected_pattern": data["detected_pattern"],
        "is_correct": bool(data["is_correct"]),
        "user_label": data.get("user_label", ""),
        "domain": data.get("domain", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    feedback_store.append(entry)

    # Persist to file
    try:
        os.makedirs(os.path.dirname(Config.FEEDBACK_FILE), exist_ok=True)
        with open(Config.FEEDBACK_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.warning(f"Could not persist feedback: {e}")

    return jsonify({"success": True, "total_feedback": len(feedback_store)})


# ── Temporal Detection ────────────────────────────────────────────────────

@app.route("/temporal/record", methods=["POST"])
@limiter.limit("100/hour")
@require_api_key
def temporal_record():
    """Record element snapshot for temporal pattern detection."""
    data = request.get_json()
    if not data or "domain" not in data or "elements" not in data:
        return jsonify({"error": "Missing domain or elements"}), 400

    domain = data["domain"]
    now = datetime.now(timezone.utc).isoformat()

    for elem in data["elements"][:50]:  # max 50 per request
        temporal_store[domain].append({
            "text": elem.get("text", "")[:300],
            "pattern": elem.get("pattern", ""),
            "selector": elem.get("selector", ""),
            "timestamp": now,
        })

    # Keep only last 200 entries per domain
    if len(temporal_store[domain]) > 200:
        temporal_store[domain] = temporal_store[domain][-200:]

    return jsonify({"success": True, "domain": domain,
                    "stored": len(temporal_store[domain])})


@app.route("/temporal/check", methods=["POST"])
@limiter.limit("100/hour")
@require_api_key
def temporal_check():
    """Check for temporal dark patterns (fake timers, persistent urgency)."""
    data = request.get_json()
    if not data or "domain" not in data:
        return jsonify({"error": "Missing domain"}), 400

    domain = data["domain"]
    history = temporal_store.get(domain, [])
    current_elements = data.get("elements", [])

    flags = []

    # Build history index
    history_texts = defaultdict(list)
    for h in history:
        history_texts[h["text"].lower().strip()].append(h)

    for elem in current_elements:
        text = elem.get("text", "").lower().strip()
        if text in history_texts:
            prev = history_texts[text]
            if len(prev) >= 2:
                # Same urgency text appearing across multiple visits = fake urgency
                if any(p.get("pattern") == "Urgency/Scarcity" for p in prev):
                    flags.append({
                        "text": elem.get("text", ""),
                        "issue": "persistent_urgency",
                        "description": "This urgency message has appeared identically across multiple visits",
                        "occurrences": len(prev),
                        "first_seen": prev[0]["timestamp"],
                    })

        # Check countdown timers that reset
        urgency_patterns = [r"\d+\s*(left|remaining)", r"(ends?|expires?)\s*in\s*\d+",
                            r"timer", r"countdown"]
        import re
        for pat in urgency_patterns:
            if re.search(pat, text):
                similar = [h for h in history if re.search(pat, h["text"].lower())]
                if len(similar) >= 2:
                    flags.append({
                        "text": elem.get("text", ""),
                        "issue": "resetting_timer",
                        "description": "Timer/countdown appears to reset between visits",
                        "occurrences": len(similar),
                    })
                break

    return jsonify({"domain": domain, "flags": flags, "temporal_issues": len(flags)})


# ── Offline Rules Export ──────────────────────────────────────────────────

@app.route("/offline-rules", methods=["GET"])
def offline_rules():
    """Export detection rules for client-side offline detection."""
    if not rule_detector:
        return jsonify({"error": "Detector not available"}), 503

    rules = {}
    for ptype, config in rule_detector.PATTERNS.items():
        rules[ptype] = {
            "keywords": config.get("keywords", []),
            "patterns": [p for p in (config.get("patterns", []))],
            "negative_keywords": config.get("negative_keywords", []),
            "severity_weight": config.get("severity_weight", 0.5),
            "description": config.get("description", ""),
        }

    return jsonify({
        "rules": rules,
        "version": "2.0.0",
        "total_categories": len(rules),
        "cookie_signals": rule_detector.COOKIE_SIGNALS,
    })


# ═══════════════════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found",
                    "available": ["/health", "/analyze", "/batch/analyze",
                                  "/site-score", "/feedback", "/temporal/record",
                                  "/temporal/check", "/pattern-types",
                                  "/offline-rules"]}), 404


@app.errorhandler(429)
def rate_limited(error):
    logger.warning(f"Rate limit: {request.remote_addr}")
    return jsonify({"error": "Rate limit exceeded",
                    "message": "Please try again later."}), 429


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}", exc_info=True)
    return jsonify({"error": "Internal server error"}), 500


# ═══════════════════════════════════════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  PatternShield API Server v2.0 — Production")
    print("=" * 70)
    print(f"  Environment:  {Config.FLASK_ENV}")
    print(f"  Debug:        {Config.DEBUG}")
    print(f"  Rate Limit:   {Config.RATE_LIMIT_ENABLED}")
    print(f"  Auth:         {Config.API_KEY_REQUIRED}")
    print(f"  Rule-based:   {'✓ 10 categories' if rule_detector else '✗'}")
    print(f"  Transformer:  {'✓' if transformer_detector else '✗'}")
    print("=" * 70)
    print("\n  Endpoints:")
    print("  GET  /health          — Health check")
    print("  GET  /pattern-types   — List all pattern categories")
    print("  GET  /offline-rules   — Export rules for offline mode")
    print("  POST /analyze         — Analyze single element")
    print("  POST /batch/analyze   — Batch analyze elements")
    print("  POST /site-score      — Calculate site-level score")
    print("  POST /feedback        — Submit detection feedback")
    print("  POST /temporal/record — Record element snapshot")
    print("  POST /temporal/check  — Check temporal patterns")
    print("=" * 70)
    print("\n  🚀 Starting server...")
    print("=" * 70 + "\n")

    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=Config.DEBUG)

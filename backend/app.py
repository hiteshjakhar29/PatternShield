"""
PatternShield API Server v3.0
Modular Flask application — blueprints registered from api/ package.

v3.0 additions:
  - SQLAlchemy database layer (SQLite default, PostgreSQL via DATABASE_URL)
  - LLM hybrid detection via Anthropic Claude (graceful no-op when key absent)
  - PatternPipeline service (rule-based + LLM merge)
  - Historical trust scoring backed by DB
  - Structured logging with request-ID tracing
"""
import logging
import os
import time

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman

from config import Config

# ── Logging ───────────────────────────────────────────────────────────────────

os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s  %(name)-28s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/app.log"),
    ],
)
logger = logging.getLogger(__name__)


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # ── Security headers (non-debug only) ────────────────────────────
    if not Config.DEBUG:
        Talisman(
            app,
            force_https=False,
            strict_transport_security=True,
            session_cookie_secure=True,
            content_security_policy=None,
        )

    # ── CORS ─────────────────────────────────────────────────────────
    CORS(app, resources={
        r"/*": {
            "origins": Config.CORS_ORIGINS,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "X-API-Key"],
            "expose_headers": ["X-Request-ID", "X-Response-Time"],
            "supports_credentials": True,
        }
    })

    # ── Rate limiting ─────────────────────────────────────────────────
    Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[
            f"{Config.RATE_LIMIT_PER_HOUR}/hour",
            f"{Config.RATE_LIMIT_PER_MINUTE}/minute",
        ],
        storage_uri="memory://",
        enabled=Config.RATE_LIMIT_ENABLED,
    )

    # ── Request middleware ────────────────────────────────────────────
    @app.before_request
    def _before():
        request.start_time = time.time()
        request.request_id = os.urandom(8).hex()
        if request.path not in ("/health", "/metrics"):
            logger.info(
                f"→ {request.method} {request.path} "
                f"[{request.remote_addr}] rid={request.request_id}"
            )

    @app.after_request
    def _after(response):
        if hasattr(request, "start_time"):
            elapsed = time.time() - request.start_time
            response.headers["X-Request-ID"] = getattr(request, "request_id", "")
            response.headers["X-Response-Time"] = f"{elapsed:.3f}s"
            if request.path not in ("/health", "/metrics"):
                logger.info(f"← {response.status_code}  {elapsed*1000:.1f}ms")
        return response

    # ── Database ──────────────────────────────────────────────────────
    logger.info("Initialising database…")
    try:
        from database import setup_database
        setup_database()
        app.config["DB_ENABLED"] = True
    except Exception as e:
        logger.error(f"✗ Database init failed: {e}", exc_info=True)
        app.config["DB_ENABLED"] = False

    # ── Load detectors ────────────────────────────────────────────────
    logger.info("Loading PatternShield detectors…")
    detectors = {}

    try:
        from ml_detector import DarkPatternDetector
        detectors["rule"] = DarkPatternDetector()
        logger.info("✓ Rule-based detector loaded (10 categories)")
    except Exception as e:
        logger.error(f"✗ Rule-based detector failed: {e}")

    if Config.TRANSFORMER_ENABLED:
        try:
            from transformer_detector import TransformerDetector, EnsembleDetector
            detectors["transformer"] = TransformerDetector()
            detectors["ensemble"] = EnsembleDetector()
            logger.info("✓ Transformer / ensemble detectors loaded")
        except Exception as e:
            logger.warning(f"Transformer not available: {e}")

    app.config["DETECTORS"] = detectors

    # ── LLM analyzer ─────────────────────────────────────────────────
    llm_analyzer = None
    if Config.LLM_ENABLED:
        try:
            from services.llm_analyzer import AnthropicLLMAnalyzer
            llm_analyzer = AnthropicLLMAnalyzer(
                api_key=Config.ANTHROPIC_API_KEY,
                model=Config.LLM_MODEL,
                timeout=Config.LLM_TIMEOUT,
            )
            status = "enabled" if llm_analyzer.is_enabled else "disabled (no API key)"
            logger.info(f"✓ LLM analyzer loaded — {status}")
        except Exception as e:
            logger.warning(f"LLM analyzer init failed: {e}")
    else:
        logger.info("LLM_ENABLED=false — skipping LLM analyzer")

    app.config["LLM_ANALYZER"] = llm_analyzer

    # ── Pattern pipeline ──────────────────────────────────────────────
    if detectors.get("rule"):
        try:
            from services.pattern_pipeline import PatternPipeline
            pipeline = PatternPipeline(
                rule_detector=detectors["rule"],
                llm_analyzer=llm_analyzer,
            )
            app.config["PIPELINE"] = pipeline
            logger.info("✓ PatternPipeline ready (rule-based + LLM hybrid)")
        except Exception as e:
            logger.warning(f"PatternPipeline init failed: {e}")
            app.config["PIPELINE"] = None
    else:
        app.config["PIPELINE"] = None

    # ── Load services ─────────────────────────────────────────────────
    try:
        from services.feedback_service import FeedbackService
        app.config["FEEDBACK_SERVICE"] = FeedbackService(Config.FEEDBACK_FILE)
        logger.info("✓ Feedback service ready (JSONL)")
    except Exception as e:
        logger.warning(f"Feedback service failed: {e}")

    try:
        from services.temporal_service import TemporalService
        app.config["TEMPORAL_SERVICE"] = TemporalService(
            Config.TEMPORAL_FILE, Config.MAX_TEMPORAL_PER_DOMAIN
        )
        logger.info("✓ Temporal service ready (persistent)")
    except Exception as e:
        logger.warning(f"Temporal service failed: {e}")

    # ── Register blueprints ───────────────────────────────────────────
    from api.health import bp as health_bp
    from api.analysis import bp as analysis_bp
    from api.feedback import bp as feedback_bp
    from api.temporal import bp as temporal_bp
    from api.reports import bp as reports_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(temporal_bp)
    app.register_blueprint(reports_bp)

    # ── Error handlers ────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(_):
        return jsonify({
            "error": "Endpoint not found",
            "hint": "GET / for a full list of endpoints",
        }), 404

    @app.errorhandler(429)
    def rate_limited(_):
        logger.warning(f"Rate limit hit: {request.remote_addr}")
        return jsonify({"error": "Rate limit exceeded", "message": "Please slow down."}), 429

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Internal error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

    return app


# ── Entry point ───────────────────────────────────────────────────────────────

app = create_app()

if __name__ == "__main__":
    llm_status = (
        f"{'active' if Config.ANTHROPIC_API_KEY else 'disabled (set ANTHROPIC_API_KEY)'}"
    )
    print("\n" + "=" * 66)
    print("  PatternShield API  v3.0  —  LLM-Hybrid Detection")
    print("=" * 66)
    print(f"  Environment  : {Config.FLASK_ENV}")
    print(f"  Debug        : {Config.DEBUG}")
    print(f"  Database     : {Config.DATABASE_URL.split('://')[0]}")
    print(f"  LLM          : {llm_status}")
    print(f"  Rate limit   : {Config.RATE_LIMIT_ENABLED}")
    print(f"  Auth         : {Config.API_KEY_REQUIRED}")
    print(f"  Transformer  : {Config.TRANSFORMER_ENABLED}")
    print("=" * 66)
    print(f"\n  API root  -> http://localhost:{Config.PORT}")
    print(f"  Health    -> http://localhost:{Config.PORT}/health")
    print("=" * 66 + "\n")

    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.DEBUG,
    )

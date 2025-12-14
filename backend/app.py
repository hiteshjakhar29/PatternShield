"""PatternShield Flask application with production-ready setup."""
from __future__ import annotations

import logging
import time
from typing import Any, Dict

from flask import Flask, jsonify, request
from flask_cors import CORS

from backend import auth, cache, database, error_tracking, health, logging_config, metrics, rate_limit, security
from backend.config import get_config
from backend.ml_detector import DarkPatternDetector
from backend.models import PredictionLog
from backend.transformer_detector import EnsembleDetector, TransformerDetector
from backend.validators import AnalyzeRequestSchema, validate_request


def create_app() -> Flask:
    config = get_config()
    logging_config.configure_logging(level=config.LOG_LEVEL, fmt=config.LOG_FORMAT)
    error_tracking.init_sentry(config)

    app = Flask(__name__)
    app.config.from_mapping(secret_key=config.SECRET_KEY)
    CORS(app, origins=config.CORS_ORIGINS, supports_credentials=True)
    security.configure_talisman(app)

    db_engine = database.create_db_engine(config)
    SessionLocal = database.create_session_factory(db_engine, pool_size=config.DB_POOL_SIZE)
    cache_client = cache.get_client(config.REDIS_URL)
    limiter = rate_limit.init_limiter(app, config, cache_client)

    metrics.init_metrics(app)

    detectors = _load_detectors(config)

    analyze_schema = AnalyzeRequestSchema()

    app.before_request(logging_config.attach_request_id)

    @app.route("/health")
    def healthcheck() -> Any:
        return health.liveness_response()

    @app.route("/health/ready")
    def readiness() -> Any:
        return health.readiness_response(db_engine, cache_client, detectors["transformer_available"])

    @app.route("/health/live")
    def live() -> Any:
        return health.liveness_response()

    @app.route("/analyze", methods=["POST"])
    @auth.require_api_key
    @limiter.limit(config.API_RATE_LIMIT, override_defaults=config.RATE_LIMIT_ENABLED)
    @metrics.track_request
    @validate_request(analyze_schema)
    def analyze(validated_data: Dict[str, Any]) -> Any:
        cache_key = cache.build_cache_key("analyze", validated_data)
        cache_hit, cached_payload = cache.get_cached_response(cache_client, cache_key)
        if cache_hit:
            _log_prediction(SessionLocal, validated_data["text"], cached_payload, config, cache_hit=True)
            return cache.cached_json_response({**cached_payload, "cache": True})

        start_time = time.time()
        text = validated_data["text"]
        result = detectors["rule"].analyze_element(
            text, validated_data.get("element_type", "div"), validated_data.get("color", "#000000")
        )
        formatted = _format_rule_response(text, result)
        duration_ms = int((time.time() - start_time) * 1000)
        _log_prediction(SessionLocal, text, formatted, config, duration_ms=duration_ms)
        cache.set_cached_response(cache_client, cache_key, formatted, config.CACHE_TTL)
        return cache.cached_json_response(formatted)

    @app.route("/analyze/transformer", methods=["POST"])
    @auth.require_api_key
    @auth.require_jwt
    @limiter.limit(config.API_RATE_LIMIT, override_defaults=config.RATE_LIMIT_ENABLED)
    @metrics.track_request
    @validate_request(analyze_schema)
    def analyze_transformer(validated_data: Dict[str, Any]) -> Any:
        if not detectors["transformer_available"]:
            return jsonify({"error": "Transformer model not available"}), 503
        start_time = time.time()
        prediction = detectors["transformer"].predict(validated_data["text"], return_probabilities=True)
        formatted = _format_transformer_response(prediction)
        duration_ms = int((time.time() - start_time) * 1000)
        _log_prediction(SessionLocal, validated_data["text"], formatted, config, duration_ms=duration_ms, model_version="transformer")
        return jsonify(formatted)

    @app.route("/analyze/ensemble", methods=["POST"])
    @auth.require_api_key
    @auth.require_jwt
    @limiter.limit(config.API_RATE_LIMIT, override_defaults=config.RATE_LIMIT_ENABLED)
    @metrics.track_request
    @validate_request(analyze_schema)
    def analyze_ensemble(validated_data: Dict[str, Any]) -> Any:
        if not detectors["transformer_available"]:
            return jsonify({"error": "Ensemble not available"}), 503
        start_time = time.time()
        result = detectors["ensemble"].predict(
            validated_data["text"], validated_data.get("element_type", "div"), validated_data.get("color", "#000000")
        )
        formatted = _format_ensemble_response(result)
        duration_ms = int((time.time() - start_time) * 1000)
        _log_prediction(SessionLocal, validated_data["text"], formatted, config, duration_ms=duration_ms, model_version="ensemble")
        return jsonify(formatted)

    app.logger.setLevel(logging.getLevelName(config.LOG_LEVEL))
    return app


def _load_detectors(config: Any) -> Dict[str, Any]:
    rule_detector = DarkPatternDetector()
    transformer_available = TransformerDetector.model_exists(config.MODEL_PATH)
    transformer_detector = TransformerDetector() if transformer_available else None
    ensemble_detector = EnsembleDetector() if transformer_available else None
    return {
        "rule": rule_detector,
        "transformer": transformer_detector,
        "ensemble": ensemble_detector,
        "transformer_available": transformer_available,
    }


def _format_rule_response(text: str, result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "text": text,
        "primary_pattern": result.get("primary_pattern"),
        "detected_patterns": result.get("detected_patterns", []),
        "confidence_scores": result.get("confidence_scores", {}),
        "sentiment": result.get("sentiment"),
        "method": "rule_based",
    }


def _format_transformer_response(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "text": result.get("text"),
        "label": result.get("label"),
        "confidence": result.get("confidence"),
        "probabilities": result.get("probabilities"),
        "method": "transformer",
    }


def _format_ensemble_response(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "text": result.get("text"),
        "label": result.get("label"),
        "confidence": result.get("confidence"),
        "probabilities": result.get("probabilities"),
        "transformer_prediction": result.get("transformer_prediction"),
        "rule_based_prediction": result.get("rule_based_prediction"),
        "method": "ensemble",
    }


def _extract_confidence(result: Dict[str, Any]) -> float:
    if "confidence" in result and result["confidence"] is not None:
        return float(result["confidence"])
    scores = result.get("confidence_scores", {})
    return float(max(scores.values())) if scores else 0.0


def _log_prediction(SessionLocal, text: str, result: Dict[str, Any], config, duration_ms: int | None = None, model_version: str = "rule_based", cache_hit: bool = False) -> None:
    try:
        with database.session_scope(SessionLocal) as session:
            session.add(
                PredictionLog(
                    text=text,
                    prediction=result.get("primary_pattern") or result.get("label") or "unknown",
                    confidence=_extract_confidence(result),
                    model_version=model_version,
                    api_key=request.headers.get(config.API_KEY_HEADER),
                    ip_address=request.remote_addr,
                    response_time_ms=duration_ms,
                    metadata_json={"cache_hit": cache_hit, "method": result.get("method")},
                )
            )
    except Exception as exc:  # pragma: no cover - avoid impacting response flow
        logging.getLogger(__name__).warning("Failed to log prediction: %s", exc)


if __name__ == "__main__":
    app = create_app()
    app.run(host=app.config.get("HOST", "0.0.0.0"), port=app.config.get("PORT", 5000))

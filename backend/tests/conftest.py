"""
Shared pytest fixtures for PatternShield backend tests.
"""
import sys
import os
import pytest

# Make backend/ importable from tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="session")
def app():
    """Create a test Flask app with test config."""
    os.environ.setdefault("FLASK_DEBUG", "false")
    os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
    os.environ.setdefault("API_KEY_REQUIRED", "false")
    os.environ.setdefault("FEEDBACK_FILE", "/tmp/test_feedback.jsonl")
    os.environ.setdefault("TEMPORAL_FILE", "/tmp/test_temporal.json")
    # Use in-memory SQLite for tests — fast, isolated, no file cleanup needed
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    os.environ.setdefault("TESTING", "true")
    # Disable LLM in tests — no API key available in CI; rule-based only
    os.environ.setdefault("LLM_ENABLED", "false")

    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture(scope="session")
def client(app):
    """Test client for the Flask app."""
    return app.test_client()


@pytest.fixture(scope="session")
def detector():
    """Shared DarkPatternDetector instance."""
    from ml_detector import DarkPatternDetector
    return DarkPatternDetector()

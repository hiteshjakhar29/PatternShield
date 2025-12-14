#!/usr/bin/env python3
"""Smoke tests to ensure critical components initialize."""

from __future__ import annotations

import pytest


def test_experiment_tracker(tmp_path):
    """Experiment tracker should log runs and return best model info."""

    from backend.experiments.experiment_tracker import ExperimentTracker

    tracker = ExperimentTracker(log_file=tmp_path / "test_smoke.json")
    tracker.log_experiment(
        name="smoke_test", config={"test": True}, metrics={"accuracy": 0.95}
    )
    best = tracker.get_best_model("accuracy")
    assert best is not None


def test_feature_extraction():
    """Feature extractor should return a non-empty feature vector."""

    from backend.feature_extraction import FeatureExtractor

    extractor = FeatureExtractor()
    features = extractor.extract_features(
        text="Only 2 left in stock!", element_type="span", color="#ff0000"
    )
    assert len(features) > 0


def test_cv_utils():
    """WCAG contrast helpers should compute expected values."""

    pytest.importorskip("cv2", reason="OpenCV not installed", exc_type=ImportError)
    from backend.cv_utils import calculate_contrast_ratio, check_wcag_compliance

    ratio = calculate_contrast_ratio((255, 255, 255), (0, 0, 0))
    assert 20.9 < ratio < 21.1
    compliance = check_wcag_compliance(ratio)
    assert compliance["compliant_aa"]


def test_vision_detector():
    """Vision detector should initialize when OpenCV is available."""

    pytest.importorskip("cv2", reason="OpenCV not installed", exc_type=ImportError)
    from backend.vision_detector import VisionDetector

    VisionDetector()


def test_multimodal_detector():
    """Multimodal detector should initialize when dependencies are present."""

    pytest.importorskip("cv2", reason="OpenCV not installed", exc_type=ImportError)
    from backend.multimodal_detector import MultimodalDetector

    MultimodalDetector()


def test_flask_app_import():
    """Flask application factory should be importable."""

    from backend import app

    assert hasattr(app, "create_app")

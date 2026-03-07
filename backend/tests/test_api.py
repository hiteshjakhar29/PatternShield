"""
Integration tests for PatternShield API endpoints.
"""
import json
import pytest


class TestHealth:
    def test_health_returns_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_has_version(self, client):
        data = r = client.get("/health").get_json()
        assert "version" in data
        assert data["version"] == "2.1.0"

    def test_health_has_status_healthy(self, client):
        data = client.get("/health").get_json()
        assert data["status"] == "healthy"

    def test_health_has_services(self, client):
        data = client.get("/health").get_json()
        assert "services" in data
        assert "models" in data

    def test_root_returns_endpoint_list(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.get_json()
        assert "endpoints" in data

    def test_metrics_returns_200(self, client):
        r = client.get("/metrics")
        assert r.status_code == 200

    def test_pattern_types_returns_10(self, client):
        data = client.get("/pattern-types").get_json()
        assert data["total"] == 10

    def test_offline_rules_export(self, client):
        data = client.get("/offline-rules").get_json()
        assert "rules" in data
        assert len(data["rules"]) == 10
        assert "version" in data


class TestAnalyze:
    def test_analyze_returns_200(self, client):
        r = client.post("/analyze", json={"text": "Only 3 left in stock!"})
        assert r.status_code == 200

    def test_analyze_detects_urgency(self, client):
        data = client.post("/analyze", json={"text": "Only 3 left in stock!"}).get_json()
        assert data["primary_pattern"] == "Urgency/Scarcity"

    def test_analyze_missing_text_returns_400(self, client):
        r = client.post("/analyze", json={})
        assert r.status_code == 400

    def test_analyze_empty_text_returns_400(self, client):
        r = client.post("/analyze", json={"text": ""})
        assert r.status_code == 400

    def test_analyze_returns_method_field(self, client):
        data = client.post("/analyze", json={"text": "test"}).get_json()
        assert "method" in data

    def test_analyze_returns_latency(self, client):
        data = client.post("/analyze", json={"text": "test"}).get_json()
        assert "latency_ms" in data

    def test_analyze_with_element_type(self, client):
        r = client.post("/analyze", json={
            "text": "No thanks, I hate saving money",
            "element_type": "a",
            "color": "#888888",
        })
        assert r.status_code == 200
        data = r.get_json()
        assert "primary_pattern" in data

    def test_analyze_clean_text_no_pattern(self, client):
        data = client.post("/analyze", json={"text": "Add to cart"}).get_json()
        # May or may not detect, but should not error
        assert "primary_pattern" in data
        assert "confidence_scores" in data

    def test_analyze_text_too_long_returns_400(self, client):
        r = client.post("/analyze", json={"text": "x" * 3000})
        assert r.status_code == 400


class TestBatchAnalyze:
    def test_batch_returns_results_array(self, client):
        payload = {"elements": [
            {"text": "Only 2 left in stock!"},
            {"text": "No thanks, I don't want savings"},
            {"text": "Add to cart"},
        ]}
        data = client.post("/batch/analyze", json=payload).get_json()
        assert "results" in data
        assert len(data["results"]) == 3

    def test_batch_count_matches(self, client):
        payload = {"elements": [{"text": f"item {i}"} for i in range(5)]}
        data = client.post("/batch/analyze", json=payload).get_json()
        assert data["count"] == 5

    def test_batch_has_latency(self, client):
        data = client.post("/batch/analyze", json={"elements": [{"text": "test"}]}).get_json()
        assert "latency_ms" in data

    def test_batch_empty_elements_returns_400(self, client):
        r = client.post("/batch/analyze", json={"elements": []})
        assert r.status_code == 400

    def test_batch_no_body_returns_400(self, client):
        r = client.post("/batch/analyze")
        assert r.status_code == 400

    def test_batch_missing_key_returns_400(self, client):
        r = client.post("/batch/analyze", json={"texts_wrong": []})
        assert r.status_code == 400

    def test_batch_each_result_has_required_fields(self, client):
        data = client.post("/batch/analyze", json={
            "elements": [{"text": "Free trial will auto-renew at $9.99"}]
        }).get_json()
        result = data["results"][0]
        assert "primary_pattern" in result
        assert "confidence_scores" in result
        assert "severity" in result
        assert "explanations" in result
        assert "is_cookie_consent" in result

    def test_batch_accepts_legacy_texts_format(self, client):
        data = client.post("/batch/analyze", json={
            "texts": ["Only 2 left!", "Add to cart"]
        }).get_json()
        assert "results" in data
        assert len(data["results"]) == 2


class TestSiteScore:
    def test_site_score_clean(self, client):
        data = client.post("/site-score", json={"detections": [], "domain": "example.com"}).get_json()
        assert data["score"] == 100
        assert data["grade"] == "A"
        assert data["domain"] == "example.com"

    def test_site_score_with_detections(self, client):
        payload = {
            "domain": "bad.example.com",
            "detections": [
                {"primary_pattern": "Urgency/Scarcity", "confidence_scores": {"Urgency/Scarcity": 0.9}},
                {"primary_pattern": "Hidden Costs",     "confidence_scores": {"Hidden Costs": 0.85}},
            ],
        }
        data = client.post("/site-score", json=payload).get_json()
        assert data["score"] < 100
        assert data["grade"] in ("A", "B", "C", "D", "F")
        assert "timestamp" in data

    def test_site_score_missing_detections_returns_400(self, client):
        r = client.post("/site-score", json={"domain": "x.com"})
        assert r.status_code == 400


class TestFeedback:
    def test_submit_feedback_success(self, client):
        payload = {
            "text": "Only 2 left!",
            "detected_pattern": "Urgency/Scarcity",
            "is_correct": True,
            "domain": "test.com",
        }
        r = client.post("/feedback", json=payload)
        assert r.status_code == 200
        data = r.get_json()
        assert data["success"] is True

    def test_submit_feedback_wrong(self, client):
        payload = {
            "text": "Sale ends soon",
            "detected_pattern": "Urgency/Scarcity",
            "is_correct": False,
        }
        r = client.post("/feedback", json=payload)
        assert r.status_code == 200

    def test_feedback_missing_field_returns_400(self, client):
        r = client.post("/feedback", json={"text": "test"})
        assert r.status_code == 400

    def test_feedback_report(self, client):
        data = client.get("/report/feedback").get_json()
        assert "overall" in data
        assert "by_pattern" in data


class TestTemporal:
    def test_record_snapshots(self, client):
        payload = {
            "domain": "test-temporal.com",
            "elements": [{"text": "Sale ends in 02:34:00", "pattern": "Urgency/Scarcity"}],
        }
        r = client.post("/temporal/record", json=payload)
        assert r.status_code == 200
        assert r.get_json()["success"] is True

    def test_check_temporal_no_history(self, client):
        payload = {
            "domain": "unknown-domain-xyz.com",
            "elements": [],
        }
        data = client.post("/temporal/check", json=payload).get_json()
        assert "flags" in data
        assert "temporal_issues" in data

    def test_temporal_record_missing_domain_returns_400(self, client):
        r = client.post("/temporal/record", json={"elements": []})
        assert r.status_code == 400


class TestErrorHandling:
    def test_404_returns_json(self, client):
        r = client.get("/nonexistent-endpoint")
        assert r.status_code == 404
        data = r.get_json()
        assert "error" in data

"""
PatternShield v2.0 — Test Suite
Run: python test_production.py
"""

import json
import sys
import time

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    sys.exit(1)

BASE = "http://localhost:5000"
PASS = 0
FAIL = 0


def test(name, fn):
    global PASS, FAIL
    try:
        fn()
        print(f"  ✅ {name}")
        PASS += 1
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        FAIL += 1


def t_health():
    r = requests.get(f"{BASE}/health")
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "healthy"
    assert d["version"] == "2.0.0"
    assert d["pattern_categories"] == 10


def t_pattern_types():
    r = requests.get(f"{BASE}/pattern-types")
    assert r.status_code == 200
    d = r.json()
    assert d["total"] == 10
    names = [p["type"] for p in d["pattern_types"]]
    assert "Hidden Costs" in names
    assert "Forced Continuity" in names


def t_offline_rules():
    r = requests.get(f"{BASE}/offline-rules")
    assert r.status_code == 200
    d = r.json()
    assert len(d["rules"]) == 10
    assert "Sneaking" in d["rules"]


def t_analyze_urgency():
    r = requests.post(f"{BASE}/analyze", json={"text": "Only 3 left in stock! Hurry!"})
    assert r.status_code == 200
    d = r.json()
    assert d["primary_pattern"] == "Urgency/Scarcity"
    assert d["severity"] in ("medium", "high", "critical")
    assert "explanations" in d


def t_analyze_confirmshaming():
    r = requests.post(f"{BASE}/analyze", json={"text": "No thanks, I don't want to save money"})
    d = r.json()
    assert "Confirmshaming" in d["detected_patterns"]


def t_analyze_hidden_costs():
    r = requests.post(f"{BASE}/analyze", json={"text": "Price does not include $4.99 processing fee and service fee"})
    d = r.json()
    assert "Hidden Costs" in d["detected_patterns"]


def t_analyze_forced_continuity():
    r = requests.post(f"{BASE}/analyze", json={"text": "Free trial will automatically convert to $19.99/month unless cancelled"})
    d = r.json()
    assert "Forced Continuity" in d["detected_patterns"]


def t_analyze_sneaking():
    r = requests.post(f"{BASE}/analyze", json={"text": "We've added Premium Protection to your cart — pre-selected for you"})
    d = r.json()
    assert "Sneaking" in d["detected_patterns"]


def t_analyze_social_proof():
    r = requests.post(f"{BASE}/analyze", json={"text": "1,247 people bought this today! Someone in Delhi just purchased this"})
    d = r.json()
    assert "Social Proof" in d["detected_patterns"]


def t_analyze_no_pattern():
    r = requests.post(f"{BASE}/analyze", json={"text": "Welcome to our store. Browse our collection."})
    d = r.json()
    assert d["primary_pattern"] is None
    assert len(d["detected_patterns"]) == 0


def t_analyze_cookie():
    r = requests.post(f"{BASE}/analyze", json={
        "text": "Accept all cookies", "element_type": "button", "font_size": 18
    })
    d = r.json()
    assert d["is_cookie_consent"] is True


def t_batch():
    r = requests.post(f"{BASE}/batch/analyze", json={
        "elements": [
            {"text": "Only 2 left!", "element_type": "span"},
            {"text": "No thanks, I prefer paying full price", "element_type": "a"},
            {"text": "Welcome to our site", "element_type": "p"},
        ]
    })
    assert r.status_code == 200
    d = r.json()
    assert d["count"] == 3
    assert d["results"][0]["primary_pattern"] is not None  # urgency
    assert d["results"][1]["primary_pattern"] is not None  # confirmshaming
    assert d["results"][2]["primary_pattern"] is None       # clean


def t_batch_legacy():
    r = requests.post(f"{BASE}/batch/analyze", json={
        "texts": ["Sale ends in 3 hours!", "Hello world"]
    })
    assert r.status_code == 200
    assert r.json()["count"] == 2


def t_site_score():
    detections = [
        {"primary_pattern": "Urgency/Scarcity", "confidence_scores": {"Urgency/Scarcity": 0.8}},
        {"primary_pattern": "Confirmshaming", "confidence_scores": {"Confirmshaming": 0.6}},
        {"primary_pattern": None, "confidence_scores": {}},
    ]
    r = requests.post(f"{BASE}/site-score", json={"detections": detections, "domain": "test.com"})
    assert r.status_code == 200
    d = r.json()
    assert "score" in d and "grade" in d


def t_feedback():
    r = requests.post(f"{BASE}/feedback", json={
        "text": "Only 2 left!",
        "detected_pattern": "Urgency/Scarcity",
        "is_correct": True,
        "domain": "test.com",
    })
    assert r.status_code == 200
    assert r.json()["success"] is True


def t_temporal_record():
    r = requests.post(f"{BASE}/temporal/record", json={
        "domain": "test.com",
        "elements": [{"text": "Only 3 left!", "pattern": "Urgency/Scarcity"}],
    })
    assert r.status_code == 200


def t_temporal_check():
    # Record twice
    for _ in range(3):
        requests.post(f"{BASE}/temporal/record", json={
            "domain": "temporal-test.com",
            "elements": [{"text": "Only 3 left!", "pattern": "Urgency/Scarcity"}],
        })
    r = requests.post(f"{BASE}/temporal/check", json={
        "domain": "temporal-test.com",
        "elements": [{"text": "Only 3 left!", "pattern": "Urgency/Scarcity"}],
    })
    assert r.status_code == 200


def t_404():
    r = requests.get(f"{BASE}/nonexistent")
    assert r.status_code == 404
    assert "available" in r.json()


if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"  PatternShield v2.0 — Test Suite")
    print(f"  Server: {BASE}")
    print(f"{'='*60}\n")

    # Check server
    try:
        requests.get(f"{BASE}/health", timeout=3)
    except Exception:
        print("❌ Server not running! Start with: python app.py")
        sys.exit(1)

    print("Core Endpoints:")
    test("Health check", t_health)
    test("Pattern types", t_pattern_types)
    test("Offline rules", t_offline_rules)
    test("404 handling", t_404)

    print("\nDetection (10 categories):")
    test("Urgency/Scarcity", t_analyze_urgency)
    test("Confirmshaming", t_analyze_confirmshaming)
    test("Hidden Costs", t_analyze_hidden_costs)
    test("Forced Continuity", t_analyze_forced_continuity)
    test("Sneaking", t_analyze_sneaking)
    test("Social Proof", t_analyze_social_proof)
    test("No pattern (clean)", t_analyze_no_pattern)
    test("Cookie consent", t_analyze_cookie)

    print("\nBatch & Scoring:")
    test("Batch analyze", t_batch)
    test("Batch legacy format", t_batch_legacy)
    test("Site score", t_site_score)

    print("\nFeedback & Temporal:")
    test("Feedback submit", t_feedback)
    test("Temporal record", t_temporal_record)
    test("Temporal check", t_temporal_check)

    print(f"\n{'='*60}")
    print(f"  Results: {PASS} passed, {FAIL} failed")
    print(f"{'='*60}\n")
    sys.exit(1 if FAIL > 0 else 0)

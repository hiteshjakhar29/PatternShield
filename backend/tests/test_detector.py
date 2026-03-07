"""
Unit tests for DarkPatternDetector.
Tests each of the 10 pattern categories plus edge cases.
"""
import pytest


class TestDetectorInit:
    def test_has_ten_patterns(self, detector):
        assert len(detector.PATTERNS) == 10

    def test_all_patterns_have_required_keys(self, detector):
        for ptype, cfg in detector.PATTERNS.items():
            assert "description" in cfg, f"{ptype} missing description"
            assert "severity_weight" in cfg, f"{ptype} missing severity_weight"
            assert "keywords" in cfg, f"{ptype} missing keywords"
            assert 0 < cfg["severity_weight"] <= 1.0, f"{ptype} severity_weight out of range"

    def test_compiled_patterns_populated(self, detector):
        for ptype in detector.PATTERNS:
            assert ptype in detector._compiled


class TestUrgencyScarcity:
    def test_only_N_left(self, detector):
        r = detector.analyze_element("Only 3 left in stock!")
        assert r["primary_pattern"] == "Urgency/Scarcity"
        assert r["confidence_scores"]["Urgency/Scarcity"] >= 0.5

    def test_countdown_timer(self, detector):
        r = detector.analyze_element("Sale ends in 2 hours!")
        assert r["primary_pattern"] == "Urgency/Scarcity"

    def test_flash_sale(self, detector):
        r = detector.analyze_element("Flash sale: prices go up in 30 minutes")
        assert r["primary_pattern"] == "Urgency/Scarcity"

    def test_people_viewing(self, detector):
        r = detector.analyze_element("42 people viewing this right now")
        assert "Urgency/Scarcity" in r["detected_patterns"]

    def test_negative_keyword_suppresses(self, detector):
        r = detector.analyze_element("Office hours: Monday-Friday 9-5")
        # Should not flag urgency (contains negative keyword "hours")
        if "Urgency/Scarcity" in r["confidence_scores"]:
            assert r["confidence_scores"]["Urgency/Scarcity"] < 0.6


class TestConfirmshaming:
    def test_no_thanks_guilt(self, detector):
        r = detector.analyze_element("No thanks, I don't want to save money")
        assert r["primary_pattern"] == "Confirmshaming"
        assert r["confidence_scores"]["Confirmshaming"] >= 0.5

    def test_stay_basic(self, detector):
        r = detector.analyze_element("No thanks, I prefer to stay basic")
        assert "Confirmshaming" in r["detected_patterns"]

    def test_continue_without(self, detector):
        r = detector.analyze_element("Continue without saving")
        assert "Confirmshaming" in r["detected_patterns"]


class TestObstruction:
    def test_written_request(self, detector):
        r = detector.analyze_element("Send a written request to our headquarters")
        assert r["primary_pattern"] == "Obstruction"

    def test_cancellation_fee(self, detector):
        r = detector.analyze_element("Cancellation fee of $50 applies")
        assert "Obstruction" in r["detected_patterns"]

    def test_business_days(self, detector):
        r = detector.analyze_element("Processing takes 14 business days")
        assert "Obstruction" in r["detected_patterns"]

    def test_early_termination(self, detector):
        r = detector.analyze_element("Early termination fee: $200")
        assert "Obstruction" in r["detected_patterns"]


class TestHiddenCosts:
    def test_processing_fee(self, detector):
        r = detector.analyze_element("$5.99 processing fee added at checkout")
        assert r["primary_pattern"] == "Hidden Costs"

    def test_surcharge(self, detector):
        r = detector.analyze_element("A 3% surcharge applies to credit cards")
        assert "Hidden Costs" in r["detected_patterns"]

    def test_plus_tax(self, detector):
        r = detector.analyze_element("$29.99 plus tax and fees apply")
        assert "Hidden Costs" in r["detected_patterns"]

    def test_free_shipping_not_flagged(self, detector):
        r = detector.analyze_element("Free shipping on orders over $50")
        if "Hidden Costs" in r["confidence_scores"]:
            assert r["confidence_scores"]["Hidden Costs"] < 0.5


class TestForcedContinuity:
    def test_auto_renew(self, detector):
        r = detector.analyze_element("Your free trial will auto-renew at $9.99/month")
        assert r["primary_pattern"] == "Forced Continuity"
        assert r["confidence_scores"]["Forced Continuity"] >= 0.6

    def test_unless_cancel(self, detector):
        r = detector.analyze_element("You will be charged unless you cancel")
        assert "Forced Continuity" in r["detected_patterns"]

    def test_recurring_billing(self, detector):
        r = detector.analyze_element("Automatic recurring billing starts after trial")
        assert "Forced Continuity" in r["detected_patterns"]


class TestSneaking:
    def test_pre_selected(self, detector):
        r = detector.analyze_element("Travel insurance pre-selected for you")
        assert "Sneaking" in r["detected_patterns"]

    def test_added_to_cart(self, detector):
        r = detector.analyze_element("We've added protection plan to your cart")
        assert "Sneaking" in r["detected_patterns"]

    def test_opted_in_by_default(self, detector):
        r = detector.analyze_element("Opted in by default to marketing emails")
        assert "Sneaking" in r["detected_patterns"]


class TestSocialProof:
    def test_people_bought(self, detector):
        r = detector.analyze_element("1,234 people bought this in the last 24 hours")
        assert "Social Proof" in r["detected_patterns"]

    def test_trusted_by_millions(self, detector):
        r = detector.analyze_element("Trusted by 2 million customers worldwide")
        assert "Social Proof" in r["detected_patterns"]

    def test_bestseller(self, detector):
        r = detector.analyze_element("Bestseller — top rated product")
        assert "Social Proof" in r["detected_patterns"]


class TestMisdirection:
    def test_recommended(self, detector):
        r = detector.analyze_element("Recommended plan — our best value pick")
        assert "Misdirection" in r["detected_patterns"]

    def test_most_popular(self, detector):
        r = detector.analyze_element("Most popular option — chosen by 80% of users")
        assert "Misdirection" in r["detected_patterns"]


class TestPriceComparisonPrevention:
    def test_billed_annually(self, detector):
        r = detector.analyze_element("$8/month billed annually ($96/year)")
        assert "Price Comparison Prevention" in r["detected_patterns"]

    def test_contact_for_price(self, detector):
        r = detector.analyze_element("Contact us for custom pricing")
        assert "Price Comparison Prevention" in r["detected_patterns"]

    def test_starting_at(self, detector):
        r = detector.analyze_element("Starting at $4.99/month")
        assert "Price Comparison Prevention" in r["detected_patterns"]


class TestEdgeCases:
    def test_empty_text_returns_safe(self, detector):
        r = detector.analyze_element("")
        assert r["primary_pattern"] is None
        assert r["detected_patterns"] == []

    def test_whitespace_only(self, detector):
        r = detector.analyze_element("   ")
        assert r["primary_pattern"] is None

    def test_clean_text_not_flagged(self, detector):
        r = detector.analyze_element("Add to cart")
        # A plain CTA should not be flagged with high confidence
        if r["primary_pattern"]:
            for c in r["confidence_scores"].values():
                assert c < 0.7, f"Clean text flagged with too high confidence: {c}"

    def test_severity_ordering(self, detector):
        r = detector.analyze_element("Only 1 left! Free trial auto-renews at $49.99 unless cancelled")
        assert r["severity"] in ("low", "medium", "high", "critical")

    def test_cookie_consent_detected(self, detector):
        r = detector.analyze_element("We use cookies. Accept all cookies to continue.")
        assert r["is_cookie_consent"] is True

    def test_explanation_present_for_detections(self, detector):
        r = detector.analyze_element("Only 2 left in stock!")
        for ptype in r["detected_patterns"]:
            assert ptype in r["explanations"], f"No explanation for {ptype}"

    def test_to_dict_keys(self, detector):
        r = detector.analyze_element("Free trial auto-renews")
        required_keys = {
            "detected_patterns", "primary_pattern", "confidence_scores",
            "severity", "explanations", "text_analyzed", "is_cookie_consent",
        }
        assert required_keys.issubset(r.keys())


class TestSiteScore:
    def test_clean_site_scores_100(self):
        from ml_detector import DarkPatternDetector
        score = DarkPatternDetector.calculate_site_score([])
        assert score["score"] == 100
        assert score["grade"] == "A"

    def test_many_patterns_lower_score(self):
        from ml_detector import DarkPatternDetector
        detections = [
            {"primary_pattern": "Urgency/Scarcity", "confidence_scores": {"Urgency/Scarcity": 0.9}},
            {"primary_pattern": "Hidden Costs",     "confidence_scores": {"Hidden Costs": 0.85}},
            {"primary_pattern": "Forced Continuity","confidence_scores": {"Forced Continuity": 0.88}},
            {"primary_pattern": "Obstruction",      "confidence_scores": {"Obstruction": 0.75}},
        ]
        score = DarkPatternDetector.calculate_site_score(detections)
        assert score["score"] < 100
        assert score["grade"] in ("B", "C", "D", "F")

    def test_score_has_required_fields(self):
        from ml_detector import DarkPatternDetector
        score = DarkPatternDetector.calculate_site_score([])
        assert "score" in score
        assert "grade" in score
        assert "risk_level" in score
        assert "pattern_breakdown" in score

"""
Unit tests for FeedbackService, TemporalService, and storage layer.
"""
import os
import tempfile
import pytest


@pytest.fixture
def feedback_file():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def temporal_file():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


class TestFeedbackService:
    def test_record_increases_count(self, feedback_file):
        from services.feedback_service import FeedbackService
        svc = FeedbackService(feedback_file)
        assert svc.count() == 0
        svc.record(text="test", detected_pattern="Urgency/Scarcity", is_correct=True)
        assert svc.count() == 1

    def test_record_returns_entry_with_id(self, feedback_file):
        from services.feedback_service import FeedbackService
        svc = FeedbackService(feedback_file)
        entry = svc.record(text="test", detected_pattern="Urgency/Scarcity", is_correct=True)
        assert "id" in entry
        assert "timestamp" in entry
        assert len(entry["id"]) > 0

    def test_accuracy_stats_empty(self, feedback_file):
        from services.feedback_service import FeedbackService
        svc = FeedbackService(feedback_file)
        stats = svc.accuracy_stats()
        assert stats["total"] == 0

    def test_accuracy_stats_correct(self, feedback_file):
        from services.feedback_service import FeedbackService
        svc = FeedbackService(feedback_file)
        svc.record("t1", "Urgency/Scarcity", True)
        svc.record("t2", "Urgency/Scarcity", True)
        svc.record("t3", "Urgency/Scarcity", False)
        stats = svc.accuracy_stats()
        assert stats["total"] == 3
        assert stats["correct"] == 2
        assert abs(stats["accuracy"] - 2 / 3) < 0.01

    def test_by_pattern_aggregation(self, feedback_file):
        from services.feedback_service import FeedbackService
        svc = FeedbackService(feedback_file)
        svc.record("t1", "Urgency/Scarcity", True)
        svc.record("t2", "Confirmshaming", False)
        by_pat = svc.by_pattern()
        assert "Urgency/Scarcity" in by_pat
        assert "Confirmshaming" in by_pat

    def test_persistence_across_instances(self, feedback_file):
        from services.feedback_service import FeedbackService
        svc1 = FeedbackService(feedback_file)
        svc1.record("test", "Sneaking", True)
        svc2 = FeedbackService(feedback_file)
        assert svc2.count() == 1


class TestTemporalService:
    def test_record_returns_stored_count(self, temporal_file):
        from services.temporal_service import TemporalService
        svc = TemporalService(temporal_file)
        stored = svc.record("example.com", [{"text": "Only 3 left!", "pattern": "Urgency/Scarcity"}])
        assert stored == 1

    def test_history_returns_empty_for_unknown_domain(self, temporal_file):
        from services.temporal_service import TemporalService
        svc = TemporalService(temporal_file)
        assert svc.history("unknown.com") == []

    def test_history_grows_with_records(self, temporal_file):
        from services.temporal_service import TemporalService
        svc = TemporalService(temporal_file)
        svc.record("example.com", [{"text": "Sale ends in 1 hour", "pattern": "Urgency/Scarcity"}])
        svc.record("example.com", [{"text": "Sale ends in 1 hour", "pattern": "Urgency/Scarcity"}])
        assert len(svc.history("example.com")) == 2

    def test_check_no_history_returns_empty_flags(self, temporal_file):
        from services.temporal_service import TemporalService
        svc = TemporalService(temporal_file)
        flags = svc.check("fresh.com", [{"text": "Only 2 left", "pattern": "Urgency/Scarcity"}])
        assert flags == []

    def test_check_persistent_urgency_detected(self, temporal_file):
        from services.temporal_service import TemporalService
        svc = TemporalService(temporal_file)
        text = "Only 3 left in stock!"
        svc.record("urgent.com", [{"text": text, "pattern": "Urgency/Scarcity"}])
        svc.record("urgent.com", [{"text": text, "pattern": "Urgency/Scarcity"}])
        flags = svc.check("urgent.com", [{"text": text, "pattern": "Urgency/Scarcity"}])
        flag_types = [f["type"] for f in flags]
        assert "persistent_urgency" in flag_types

    def test_domain_count(self, temporal_file):
        from services.temporal_service import TemporalService
        svc = TemporalService(temporal_file)
        svc.record("a.com", [{"text": "t", "pattern": "Urgency/Scarcity"}])
        svc.record("b.com", [{"text": "t", "pattern": "Urgency/Scarcity"}])
        assert svc.domain_count() == 2

    def test_max_per_domain_trimming(self, temporal_file):
        from services.temporal_service import TemporalService
        svc = TemporalService(temporal_file, max_per_domain=3)
        for i in range(5):
            svc.record("trim.com", [{"text": f"text {i}", "pattern": "Urgency/Scarcity"}])
        assert len(svc.history("trim.com")) <= 3

    def test_persistence_across_instances(self, temporal_file):
        from services.temporal_service import TemporalService
        svc1 = TemporalService(temporal_file)
        svc1.record("persist.com", [{"text": "deal", "pattern": "Urgency/Scarcity"}])
        svc2 = TemporalService(temporal_file)
        assert len(svc2.history("persist.com")) == 1


class TestJSONStore:
    def test_read_default_on_missing_file(self):
        from storage.json_store import JSONStore
        store = JSONStore("/tmp/nonexistent_ps_test_xyz.json", default={})
        assert store.read() == {}

    def test_write_and_read(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            from storage.json_store import JSONStore
            store = JSONStore(path, default={})
            store.write({"key": "value"})
            assert store.read() == {"key": "value"}
        finally:
            os.unlink(path)

    def test_update_merges_via_callable(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            from storage.json_store import JSONStore
            store = JSONStore(path, default={})
            store.write({"a": 1})
            store.update(lambda data: {**data, "b": 2})
            data = store.read()
            assert data["a"] == 1
            assert data["b"] == 2
        finally:
            os.unlink(path)

    def test_jsonl_append_and_count(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            from storage.json_store import JSONLStore
            store = JSONLStore(path)
            store.append({"x": 1})
            store.append({"x": 2})
            assert store.count() == 2
            records = store.read_all()
            assert len(records) == 2
        finally:
            os.unlink(path)

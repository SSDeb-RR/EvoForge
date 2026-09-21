import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("memory.py")
SPEC = importlib.util.spec_from_file_location("metric_memory", SCRIPT)
memory = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(memory)


class ExperienceMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def payload(self):
        return {
            "session_id": "session-test",
            "metric_slug": "example-metric",
            "metric_family": "conversation-state",
            "event_type": "state_transition_gap",
            "engineering_event": {
                "reported_behavior": "false positive",
                "observed_cause": "stale state",
                "correction_or_outcome": "later acceptance supersedes it",
            },
            "learning_signal": "Explicit supersession may be reusable.",
            "confidence": "high",
            "scope": {"kind": "metric_family", "subject_id": "conversation-state"},
            "pattern_keys": ["state-supersession"],
        }

    def test_session_and_experience_are_persisted(self):
        session = memory.register_session("example-metric", "fix false positives", override=self.root)
        stored = memory.record(self.payload(), override=self.root)
        result = memory.status(override=self.root)
        self.assertTrue(session["session_id"].startswith("session-"))
        self.assertTrue(stored["experience_id"].startswith("memexp-"))
        self.assertEqual(result["session_count"], 1)
        self.assertEqual(result["experience_count"], 1)

    def test_duplicate_is_not_appended(self):
        first = memory.record(self.payload(), override=self.root)
        second = memory.record(self.payload(), override=self.root)
        self.assertFalse(first["duplicate"])
        self.assertTrue(second["duplicate"])
        self.assertEqual(memory.status(override=self.root)["experience_count"], 1)

    def test_invalid_scope_is_rejected_but_best_effort_does_not_raise(self):
        payload = self.payload()
        payload["scope"] = {"kind": "recruiter"}
        result = memory.record_best_effort(payload, override=self.root)
        self.assertFalse(result["captured"])
        self.assertIn("scope.kind", result["warning"])

    def test_malformed_lines_are_reported_without_hiding_valid_rows(self):
        memory.record(self.payload(), override=self.root)
        experiences = self.root / memory.SKILL_NAME / "experiences.jsonl"
        with experiences.open("a", encoding="utf-8") as stream:
            stream.write("{broken\n")
        result = memory.status(override=self.root)
        self.assertEqual(result["experience_count"], 1)
        self.assertTrue(result["warnings"])


if __name__ == "__main__":
    unittest.main()

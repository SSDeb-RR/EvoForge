import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("evolve.py")
SPEC = importlib.util.spec_from_file_location("evolve", SCRIPT)
evolve = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(evolve)


class NormalizeTests(unittest.TestCase):
    def test_chatgpt_style_json(self):
        raw = json.dumps({"messages": [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}]}).encode()
        kind, messages, parser, warnings, _ = evolve.detect_and_normalize(raw)
        self.assertEqual((kind, parser, warnings), ("json", "json_messages", []))
        self.assertEqual([m["role"] for m in messages], ["user", "assistant"])

    def test_nested_json_and_content_parts(self):
        raw = json.dumps({"export": {"turns": [{"speaker": "human", "content": [{"text": "A"}, {"text": "B"}]}]}}).encode()
        _, messages, parser, _, _ = evolve.detect_and_normalize(raw)
        self.assertEqual(parser, "json_messages")
        self.assertEqual(messages[0]["content"], "A\nB")

    def test_markdown_speakers_and_code(self):
        raw = b"# User\nPlease inspect\n# Assistant\n```python\nprint(1)\n```\n"
        kind, messages, parser, warnings, _ = evolve.detect_and_normalize(raw)
        self.assertEqual((kind, parser, warnings), ("markdown", "speaker_text", []))
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[1]["code_blocks"][0]["language"], "python")

    def test_plain_text_is_preserved(self):
        raw = b"unstructured but useful"
        kind, messages, parser, warnings, _ = evolve.detect_and_normalize(raw)
        self.assertEqual((kind, parser), ("text", "plain_text"))
        self.assertTrue(warnings)
        self.assertEqual(messages[0]["content"], raw.decode())


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        self.memory = self.root / "memory"
        self.target = self.root / "target"
        self.target.mkdir()
        (self.target / "SKILL.md").write_text("---\nname: demo\ndescription: >\n  Demo.\n---\n\n# Demo\n\nOld.\n", encoding="utf-8")
        (self.data).mkdir()
        (self.data / "targets.yaml").write_text(json.dumps({"default_target": "demo", "targets": {"demo": {"path": str(self.target), "skill_file": "SKILL.md"}}}), encoding="utf-8")
        self.patchers = [
            mock.patch.object(evolve, "DATA_DIR", self.data),
            mock.patch.object(evolve, "TARGETS_FILE", self.data / "targets.yaml"),
            mock.patch.object(evolve, "MEMORY_ROOT", self.memory),
        ]
        for patcher in self.patchers: patcher.start()
        evolve.ensure_layout()

    def tearDown(self):
        for patcher in reversed(self.patchers): patcher.stop()
        self.temp.cleanup()

    def test_ingest_duplicate_is_refused(self):
        source = self.root / "chat.txt"
        source.write_text("User: issue\nAssistant: correction", encoding="utf-8")
        first = evolve.ingest(str(source))
        with self.assertRaises(evolve.EvolutionError):
            evolve.ingest(str(source))
        self.assertEqual(len(first["messages"]), 2)

    def test_empty_memory_is_safe(self):
        result = evolve.retrieve_memory("demo", memory_root=self.memory)
        self.assertFalse(result["available"])
        self.assertEqual(result["experiences"], [])

    def test_metric_memory_retrieval_groups_patterns_and_reports_damage(self):
        skill_memory = self.memory / "demo"
        skill_memory.mkdir(parents=True)
        rows = [
            {
                "experience_id": "memexp-1", "skill_name": "demo",
                "created_at": "2026-01-01T00:00:00Z", "event_type": "state_transition_gap",
                "learning_signal": "Later acceptance should supersede prior state",
                "scope": {"kind": "metric", "subject_id": "metric-a"},
                "pattern_keys": ["state-supersession"], "content_sha256": "a" * 64,
            },
            {
                "experience_id": "memexp-2", "skill_name": "demo",
                "created_at": "2026-01-02T00:00:00Z", "event_type": "false_positive",
                "learning_signal": "A second state supersession failure",
                "scope": {"kind": "metric_family", "subject_id": "conversation-state"},
                "pattern_keys": ["state-supersession"], "content_sha256": "b" * 64,
            },
        ]
        (skill_memory / "experiences.jsonl").write_text(
            "\n".join(json.dumps(row) for row in rows) + "\n{broken\n", encoding="utf-8"
        )
        result = evolve.retrieve_memory("demo", "supersession", memory_root=self.memory)
        self.assertEqual(result["returned_count"], 2)
        self.assertEqual(result["recurring_patterns"][0]["count"], 2)
        self.assertEqual(result["event_type_counts"]["false_positive"], 1)
        self.assertTrue(result["warnings"])

    def test_metric_memory_import_preserves_engineering_metadata(self):
        skill_memory = self.memory / "demo"
        skill_memory.mkdir(parents=True)
        row = {
            "experience_id": "memexp-import", "skill_name": "demo",
            "created_at": "2026-01-01T00:00:00Z", "metric_slug": "metric-a",
            "metric_family": "conversation-state", "event_type": "state_transition_gap",
            "engineering_event": {
                "reported_behavior": "false positive", "observed_cause": "stale state",
                "correction_or_outcome": "acceptance supersedes it", "validation": "regressions passed",
            },
            "learning_signal": "Possible reusable state rule",
            "scope": {"kind": "metric", "subject_id": "metric-a"},
            "confidence": "medium", "pattern_keys": ["state-supersession"],
            "content_sha256": "c" * 64,
        }
        (skill_memory / "experiences.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
        imported = evolve.import_memory_experience("memexp-import", self.memory)
        self.assertEqual(imported["source"]["kind"], "local_memory")
        self.assertEqual(imported["metadata"]["metric_slug"], "metric-a")
        self.assertEqual(imported["metadata"]["event_type"], "state_transition_gap")
        self.assertTrue((self.data / "experiences" / "distilled" / "memexp-import.json").is_file())

    def _stage(self):
        source = self.root / "chat.txt"
        source.write_text("User: issue\nAssistant: correction", encoding="utf-8")
        exp = evolve.ingest(str(source))["conversation_id"]
        lesson_input = self.root / "lesson.json"
        lesson_input.write_text(json.dumps({
            "summary": "Missing generalized check", "source_experiences": [exp],
            "events": [{"type": "SKILL_INSTRUCTION_GAP", "evidence": [{"experience_id": exp, "message_sequences": [0, 1], "note": "observed"}]}],
            "attribution": {"primary": "A", "secondary": [], "rationale": "missing", "alternatives_rejected": []},
            "specific_fix": "Fix one case", "generalization_hypothesis": "Add a reusable check",
            "transfer_cases": ["another family"], "scope": {"applies": ["metrics"], "excludes": ["literal phrases"]},
            "counterargument": "one source", "confidence": "medium",
            "novelty": {"rating": "new", "matches": [], "rationale": "not present"},
            "expected_impact": "fewer misses", "affected_component": "workflow",
            "proposed_action": "add one instruction", "decision": "propose", "decision_reason": "evidence",
        }), encoding="utf-8")
        lesson = evolve.store_lesson(exp, lesson_input)
        candidate = self.root / "candidate.md"
        candidate.write_text((self.target / "SKILL.md").read_text() + "\nNew reusable check.\n", encoding="utf-8")
        return evolve.stage(lesson["lesson_id"], candidate)

    def test_apply_requires_passing_validation_and_approval(self):
        proposal = self._stage()
        pid = proposal["proposal_id"]
        with self.assertRaises(evolve.EvolutionError):
            evolve.apply_proposal(pid, True)
        assessment = self.root / "assessment.json"
        assessment.write_text(json.dumps({
            "reviewer": "test", "claims": [{"claim": "compared", "status": "executed", "evidence": "run output"}],
            "rubric": {"trigger_addressed": True, "different_family_transfer_passed": True, "no_critical_regressions": True, "no_instruction_contradiction": True, "minimal_localized_delta": True, "no_unjustified_metric_specificity": True},
            "scenarios": [
                {"scenario_id": "t", "kind": "trigger", "metric_family": "a", "mode": "executed", "comparison": "improved", "expected_behavior_met": True, "critical_regression": False, "evidence": "output A"},
                {"scenario_id": "x", "kind": "transfer", "metric_family": "b", "mode": "executed", "comparison": "same", "expected_behavior_met": True, "critical_regression": False, "evidence": "output B"},
            ], "summary": "pass", "limitations": [],
        }), encoding="utf-8")
        result = evolve.validate(pid, assessment)
        self.assertEqual(result["decision"], "approval_ready")
        with self.assertRaises(evolve.EvolutionError):
            evolve.apply_proposal(pid, False)
        applied = evolve.apply_proposal(pid, True)
        self.assertEqual(applied["status"], "applied")
        self.assertIn("New reusable check", (self.target / "SKILL.md").read_text())
        rolled_back = evolve.rollback(pid, True)
        self.assertEqual(rolled_back["restored_sha256"], proposal["base_sha256"])

    def test_stale_target_blocks_apply(self):
        proposal = self._stage()
        (self.target / "SKILL.md").write_text((self.target / "SKILL.md").read_text() + "external\n", encoding="utf-8")
        assessment = self.root / "assessment.json"
        assessment.write_text(json.dumps({"claims": [], "rubric": {}, "scenarios": []}), encoding="utf-8")
        result = evolve.validate(proposal["proposal_id"], assessment)
        self.assertEqual(result["decision"], "failed")
        self.assertIn("Live target hash differs from proposal base", result["reasons"])

    def test_rejection_is_terminal(self):
        proposal = self._stage()
        pid = proposal["proposal_id"]
        rejected = evolve.reject(pid, "Duplicates existing guidance")
        self.assertEqual(rejected["status"], "rejected")
        with self.assertRaises(evolve.EvolutionError):
            evolve.pending_proposal(pid)

    def test_independent_evaluation_generates_approval_assessment(self):
        proposal = self._stage()
        trigger = self.root / "trigger.json"
        transfer = self.root / "transfer.json"
        trigger.write_text(json.dumps({"scenario_id": "trigger", "metric_family": "family-a", "kind": "trigger", "task": "Solve task A", "evidence": "facts A"}), encoding="utf-8")
        transfer.write_text(json.dumps({"scenario_id": "transfer", "metric_family": "family-b", "kind": "transfer", "task": "Solve task B", "evidence": "facts B"}), encoding="utf-8")
        manifest = evolve.prepare_evaluation(proposal["proposal_id"], [trigger, transfer])
        evaluation_id = manifest["evaluation_id"]
        self.assertEqual(len(manifest["packets"]), 4)
        results = self.root / "results.json"
        runs = []
        for scenario in ("trigger", "transfer"):
            for variant in ("A", "B"):
                runs.append({"scenario_id": scenario, "variant": variant, "mode": "executed", "evaluator_run_id": f"{scenario}-{variant}", "output": f"{scenario} {variant} output", "evidence": f"{scenario} {variant} run"})
        results.write_text(json.dumps({"evaluation_id": evaluation_id, "reviewer": "tester", "runs": runs}), encoding="utf-8")
        evolve.record_evaluation(evaluation_id, results)
        judgment = self.root / "judgment.json"
        judgment.write_text(json.dumps({
            "evaluation_id": evaluation_id, "reviewer": "reviewer",
            "claims": [{"claim": "Compared fresh outputs", "status": "executed", "evidence": "stored outputs"}],
            "rubric": {"trigger_addressed": True, "different_family_transfer_passed": True, "no_critical_regressions": True, "no_instruction_contradiction": True, "minimal_localized_delta": True, "no_unjustified_metric_specificity": True},
            "scenarios": [{"scenario_id": "trigger", "comparison": "improved", "expected_behavior_met": True, "critical_regression": False, "evidence": "B adds needed step"}, {"scenario_id": "transfer", "comparison": "same", "expected_behavior_met": True, "critical_regression": False, "evidence": "B preserves behavior"}],
            "summary": "pass", "limitations": []
        }), encoding="utf-8")
        assessment = evolve.assess_evaluation(evaluation_id, judgment)
        self.assertEqual(assessment["scenarios"][0]["mode"], "executed")
        assessment_path = self.data / "evaluations" / "completed" / f"{evaluation_id}.assessment.json"
        self.assertEqual(evolve.validate(proposal["proposal_id"], assessment_path)["decision"], "approval_ready")

    def test_status_surfaces_action_for_pending_evaluation(self):
        proposal = self._stage()
        trigger = self.root / "trigger.json"
        transfer = self.root / "transfer.json"
        trigger.write_text(json.dumps({"scenario_id": "trigger", "metric_family": "family-a", "kind": "trigger", "task": "Solve task A", "evidence": "facts A"}), encoding="utf-8")
        transfer.write_text(json.dumps({"scenario_id": "transfer", "metric_family": "family-b", "kind": "transfer", "task": "Solve task B", "evidence": "facts B"}), encoding="utf-8")
        manifest = evolve.prepare_evaluation(proposal["proposal_id"], [trigger, transfer])
        actions = evolve.status()["next_actions"]
        action = next(item for item in actions if item["proposal_id"] == proposal["proposal_id"])
        self.assertEqual(action["kind"], "run_independent_evaluation")
        self.assertEqual(action["evaluation_id"], manifest["evaluation_id"])
        self.assertIn("fresh evaluator runs", action["user_prompt"])

    def test_target_discovery_honors_explicit_override(self):
        alternate = self.root / "alternate-target"
        alternate.mkdir()
        (alternate / "SKILL.md").write_text("---\nname: alternate\ndescription: >\n  Alternate.\n---\n", encoding="utf-8")
        with mock.patch.dict(evolve.os.environ, {"SKILL_EVOLUTION_TARGET": str(alternate)}):
            _, root, skill_file = evolve.target_config()
        self.assertEqual(root, alternate.resolve())
        self.assertEqual(skill_file, alternate.resolve() / "SKILL.md")

    def test_target_discovery_searches_configured_roots(self):
        claude_root = self.root / ".claude" / "skills"
        target = claude_root / "deterministic-metric-engineering"
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("---\nname: target\ndescription: >\n  Target.\n---\n", encoding="utf-8")
        (self.data / "targets.yaml").write_text(json.dumps({
            "default_target": "deterministic-metric-engineering",
            "targets": {"deterministic-metric-engineering": {
                "skill_file": "SKILL.md",
                "directory_names": ["deterministic-metric-engineering"],
                "search_roots": [str(claude_root)]
            }}
        }), encoding="utf-8")
        _, root, _ = evolve.target_config()
        self.assertEqual(root, target.resolve())

    def test_status_explains_missing_target(self):
        (self.target / "SKILL.md").unlink()
        status = evolve.status()
        self.assertIsNone(status["target_path"])
        self.assertEqual(status["next_actions"][0]["kind"], "install_metric_forge_target")



if __name__ == "__main__":
    unittest.main()

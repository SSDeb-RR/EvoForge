#!/usr/bin/env python3
"""Deterministic storage and promotion mechanics for the Skill Evolution skill."""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable


SKILL_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("SKILL_EVOLUTION_DATA", SKILL_DIR / "evolution"))
TARGETS_FILE = Path(os.environ.get("SKILL_EVOLUTION_TARGETS", SKILL_DIR / "config" / "targets.json"))
ROLE_ALIASES = {
    "human": "user", "customer": "user", "user": "user",
    "assistant": "assistant", "agent": "assistant", "ai": "assistant",
    "system": "system", "developer": "system", "tool": "tool",
}
SPEAKER_RE = re.compile(
    r"^(?:#{1,6}\s*)?(user|human|customer|assistant|agent|ai|system|developer|tool)\s*:\s*(.*)$",
    re.IGNORECASE,
)
HEADING_RE = re.compile(
    r"^#{1,6}\s+(user|human|customer|assistant|agent|ai|system|developer|tool)\s*$",
    re.IGNORECASE,
)
FENCE_RE = re.compile(r"```([^\n`]*)\n(.*?)```", re.DOTALL)
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


class EvolutionError(RuntimeError):
    pass


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def compact_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def short_id(prefix: str, seed: bytes) -> str:
    stamp = compact_stamp()
    return f"{prefix}-{stamp}-{digest_bytes(seed)[:10]}"


def json_read(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvolutionError(f"Cannot read valid JSON from {path}: {exc}") from exc


def write_new_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise EvolutionError(f"Refusing to overwrite immutable artifact: {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def stored_path(path: Path) -> str:
    """Prefer portable skill-relative artifact paths, falling back to absolute."""
    try:
        return str(path.relative_to(SKILL_DIR))
    except ValueError:
        return str(path)


def append_event(event_type: str, **fields: Any) -> None:
    path = DATA_DIR / "history" / "events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"timestamp": utc_now(), "event": event_type, **fields}
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def ensure_layout() -> None:
    for relative in (
        "experiences/raw", "experiences/distilled", "lessons",
        "proposals/pending", "proposals/accepted", "proposals/rejected",
        "regressions/scenarios", "regressions/runs", "evaluations/pending",
        "evaluations/completed", "snapshots", "history",
    ):
        (DATA_DIR / relative).mkdir(parents=True, exist_ok=True)


def target_candidates(entry: dict[str, Any]) -> list[Path]:
    """Return portable target roots in deterministic search order."""
    explicit = os.environ.get("SKILL_EVOLUTION_TARGET", "").strip()
    if explicit:
        return [Path(explicit).expanduser()]
    configured_path = str(entry.get("path", "")).strip()
    if configured_path:
        return [Path(configured_path).expanduser()]
    names = entry.get("directory_names", ["deterministic-metric-engineering"])
    roots = [Path(item).expanduser() for item in entry.get("search_roots", [])]
    codex_home = os.environ.get("CODEX_HOME", "").strip()
    claude_home = os.environ.get("CLAUDE_CONFIG_DIR", "").strip()
    if codex_home:
        roots.insert(0, Path(codex_home).expanduser() / "skills")
    if claude_home:
        roots.insert(0, Path(claude_home).expanduser() / "skills")
    candidates: list[Path] = []
    for root in roots:
        for name in names:
            candidate = root / name
            if candidate not in candidates:
                candidates.append(candidate)
    return candidates


def target_config() -> tuple[str, Path, Path]:
    config = json_read(TARGETS_FILE)
    key = config.get("default_target")
    entry = config.get("targets", {}).get(key, {})
    skill_name = entry.get("skill_file", "SKILL.md")
    candidates = target_candidates(entry)
    for candidate in candidates:
        root = candidate.resolve()
        skill_file = root / skill_name
        if root.is_dir() and skill_file.is_file():
            return key, root, skill_file
    searched = ", ".join(str(item) for item in candidates) or "no configured locations"
    raise EvolutionError(
        "Configured deterministic-metric-engineering target is unavailable. "
        f"Searched: {searched}. Install the target harness or set SKILL_EVOLUTION_TARGET."
    )


def target_status() -> dict[str, Any]:
    config = json_read(TARGETS_FILE)
    key = config.get("default_target")
    entry = config.get("targets", {}).get(key, {})
    skill_name = entry.get("skill_file", "SKILL.md")
    candidates = target_candidates(entry)
    available = [str(path.resolve()) for path in candidates if path.is_dir() and (path / skill_name).is_file()]
    selected = None
    try:
        _, root, target_file = target_config()
        selected = {"path": str(root), "skill_file": str(target_file), "sha256": digest_file(target_file)}
    except EvolutionError:
        pass
    return {
        "target": key,
        "selected": selected,
        "available_candidates": available,
        "searched_candidates": [str(path) for path in candidates],
        "override_environment_variable": "SKILL_EVOLUTION_TARGET",
    }


def normalize_role(value: Any) -> str:
    return ROLE_ALIASES.get(str(value).strip().lower(), "unknown")


def content_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                candidate = item.get("text", item.get("content"))
                if isinstance(candidate, str):
                    parts.append(candidate)
        return "\n".join(parts)
    if value is None:
        return ""
    return json.dumps(value, ensure_ascii=False)


def code_blocks(text: str) -> list[dict[str, str]]:
    return [{"language": lang.strip() or None, "content": body} for lang, body in FENCE_RE.findall(text)]


def message(role: Any, content: Any, sequence: int, locator: dict[str, Any], timestamp: Any = None) -> dict[str, Any]:
    text = content_text(content)
    return {
        "sequence": sequence,
        "role": normalize_role(role),
        "content": text,
        "timestamp": timestamp if isinstance(timestamp, (str, int, float)) else None,
        "code_blocks": code_blocks(text),
        "references": [],
        "source_locator": locator,
    }


def find_message_lists(node: Any, path: tuple[Any, ...] = ()) -> list[tuple[tuple[Any, ...], list[Any]]]:
    found: list[tuple[tuple[Any, ...], list[Any]]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            next_path = path + (key,)
            if isinstance(value, list) and value and all(isinstance(x, dict) for x in value):
                if any(any(k in x for k in ("role", "speaker", "author")) and any(k in x for k in ("content", "text", "message")) for x in value):
                    found.append((next_path, value))
            found.extend(find_message_lists(value, next_path))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(find_message_lists(value, path + (index,)))
    return found


def parse_json_messages(data: Any) -> tuple[list[dict[str, Any]], str, list[str]]:
    candidates = find_message_lists(data)
    warnings: list[str] = []
    if not candidates:
        text = json.dumps(data, indent=2, ensure_ascii=False)
        return [message("unknown", text, 0, {"path": []})], "json_recursive", ["No recognizable message list; preserved JSON as one message"]
    candidates.sort(key=lambda item: len(item[1]), reverse=True)
    path, rows = candidates[0]
    if len(candidates) > 1:
        warnings.append(f"Multiple message arrays found; selected largest at {list(path)}")
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        role = row.get("role", row.get("speaker", row.get("author", "unknown")))
        if isinstance(role, dict):
            role = role.get("role", role.get("name", "unknown"))
        content = row.get("content", row.get("text", row.get("message", "")))
        timestamp = row.get("timestamp", row.get("created_at", row.get("time")))
        output.append(message(role, content, index, {"path": [*path, index]}, timestamp))
    return output, "json_messages", warnings


def parse_speaker_text(text: str) -> tuple[list[dict[str, Any]], str, list[str]]:
    lines = text.splitlines()
    chunks: list[tuple[str, list[str], int, int]] = []
    current_role: str | None = None
    current_lines: list[str] = []
    start = 1
    in_fence = False
    for number, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
        match = None if in_fence else SPEAKER_RE.match(line.strip())
        heading = None if in_fence else HEADING_RE.match(line.strip())
        if match or heading:
            if current_role is not None:
                chunks.append((current_role, current_lines, start, number - 1))
            current_role = (match or heading).group(1)
            current_lines = [match.group(2)] if match and match.group(2) else []
            start = number
        elif current_role is not None:
            current_lines.append(line)
    if current_role is not None:
        chunks.append((current_role, current_lines, start, len(lines)))
    if not chunks:
        return [message("unknown", text, 0, {"line_start": 1, "line_end": len(lines)})], "plain_text", ["No speaker markers detected"]
    messages = [message(role, "\n".join(body).strip(), index, {"line_start": first, "line_end": last}) for index, (role, body, first, last) in enumerate(chunks)]
    return messages, "speaker_text", []


def detect_and_normalize(raw: bytes) -> tuple[str, list[dict[str, Any]], str, list[str], dict[str, Any]]:
    text = raw.decode("utf-8", errors="replace")
    warnings: list[str] = []
    if "\ufffd" in text:
        warnings.append("Input contained invalid UTF-8 bytes; replacement characters were used")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        messages, parser, parse_warnings = parse_speaker_text(text)
        kind = "markdown" if re.search(r"(?m)^#{1,6}\s|```", text) else "text"
        return kind, messages, parser, warnings + parse_warnings, {}
    messages, parser, parse_warnings = parse_json_messages(data)
    metadata = data.get("metadata", {}) if isinstance(data, dict) and isinstance(data.get("metadata"), dict) else {}
    return "json", messages, parser, warnings + parse_warnings, metadata


def ingest(path_arg: str) -> dict[str, Any]:
    ensure_layout()
    if path_arg == "-":
        raw = sys.stdin.buffer.read()
        original: str | None = None
        suffix = ".txt"
    else:
        source = Path(path_arg).expanduser().resolve()
        if not source.is_file():
            raise EvolutionError(f"Conversation file not found: {source}")
        raw = source.read_bytes()
        original = str(source)
        suffix = source.suffix or ".txt"
    if not raw:
        raise EvolutionError("Conversation input is empty")
    source_hash = digest_bytes(raw)
    for existing in (DATA_DIR / "experiences" / "distilled").glob("*.json"):
        record = json_read(existing)
        if record.get("source", {}).get("sha256") == source_hash:
            raise EvolutionError(f"This exact experience is already stored as {record.get('conversation_id', existing.stem)}")
    experience_id = short_id("exp", raw)
    raw_path = DATA_DIR / "experiences" / "raw" / f"{experience_id}{suffix}"
    if raw_path.exists() or (DATA_DIR / "experiences" / "distilled" / f"{experience_id}.json").exists():
        raise EvolutionError(f"This exact experience is already stored as {experience_id}")
    kind, messages, parser, warnings, metadata = detect_and_normalize(raw)
    raw_path.write_bytes(raw)
    normalized = {
        "schema_version": 1,
        "conversation_id": experience_id,
        "created_at": utc_now(),
        "source": {
            "kind": kind, "original_path": original,
            "stored_path": stored_path(raw_path),
            "sha256": source_hash, "parser": parser, "warnings": warnings,
        },
        "metadata": metadata,
        "messages": messages,
    }
    distilled = DATA_DIR / "experiences" / "distilled" / f"{experience_id}.json"
    write_new_json(distilled, normalized)
    append_event("experience_ingested", experience_id=experience_id, source_kind=kind, message_count=len(messages))
    return normalized


REQUIRED_LESSON_FIELDS = {
    "summary", "source_experiences", "events", "attribution", "specific_fix",
    "generalization_hypothesis", "transfer_cases", "scope", "counterargument",
    "confidence", "novelty", "expected_impact", "affected_component",
    "proposed_action", "decision", "decision_reason",
}


def store_lesson(experience_id: str, source_path: Path) -> dict[str, Any]:
    ensure_layout()
    experience = DATA_DIR / "experiences" / "distilled" / f"{experience_id}.json"
    if not experience.is_file():
        raise EvolutionError(f"Unknown experience: {experience_id}")
    payload = json_read(source_path)
    missing = sorted(REQUIRED_LESSON_FIELDS - set(payload))
    if missing:
        raise EvolutionError(f"Lesson is missing fields: {', '.join(missing)}")
    if experience_id not in payload.get("source_experiences", []):
        raise EvolutionError("Primary experience must appear in source_experiences")
    if payload.get("decision") not in {"propose", "gather_more_evidence", "do_not_evolve"}:
        raise EvolutionError("Invalid lesson decision")
    for exp_id in payload.get("source_experiences", []):
        if not (DATA_DIR / "experiences" / "distilled" / f"{exp_id}.json").is_file():
            raise EvolutionError(f"Lesson references unknown experience: {exp_id}")
    seed = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    lesson_id = short_id("lesson", seed)
    record = {"schema_version": 1, "lesson_id": lesson_id, "created_at": utc_now(), "primary_experience_id": experience_id, **payload}
    write_new_json(DATA_DIR / "lessons" / f"{lesson_id}.json", record)
    append_event("lesson_recorded", lesson_id=lesson_id, experience_id=experience_id, decision=payload["decision"])
    return record


def validate_frontmatter(text: str) -> list[str]:
    errors: list[str] = []
    if not text.startswith("---\n"):
        return ["SKILL.md must start with YAML frontmatter"]
    end = text.find("\n---\n", 4)
    if end < 0:
        return ["SKILL.md frontmatter is not closed"]
    header = text[4:end]
    if not re.search(r"(?m)^name:\s*\S+", header):
        errors.append("Frontmatter is missing name")
    if not re.search(r"(?m)^description:\s*(?:>|\S+)", header):
        errors.append("Frontmatter is missing description")
    return errors


def validate_links(text: str, root: Path) -> list[str]:
    errors: list[str] = []
    for link in LINK_RE.findall(text):
        target = link.strip().split("#", 1)[0]
        if not target or re.match(r"^[a-z]+://", target) or target.startswith(("#", "/")):
            continue
        if not (root / target).resolve().exists():
            errors.append(f"Broken relative link: {link}")
    return errors


def stage(lesson_id: str, candidate_path: Path) -> dict[str, Any]:
    ensure_layout()
    lesson_path = DATA_DIR / "lessons" / f"{lesson_id}.json"
    if not lesson_path.is_file():
        raise EvolutionError(f"Unknown lesson: {lesson_id}")
    lesson = json_read(lesson_path)
    if lesson.get("decision") != "propose":
        raise EvolutionError("Only a lesson with decision=propose may be staged")
    _, target_root, target_file = target_config()
    candidate_path = candidate_path.expanduser().resolve()
    if not candidate_path.is_file():
        raise EvolutionError(f"Candidate file not found: {candidate_path}")
    base = target_file.read_text(encoding="utf-8")
    candidate = candidate_path.read_text(encoding="utf-8")
    if base == candidate:
        raise EvolutionError("Candidate is identical to the live target")
    errors = validate_frontmatter(candidate) + validate_links(candidate, target_root)
    if errors:
        raise EvolutionError("Invalid candidate: " + "; ".join(errors))
    diff_lines = list(difflib.unified_diff(base.splitlines(), candidate.splitlines(), fromfile="current/SKILL.md", tofile="candidate/SKILL.md", lineterm=""))
    changed = sum(1 for line in diff_lines if line.startswith(("+", "-")) and not line.startswith(("+++", "---")))
    seed = f"{lesson_id}\0{digest_file(target_file)}\0{digest_file(candidate_path)}".encode()
    proposal_id = short_id("proposal", seed)
    stored_candidate = DATA_DIR / "proposals" / "pending" / f"{proposal_id}.candidate.md"
    if stored_candidate.exists():
        raise EvolutionError(f"Proposal already exists: {proposal_id}")
    stored_candidate.write_text(candidate, encoding="utf-8")
    record = {
        "schema_version": 1, "proposal_id": proposal_id, "created_at": utc_now(),
        "status": "pending", "lesson_ids": [lesson_id], "target_path": str(target_root),
        "target_file": str(target_file), "base_sha256": digest_file(target_file),
        "candidate_sha256": digest_file(stored_candidate),
        "candidate_path": stored_path(stored_candidate),
        "changed_lines": changed, "diff": "\n".join(diff_lines) + "\n",
        "explicit_exclusions": lesson.get("scope", {}).get("excludes", []),
    }
    write_new_json(DATA_DIR / "proposals" / "pending" / f"{proposal_id}.json", record)
    append_event("proposal_staged", proposal_id=proposal_id, lesson_id=lesson_id, changed_lines=changed)
    return record


def pending_proposal(proposal_id: str) -> dict[str, Any]:
    path = DATA_DIR / "proposals" / "pending" / f"{proposal_id}.json"
    if not path.is_file():
        raise EvolutionError(f"Unknown pending proposal: {proposal_id}")
    if (DATA_DIR / "proposals" / "rejected" / f"{proposal_id}.json").exists():
        raise EvolutionError(f"Proposal is rejected and terminal: {proposal_id}")
    if (DATA_DIR / "proposals" / "accepted" / f"{proposal_id}.json").exists():
        raise EvolutionError(f"Proposal is already applied: {proposal_id}")
    return json_read(path)


def latest_validation(proposal_id: str) -> dict[str, Any] | None:
    runs = sorted((DATA_DIR / "regressions" / "runs").glob(f"{proposal_id}-*.json"))
    return json_read(runs[-1]) if runs else None


REQUIRED_SCENARIO_FIELDS = {"scenario_id", "metric_family", "kind", "task", "evidence"}


def load_scenario(path: Path) -> dict[str, Any]:
    scenario = json_read(path)
    missing = sorted(REQUIRED_SCENARIO_FIELDS - set(scenario))
    if missing or scenario.get("kind") not in {"trigger", "transfer", "regression"}:
        raise EvolutionError(f"Invalid scenario {path}: missing {', '.join(missing)} or invalid kind")
    return scenario


def evaluation_packet(variant: str, skill_text: str, scenario: dict[str, Any]) -> str:
    return f"""# Independent evaluation packet {variant}

Use the supplied skill and scenario in a fresh context. Do not compare this
packet with another version, infer the intended answer, or mention evaluation.

## Skill

{skill_text}

## Task

{scenario['task']}

## Available evidence

{scenario['evidence']}

## Response

Explain the deterministic approach, key distinctions, and regression cases.
Preserve uncertainty when evidence is insufficient. Return the full response.
"""


def prepare_evaluation(proposal_id: str, scenario_paths: list[Path]) -> dict[str, Any]:
    ensure_layout()
    proposal = pending_proposal(proposal_id)
    scenarios = [load_scenario(path.expanduser().resolve()) for path in scenario_paths]
    trigger_families = {item["metric_family"] for item in scenarios if item["kind"] == "trigger"}
    if not trigger_families or not any(item["kind"] == "transfer" and item["metric_family"] not in trigger_families for item in scenarios):
        raise EvolutionError("Provide a trigger and a different-family transfer scenario")
    _, _, target_file = target_config()
    candidate = SKILL_DIR / proposal["candidate_path"]
    evaluation_id = short_id("evaluation", f"{proposal_id}:{','.join(item['scenario_id'] for item in scenarios)}".encode())
    packet_dir = DATA_DIR / "evaluations" / "pending" / evaluation_id
    packet_dir.mkdir(parents=True, exist_ok=False)
    packets: list[dict[str, str]] = []
    for scenario in scenarios:
        for variant, skill_text in (("A", target_file.read_text(encoding="utf-8")), ("B", candidate.read_text(encoding="utf-8"))):
            packet = packet_dir / f"{scenario['scenario_id']}-{variant}.md"
            packet.write_text(evaluation_packet(variant, skill_text, scenario), encoding="utf-8")
            packets.append({"scenario_id": scenario["scenario_id"], "variant": variant, "path": stored_path(packet)})
    manifest = {
        "schema_version": 1, "evaluation_id": evaluation_id, "created_at": utc_now(), "proposal_id": proposal_id,
        "scenarios": scenarios, "packets": packets, "variant_mapping": {"A": "current", "B": "candidate"},
        "result_template": {"evaluation_id": evaluation_id, "reviewer": "...", "runs": [{"scenario_id": "...", "variant": "A|B", "mode": "executed", "evaluator_run_id": "fresh session ID", "output": "verbatim output", "evidence": "run link or note"}]},
    }
    write_new_json(packet_dir / "manifest.json", manifest)
    append_event("evaluation_prepared", evaluation_id=evaluation_id, proposal_id=proposal_id, scenario_count=len(scenarios))
    return manifest


def evaluation_manifest(evaluation_id: str) -> tuple[Path, dict[str, Any]]:
    path = DATA_DIR / "evaluations" / "pending" / evaluation_id / "manifest.json"
    if not path.is_file():
        raise EvolutionError(f"Unknown pending evaluation: {evaluation_id}")
    return path, json_read(path)


def record_evaluation(evaluation_id: str, results_path: Path) -> dict[str, Any]:
    ensure_layout()
    _, manifest = evaluation_manifest(evaluation_id)
    results = json_read(results_path)
    if results.get("evaluation_id") != evaluation_id:
        raise EvolutionError("Results evaluation_id does not match")
    expected = {(item["scenario_id"], variant) for item in manifest["scenarios"] for variant in ("A", "B")}
    seen: set[tuple[str, str]] = set(); run_ids: dict[str, set[str]] = {}
    for run in results.get("runs", []):
        key = (run.get("scenario_id"), run.get("variant"))
        if key not in expected or key in seen or run.get("mode") != "executed":
            raise EvolutionError(f"Unexpected, duplicate, or unexecuted run: {key}")
        if not all(str(run.get(field, "")).strip() for field in ("evaluator_run_id", "output", "evidence")):
            raise EvolutionError(f"Run lacks session ID, output, or evidence: {key}")
        seen.add(key); run_ids.setdefault(str(run["scenario_id"]), set()).add(str(run["evaluator_run_id"]))
    if seen != expected or any(len(ids) < 2 for ids in run_ids.values()):
        raise EvolutionError("Record exactly one executed A/B pair in separate fresh sessions for every scenario")
    record = {"schema_version": 1, "recorded_at": utc_now(), **results}
    destination = DATA_DIR / "evaluations" / "completed" / f"{evaluation_id}.results.json"
    write_new_json(destination, record)
    append_event("evaluation_recorded", evaluation_id=evaluation_id, proposal_id=manifest["proposal_id"])
    return record


def assess_evaluation(evaluation_id: str, judgment_path: Path) -> dict[str, Any]:
    _, manifest = evaluation_manifest(evaluation_id)
    results_file = DATA_DIR / "evaluations" / "completed" / f"{evaluation_id}.results.json"
    if not results_file.is_file():
        raise EvolutionError("Record executed evaluator outputs before assessing them")
    results, judgment = json_read(results_file), json_read(judgment_path)
    if judgment.get("evaluation_id") != evaluation_id:
        raise EvolutionError("Judgment evaluation_id does not match")
    scenarios = {item["scenario_id"]: item for item in manifest["scenarios"]}
    judgments = judgment.get("scenarios", [])
    if {item.get("scenario_id") for item in judgments} != set(scenarios):
        raise EvolutionError("Judgment must assess every prepared scenario exactly once")
    outputs = {(item["scenario_id"], item["variant"]): item for item in results["runs"]}
    normalized = []
    for item in judgments:
        scenario = scenarios[item["scenario_id"]]
        if item.get("comparison") not in {"improved", "same", "regressed"} or not str(item.get("evidence", "")).strip():
            raise EvolutionError(f"Invalid or unsupported judgment for {item['scenario_id']}")
        normalized.append({"scenario_id": scenario["scenario_id"], "kind": scenario["kind"], "metric_family": scenario["metric_family"], "mode": "executed", "current_outcome": outputs[(scenario["scenario_id"], "A")]["output"], "candidate_outcome": outputs[(scenario["scenario_id"], "B")]["output"], "comparison": item["comparison"], "expected_behavior_met": item.get("expected_behavior_met") is True, "critical_regression": item.get("critical_regression") is True, "evidence": item["evidence"]})
    assessment = {"schema_version": 1, "evaluation_id": evaluation_id, "reviewer": judgment.get("reviewer", "unknown"), "claims": judgment.get("claims", []), "rubric": judgment.get("rubric", {}), "scenarios": normalized, "summary": judgment.get("summary", ""), "limitations": judgment.get("limitations", []), "evaluator_results_path": stored_path(results_file)}
    destination = DATA_DIR / "evaluations" / "completed" / f"{evaluation_id}.assessment.json"
    write_new_json(destination, assessment)
    append_event("evaluation_assessed", evaluation_id=evaluation_id, proposal_id=manifest["proposal_id"])
    return assessment


def gate_assessment(assessment: dict[str, Any], proposal: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    reasons: list[str] = []
    rubric_keys = {
        "trigger_addressed", "different_family_transfer_passed", "no_critical_regressions",
        "no_instruction_contradiction", "minimal_localized_delta", "no_unjustified_metric_specificity",
    }
    rubric = assessment.get("rubric", {})
    for key in sorted(rubric_keys):
        if rubric.get(key) is not True:
            reasons.append(f"Rubric check is not true: {key}")
    scenarios = assessment.get("scenarios", [])
    executed = [s for s in scenarios if s.get("mode") == "executed"]
    triggers = [s for s in executed if s.get("kind") == "trigger" and s.get("comparison") == "improved" and s.get("expected_behavior_met") is True]
    transfers = [s for s in executed if s.get("kind") == "transfer" and s.get("comparison") in {"improved", "same"} and s.get("expected_behavior_met") is True]
    trigger_families = {s.get("metric_family") for s in triggers}
    transfers = [s for s in transfers if s.get("metric_family") not in trigger_families]
    if not triggers:
        reasons.append("No executed, improved triggering scenario met expectations")
    if not transfers:
        reasons.append("No executed transfer scenario from a different metric family met expectations")
    for scenario in scenarios:
        if not str(scenario.get("evidence", "")).strip():
            reasons.append(f"Scenario lacks evidence: {scenario.get('scenario_id', '<unknown>')}")
        if scenario.get("critical_regression") is True or scenario.get("comparison") == "regressed":
            reasons.append(f"Regression reported: {scenario.get('scenario_id', '<unknown>')}")
    claims = assessment.get("claims", [])
    if not claims:
        reasons.append("Assessment contains no claims")
    for index, claim in enumerate(claims):
        if claim.get("status") not in {"executed", "inferred", "not_tested"}:
            reasons.append(f"Claim {index} has invalid status")
        if not str(claim.get("evidence", "")).strip():
            reasons.append(f"Claim {index} lacks evidence or limitation")
    candidate = SKILL_DIR / proposal["candidate_path"]
    _, target_root, target_file = target_config()
    structural = validate_frontmatter(candidate.read_text(encoding="utf-8")) + validate_links(candidate.read_text(encoding="utf-8"), target_root)
    reasons.extend(structural)
    if digest_file(target_file) != proposal["base_sha256"]:
        reasons.append("Live target hash differs from proposal base")
    if digest_file(candidate) != proposal["candidate_sha256"]:
        reasons.append("Stored candidate hash differs from proposal")
    if proposal.get("changed_lines", 0) <= 0:
        reasons.append("Proposal has no changed lines")
    checks = {"frontmatter_and_links": not structural, "base_hash_current": digest_file(target_file) == proposal["base_sha256"], "candidate_hash_valid": digest_file(candidate) == proposal["candidate_sha256"]}
    return reasons, checks


def validate(proposal_id: str, assessment_path: Path) -> dict[str, Any]:
    ensure_layout()
    proposal = pending_proposal(proposal_id)
    assessment = json_read(assessment_path)
    reasons, checks = gate_assessment(assessment, proposal)
    stamp = compact_stamp()
    record = {
        "schema_version": 1, "validation_id": f"validation-{stamp}-{digest_bytes(json.dumps(assessment, sort_keys=True).encode())[:10]}",
        "proposal_id": proposal_id, "created_at": utc_now(),
        "decision": "approval_ready" if not reasons else "failed",
        "deterministic_checks": checks, "reasons": reasons, "assessment": assessment,
    }
    path = DATA_DIR / "regressions" / "runs" / f"{proposal_id}-{stamp}.json"
    write_new_json(path, record)
    append_event("proposal_validated", proposal_id=proposal_id, decision=record["decision"], validation_id=record["validation_id"])
    return record


def reject(proposal_id: str, reason: str) -> dict[str, Any]:
    if not reason.strip():
        raise EvolutionError("A non-empty rejection reason is required")
    proposal = pending_proposal(proposal_id)
    record = {**proposal, "status": "rejected", "rejected_at": utc_now(), "rejection_reason": reason.strip()}
    write_new_json(DATA_DIR / "proposals" / "rejected" / f"{proposal_id}.json", record)
    append_event("proposal_rejected", proposal_id=proposal_id, reason=reason.strip())
    return record


def atomic_write(path: Path, data: bytes) -> None:
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(root)).encode() + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def apply_proposal(proposal_id: str, approved: bool) -> dict[str, Any]:
    if not approved:
        raise EvolutionError("Application requires --approve after explicit human approval")
    proposal = pending_proposal(proposal_id)
    validation = latest_validation(proposal_id)
    if not validation or validation.get("decision") != "approval_ready":
        raise EvolutionError("Proposal has no approval-ready validation run")
    _, target_root, target_file = target_config()
    if str(target_root) != proposal["target_path"] or digest_file(target_file) != proposal["base_sha256"]:
        append_event("proposal_stale", proposal_id=proposal_id)
        raise EvolutionError("Proposal is stale: live target does not match recorded base")
    candidate = SKILL_DIR / proposal["candidate_path"]
    if digest_file(candidate) != proposal["candidate_sha256"]:
        raise EvolutionError("Stored candidate hash mismatch")
    snapshot = DATA_DIR / "snapshots" / proposal_id
    if snapshot.exists():
        raise EvolutionError(f"Snapshot already exists: {snapshot}")
    shutil.copytree(target_root, snapshot)
    before_tree = tree_hash(target_root)
    try:
        atomic_write(target_file, candidate.read_bytes())
        errors = validate_frontmatter(target_file.read_text(encoding="utf-8")) + validate_links(target_file.read_text(encoding="utf-8"), target_root)
        if errors or digest_file(target_file) != proposal["candidate_sha256"]:
            atomic_write(target_file, (snapshot / target_file.relative_to(target_root)).read_bytes())
            raise EvolutionError("Post-apply verification failed: " + "; ".join(errors))
    except Exception:
        if digest_file(target_file) != proposal["base_sha256"]:
            atomic_write(target_file, (snapshot / target_file.relative_to(target_root)).read_bytes())
        raise
    record = {
        **proposal, "status": "applied", "applied_at": utc_now(),
        "validation_id": validation["validation_id"], "snapshot_path": stored_path(snapshot),
        "base_tree_sha256": before_tree, "successor_sha256": digest_file(target_file),
        "successor_tree_sha256": tree_hash(target_root),
    }
    write_new_json(DATA_DIR / "proposals" / "accepted" / f"{proposal_id}.json", record)
    append_event("proposal_applied", proposal_id=proposal_id, successor_sha256=record["successor_sha256"])
    return record


def rollback(proposal_id: str, approved: bool) -> dict[str, Any]:
    if not approved:
        raise EvolutionError("Rollback requires --approve after explicit human approval")
    accepted_path = DATA_DIR / "proposals" / "accepted" / f"{proposal_id}.json"
    if not accepted_path.is_file():
        raise EvolutionError(f"Unknown applied proposal: {proposal_id}")
    applied = json_read(accepted_path)
    _, target_root, target_file = target_config()
    if digest_file(target_file) != applied.get("successor_sha256"):
        raise EvolutionError("Rollback refused: live target changed after this proposal")
    snapshot = SKILL_DIR / applied["snapshot_path"]
    snapshot_skill = snapshot / target_file.relative_to(target_root)
    if not snapshot_skill.is_file() or digest_file(snapshot_skill) != applied["base_sha256"]:
        raise EvolutionError("Rollback snapshot is missing or invalid")
    atomic_write(target_file, snapshot_skill.read_bytes())
    record = {"schema_version": 1, "proposal_id": proposal_id, "rolled_back_at": utc_now(), "restored_sha256": digest_file(target_file)}
    write_new_json(DATA_DIR / "proposals" / "accepted" / f"{proposal_id}.rollback.json", record)
    append_event("proposal_rolled_back", proposal_id=proposal_id, restored_sha256=record["restored_sha256"])
    return record


def status() -> dict[str, Any]:
    ensure_layout()
    target_info = target_status()
    target_name = target_info["target"]
    selected_target = target_info["selected"]
    def count(pattern: str) -> int:
        return len(list(DATA_DIR.glob(pattern)))
    pending_evaluation_manifests = sorted(DATA_DIR.glob("evaluations/pending/*/manifest.json"))
    pending_evaluation_proposals: set[str] = set()
    next_actions: list[dict[str, Any]] = []
    if selected_target is None:
        next_actions.append({
            "kind": "install_metric_forge_target",
            "message": "The deterministic-metric-engineering target is not installed in a supported Codex or Claude Code skill root.",
            "user_prompt": "Would you like installation guidance for Metric Forge, or would you like to set SKILL_EVOLUTION_TARGET to an existing installed copy?",
        })
    for path in pending_evaluation_manifests:
        manifest = json_read(path)
        proposal_id = manifest.get("proposal_id", "unknown")
        evaluation_id = manifest.get("evaluation_id", path.parent.name)
        pending_evaluation_proposals.add(proposal_id)
        next_actions.append({
            "kind": "run_independent_evaluation",
            "proposal_id": proposal_id,
            "evaluation_id": evaluation_id,
            "message": "Run every A/B packet in separate fresh, blinded sessions, then record outputs and assess the comparison.",
            "user_prompt": "Would you like me to arrange fresh evaluator runs if this environment supports them, show you the packets for user-run evaluation, or leave this proposal pending?",
        })
    for path in sorted(DATA_DIR.glob("proposals/pending/*.json")):
        proposal = json_read(path)
        proposal_id = proposal["proposal_id"]
        if proposal_id in pending_evaluation_proposals:
            continue
        validation = latest_validation(proposal_id)
        if validation and validation.get("decision") == "approval_ready":
            next_actions.append({
                "kind": "request_deployment_approval",
                "proposal_id": proposal_id,
                "message": "This proposal is approval-ready and has not changed the live target.",
                "user_prompt": f"Would you like me to apply proposal {proposal_id} now?",
            })
        else:
            next_actions.append({
                "kind": "prepare_or_complete_validation",
                "proposal_id": proposal_id,
                "message": "This proposal needs independent trigger and different-family transfer evidence before it can become approval-ready.",
                "user_prompt": "Would you like me to prepare fresh A/B evaluation packets, show the existing review artifacts, or leave the proposal pending?",
            })
    return {
        "target": target_name,
        "target_path": selected_target["path"] if selected_target else None,
        "target_sha256": selected_target["sha256"] if selected_target else None,
        "target_discovery": target_info,
        "experiences": count("experiences/distilled/*.json"), "lessons": count("lessons/*.json"),
        "pending_proposals": count("proposals/pending/*.json"),
        "accepted_proposals": count("proposals/accepted/*.json") - count("proposals/accepted/*.rollback.json"),
        "rejected_proposals": count("proposals/rejected/*.json"),
        "validation_runs": count("regressions/runs/*.json"), "scenario_cards": count("regressions/scenarios/*.json"),
        "pending_evaluations": len(pending_evaluation_manifests), "completed_evaluations": count("evaluations/completed/*.results.json"),
        "next_actions": next_actions,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    ingest_p = sub.add_parser("ingest", help="Copy and normalize a conversation file; use - for stdin")
    ingest_p.add_argument("input")
    lesson_p = sub.add_parser("lesson", help="Store an agent-authored candidate lesson")
    lesson_p.add_argument("experience_id"); lesson_p.add_argument("--from", dest="source", type=Path, required=True)
    stage_p = sub.add_parser("stage", help="Stage a candidate SKILL.md without changing the target")
    stage_p.add_argument("lesson_id"); stage_p.add_argument("--candidate", type=Path, required=True)
    validate_p = sub.add_parser("validate", help="Run deterministic gates over an evidence-bearing assessment")
    validate_p.add_argument("proposal_id"); validate_p.add_argument("--assessment", type=Path, required=True)
    evaluate_prepare_p = sub.add_parser("evaluate-prepare", help="Create separate fresh A/B evaluation packets")
    evaluate_prepare_p.add_argument("proposal_id"); evaluate_prepare_p.add_argument("--scenario", type=Path, action="append", required=True)
    evaluate_record_p = sub.add_parser("evaluate-record", help="Store evaluator outputs from prepared packets")
    evaluate_record_p.add_argument("evaluation_id"); evaluate_record_p.add_argument("--results", type=Path, required=True)
    evaluate_assess_p = sub.add_parser("evaluate-assess", help="Build executed assessment from evaluator outputs")
    evaluate_assess_p.add_argument("evaluation_id"); evaluate_assess_p.add_argument("--judgment", type=Path, required=True)
    reject_p = sub.add_parser("reject", help="Record an immutable rejection")
    reject_p.add_argument("proposal_id"); reject_p.add_argument("--reason", required=True)
    apply_p = sub.add_parser("apply", help="Apply an approval-ready proposal after explicit approval")
    apply_p.add_argument("proposal_id"); apply_p.add_argument("--approve", action="store_true")
    rollback_p = sub.add_parser("rollback", help="Rollback an applied proposal when the live target is unchanged")
    rollback_p.add_argument("proposal_id"); rollback_p.add_argument("--approve", action="store_true")
    sub.add_parser("status", help="Show target identity, hash, and artifact counts")
    sub.add_parser("target", help="Show deterministic-metric-engineering discovery candidates")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "ingest": output = ingest(args.input)
        elif args.command == "lesson": output = store_lesson(args.experience_id, args.source)
        elif args.command == "stage": output = stage(args.lesson_id, args.candidate)
        elif args.command == "validate": output = validate(args.proposal_id, args.assessment)
        elif args.command == "evaluate-prepare": output = prepare_evaluation(args.proposal_id, args.scenario)
        elif args.command == "evaluate-record": output = record_evaluation(args.evaluation_id, args.results)
        elif args.command == "evaluate-assess": output = assess_evaluation(args.evaluation_id, args.judgment)
        elif args.command == "reject": output = reject(args.proposal_id, args.reason)
        elif args.command == "apply": output = apply_proposal(args.proposal_id, args.approve)
        elif args.command == "rollback": output = rollback(args.proposal_id, args.approve)
        elif args.command == "target": output = target_status()
        else: output = status()
    except EvolutionError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "result": output}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

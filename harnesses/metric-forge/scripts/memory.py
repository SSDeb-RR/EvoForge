#!/usr/bin/env python3
"""Local, append-only experience memory for Deterministic Metric Forge."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SKILL_NAME = "deterministic-metric-engineering"
VALID_EVENT_TYPES = {
    "false_positive", "false_negative", "label_correction",
    "definition_ambiguity", "parsing_gap", "normalization_gap",
    "event_extraction_gap", "state_transition_gap", "regression_gap",
    "execution_mistake", "tooling_issue", "successful_strategy", "other",
}
VALID_SCOPES = {"session", "metric", "metric_family", "skill_candidate"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def stable_id(prefix: str, *parts: str) -> str:
    body = "\0".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(body.encode('utf-8')).hexdigest()[:12]}"


def memory_root(override: Path | None = None) -> Path:
    if override is not None:
        return Path(override).expanduser()
    configured = os.environ.get("EVOFORGE_MEMORY_DIR", "").strip()
    return Path(configured).expanduser() if configured else Path.home() / ".evoforge" / "memory"


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.exists():
        return [], []
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            warnings.append(f"Skipped malformed memory line {line_number}: {exc.msg}")
            continue
        if not isinstance(value, dict):
            warnings.append(f"Skipped non-object memory line {line_number}")
            continue
        rows.append(value)
    return rows, warnings


def initialize(override: Path | None = None) -> dict[str, str]:
    root = memory_root(override)
    skill_directory = root / SKILL_NAME
    skill_directory.mkdir(parents=True, exist_ok=True)
    sessions = skill_directory / "sessions.jsonl"
    experiences = skill_directory / "experiences.jsonl"
    sessions.touch(exist_ok=True)
    experiences.touch(exist_ok=True)
    manifest = skill_directory / "manifest.json"
    if not manifest.exists():
        atomic_write_json(manifest, {
            "schema_version": SCHEMA_VERSION,
            "skill_name": SKILL_NAME,
            "created_at": utc_now(),
            "format": "append-only-jsonl",
            "purpose": "Metric-engineering experiences for explicit EvoForge RSI review",
        })
    return {
        "memory_root": str(root),
        "skill_name": SKILL_NAME,
        "skill_memory": str(skill_directory),
        "manifest": str(manifest),
        "sessions": str(sessions),
        "experiences": str(experiences),
    }


def register_session(metric_slug: str = "", task: str = "", session_id: str = "", override: Path | None = None) -> dict[str, Any]:
    layout = initialize(override)
    timestamp = utc_now()
    effective_id = session_id.strip() or stable_id("session", SKILL_NAME, metric_slug, task, timestamp)
    row = {
        "schema_version": SCHEMA_VERSION,
        "session_id": effective_id,
        "skill_name": SKILL_NAME,
        "metric_slug": metric_slug.strip() or None,
        "task": task.strip(),
        "started_at": timestamp,
    }
    append_jsonl(Path(layout["sessions"]), row)
    return row


def validate_payload(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("experience payload must be a JSON object")
    if not str(payload.get("learning_signal", "")).strip():
        raise ValueError("experience requires a non-empty learning_signal")
    event_type = str(payload.get("event_type", "other"))
    if event_type not in VALID_EVENT_TYPES:
        raise ValueError(f"event_type must be one of: {', '.join(sorted(VALID_EVENT_TYPES))}")
    confidence = str(payload.get("confidence", "medium"))
    if confidence not in {"low", "medium", "high"}:
        raise ValueError("confidence must be low, medium, or high")
    scope = payload.get("scope", {"kind": "session"})
    if not isinstance(scope, dict) or scope.get("kind", "session") not in VALID_SCOPES:
        raise ValueError(f"scope.kind must be one of: {', '.join(sorted(VALID_SCOPES))}")
    if not isinstance(payload.get("engineering_event", {}), dict):
        raise ValueError("engineering_event must be an object")


def record(payload: dict[str, Any], override: Path | None = None) -> dict[str, Any]:
    validate_payload(payload)
    layout = initialize(override)
    source = {
        "session_id": payload.get("session_id"),
        "metric_slug": payload.get("metric_slug"),
        "metric_family": payload.get("metric_family"),
        "event_type": payload.get("event_type", "other"),
        "engineering_event": payload.get("engineering_event", {}),
        "learning_signal": str(payload["learning_signal"]).strip(),
        "why_useful": str(payload.get("why_useful", "")).strip(),
        "evidence": payload.get("evidence", []),
        "scope": payload.get("scope", {"kind": "session"}),
        "confidence": payload.get("confidence", "medium"),
        "pattern_keys": sorted({str(value).strip() for value in payload.get("pattern_keys", []) if str(value).strip()}),
        "tags": sorted({str(value).strip() for value in payload.get("tags", []) if str(value).strip()}),
        "source_artifacts": payload.get("source_artifacts", []),
    }
    canonical = json.dumps(source, sort_keys=True, ensure_ascii=False)
    content_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    path = Path(layout["experiences"])
    existing, _ = load_jsonl(path)
    duplicate = next((row for row in existing if row.get("content_sha256") == content_hash), None)
    if duplicate:
        return {**duplicate, "duplicate": True}
    row = {
        "schema_version": SCHEMA_VERSION,
        "experience_id": stable_id("memexp", SKILL_NAME, content_hash),
        "skill_name": SKILL_NAME,
        "created_at": utc_now(),
        "content_sha256": content_hash,
        **source,
    }
    append_jsonl(path, row)
    return {**row, "duplicate": False}


def record_best_effort(payload: dict[str, Any], override: Path | None = None) -> dict[str, Any]:
    try:
        return {"captured": True, "experience": record(payload, override)}
    except Exception as exc:
        return {"captured": False, "warning": f"Experience capture failed: {exc}"}


def status(override: Path | None = None) -> dict[str, Any]:
    layout = initialize(override)
    sessions, session_warnings = load_jsonl(Path(layout["sessions"]))
    experiences, experience_warnings = load_jsonl(Path(layout["experiences"]))
    return {
        **layout,
        "session_count": len(sessions),
        "experience_count": len(experiences),
        "warnings": session_warnings + experience_warnings,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Create local experience memory")
    session = sub.add_parser("session", help="Register a Metric Forge invocation")
    session.add_argument("--metric-slug", default="")
    session.add_argument("--task", default="")
    session.add_argument("--session-id", default="")
    record_parser = sub.add_parser("record", help="Best-effort append of a structured experience")
    record_parser.add_argument("input", type=Path)
    sub.add_parser("status", help="Show memory paths, counts, and warnings")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "init":
            output = initialize()
        elif args.command == "session":
            output = register_session(args.metric_slug, args.task, args.session_id)
        elif args.command == "record":
            payload = json.loads(args.input.read_text(encoding="utf-8"))
            output = record_best_effort(payload)
        else:
            output = status()
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "result": output}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

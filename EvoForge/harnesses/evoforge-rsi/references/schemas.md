# Artifact schemas

Artifacts are JSON encoded as UTF-8. Unknown optional fields may be retained.
Core records are immutable after creation; lifecycle facts are separate files
and append-only history events.

## Normalized conversation

```json
{
  "schema_version": 1,
  "conversation_id": "exp-...",
  "source": {
    "kind": "json|markdown|text|unknown",
    "original_path": "/absolute/path/or/null",
    "stored_path": "evolution/experiences/raw/...",
    "sha256": "...",
    "parser": "json_messages|json_recursive|speaker_text|plain_text",
    "warnings": []
  },
  "metadata": {},
  "messages": [{
    "sequence": 0,
    "role": "user|assistant|tool|system|unknown",
    "content": "verbatim usable content",
    "timestamp": null,
    "code_blocks": [],
    "references": [],
    "source_locator": {"path": [], "line_start": null, "line_end": null}
  }]
}
```

## Candidate lesson

```json
{
  "schema_version": 1,
  "summary": "...",
  "source_experiences": ["exp-..."],
  "events": [{
    "type": "SKILL_INSTRUCTION_GAP",
    "evidence": [{"experience_id": "exp-...", "message_sequences": [1, 4], "note": "..."}]
  }],
  "attribution": {"primary": "A", "secondary": [], "rationale": "...", "alternatives_rejected": []},
  "specific_fix": "...",
  "generalization_hypothesis": "...",
  "transfer_cases": ["..."],
  "scope": {"applies": ["..."], "excludes": ["..."]},
  "counterargument": "...",
  "confidence": "low|medium|high",
  "novelty": {"rating": "new|extends|duplicate|previously_rejected", "matches": [], "rationale": "..."},
  "expected_impact": "...",
  "affected_component": "...",
  "proposed_action": "...",
  "decision": "propose|gather_more_evidence|do_not_evolve",
  "decision_reason": "..."
}
```

The helper adds `lesson_id`, `created_at`, and the primary `experience_id`.

## Proposal core

The helper creates the proposal from an eligible lesson and candidate file. It
contains `proposal_id`, base and candidate hashes, target path, lesson IDs,
candidate path, unified diff, changed-line counts, explicit exclusions, and the
initial `pending` status. Do not hand-edit it.

## Scenario card

```json
{
  "schema_version": 1,
  "scenario_id": "scenario-...",
  "title": "...",
  "metric_family": "...",
  "kind": "trigger|transfer|regression",
  "task": "What the agent must decide or do",
  "evidence": "Inputs available to the agent",
  "expected_behavior": ["Observable requirement"],
  "failure_conditions": ["Observable regression"],
  "provenance": ["lesson or experience ID"]
}
```

## Validation assessment

See [validation.md](validation.md). The helper stores the submitted assessment,
deterministic checks, decision, hashes, and timestamp as an immutable run.


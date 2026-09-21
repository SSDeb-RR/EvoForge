# Metric-engineering experience memory

Metric Forge preserves selected engineering discoveries as structured local
experience so EvoForge RSI can analyze patterns across sessions. Capture is
best-effort: failure to write memory must never block the metric task.

## Local storage

The helper creates this directory on first invocation:

```text
~/.evoforge/memory/deterministic-metric-engineering/
├── manifest.json
├── sessions.jsonl
└── experiences.jsonl
```

Set `EVOFORGE_MEMORY_DIR` to choose another root. No daemon, database,
embedding service, model API, or background transcript collector is involved.

## What to capture

Record a compact experience only when the work produces a potentially useful
maintenance signal:

- a confirmed false positive or false negative and its actual failure stage;
- a corrected source label or newly exposed definition ambiguity;
- a parsing, normalization, event-extraction, state-transition, or regression gap;
- a reusable debugging or regression strategy;
- an execution mistake that should be remembered but may not justify evolution.

Do not store ordinary successful steps, entire transcripts, secrets, or
metric-specific regexes as generalized lessons. Point to local artifacts when
possible and retain the narrow metric scope until EvoForge RSI establishes
transfer.

## Record shape

```json
{
  "session_id": "session-...",
  "metric_slug": "delivery-date-mismatch",
  "metric_family": "temporal-scheduling",
  "event_type": "state_transition_gap",
  "engineering_event": {
    "reported_behavior": "Accepted alternatives were still flagged as mismatches.",
    "observed_cause": "The state machine retained the rejected request after later acceptance.",
    "correction_or_outcome": "Acceptance now supersedes the earlier request state.",
    "validation": "All supplied calls and prior regressions passed."
  },
  "learning_signal": "Temporal metrics may need explicit supersession rules when conversational state changes.",
  "why_useful": "The mechanism may recur in other request-proposal-acceptance metrics.",
  "evidence": [{"artifact": "tests/test_regression_suite.py", "locator": "test_accepted_alternative"}],
  "confidence": "high",
  "scope": {"kind": "metric_family", "subject_id": "temporal-scheduling"},
  "pattern_keys": ["accepted-value-supersedes-prior-request"],
  "tags": ["state-machine", "false-positive"]
}
```

Scopes are `session`, `metric`, `metric_family`, and `skill_candidate`.
`skill_candidate` means eligible for later analysis, not established guidance.

## Commands

```bash
python3 scripts/memory.py session --metric-slug METRIC --task "brief task"
python3 scripts/memory.py record /path/to/experience.json
python3 scripts/memory.py status
```

The helper validates, hashes, deduplicates, timestamps, and appends records.
EvoForge RSI still performs attribution, novelty checking, generalization,
validation, and explicit human-approved promotion.

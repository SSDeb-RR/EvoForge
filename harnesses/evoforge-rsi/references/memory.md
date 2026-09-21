# Consuming Metric Forge experience memory

Metric Forge may accumulate structured experiences under
`~/.evoforge/memory/deterministic-metric-engineering/`. Set
`EVOFORGE_MEMORY_DIR` only to choose another local root. EvoForge RSI reads the
ledger when explicitly invoked; memory never triggers evolution.

## Retrieve

```bash
python3 scripts/evolve.py memory retrieve --limit 50
python3 scripts/evolve.py memory retrieve --query "state transition" --limit 20
```

Retrieval is local and deterministic. It filters records for the fixed Metric
Forge target, orders by textual relevance or recency, reports malformed lines,
summarizes event types and scopes, and groups recurring `pattern_keys`.

Inspect records before importing. Repetition is useful evidence but does not
establish causality or generality. Several observations from one metric
strengthen a metric-specific hypothesis, not independent cross-family evidence.

## Import

```bash
python3 scripts/evolve.py memory import memexp-...
```

Import converts one record into the existing normalized-experience format and
preserves its hash, metric identity, event type, engineering evidence, scope,
confidence, and pattern keys. Continue with the same attribution, lesson,
proposal, A/B validation, and human approval pipeline used for a supplied
session transcript.

## Scope discipline

- `session`: one engineering interaction; normally insufficient alone.
- `metric`: evidence about one evaluator, not Metric Forge as a whole.
- `metric_family`: a possible shared mechanism within one family.
- `skill_candidate`: explicitly marked for broader analysis, but still unproven.

A stored false positive is not automatically a skill deficiency. It may still
be an implementation bug, ambiguous definition, wrong label, missing example,
execution mistake, or tooling failure. Preserve `do_not_evolve` and
`gather_more_evidence` as valid outcomes.

If memory is absent, empty, damaged, or unreadable, explain the warning and
continue with supplied session evidence. Never invent missing records.

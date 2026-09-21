# Architecture

EvoForge contains a specialized two-harness loop, not an autonomous agent
platform.

```text
Metric Forge
  metric definition + conversational data + code/tests
  → deterministic evaluator + regressions
  → selected structured experiences in persistent local memory

EvoForge RSI
  accumulated experiences and/or selected work conversation + Metric Forge + local ledger
  → attribution → generalized lesson → staged delta → A/B gate → explicit apply
```

## Why the target stays fixed in V1

The evolution mechanics are reusable, but the attribution rubric, validation
scenarios, and delta quality rules are currently designed for deterministic
conversational evaluator engineering. Allowing arbitrary target skills would
make a successful-looking proposal less trustworthy. Future target adapters may
extend this package without weakening the V1 boundary.

## Local data and privacy

The repository contains an empty evolution-ledger skeleton only. Metric Forge
writes structured experiences to `~/.evoforge/memory/` by default, or the root
named by `EVOFORGE_MEMORY_DIR`. EvoForge RSI writes proposal and lineage data
beside its installed harness by default, or under `SKILL_EVOLUTION_DATA`.
Records remain inspectable local JSON/JSONL; users control retention, redaction,
backup, and deletion.

Memory accumulation is not autonomous evolution. Metric Forge records compact
engineering evidence best-effort. EvoForge RSI reads it only after explicit
invocation and retains the existing attribution, transfer-validation, and
human-approval gates.

## Cross-product target discovery

EvoForge RSI searches Codex and Claude Code roots for the fixed Metric Forge
target. A mixed installation is therefore supported without copying both
harnesses into the same product. `SKILL_EVOLUTION_TARGET` resolves intentional
ambiguity when multiple target copies exist.

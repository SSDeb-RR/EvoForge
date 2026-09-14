# Architecture

EvoForge contains a specialized two-harness loop, not an autonomous agent
platform.

```text
Metric Forge
  metric definition + conversational data + code/tests
  → deterministic evaluator + regressions

EvoForge RSI
  selected work conversation + Metric Forge + local ledger
  → attribution → generalized lesson → staged delta → A/B gate → explicit apply
```

## Why the target stays fixed in V1

The evolution mechanics are reusable, but the attribution rubric, validation
scenarios, and delta quality rules are currently designed for deterministic
conversational evaluator engineering. Allowing arbitrary target skills would
make a successful-looking proposal less trustworthy. Future target adapters may
extend this package without weakening the V1 boundary.

## Local data and privacy

The repository contains an empty ledger skeleton only. Each installation writes
its own data beside the installed EvoForge RSI harness by default, or at the
directory named by `SKILL_EVOLUTION_DATA`. Raw conversations may contain
sensitive data; users should decide whether to retain, redact, back up, or
delete their own local ledger.

## Cross-product target discovery

EvoForge RSI searches Codex and Claude Code roots for the fixed Metric Forge
target. A mixed installation is therefore supported without copying both
harnesses into the same product. `SKILL_EVOLUTION_TARGET` resolves intentional
ambiguity when multiple target copies exist.

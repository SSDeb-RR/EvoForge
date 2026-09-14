# EvoForge

**Evidence-grounded evolution for agent harnesses.**

EvoForge is a human-controlled meta-harness that learns from real engineering experience to improve deterministic evaluator-building workflows.

## What is included

| Harness | Role |
|---|---|
| **Metric Forge** (`deterministic-metric-engineering`) | Builds, audits, debugs, and optimizes deterministic Python evaluators and their regression suites from metric definitions, transcript data, and existing code. |
| **EvoForge RSI** (`skill-evolution`) | Reviews a manually supplied work conversation, attributes the cause, extracts a reusable lesson, stages a minimal improvement to Metric Forge, independently validates it, and requires explicit approval before applying it. |

The meta-harness is the center of this repository. Metric Forge is its first
concrete target and the only target supported in V1.

## The core loop

```text
Real engineering conversation
        ↓
Evidence and cause attribution
        ↓
Reusable lesson or do-not-evolve decision
        ↓
Minimal staged Metric Forge change
        ↓
Fresh A/B behavioral evaluation
        ↓
Human review and explicit local application
```

Nothing is changed merely because an evaluator was wrong. A parser bug,
ambiguous metric definition, missing data, or agent execution mistake may be
recorded without changing the reusable harness.

## Start here

1. Read [installation](docs/INSTALL.md) and install both harnesses in Codex,
   Claude Code, or one of each.
2. Confirm discovery from the installed EvoForge RSI directory:

   ```bash
   python scripts/evolve.py target
   ```

3. Use Metric Forge for evaluator work.
4. When a conversation contains reusable learning, explicitly invoke
   `$skill-evolution` with the transcript or export.
5. Follow the next action shown by the harness. A pending proposal will always
   say whether it needs A/B evaluation, review, more evidence, rejection, or
   explicit deployment approval.

See [usage](docs/USAGE.md), [architecture](docs/ARCHITECTURE.md), and
[publishing notes](docs/PUBLISHING.md).

## Boundaries

- V1 targets only the included deterministic evaluator-engineering harness.
- It supports arbitrary conversation-export formats, but does not upload them.
- It is manually invoked; there is no daemon, webhook, scheduler, or automatic
  skill mutation.
- It stages and validates before application; it never auto-applies or merges.
- Generated evidence and lessons are local state and are intentionally ignored
  by this distribution.

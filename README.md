# EvoForge

> **Evidence-grounded evolution for deterministic evaluator engineering.**

EvoForge is a human-supervised package for building and improving deterministic
evaluators for conversational and voice-agent systems. It pairs two harnesses:

| Harness | Purpose |
|---|---|
| **Metric Forge** | Converts metric definitions, transcripts, labels, code, and tests into deterministic Python evaluators with regression coverage, while selectively accumulating structured engineering experience. |
| **EvoForge RSI** | Extracts reusable engineering lessons from accumulated experiences or supplied agent-session transcripts and evolves Metric Forge through validation-gated, human-approved deltas. |

## Motivation

Converting an LLM judge, broad heuristic, or informal business rule into a
deterministic evaluator is iterative engineering. Definitions are incomplete,
labels can be wrong, transcripts reveal linguistic variation, parsers encode
assumptions, and a local false-positive fix can create a regression.

Metric Forge addresses the evaluator itself. EvoForge RSI addresses the
engineering procedure used to build evaluators. It asks not “how do we patch
this metric?”, but “does this session reveal a missing reusable capability in
the evaluator-engineering harness?”

```text
Metric definition + transcripts + implementation
        ↓
Metric Forge → deterministic evaluator + evidence + regressions
        ↓
Structured local experiences and/or selected engineering-session transcript
        ↓
EvoForge RSI → lesson → staged delta → A/B validation → explicit approval
```

## What it enables

### Metric Forge

- Audits labels before treating them as ground truth.
- Prefers normalization, role-aware pattern families, event extraction,
  finite-state logic, and deterministic temporal reasoning over LLM judging.
- Separates historical context, customer requests, agent proposals, rejections,
  acceptance, confirmation, and non-applicable cases.
- Produces structured evidence with the production result.
- Builds regression suites from all supplied calls plus targeted edge cases.
- Preserves selected false-positive/negative analyses, label corrections,
  failure-stage discoveries, and regression insights as local structured memory.
- Supports multilingual conversational evidence when the data requires it,
  including English, Hindi, and Hinglish variants.

### EvoForge RSI

- Ingests JSON, Markdown, plain text, pasted chat, transcript files, and
  partially structured session exports.
- Retrieves and imports accumulated Metric Forge experiences without requiring
  users to manually reconstruct earlier engineering sessions.
- Preserves raw hashes, normalized message locators, lessons, proposal diffs,
  validation records, snapshots, and append-only lineage.
- Attributes a failure before evolving: target-harness deficiency, execution
  mistake, metric-specific edge case, ambiguity, missing evidence, environment,
  or regression gap.
- Records `do_not_evolve` decisions when the reusable harness should not change.
- Stages the smallest target `SKILL.md` delta without editing the live target.
- Requires fresh blinded A/B outputs and an evidence-bearing validation gate.
- Explains pending states and asks the user to review, evaluate, reject, or
  explicitly apply; it never auto-applies a change.

## Installation

EvoForge contains two directories:

```text
harnesses/metric-forge/  → install as deterministic-metric-engineering
harnesses/evoforge-rsi/  → install as skill-evolution
```

This guide means **Claude Code**, not Google Cloud Code.

### macOS — Codex

```bash
mkdir -p ~/.codex/skills
cp -R harnesses/metric-forge ~/.codex/skills/deterministic-metric-engineering
cp -R harnesses/evoforge-rsi ~/.codex/skills/skill-evolution
cd ~/.codex/skills/skill-evolution
python scripts/evolve.py target
```

### macOS — Claude Code

```bash
mkdir -p ~/.claude/skills
cp -R harnesses/metric-forge ~/.claude/skills/deterministic-metric-engineering
cp -R harnesses/evoforge-rsi ~/.claude/skills/skill-evolution
cd ~/.claude/skills/skill-evolution
python scripts/evolve.py target
```

### Windows — Codex

```powershell
$skills = Join-Path $env:USERPROFILE ".codex\skills"
New-Item -ItemType Directory -Force -Path $skills
Copy-Item -Recurse harnesses\metric-forge (Join-Path $skills "deterministic-metric-engineering")
Copy-Item -Recurse harnesses\evoforge-rsi (Join-Path $skills "skill-evolution")
Set-Location (Join-Path $skills "skill-evolution")
python scripts\evolve.py target
```

### Windows — Claude Code

```powershell
$skills = Join-Path $env:USERPROFILE ".claude\skills"
New-Item -ItemType Directory -Force -Path $skills
Copy-Item -Recurse harnesses\metric-forge (Join-Path $skills "deterministic-metric-engineering")
Copy-Item -Recurse harnesses\evoforge-rsi (Join-Path $skills "skill-evolution")
Set-Location (Join-Path $skills "skill-evolution")
python scripts\evolve.py target
```

The two harnesses may be installed in different products. EvoForge RSI searches
both Codex and Claude Code local skill roots for Metric Forge. If two copies
exist, select one explicitly with `SKILL_EVOLUTION_TARGET`.

## Usage

Build or optimize an evaluator:

```text
Use $deterministic-metric-engineering to audit the supplied labels, implement
this conversational metric deterministically, preserve the output contract, and
add regression coverage from all supplied calls plus targeted edge cases.
```

Metric Forge registers each invocation and appends only meaningful engineering
signals best-effort. Inspect this local memory with:

```bash
cd ~/.codex/skills/deterministic-metric-engineering
python3 scripts/memory.py status
```

For Claude Code, use the corresponding path under `~/.claude/skills/`.

The default root is `~/.evoforge/memory/deterministic-metric-engineering/`.
Set `EVOFORGE_MEMORY_DIR` to choose a different local root.

Evolve the reusable evaluator-engineering harness:

```text
Use $skill-evolution to analyze accumulated Metric Forge experiences and this
agent-session transcript, if supplied, for a reusable improvement to the
deterministic evaluator-engineering harness. Create and validate any justified
proposal, show review artifacts, and stop before deployment.
```

EvoForge RSI first retrieves target-scoped memory, preserves metric and
metric-family boundaries, and then reuses the existing experience → lesson →
proposal → validation workflow. Memory never triggers evolution on its own.

Artifacts remain local under `evolution/`: raw/normalized sessions, lessons,
pending/accepted/rejected proposals, A/B evaluations, regression records,
snapshots, and append-only history. `python scripts/evolve.py status` reports
the current state and the next required user action.

## Relationship to SkillOpt and SkillOps

| Dimension | EvoForge | SkillOpt | SkillOps |
|---|---|---|---|
| Target | Deterministic conversational evaluator engineering | General text-space skill optimization | Skill-library operations and lifecycle management |
| Evidence | Accumulated structured engineering experience plus human-selected sessions | Scored rollouts and benchmark splits | Contracts, validators, artifacts, thresholds |
| Generalization | Cause attribution, novelty search, bounded lesson | Optimizer reflection and bounded edit selection | Typed contracts and maintenance actions |
| Promotion | Fresh A/B validation plus explicit human approval | Held-out validation/selection | Versioned, threshold-gated lifecycle |
| Runtime posture | Local and manually triggered | Research optimizer / optional session review | Broader control-loop framework |

[SkillOpt](https://github.com/microsoft/SkillOpt) treats a skill document as a
trainable external parameter and optimizes it using rollout/reflection/edit/gate
cycles. EvoForge borrows bounded edits and validation-gated adoption, but starts
from a human-selected engineering session, requires causal attribution, allows a
durable `do_not_evolve` outcome, and remains specialized to evaluator
engineering.

SkillOps emphasizes explicit contracts, validators, failure modes, lineage, and
maintenance actions. EvoForge shares its auditability discipline but avoids a
full manifest graph or autonomous control-loop runtime. Its distinctive bridge
is: session evidence → generalized engineering lesson → minimal validated delta.

## Research framing

EvoForge couples task-level adaptation (build a deterministic evaluator) with
process-level adaptation (improve the reusable engineering harness). Every
accepted change is traceable:

```text
structured experience or session evidence → experience event → attribution → lesson
→ proposal → validation → applied successor
```

## Privacy and publication

Publish only an empty `evolution/` skeleton. Metric Forge memory lives outside
the repository under `~/.evoforge/` by default. Session exports, experiences,
lessons, proposals, evaluator outputs, snapshots, and history are local
operational data and should never be committed. Choose a license and review the
package for private transcripts, credentials, and local paths before release.

## References

- Microsoft SkillOpt: <https://github.com/microsoft/SkillOpt>
- SkillOpt docs: <https://microsoft.github.io/SkillOpt/>
- SkillOps paper: <https://arxiv.org/abs/2605.13716>

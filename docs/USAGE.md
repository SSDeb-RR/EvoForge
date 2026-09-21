# Use EvoForge

## 1. Engineer or optimize an evaluator

In Codex or Claude Code, invoke Metric Forge with a metric definition,
transcripts, labels when available, and existing code/tests:

```text
Use $deterministic-metric-engineering to audit the supplied labels, implement
this conversational evaluator deterministically, and add regression coverage.
```

It prioritizes deterministic event/state logic, role-aware context, corrected
ground truth, and regression suites over an LLM judge.

At invocation, Metric Forge registers a local session. When the work reveals a
meaningful false positive/negative mechanism, label correction, definition
ambiguity, reusable debugging method, or regression gap, it appends a compact
structured experience. Routine turns and ordinary success are not retained.

Inspect accumulated experience with:

```bash
cd ~/.codex/skills/deterministic-metric-engineering
python3 scripts/memory.py status
```

## 2. Trigger reflection deliberately

When accumulated work or a specific conversation contains a possible reusable
insight, invoke EvoForge RSI. You may also supply pasted chat, Markdown, JSON,
plain text, or a transcript file:

```text
Use $skill-evolution to analyze accumulated Metric Forge experiences and this
conversation, if supplied, for a reusable improvement to the deterministic
evaluator-engineering harness. Create and validate any justified proposal, show
review artifacts, and stop before deployment.
```

The harness retrieves relevant target memory, optionally normalizes the supplied
session, reads Metric Forge and evolution history, then records an
evidence-linked lesson. It preserves metric scope and may conclude
`do_not_evolve`; that is useful when the issue belongs in an individual
evaluator, a definition, data, tooling, or execution discipline.

## 3. Review a staged proposal

Review artifacts are stored locally under the installed EvoForge RSI directory:

```text
evolution/experiences/   raw inputs and normalized representations
evolution/lessons/       distilled evidence-backed lessons
evolution/proposals/     pending, accepted, and rejected deltas
evolution/evaluations/   A/B packets, raw outputs, and judgments
evolution/regressions/   scenario cards and validation runs
evolution/snapshots/     pre-application target copies
evolution/history/       append-only event ledger
```

Run `python scripts/evolve.py status` for counts and the precise next action.
Pending A/B evaluation means the proposal is structurally valid but still needs
fresh current-versus-candidate behavioral outputs. It is not a deployment
failure and it is not silent.

## 4. Validate and apply intentionally

The agent either asks to arrange fresh evaluator sessions (when authorized and
available), guides you through user-run packets, or leaves the proposal pending.
Only after the recorded comparison passes the validation gate does a proposal
become `approval_ready`.

Then the agent must ask an explicit question naming the proposal. A clear reply
such as “Apply proposal proposal-...” permits:

```bash
python scripts/evolve.py apply PROPOSAL_ID --approve
```

Application verifies the base hash, snapshots the complete target harness,
writes only the staged `SKILL.md` atomically, and records lineage. It never
automatically merges or changes an unrelated skill.

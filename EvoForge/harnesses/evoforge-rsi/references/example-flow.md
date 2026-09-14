# Example input and output flow

This example illustrates mechanics, not a pre-approved lesson.

## Invoke and ingest

The user invokes the skill with a Markdown export:

```text
Use $skill-evolution with /tmp/metric-debug-chat.md.
```

The agent runs:

```bash
python scripts/evolve.py ingest /tmp/metric-debug-chat.md
```

The helper returns an experience ID, detected format, parser, warnings, and
normalized messages. The agent inspects the stored conversation, live target,
history, and scenario cards.

## Analyze and record

Suppose the conversation shows that an agent repeatedly patched a final Boolean
decision before locating whether parsing, normalization, event extraction, or
state transition failed. The agent first checks the target skill. If the target
already contains that diagnostic sequence, the correct lesson attribution is B
(execution mistake) and the run ends without a proposal.

If the instruction were genuinely absent, the agent would create a lesson JSON
with source message sequences, attribution A, the narrow fix, a generalized
diagnostic-stage hypothesis, transfer cases, boundaries, novelty search, and a
`propose` decision. It records that immutable lesson:

```bash
python scripts/evolve.py lesson EXP_ID --from /tmp/lesson.json
```

## Stage without modifying the target

The agent copies the live target `SKILL.md` to a temporary workspace and adds
only the missing diagnostic step. It then runs:

```bash
python scripts/evolve.py stage LESSON_ID --candidate /tmp/candidate-SKILL.md
```

The output includes a proposal ID, live base hash, candidate hash, exact unified
diff, changed-line count, and exclusions. The live target remains untouched.

## Validate and stop for review

The agent evaluates current and candidate skills using an executed triggering
scenario, an executed transfer scenario from another metric family, and all
relevant regression cards. After truthfully recording outcomes in the
assessment schema, it runs:

```bash
python scripts/evolve.py validate PROPOSAL_ID --assessment /tmp/assessment.json
```

If the returned decision is `approval_ready`, the agent shows the exact diff,
evidence, limitations, and risks, then stops. Approval-ready does not mean
applied.

## Apply only after explicit approval

After the user explicitly approves that proposal ID:

```bash
python scripts/evolve.py apply PROPOSAL_ID --approve
```

The helper rejects a stale live target, otherwise snapshots the full target
directory, atomically updates only `SKILL.md`, verifies its hash and structure,
and records the accepted lineage. A later explicit rollback is available only
while the live target still equals that applied successor.


---
name: skill-evolution
description: >
  Manually analyze accumulated Metric Forge experiences or supplied
  human-and-LLM work conversations for reusable lessons that may improve the
  deterministic metric-engineering harness. Use only when explicitly invoked
  to attribute evidence, stage and validate a minimal skill delta, and record
  auditable local lineage. Do not use for ordinary metric fixes or automatic
  self modification.
---

# Skill Evolution

Evolve a reusable skill from real conversational experience without turning
one task failure into a universal rule. The live target is never changed during
analysis or validation. Apply a staged change only after the user explicitly
approves that exact proposal.

## Deterministic Metric Forge target and helper

This V1 harness evolves only the included **Deterministic Metric Forge**
harness (`deterministic-metric-engineering`). It is intentionally not a
general-purpose mutator for arbitrary skills.

The target resolver searches the standard local Codex and Claude Code skill
roots, so the two harnesses may be installed in different products. It accepts
either `deterministic-metric-engineering` or the older
`deterministic_metric_engineering_skill` directory name. Use an explicit
`SKILL_EVOLUTION_TARGET` environment variable only to select one installed
copy when more than one is present. Read [interoperability guidance](references/interoperability.md)
before a cross-product setup.

Resolve this skill's directory, then invoke its helper as:

```bash
python scripts/evolve.py status
python scripts/evolve.py target
python scripts/evolve.py memory retrieve --limit 50
python scripts/evolve.py ingest /path/to/conversation
```

The helper owns format detection, normalization, IDs, storage, hashing,
diffs, validation bookkeeping, snapshots, and guarded state transitions. The
agent owns interpretation: evidence extraction, causal attribution, generalization,
lesson drafting, delta design, and scenario assessment.

## Required workflow

Follow these phases in order. Read [the detailed workflow](references/workflow.md)
before conducting an evolution run.

1. Retrieve locally accumulated Metric Forge experiences. If the user also
   provides a conversation file or pasted text, ingest it; for pasted text,
   save the exact content to a temporary file first. Never require reformatting.
2. Inspect the normalized conversation, the entire current target skill, related
   files, target hash, prior lessons, proposals, rejections, and regressions.
3. Extract only evidence-backed experience events with exact source locators.
4. Attribute each event's cause before considering a skill edit.
5. Test novelty and generality against the current skill and history.
6. Record a candidate lesson, including a `do_not_evolve` decision when that is
   the correct outcome.
7. For a justified lesson, draft the smallest useful replacement `SKILL.md` and
   stage it. Do not edit the live target.
8. Prepare separate fresh A/B evaluation packets for the triggering scenario,
   at least one different metric-family transfer scenario, and relevant
   regressions. Read [evaluation guidance](references/evaluation.md).
9. Record the independent evaluator outputs, assess the comparison, then run
   deterministic validation with the generated evidence-bearing assessment. Never
   describe a proposal as validated unless the resulting validation record says
   `approval_ready`.
10. Present the exact diff, evidence, validation, exclusions, and risks. Stop.
11. Only after explicit approval of that proposal, run `apply <proposal-id>
   --approve`. Recheck the base hash, snapshot the target, apply atomically, and
   verify the result.

## Conversation continuity

Do not end an evolution run with an unexplained pending state. Read the
[review dialogue guide](references/review-dialogue.md) whenever a proposal,
evaluation, validation, rejection, or deployment decision needs user input.

- After staging, say whether behavioral validation is still required and what
  artifact was created.
- If A/B packets are pending, explain in plain language what they test and ask
  the user whether they want the agent to arrange fresh evaluator runs (when
  the environment and user authorization allow), review the packets themselves,
  or leave the proposal pending.
- After evaluator outputs exist, offer to compare and assess them; show the
  exact judgment and validation artifacts before asking for deployment.
- Ask for deployment approval only when the helper reports `approval_ready`.
  Ask for the exact proposal ID and an unambiguous approval, such as “Apply
  proposal PROPOSAL_ID.” Never treat approval to review or validate as approval
  to modify the live target.
- If a proposal cannot progress, state why, give the smallest concrete next
  action, and offer rejection as an explicit alternative. Do not manufacture
  evaluator outputs, reviewer judgment, or approval.

## Decision boundary

A failed metric task is not automatically a failed skill.

Proceed toward a target-skill delta only when evidence supports a reusable
instruction or capability gap. Record but do not generalize:

- an execution mistake despite adequate instructions;
- a phrase, regex, exception, or business rule unique to one metric;
- an ambiguity that belongs in the metric definition;
- missing examples or data;
- an environment or tooling failure;
- a duplicate of guidance already present.

Read [the attribution and generalization rubric](references/attribution-and-generalization.md)
whenever deciding whether an event warrants evolution.

Read [local memory guidance](references/memory.md) before retrieving or
importing accumulated experience. A repeated metric-specific pattern is not
automatically a generalized Metric Forge lesson.

## Artifact rules

- Raw inputs are immutable local evidence. Preserve source bytes and SHA-256.
- Every distilled claim cites message sequence numbers or source locators.
- Lessons and proposals use the schemas in [schemas](references/schemas.md).
- Proposal deltas may replace only the target `SKILL.md` in V1.
- Keep proposal cores immutable. Store validation, rejection, application, and
  rollback as separate append-only artifacts and history events.
- Never overwrite or silently discard a rejected proposal.
- Never weaken an existing instruction merely to make the triggering case pass.
- Never claim execution, comparison, or validation that did not occur.

## Helper commands

```bash
python scripts/evolve.py ingest INPUT
python scripts/evolve.py memory retrieve --limit 50
python scripts/evolve.py memory import MEMORY_EXPERIENCE_ID
python scripts/evolve.py lesson EXPERIENCE_ID --from LESSON.json
python scripts/evolve.py stage LESSON_ID --candidate CANDIDATE_SKILL.md
python scripts/evolve.py evaluate-prepare PROPOSAL_ID --scenario TRIGGER.json --scenario TRANSFER.json
python scripts/evolve.py evaluate-record EVALUATION_ID --results RESULTS.json
python scripts/evolve.py evaluate-assess EVALUATION_ID --judgment JUDGMENT.json
python scripts/evolve.py validate PROPOSAL_ID --assessment ASSESSMENT.json
python scripts/evolve.py reject PROPOSAL_ID --reason "..."
python scripts/evolve.py apply PROPOSAL_ID --approve
python scripts/evolve.py rollback PROPOSAL_ID --approve
python scripts/evolve.py status
python scripts/evolve.py target
```

Read [validation guidance](references/validation.md) before preparing the
assessment. If evidence is insufficient, leave the proposal pending or reject
it with a durable reason. Read the [example flow](references/example-flow.md)
when performing the workflow for the first time.

## Final report

Report the experience ID, attribution, generalization decision, lesson ID,
proposal ID, target hash, changed sections, validation status, executed checks,
untested claims, exclusions, risks, and the exact next user action. If no skill
change is warranted, say so directly and identify where the issue belongs.

# Evolution workflow

## 1. Ingest and establish the baseline

Begin with `memory retrieve` to inspect target-scoped Metric Forge experiences.
Import the bounded records relevant to the mechanism under review. When a
source conversation is supplied, run `ingest`; for pasted content, place the
exact text in a temporary file first. Inspect stored evidence and treat parser
or memory warnings as uncertainty, not evidence.

Before analysis, read:

- every instruction and reference in the configured target skill;
- the current target hash shown by `status`;
- related distilled experiences and lessons;
- pending, accepted, and rejected proposals;
- prior validation runs and stored scenarios.

Search by concepts and failure mechanisms, not just exact phrases. Do not
propose knowledge already encoded.

## 2. Extract experience events

Identify concrete moments such as a new failure class, repeated mistake,
debugging strategy, abstraction, disambiguation method, instruction gap, or
regression improvement. Each event must include:

- what occurred;
- exact message sequence or source locator;
- observed consequence;
- correction or confirming evidence when available;
- uncertainties and competing explanations.

Do not treat speculation, an unverified assertion, or mere user dissatisfaction
as a confirmed event.

## 3. Attribute the cause

Apply the taxonomy and tests in
[attribution-and-generalization.md](attribution-and-generalization.md). The
primary attribution determines ownership; secondary attributions may be
recorded. Explain why plausible alternatives were rejected.

## 4. Generalize and search history

State the specific fix first, then state the proposed broader capability. Test
whether the broader form:

- applies to at least one different metric family;
- changes an agent decision that the current skill does not already guide;
- avoids source-specific vocabulary and implementation details;
- has a bounded scope and a falsifiable expected effect;
- does not conflict with accepted lessons or repeat a rejected proposal without
  materially stronger evidence.

Cluster compatible experiences when that produces a stronger abstraction. Do
not delay a high-confidence, safety-relevant lesson solely because it has one
source; instead require stronger transfer validation and state the evidence
limitation.

## 5. Record the lesson

Create a JSON lesson using the schema reference. Use `decision:
"do_not_evolve"` for execution mistakes, task-specific fixes, ambiguity, and
insufficient evidence. The history is valuable even when no patch follows.

Store it with:

```bash
python scripts/evolve.py lesson EXPERIENCE_ID --from /path/to/lesson.json
```

## 6. Stage a minimal delta

Copy the current target `SKILL.md` to a temporary workspace, make only the
candidate change there, and verify the text independently. The candidate should
usually add or refine one reasoning step, checklist item, failure category, or
validation requirement. Avoid broad rewrites.

Stage it with:

```bash
python scripts/evolve.py stage LESSON_ID --candidate /path/to/SKILL.md
```

The command records the live base hash, candidate hash, unified diff, explicit
exclusions, and immutable proposal core. It does not modify the target.

## 7. Run an independent comparison

Create one trigger and one different-family transfer scenario. The evaluator
must run the current and candidate skill in separate fresh sessions, without
being told which version is current or candidate. Generate packets, record the
verbatim outputs, then assess them using
[evaluation guidance](evaluation.md). Record observable decisions and evidence,
not stylistic preference. The evaluation commands create the assessment passed
to `validate`.

A failed gate remains pending unless explicitly rejected. A passed gate is only
`approval_ready`; it is not permission to apply.

If the comparison has not yet run, do not merely report “pending.” Explain that
it compares decisions made from the current and candidate skills in fresh,
separate sessions. Then ask the user for one concrete next step using the
wording and boundaries in [review dialogue](review-dialogue.md). Do not create
new evaluator sessions without any authorization required by the environment.

## 8. Human review and application

Show the exact proposal diff and validation record. Ask for approval only when
the proposal is approval-ready. After the user explicitly approves that exact
proposal, run:

```bash
python scripts/evolve.py apply PROPOSAL_ID --approve
```

The helper refuses stale bases, creates a full target snapshot, replaces
`SKILL.md` atomically, verifies the applied hash, and records lineage.

Rollback is also explicit:

```bash
python scripts/evolve.py rollback PROPOSAL_ID --approve
```

Rollback is refused if the live target differs from the applied successor, so a
later evolution cannot be silently erased.

At every terminal or waiting state, give the user an outcome plus a next action:

- no lesson: explain the attribution and whether to archive the experience;
- pending proposal: say what validation evidence is missing and offer the
  applicable review choices;
- failed validation: show the failed checks and offer revision, more evidence,
  or explicit rejection;
- approval-ready: show the reviewed artifacts and request exact deployment
  approval;
- applied or rolled back: report the target hash, snapshot or rollback record,
  and the result.

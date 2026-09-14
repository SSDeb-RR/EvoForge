# Attribution and generalization rubric

## Cause taxonomy

Use one primary cause and any supported secondary causes:

| Code | Cause | Skill-evolution implication |
|---|---|---|
| A | Target skill deficiency | Eligible if novel and generalizable |
| B | Execution mistake despite adequate skill | Record; normally do not evolve |
| C | Metric-specific edge case | Fix the metric, not the skill |
| D | Insufficient or ambiguous definition | Clarify the definition |
| E | Missing examples or data | Acquire evidence before evolving |
| F | Tooling or environment problem | Repair tooling/environment |
| G | Regression or test coverage gap | Eligible when the testing lesson transfers |
| H | Other | Explain ownership explicitly |

## Attribution test

For each event answer:

1. What exact decision or action failed?
2. Which instruction, if followed, would have prevented it?
3. Is that instruction already explicit in the current skill or references?
4. Did the agent ignore adequate guidance, or was the guidance absent,
   ambiguous, misplaced, or non-actionable?
5. Does the correction belong to the reusable workflow, the metric definition,
   an individual implementation, its tests, or the environment?
6. What evidence would falsify the chosen attribution?

Classify as A only when the current skill lacks sufficiently actionable guidance
for the demonstrated decision. Repetition strengthens evidence but does not
convert an execution mistake into a skill deficiency automatically.

## Generalization test

Record all of the following:

- **Specific fix:** the narrow correction for the observed task.
- **Capability hypothesis:** the reusable decision procedure suggested by it.
- **Transfer cases:** different metric families where it should help.
- **Boundary:** cases where the lesson must not apply.
- **Mechanism:** why the new instruction should change behavior.
- **Counterargument:** the strongest reason it may be accidental
  overgeneralization.
- **Novelty:** exact current-skill or history matches and how this differs.
- **Evidence strength:** number, independence, and quality of experiences.

Reject or retain as `do_not_evolve` when the generalized form merely hides a
metric-specific phrase, regex, exception, entity, date, or anecdote.

## Confidence guidance

- `high`: direct causal evidence, actionable missing guidance, and successful
  transfer validation without regressions.
- `medium`: credible gap and mechanism, but limited independent evidence.
- `low`: ambiguous cause, speculative transfer, or weak provenance.

Confidence is not the validation decision. A high-confidence lesson can still
fail regression; a medium-confidence lesson can be staged for more evidence.


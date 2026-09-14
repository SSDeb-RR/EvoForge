# Independent evaluation

The harness performs provider-neutral behavioral validation. It does not call
an LLM API itself. Instead it creates two task packets for each scenario:

- Packet A contains the current skill.
- Packet B contains the candidate skill.

Run each packet in a separate fresh agent session or give it to different human
evaluators. Do not expose the other packet, the proposal diff, or the desired
comparison while either task is being completed. Record the fresh session ID,
verbatim output, and a link or note proving the run occurred.

## Commands

```bash
python scripts/evolve.py evaluate-prepare PROPOSAL_ID \
  --scenario trigger.json --scenario transfer.json
```

This writes packet files and a manifest under `evolution/evaluations/pending/`.
Give one packet at a time to fresh evaluator sessions. After both A/B packets
for every scenario are complete, create a results JSON matching the manifest's
`result_template` and run:

```bash
python scripts/evolve.py evaluate-record EVALUATION_ID --results results.json
```

The helper refuses missing A/B runs, repeated packets, non-executed runs, empty
outputs, and reuse of the same evaluator session for A and B on one scenario.

Then prepare a human or reviewer judgment JSON:

```json
{
  "evaluation_id": "evaluation-...",
  "reviewer": "reviewer identifier",
  "claims": [{"claim": "...", "status": "executed", "evidence": "..."}],
  "rubric": {
    "trigger_addressed": true,
    "different_family_transfer_passed": true,
    "no_critical_regressions": true,
    "no_instruction_contradiction": true,
    "minimal_localized_delta": true,
    "no_unjustified_metric_specificity": true
  },
  "scenarios": [{
    "scenario_id": "...",
    "comparison": "improved|same|regressed",
    "expected_behavior_met": true,
    "critical_regression": false,
    "evidence": "Specific comparison of the two outputs"
  }],
  "summary": "...",
  "limitations": []
}
```

Create the validation assessment with:

```bash
python scripts/evolve.py evaluate-assess EVALUATION_ID --judgment judgment.json
```

This preserves the raw evaluator outputs and writes a generated assessment in
`evolution/evaluations/completed/`. Pass that generated assessment to
`validate`. The validation gate then decides whether the proposal is
`approval_ready`.

If the packets are prepared but no outputs are recorded, the agent must use the
[review dialogue guide](review-dialogue.md) to tell the user what is missing
and offer the available next step. Packet preparation is not an executed
evaluation.

## What the harness verifies

It verifies the evaluation record is complete, every packet was executed in a
separate fresh session, and the judgment covers every scenario. It cannot prove
that a human or model output was honest or semantically correct; the reviewer
must ground the judgment in the recorded outputs. Approval-ready remains a
reviewable gate, not a guarantee of universal improvement.

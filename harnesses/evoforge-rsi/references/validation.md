# Validation guidance

Validation combines deterministic integrity checks with evidence-bearing
current-versus-candidate scenario assessment. It is a gate against unsupported
adoption, not proof of universal improvement.

## Prepare scenarios

Use the triggering scenario plus at least one transfer scenario from a
different metric family. Include every stored regression scenario relevant to
the changed instruction. A scenario describes observable decisions, not desired
wording. Use [evaluation.md](evaluation.md) to generate and record the separate
fresh A/B runs before creating this assessment.

Evaluate the current and candidate skills separately. For each scenario record:

- current outcome and evidence;
- candidate outcome and evidence;
- `improved`, `same`, or `regressed`;
- whether expected behavior was met;
- whether a critical regression occurred.

Do not mark a scenario executed if it was only reasoned about. Use
`mode: "executed"`, `"inferred"`, or `"not_tested"` truthfully.

## Assessment contract

```json
{
  "schema_version": 1,
  "reviewer": "agent or human identifier",
  "claims": [{"claim": "...", "status": "executed|inferred|not_tested", "evidence": "..."}],
  "rubric": {
    "trigger_addressed": true,
    "different_family_transfer_passed": true,
    "no_critical_regressions": true,
    "no_instruction_contradiction": true,
    "minimal_localized_delta": true,
    "no_unjustified_metric_specificity": true
  },
  "scenarios": [{
    "scenario_id": "scenario-...",
    "kind": "trigger|transfer|regression",
    "metric_family": "...",
    "mode": "executed|inferred|not_tested",
    "current_outcome": "...",
    "candidate_outcome": "...",
    "comparison": "improved|same|regressed",
    "expected_behavior_met": true,
    "critical_regression": false,
    "evidence": "..."
  }],
  "summary": "...",
  "limitations": ["..."]
}
```

## Approval-ready gate

The helper requires:

- valid target and candidate skill frontmatter;
- resolvable relative Markdown links in the candidate;
- unchanged live base hash;
- a non-empty localized diff;
- every rubric flag true;
- an executed triggering scenario that improves and meets expectations;
- an executed transfer scenario from a different metric family that improves
  or preserves correct behavior and meets expectations;
- no critical or reported regression;
- non-empty evidence for every scenario and claim;
- no claim falsely labelled as executed without evidence.

Structural success alone never makes a proposal approval-ready. If the gate
fails, retain the proposal and validation record with explicit reasons.

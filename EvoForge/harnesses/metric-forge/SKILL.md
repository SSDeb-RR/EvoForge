---
name: deterministic-metric-engineering
description: >
  Build, debug, review, or improve deterministic Python evaluators for
  conversational and voice-agent transcripts. Use when given a metric definition,
  transcripts, optional metric results/labels, or an existing metric
  implementation and asked to make the metric deterministic, create regression
  tests, audit labels, or fix false positives/negatives. Prefer reusable
  event extraction, finite-state/rule-based logic, regex normalization, and
  deterministic date/temporal resolution over LLM-as-a-judge. Works especially
  well for multilingual English/Hindi/Hinglish call transcripts.
---

# Deterministic Metric Forge

## Mission

Convert a human-language conversational metric into a deterministic,
testable, maintainable Python evaluator. This harness can replace or optimize
an LLM-as-a-judge metric when deterministic evidence is sufficient.

The implementation must reflect the metric definition, not merely fit the
provided examples.

The default priority order is:

1. Understand the metric precisely.
2. Inspect existing code and shared utilities before writing anything.
3. Audit supplied labels before treating them as ground truth.
4. Design the smallest deterministic decision procedure that generalizes.
5. Build exhaustive regression coverage from the supplied transcripts plus
   targeted edge cases.
6. Run tests and inspect mismatches.
7. Only introduce semantic/ML approaches when deterministic rules are genuinely
   insufficient and the user explicitly permits them.

## Input contract

Typical user input may contain only some of:

- Metric definition.
- A transcript file or pasted transcripts.
- Optional `metric_result` / label column.
- Existing metric code.
- Existing test suite.
- Examples of known false positives/false negatives.

Do not require a specific transcript schema unless the repository already
does. First inspect the project and support the formats already used there.

Common transcript forms include:

```json
{"customer": "...", "agent": "..."}
```

```json
{
  "turns": [
    {"role": "customer", "text": "..."},
    {"role": "agent", "text": "..."}
  ]
}
```

and raw transcript text such as:

```text
customer: ...
agent: ...
```

Preserve compatibility with existing repository formats unless the user asks
for a breaking change.

## Phase 1: Understand before coding

Before changing code:

- Read the metric definition in full.
- Identify the exact outcome domain (`true/false`, `pass/fail`, or possibly
  `not_applicable`) and any user-requested remapping.
- Identify what the metric actually measures and what it explicitly does NOT
  measure.
- Inspect the current implementation, tests, and relevant shared utilities.
- Search the supplied transcripts for recurring linguistic and structural
  patterns.
- Identify known edge cases and contradictions in the definition.

Do not invent requirements from generic best practices when the metric
definition provides a specific rule.

## Label discipline

Never automatically treat a supplied label column as ground truth.

First determine what the labels mean.

Possible meanings include:

- Actual metric result / ground truth.
- Human review agreement with an LLM output.
- UI thumbs-up/thumbs-down feedback.
- An intermediate annotation.
- Unknown.

If the label semantics are unclear, ask the user rather than silently
interpreting them.

If labels are actual ground truth but some appear inconsistent with the
definition:

1. Inspect the transcript.
2. Explain the inconsistency.
3. Create a corrected ground-truth mapping.
4. Preserve the original source label separately.
5. Use corrected ground truth for regression tests.

Never "fix" labels merely to make the implementation pass.

## Deterministic-first design

Prefer, in roughly this order:

- text normalization
- regex/pattern families
- keyword/context rules
- speaker-aware rules
- sentence/clause segmentation
- finite-state/event/state-machine logic
- deterministic temporal/date resolution
- small scoring/priority rules when necessary

Avoid:

- LLM calls inside the metric.
- Embeddings or semantic models when simple deterministic logic works.
- Hard-coding entire test transcripts.
- Rules written only to match one example.
- "Any date mentioned" or "any keyword mentioned" shortcuts when roles matter.

A pattern family should cover linguistic variants rather than one literal
sentence.

For multilingual work, support English, Hindi, and Hinglish variants when the
dataset uses them. Include transliterated and mixed-language forms when they
are actually observed.

## Event-oriented architecture

When a metric depends on actions, dates, requests, confirmations, or temporal
relationships, first model those as reusable events.

Typical event fields:

- `turn_index`
- `speaker`
- `event_type`
- `expression`
- `normalized_value`
- `confidence` only if useful for diagnostics
- `reason`
- original text

Example event types:

- historical event
- customer request
- agent proposal
- agent confirmation
- agent rejection
- open-ended question

The metric should consume these semantic events instead of repeatedly
re-parsing raw transcript text.

If a shared event extractor already exists in the repository, extend/reuse it
rather than creating a second incompatible implementation.

If a reusable layer will clearly support future related metrics, keep it
separate from the individual metric.

## Temporal/date reasoning

Never compare raw date strings.

Normalize all relevant temporal expressions into a canonical date/value before
comparison.

Examples:

```text
today
tomorrow
day after tomorrow
yesterday
कल
परसों
next Sunday
next week Sunday
18 August
18th August
18/08/2026
```

Use the metric's explicitly agreed anchor rule.

Use the metric's authoritative reference-time source when one exists (for
example, provider metadata or raw call logs). When it does not, define a
transcript-relative anchor from explicit conversation context before writing
logic. Do not use the Python execution date or machine clock as an implicit
call date. Keep historical context and current scheduling intent separate, and
perform comparisons using normalized calendar dates.

If the user explicitly changes the reference-date policy for a metric, follow
the newer instruction.

## "First event" metrics

For metrics whose definition says "first", "initial", "first option", or
similar:

- Determine the exact event being counted.
- Ignore historical/contextual statements that are not the target event.
- Skip clearly incomplete/truncated attempts when the definition says to do so.
- Stop at the first complete qualifying event.
- Do not let later customer/agent turns overwrite the first-event decision.
- If the customer proactively supplies the target information before the
  agent can propose it, implement that as an explicit state/edge case when
  required by the definition.

This is especially important for rescheduling metrics: a historical failed
delivery date is not a rescheduling proposal; a customer-provided preferred
date is not an agent proposal; a later confirmed date may be irrelevant if the
metric only evaluates the first option.

## Context and role separation

Always distinguish:

- Agent vs customer.
- Historical vs new/current.
- Proposal vs acceptance vs confirmation.
- Question vs open-ended request.
- Context/reference vs action.
- Rejection vs acceptance.
- Complete vs incomplete utterance.

A sentence containing a date is not automatically a scheduling event.

A sentence containing a scheduling keyword is not automatically the target
event.

Use local context and speaker role.

## Handling "not_applicable"

Respect the metric definition and the user's requested output contract.

If the user says all `not_applicable` results must become pass/`false`:

- Return only the requested binary domain in production code.
- Map every not-applicable path to `false`.
- Update tests to assert `false`.
- Do not silently change any other decision logic.
- Keep the reason/audit text clear that the case was non-applicable if useful.

## Structured failure evidence

For every new metric, expose structured evidence with the production result.
The public evaluator should return a JSON-serializable mapping with this
minimum contract:

```json
{
  "value": true,
  "evidence": [
    {
      "turn_index": 4,
      "speaker": "user",
      "timestamp": "00:05",
      "text": "exact original transcript turn",
      "role_in_failure": "user_context"
    },
    {
      "turn_index": 5,
      "speaker": "agent",
      "timestamp": "00:10",
      "text": "exact original transcript turn",
      "role_in_failure": "agent_failure"
    }
  ]
}
```

- `value` is the only pass/fail decision field. Determine it using the metric's
  existing deterministic logic before extracting evidence; evidence selection
  must never change the verdict.
- For `value: false`, including every non-applicable case, return
  `"evidence": []`.
- For `value: true`, include the exact offending agent turn and, when relevant,
  the user turn that provides the request, denial, correction, or conflicting
  context. Preserve the source `turn_index`, source timestamp when present
  (`null` when absent), and verbatim source text.
- Evidence extraction must support every transcript wrapper and turn schema the
  metric already accepts. Do not narrow or otherwise alter its input contract.
- If the metric needs a helper, keep an `evidence_contract.py` file inside that
  metric's own folder. Do not depend on a helper owned by another metric.
- When compatibility with Boolean callers matters, use a JSON-serializable
  mapping whose Boolean behavior is derived only from its `value` field.

## Regression methodology

Regression tests are part of the implementation, not an afterthought.

When transcripts are supplied:

1. Include all supplied calls unless the user explicitly asks to filter.
2. Assign stable case IDs.
3. Preserve original labels separately when labels exist.
4. Store corrected ground truth separately from source labels when necessary.
5. Add edge cases covering each branch of the definition.
6. Add multilingual variants observed in the real data.
7. Add false-positive cases targeting known failure modes.
8. Add false-negative cases targeting common missed phrasings.
9. Test parser compatibility with supported transcript formats.

The regression runner should report at least:

- total cases
- matches
- mismatches
- accuracy
- case ID for every mismatch
- expected vs actual
- enough audit fields to understand the decision

## Tests must test behavior, not implementation tricks

Do not write tests that merely mirror the internal regex names.

Tests should express the business rule.

For example, for a "first rescheduling proposal" metric, test that:

- historical date is ignored
- tomorrow proposal is recognized
- non-tomorrow proposal is recognized
- open-ended preferred-date question is recognized
- customer-proposed date before agent proposal is handled correctly
- incomplete first attempt is skipped when required
- Hindi/Hinglish variants behave equivalently
- later turns do not change a first-event decision

## Minimal-change rule

When modifying an existing metric:

- Change only files necessary to implement the requested behavior.
- Within each file, change only the requested logic.
- Preserve existing public APIs, schemas, names, formatting, and unrelated
  behavior unless the task explicitly requires otherwise.
- If a shared utility is the correct place for a pattern-family fix, change the
  shared utility rather than duplicating the same rule in the metric.
- If the user asks for only specific files, do not modify other files.

## Debugging a regression mismatch

When a case is misclassified:

1. Reproduce the case.
2. Identify which stage failed:
   - parsing
   - normalization
   - event extraction
   - event classification
   - state transition
   - final decision
3. Fix that stage generally.
4. Add a regression test reproducing the failure.
5. Re-run the existing suite.
6. Check for collateral regressions.

Do not patch the final result with a case-specific exception unless the transcript
reveals a genuinely distinct business rule.

## Preferred project structure

For a new metric, a reasonable structure is:

```text
metric_name/
├── metric_name.py
├── delivery_date_events.py      # only if relevant/reusable
├── date_resolver.py             # only if relevant/reusable
├── transcript_parser.py         # reuse existing one when available
├── regression_cases.json
├── test_metric_name.py
├── run_regression.py
├── README.md
└── requirements.txt
```

Do not create every file automatically. Reuse existing infrastructure and keep
the smallest maintainable structure.

## Output behavior

When the user provides a metric definition and transcripts and asks for
implementation:

- Inspect first.
- If the definition is ambiguous in a way that changes implementation, ask a
  concise clarifying question.
- Otherwise proceed.
- If labels are supplied, audit them before using them.
- Build deterministic logic.
- Build regression coverage from the supplied calls.
- Run the tests.
- Report any cases whose expected labels were corrected and why.
- Do not claim 100% accuracy unless the actual regression suite was executed
  and passed.

When the user asks for "logic/plan first", do not generate code until they
approve it.

## Compact user input template

The user should be able to provide approximately:

```text
Metric name:
<name>

Definition:
<paste definition>

Transcripts:
<attach/paste transcript file>

Metric results (optional):
<attach/paste labels>

Existing implementation (optional):
<path or repository>
```

Then follow the workflow above.

## Future-proofing for metric families

When several metrics operate on the same domain, identify shared primitives.

For delivery/rescheduling metrics, a shared delivery-date event layer should
ideally support multiple downstream metrics, for example:

- delivery scheduled today/past
- first rescheduling option
- whether tomorrow was proposed
- customer vs agent date proposal
- rescheduling date changes
- final effective schedule

Do not create separate date parsing logic for each metric.

## Final quality bar

A good result should be:

- deterministic
- explainable
- testable
- multilingual where required by the data
- resistant to historical/contextual false positives
- based on the actual first/target event when the definition requires it
- minimally invasive to the existing repository
- accompanied by regression coverage
- reusable for closely related future metrics

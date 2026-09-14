# Deterministic metric implementation checklist

Before implementation:
- Read metric definition.
- Identify exact output domain and any user-specified remapping.
- Inspect existing repository utilities.
- Determine what label columns mean.
- Audit labels instead of assuming they are ground truth.
- Inventory recurring transcript patterns and edge cases.

During implementation:
- Normalize transcript input.
- Keep speaker roles explicit.
- Extract reusable events when the metric is event-based.
- Separate historical/context dates from actionable dates.
- Resolve relative dates to canonical values before comparison.
- Use pattern families rather than one-off phrases.
- Apply "first event" constraints literally.
- Keep unrelated files and logic unchanged.

Before delivery:
- Include every supplied transcript in regression coverage unless asked not to.
- Add targeted edge cases.
- Keep source labels separate from corrected ground truth.
- Run tests.
- Inspect and explain mismatches.
- Never claim a result was tested when it was not.

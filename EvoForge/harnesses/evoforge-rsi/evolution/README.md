# Local evolution ledger

This directory starts intentionally empty. It is private, local operational
state—not part of the reusable harness definition.

During use, EvoForge RSI writes immutable conversation evidence, distilled
lessons, proposals, evaluator outputs, snapshots, and append-only history
here. Do not commit another user's ledger when redistributing this repository.
Set `SKILL_EVOLUTION_DATA` to an alternate local directory when you want the
ledger outside the installed harness.

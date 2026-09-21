# Local evolution ledger

This directory starts intentionally empty. It is private, local operational
state—not part of the reusable harness definition.

During use, EvoForge RSI writes imported structured experiences, immutable
conversation evidence, distilled lessons, proposals, evaluator outputs,
snapshots, and append-only history here. Metric Forge's source memory remains
separate under `~/.evoforge/memory/` by default. Do not commit either form of
user data when redistributing this repository. Set `SKILL_EVOLUTION_DATA` to an
alternate local directory when you want this ledger outside the installed
harness.

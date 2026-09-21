# Metric Forge

A reusable coding-agent harness for turning conversational evaluation metric
definitions and transcript datasets into deterministic Python evaluators and
regression suites. It is the evaluator-engineering component of EvoForge.

The same `SKILL.md` can be installed in both Codex and Claude Code. See the
repository-level installation guide for platform-specific instructions.

Metric Forge also keeps a selective, local, append-only record of meaningful
engineering discoveries at `~/.evoforge/memory/deterministic-metric-engineering/`.
This is evidence for later EvoForge RSI review—not automatic skill mutation.
See `references/experience-memory.md` and run `python3 scripts/memory.py status`
to inspect it.

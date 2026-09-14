# Codex and Claude Code interoperability

EvoForge distributes two cooperating harnesses:

- `deterministic-metric-engineering` — Metric Forge, the deterministic evaluator-engineering harness.
- `skill-evolution` — EvoForge RSI, the manually triggered evidence-to-improvement harness.

Install either harness in either supported product. The evolution helper finds
Metric Forge in this order: an explicit `SKILL_EVOLUTION_TARGET` path, an
installed Codex root, then an installed Claude Code root. It accepts the
canonical directory name `deterministic-metric-engineering` and the legacy
underscore name for migration only.

## Supported locations

| Product | macOS/Linux | Windows |
|---|---|---|
| Codex | `~/.codex/skills/<harness>` | `%USERPROFILE%\\.codex\\skills\\<harness>` |
| Claude Code | `~/.claude/skills/<harness>` | `%USERPROFILE%\\.claude\\skills\\<harness>` |

“Claude Code” is intended here; Google Cloud Code is a separate product and
does not use this local-harness layout.

## Mixed installation examples

- Metric Forge in Codex and EvoForge RSI in Claude Code: supported.
- Metric Forge in Claude Code and EvoForge RSI in Codex: supported.
- Both harnesses in either one product: supported.

Run `python scripts/evolve.py target` from the installed EvoForge RSI directory
to see the selected target and every location searched. If two target copies
exist, choose one deliberately:

```bash
export SKILL_EVOLUTION_TARGET="$HOME/.claude/skills/deterministic-metric-engineering"
python scripts/evolve.py target
```

In PowerShell:

```powershell
$env:SKILL_EVOLUTION_TARGET = "$env:USERPROFILE\.claude\skills\deterministic-metric-engineering"
python scripts/evolve.py target
```

The override affects only the current shell/session unless the user persists
it. Do not point it to an arbitrary skill: V1 is intentionally specialized for
the included deterministic evaluator-engineering target.

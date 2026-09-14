# Install EvoForge

EvoForge uses the same two harness directories on every platform:

```text
deterministic-metric-engineering/  # Metric Forge
skill-evolution/                  # EvoForge RSI
```

This guide uses **Claude Code**. It does not refer to Google Cloud Code.

## macOS — Codex

From the root of this downloaded or cloned repository:

```bash
mkdir -p ~/.codex/skills
cp -R harnesses/metric-forge ~/.codex/skills/deterministic-metric-engineering
cp -R harnesses/evoforge-rsi ~/.codex/skills/skill-evolution
cd ~/.codex/skills/skill-evolution
python scripts/evolve.py target
```

## macOS — Claude Code

```bash
mkdir -p ~/.claude/skills
cp -R harnesses/metric-forge ~/.claude/skills/deterministic-metric-engineering
cp -R harnesses/evoforge-rsi ~/.claude/skills/skill-evolution
cd ~/.claude/skills/skill-evolution
python scripts/evolve.py target
```

## Windows — Codex

In PowerShell, from the repository root:

```powershell
$codexSkills = Join-Path $env:USERPROFILE ".codex\skills"
New-Item -ItemType Directory -Force -Path $codexSkills
Copy-Item -Recurse harnesses\metric-forge (Join-Path $codexSkills "deterministic-metric-engineering")
Copy-Item -Recurse harnesses\evoforge-rsi (Join-Path $codexSkills "skill-evolution")
Set-Location (Join-Path $codexSkills "skill-evolution")
python scripts\evolve.py target
```

## Windows — Claude Code

```powershell
$claudeSkills = Join-Path $env:USERPROFILE ".claude\skills"
New-Item -ItemType Directory -Force -Path $claudeSkills
Copy-Item -Recurse harnesses\metric-forge (Join-Path $claudeSkills "deterministic-metric-engineering")
Copy-Item -Recurse harnesses\evoforge-rsi (Join-Path $claudeSkills "skill-evolution")
Set-Location (Join-Path $claudeSkills "skill-evolution")
python scripts\evolve.py target
```

## Mixed Codex / Claude Code installation

You may install one harness in each product. For example, install Metric Forge
into `~/.claude/skills` and EvoForge RSI into `~/.codex/skills`; then run the
same `python scripts/evolve.py target` check from EvoForge RSI. It searches
both roots automatically.

If more than one Metric Forge copy exists, select the intended one before
running an evolution workflow:

```bash
export SKILL_EVOLUTION_TARGET="$HOME/.claude/skills/deterministic-metric-engineering"
```

Use the PowerShell form in the interoperability guide on Windows.

## Verify and update safely

Run the helper tests after installing or updating EvoForge RSI:

```bash
python scripts/test_evolve.py
python scripts/evolve.py status
```

Do not copy a public repository's `evolution/` ledger over an existing local
ledger. This repository ships only an empty ledger skeleton.

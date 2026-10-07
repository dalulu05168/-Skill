# PowerShell: install Romania Stock Intelligence skill into local Codex skill directory.
# Run from an extracted package directory. Does not edit other skills or online accounts.
$ErrorActionPreference = 'Stop'
$skillRoot = Split-Path -Parent $PSScriptRoot
$skillName = 'romania-stock-intelligence'
$skillsDir = if ($env:AGENTS_SKILLS_DIR) { $env:AGENTS_SKILLS_DIR } else { Join-Path (Join-Path $HOME '.agents') 'skills' }
$dest = Join-Path $skillsDir $skillName
if (-not (Test-Path (Join-Path $skillRoot 'SKILL.md'))) { throw 'Missing SKILL.md in source directory' }
if (Test-Path $dest) { throw "Skill already exists. Refusing to overwrite: $dest" }
New-Item -ItemType Directory -Path (Split-Path -Parent $dest) -Force | Out-Null
Copy-Item -LiteralPath $skillRoot -Destination $dest -Recurse
Write-Host "Installed skill at: $dest"
Write-Host 'Restart/reload Codex and try: use romania-stock-intelligence.'
Write-Host 'Note: no ChatGPT automations or live market feeds were created.'

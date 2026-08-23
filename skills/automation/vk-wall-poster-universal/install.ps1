# install.ps1 - Automated installer for vk-wall-poster-universal skill
param(
    [string]$Target = "hermes"  # hermes | claude | opencode | custom
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== Installing vk-wall-poster-universal Skill ===" -ForegroundColor Cyan

# 1. Check Python dependencies
Write-Host "[1/3] Checking Python dependencies..."
python -m pip install --quiet websocket-client requests pillow
Write-Host "  Dependencies verified." -ForegroundColor Green

# 2. Deploy to requested agent target
Write-Host "[2/3] Deploying skill to target: $Target..."
if ($Target -eq "hermes") {
    $dest = "$env:LOCALAPPDATA\hermes\skills\vk-wall-poster-universal"
    New-Item -ItemType Directory -Path $dest -Force | Out-Null
    Copy-Item -Path "$scriptDir\*" -Destination $dest -Recurse -Force
    Write-Host "  Deployed to Hermes skills: $dest" -ForegroundColor Green
} elseif ($Target -eq "claude") {
    $dest = ".claude\skills\vk-wall-poster-universal"
    New-Item -ItemType Directory -Path $dest -Force | Out-Null
    Copy-Item -Path "$scriptDir\*" -Destination $dest -Recurse -Force
    Write-Host "  Deployed to Claude Code skills: $dest" -ForegroundColor Green
} elseif ($Target -eq "opencode") {
    $dest = "$env:USERPROFILE\.gemini\antigravity\skills\vk-wall-poster-universal"
    New-Item -ItemType Directory -Path $dest -Force | Out-Null
    Copy-Item -Path "$scriptDir\*" -Destination $dest -Recurse -Force
    Write-Host "  Deployed to OpenCode/Antigravity: $dest" -ForegroundColor Green
} else {
    Write-Host "  Source ready at $scriptDir"
}

# 3. Test check
Write-Host "[3/3] Testing VK connection..."
python "$scriptDir\scripts\vk_wall_poster.py" --check

Write-Host "`n=== Installation Complete! ===" -ForegroundColor Cyan

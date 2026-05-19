<#
  Windows entry point — same contract as ./run (see docs/RUN.md).

  powershell -ExecutionPolicy Bypass -File .\run.ps1
  powershell -ExecutionPolicy Bypass -File .\run.ps1 -Live
#>
param(
  [switch]$Live,
  [switch]$NoLive,
  [switch]$SetupOnly,
  [switch]$SkipBootstrap
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if ($Live -and $NoLive) {
  Write-Error 'Use either -Live or -NoLive, not both.'
}

$venv = if ($env:M4L_VENV) { $env:M4L_VENV } else { Join-Path $Root 'venv' }
$py = Join-Path $venv 'Scripts\python.exe'

if ($Live) {
  Write-Host ''
  Write-Host '=== Step 4: -Live (Ableton OPEN) ==='
  Write-Host '    Live must be running with AbletonOSC + AbletonMCP (step 3).'
  Write-Host '    See docs/GETTING_STARTED.md if you have not done step 3 yet.'
  Write-Host ''
} else {
  Write-Host ''
  Write-Host '=== Steps 1-2: quit Ableton, then run.ps1 ==='
  Write-Host '    Step 1: Quit Live completely.'
  Write-Host '    Step 2: This run installs tools + deploys the tutorial (Live closed).'
  Write-Host '    After M4L_RUN_OK -> docs/GETTING_STARTED.md (steps 3-4)'
  Write-Host ''
}

if (-not $SkipBootstrap) {
  if (-not (Test-Path $py)) {
    Write-Host '==> No venv yet — running bootstrap.ps1'
    & (Join-Path $Root 'bootstrap.ps1')
  } else {
    Write-Host '==> venv present — refreshing Remote Scripts'
    & $py (Join-Path $Root 'scripts\install_remote_scripts.py')
    & $py (Join-Path $Root 'scripts\configure_ableton.py')
  }
}

$envFile = Join-Path $Root '.env'
$envExample = Join-Path $Root '.env.example'
if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
  Copy-Item $envExample $envFile
  Write-Host '==> Created .env from .env.example'
}

# Load .env into process (simple KEY=VALUE lines)
if (Test-Path $envFile) {
  Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
      Set-Item -Path "env:$($matches[1])" -Value $matches[2].Trim('"')
    }
  }
}

Write-Host '==> Projects allowlist'
& $py (Join-Path $Root 'scripts\check_projects_allowlist.py')

Write-Host '==> Preflight'
& $py (Join-Path $Root 'scripts\verify_setup.py') --preflight

Write-Host '==> Tutorial spec validation'
& $py (Join-Path $Root 'scripts\validate_spec.py') (Join-Path $Root 'projects\Pipeline_Example\pipeline_example_spec.json')

if ($Live) {
  Write-Host '==> Waiting for AbletonMCP'
  & $py (Join-Path $Root 'scripts\verify_setup.py') --wait-mcp 120
} elseif (-not $NoLive) {
  Write-Host ''
  Write-Host '=== Next: Step 3 (agent guides Ableton - any IDE) ==='
  Write-Host '  Agent walks you through AbletonOSC + AbletonMCP; say Continue when done.'
  Write-Host '  Step 4: agent runs run.ps1 -Live'
  Write-Host '  See docs/GETTING_STARTED.md, docs/AGENTIC_IDES.md, AGENTS.md'
  Write-Host ''
}

if ($SetupOnly) {
  Write-Host 'M4L_RUN_OK (setup only)'
  exit 0
}

if ($NoLive -or -not $Live) {
  Write-Host '==> Tutorial build (--no-live)'
  & $py (Join-Path $Root 'projects\Pipeline_Example\build_pipeline_example.py') --no-live
  Write-Host ''
  Write-Host 'M4L_RUN_OK (step 2 complete)'
  Write-Host '  -> Step 3: Ask your agent for OSC/MCP steps; reply Continue when done.'
  Write-Host '  -> Steps 4-5: agent runs -Live, then helps you design your .amxd.'
  exit 0
}

Write-Host '==> Tutorial build + load'
& $py (Join-Path $Root 'projects\Pipeline_Example\build_pipeline_example.py')

Write-Host '==> Tutorial verify'
& $py (Join-Path $Root 'scripts\m4l_verify.py')

Write-Host ''
Write-Host 'M4L_RUN_OK (step 4 complete)'
Write-Host 'M4L_PIPELINE_READY'
Write-Host ''
Write-Host '  Pipeline connected to Ableton Live.'
  Write-Host '  Step 5: Tell your agent what type of .amxd you want to create.'

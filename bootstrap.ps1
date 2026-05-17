<# 
  PowerShell counterpart to bootstrap.sh (Windows).
  Prerequisites: Ableton Live (Suite or Std + Max for Live add-on; not Lite/Intro for MFL),
  execution policy permitting scripts. Python 3.10+ is installed via winget when missing
  (see scripts\ensure_python.ps1).
  
  Invoke from repo root:
    powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1
#>

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

. (Join-Path $Root 'scripts\ensure_python.ps1')
$Py = $env:BOOTSTRAP_PYTHON
if (-not $Py) {
  Write-Error 'BOOTSTRAP_PYTHON was not set. Run scripts\ensure_python.ps1 or install Python 3.10+.'
}

$venv = if ($env:M4L_VENV) { $env:M4L_VENV } else { Join-Path $Root 'venv' }

function Invoke-PyModule {
    param([string]$Python, [string[]]$Args)
    & $Python @Args
}

if (-not (Test-Path $venv)) {
    Write-Host "Creating venv -> $venv"
    Invoke-PyModule $Py @('-m', 'venv', $venv)
}

$pythonExe = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path $pythonExe)) {
    Write-Error "Expected $pythonExe after venv creation"
}

& $pythonExe -m pip install --upgrade pip setuptools wheel
& $pythonExe -m pip install -r (Join-Path $Root 'requirements.txt')
& $pythonExe (Join-Path $Root 'scripts\install_remote_scripts.py')
& $pythonExe (Join-Path $Root 'scripts\configure_ableton.py')

if ($env:M4L_SKIP_TEMPLATE -ne '1') {
  & $pythonExe (Join-Path $Root 'scripts\install_default_template.py')
}

$prevPyPath = $env:PYTHONPATH
$env:PYTHONPATH = Join-Path $Root 'scripts'
& $pythonExe -c "import ableton_bootstrap_common as a; print(a.MAX_FOR_LIVE_EDITION_NOTICE.strip())"
if ($null -eq $prevPyPath) { Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue } else { $env:PYTHONPATH = $prevPyPath }

Write-Host "`nBootstrap finished. Launch Live once, configure Control Surfaces, then:"
$verify = Join-Path $Root 'scripts\verify_setup.py'
Write-Host ("  & '{0}' '{1}' --wait-mcp 180" -f $pythonExe, $verify)

# Windows bootstrap wrapper. Run from repo root:
#   powershell -ExecutionPolicy Bypass -File examples\sdk-run-setup\run.ps1
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
& (Join-Path $Root 'run.ps1') @args
exit $LASTEXITCODE

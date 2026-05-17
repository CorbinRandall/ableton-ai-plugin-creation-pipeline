# Ensure Python 3.10+ exists; set env BOOTSTRAP_PYTHON for bootstrap.ps1.
# Windows: prefers winget install of Python 3.12 when no suitable interpreter exists.
# Dot-source from repo root:  . .\scripts\ensure_python.ps1

$ErrorActionPreference = 'Stop'

function Test-Python310 {
    param([string]$Exe)
    if (-not $Exe) { return $false }
    if (-not (Test-Path -LiteralPath $Exe)) { return $false }
    & $Exe -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
    return $LASTEXITCODE -eq 0
}

function Find-PythonExe {
    $candidates = New-Object System.Collections.Generic.List[string]
    if ($env:BOOTSTRAP_PYTHON) { [void]$candidates.Add($env:BOOTSTRAP_PYTHON) }
    $cmdPy = (Get-Command python -ErrorAction SilentlyContinue)
    if ($cmdPy) { [void]$candidates.Add($cmdPy.Source) }
    foreach ($n in @(312, 311, 310)) {
        [void]$candidates.Add("$env:LocalAppData\Programs\Python\Python$n\python.exe")
    }
    foreach ($c in $candidates) {
        if (Test-Python310 $c) { return $c }
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($tag in @('-3.12', '-3.11', '-3.10', '-3')) {
            $exe = & py $tag -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $exe) {
                $exe = $exe.Trim()
                if (Test-Python310 $exe) { return $exe }
            }
        }
    }
    return $null
}

$found = Find-PythonExe
if ($found) {
    $env:BOOTSTRAP_PYTHON = $found
    Write-Host "Using Python: $found"
    return
}

Write-Host "Python 3.10+ not found. Trying winget (Python.Python.3.12)…"
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Error "winget not available. Install Python 3.10+ from https://www.python.org/downloads/ or Microsoft Store."
}

$prevEap = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
try {
    winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements *>&1 | Out-Host
} finally {
    $ErrorActionPreference = $prevEap
}

$found = Find-PythonExe
if (-not $found) {
    $fallback = "$env:LocalAppData\Programs\Python\Python312\python.exe"
    if (Test-Python310 $fallback) { $found = $fallback }
}
if (-not $found) {
    Write-Error "Python install may have completed but interpreter not on PATH. Reopen PowerShell, verify Python 3.12 install, then re-run bootstrap.ps1."
}

$env:BOOTSTRAP_PYTHON = $found
Write-Host "Using Python: $found"

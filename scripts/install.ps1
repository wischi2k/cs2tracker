$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$python = Get-Command py -ErrorAction SilentlyContinue
if ($null -eq $python) {
    $python = Get-Command python -ErrorAction SilentlyContinue
}
if ($null -eq $python) {
    throw 'Python 3.9+ not found. Install Python first.'
}

& $python.Source -c "import sys; assert sys.version_info >= (3, 9), 'Python 3.9+ required'; print('Python OK:', sys.version.split()[0])"

if (-not (Test-Path '.venv')) {
    & $python.Source -m venv .venv
}

$venvPy = Join-Path $root '.venv\Scripts\python.exe'
& $venvPy -m pip install --upgrade pip
& $venvPy -m pip install -r requirements.txt

Write-Host ''
Write-Host 'Installation complete.'
Write-Host 'Start command:'
Write-Host '  .\.venv\Scripts\python.exe run.py'

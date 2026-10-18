param([string]$Output = 'dist/SSDD-Agent-Platform-v0.1.0.zip')
$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
  python scripts/package-release.py --output $Output
  if ($LASTEXITCODE -ne 0) { throw 'Release packaging failed.' }
} finally { Pop-Location }

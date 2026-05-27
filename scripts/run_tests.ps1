param(
    [switch]$Unit,
    [switch]$Integration,
    [Alias('v')][switch]$VerboseOutput,
    [switch]$Coverage,
    [switch]$Watch,
    [switch]$Report,
    [string]$Marker,
    [Alias('f')][string]$FilePath,
    [switch]$List,
    [switch]$Clean
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (Test-Path $venvPython) {
    $python = $venvPython
} else {
    $python = 'python'
}

if ($Clean) {
    $paths = @(
        (Join-Path $repoRoot 'tests\coverage_html'),
        (Join-Path $repoRoot '.pytest_cache'),
        (Join-Path $repoRoot '.coverage'),
        (Join-Path $repoRoot 'htmlcov')
    )

    foreach ($path in $paths) {
        if (Test-Path $path) {
            Remove-Item -Recurse -Force $path
        }
    }

    Get-ChildItem -Path $repoRoot -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $repoRoot -Recurse -File -Filter '*.pyc' -ErrorAction SilentlyContinue |
        Remove-Item -Force -ErrorAction SilentlyContinue

    Write-Host 'Cleaned test artifacts'
    exit 0
}

$argsList = @('tests/run_tests.py')

if ($Unit) {
    $argsList += '--unit'
}
if ($Integration) {
    $argsList += '--integration'
}
if ($VerboseOutput) {
    $argsList += '--verbose'
}
if ($Coverage) {
    $argsList += '--coverage'
}
if ($Watch) {
    $argsList += '--watch'
}
if ($Report) {
    $argsList += '--report'
}
if ($Marker) {
    $argsList += @('--marker', $Marker)
}
if ($FilePath) {
    $argsList += @('--file', $FilePath)
}
if ($List) {
    $argsList += '--list'
}

Push-Location $repoRoot
try {
    & $python @argsList
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
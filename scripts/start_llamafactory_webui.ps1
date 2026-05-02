$ErrorActionPreference = "Stop"

$llamaFactoryRoot = "\\ad.uillinois.edu\engr-ews\haoran27\微调\LLaMA-Factory"
$condaEnvRoot = "C:\Users\haoran27\miniconda3\envs\llamafactory"
$preferredCli = "C:\Users\haoran27\miniconda3\envs\llamafactory\Scripts\llamafactory-cli.exe"
$fallbackUv = "C:\Users\haoran27\AppData\Roaming\Python\Python314\Scripts\uv.exe"

if (-not (Test-Path -LiteralPath $llamaFactoryRoot)) {
    throw "LLaMA-Factory directory not found: $llamaFactoryRoot"
}

Set-Location -LiteralPath $llamaFactoryRoot

if (Test-Path -LiteralPath $preferredCli) {
    $env:Path = "$condaEnvRoot;$condaEnvRoot\Scripts;$condaEnvRoot\Library\bin;$env:Path"
    Write-Host "Starting LLaMA-Factory Web UI with conda env CLI:" -ForegroundColor Green
    Write-Host "  $preferredCli"
    & $preferredCli webui
    exit $LASTEXITCODE
}

if (Test-Path -LiteralPath $fallbackUv) {
    Write-Host "Conda env CLI not found. Falling back to uv:" -ForegroundColor Yellow
    Write-Host "  $fallbackUv"
    & $fallbackUv run llamafactory-cli webui
    exit $LASTEXITCODE
}

throw @"
Could not find a LLaMA-Factory launcher.

Tried:
  $preferredCli
  $fallbackUv

Search again with:
  Get-ChildItem "C:\Users\haoran27" -Recurse -Filter llamafactory-cli.exe -ErrorAction SilentlyContinue | Select-Object -First 20 FullName
  Get-ChildItem "C:\Users\haoran27" -Recurse -Filter uv.exe -ErrorAction SilentlyContinue | Select-Object -First 20 FullName
"@

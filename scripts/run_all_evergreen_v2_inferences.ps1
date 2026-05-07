# Run all 12 evergreen v2 inferences via LLaMA-Factory CLI.
# 6 adapters x 2 prompt forms (flagged / noflag) = 12 jobs.
#
# Prerequisites:
#   python scripts/24_merge_evergreen_v2.py
#   python scripts/25_generate_evergreen_v2_predict_configs.py
#
# Usage (from project root):
#   .\scripts\run_all_evergreen_v2_inferences.ps1

$ErrorActionPreference = "Continue"
$llamafactory = "C:\Users\haoran27\miniconda3\envs\llamafactory\Scripts\llamafactory-cli.exe"

$jobs = @(
    "evergreen_v2_predict_v3_conservative.yaml",
    "evergreen_v2_predict_v3_confident.yaml",
    "evergreen_v2_predict_v2_conservative.yaml",
    "evergreen_v2_predict_v2_confident.yaml",
    "evergreen_v2_predict_v1_8B_confident.yaml",
    "evergreen_v2_predict_v1_4B_confident.yaml",
    "evergreen_v2_noflag_predict_v3_conservative.yaml",
    "evergreen_v2_noflag_predict_v3_confident.yaml",
    "evergreen_v2_noflag_predict_v2_conservative.yaml",
    "evergreen_v2_noflag_predict_v2_confident.yaml",
    "evergreen_v2_noflag_predict_v1_8B_confident.yaml",
    "evergreen_v2_noflag_predict_v1_4B_confident.yaml"
)

$totalStart = Get-Date

foreach ($yaml in $jobs) {
    $cfgPath = "configs/llamafactory/$yaml"
    Write-Host ""
    Write-Host "=== [$(Get-Date -Format HH:mm:ss)] starting $yaml ===" -ForegroundColor Cyan

    $start = Get-Date
    & $llamafactory train $cfgPath
    $exitCode = $LASTEXITCODE
    $elapsed = (Get-Date) - $start

    if ($exitCode -eq 0) {
        Write-Host "=== [$(Get-Date -Format HH:mm:ss)] DONE $yaml in $($elapsed.ToString('mm\:ss')) ===" -ForegroundColor Green
    } else {
        Write-Host "=== [$(Get-Date -Format HH:mm:ss)] FAILED $yaml (exit=$exitCode) ===" -ForegroundColor Red
        Write-Host "Continuing to next adapter." -ForegroundColor Yellow
    }
}

$totalElapsed = (Get-Date) - $totalStart
Write-Host ""
Write-Host "=== ALL JOBS DONE in $($totalElapsed.ToString('hh\:mm\:ss')) ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next step: aggregate results with scripts/17_evaluate_on_evergreen.py"
Write-Host "  - flagged: --lf-source-dir data/labeled/evergreen_lf_v2"
Write-Host "  - noflag:  --lf-source-dir data/labeled/evergreen_lf_v2_noflag"
Write-Host "  Each adapter's predictions live in"
Write-Host "  C:\Users\haoran27\llamafactory_outputs\<adapter>_predict_evergreen_v2{,_noflag}\generated_predictions.jsonl"

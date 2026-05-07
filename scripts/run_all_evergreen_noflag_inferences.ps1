# Run all 6 evergreen NO-FLAG inferences serially via LLaMA-Factory CLI.
#
# Each adapter was trained with the rule_clean / rule_flags fields in the
# user prompt. This run scores them on the prompt-stripped variant of the
# 600 evergreen records to quantify how much each adapter relied on the
# rule_clean shortcut.
#
# Prerequisite:
#   python scripts/22_build_evergreen_noflag_lf_dataset.py
#
# Usage (from project root):
#   .\scripts\run_all_evergreen_noflag_inferences.ps1

$ErrorActionPreference = "Continue"
$llamafactory = "C:\Users\haoran27\miniconda3\envs\llamafactory\Scripts\llamafactory-cli.exe"

$jobs = @(
    "evergreen_noflag_predict_v3_conservative.yaml",
    "evergreen_noflag_predict_v3_confident.yaml",
    "evergreen_noflag_predict_v2_conservative.yaml",
    "evergreen_noflag_predict_v2_confident.yaml",
    "evergreen_noflag_predict_v1_8B_confident.yaml",
    "evergreen_noflag_predict_v1_4B_confident.yaml"
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
Write-Host "Next: aggregate with python scripts/17_evaluate_on_evergreen.py"
Write-Host "  --lf-source-dir data/labeled/evergreen_lf_noflag"
Write-Host "  --predictions <name>:<adapter_output_dir>\generated_predictions.jsonl  (repeat per adapter)"
Write-Host "  --report reports/evergreen_noflag_cross_version_eval_report.md"
Write-Host "  --metrics data/eval/evergreen_noflag_cross_version_eval_metrics.json"

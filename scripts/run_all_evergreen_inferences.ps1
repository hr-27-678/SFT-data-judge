# Run all 6 evergreen inferences serially.
# Order: v3 conservative first (current main candidate), then the rest.
# Each command supports --resume; safe to interrupt and re-run, and any
# adapter whose predictions are already complete will be skipped instantly.
#
# Usage (from project root):
#   powershell -ExecutionPolicy Bypass -File scripts/run_all_evergreen_inferences.ps1
# or after `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`:
#   .\scripts\run_all_evergreen_inferences.ps1

$ErrorActionPreference = "Continue"
$python = "C:\Users\haoran27\miniconda3\envs\llamafactory\python.exe"
$inputFile = "data/splits/teacher_judge/evergreen_test_merged_candidates.jsonl"
$adapterRoot = "C:\Users\haoran27\llamafactory_outputs"

$jobs = @(
    @{
        Name      = "v3_conservative"
        Base      = "Qwen/Qwen3-8B"
        Adapter   = "$adapterRoot\scorer_binary_v3_conservative_qwen3_8b_lora_e3"
    },
    @{
        Name      = "v3_confident"
        Base      = "Qwen/Qwen3-8B"
        Adapter   = "$adapterRoot\scorer_binary_v3_confident_qwen3_8b_lora_e3"
    },
    @{
        Name      = "v2_conservative"
        Base      = "Qwen/Qwen3-8B"
        Adapter   = "$adapterRoot\scorer_binary_v2_conservative_qwen3_8b_lora_e3"
    },
    @{
        Name      = "v2_confident"
        Base      = "Qwen/Qwen3-8B"
        Adapter   = "$adapterRoot\scorer_binary_v2_confident_qwen3_8b_lora_e3"
    },
    @{
        Name      = "v1_8B_confident"
        Base      = "Qwen/Qwen3-8B"
        Adapter   = "$adapterRoot\scorer_binary_confident_1000_qwen3_8b_lora_e3"
    },
    @{
        Name      = "v1_4B_confident"
        Base      = "Qwen/Qwen3-4B-Instruct-2507"
        Adapter   = "$adapterRoot\scorer_binary_confident_1000_qwen3_4b_lora_e3"
    }
)

$totalStart = Get-Date

foreach ($job in $jobs) {
    $name    = $job.Name
    $base    = $job.Base
    $adapter = $job.Adapter

    $output  = "data/scored/evergreen_${name}_predictions.jsonl"
    $report  = "reports/evergreen_${name}_inference_report.md"
    $metrics = "data/scored/evergreen_${name}_metrics.json"
    $runName = "evergreen__$name"

    Write-Host ""
    Write-Host "=== [$(Get-Date -Format HH:mm:ss)] starting $name ===" -ForegroundColor Cyan
    Write-Host "  base    : $base"
    Write-Host "  adapter : $adapter"
    Write-Host "  output  : $output"

    $start = Get-Date
    & $python scripts/12_infer_binary_scorer.py `
        --input $inputFile `
        --output $output `
        --report-md $report `
        --metrics-json $metrics `
        --run-name $runName `
        --model-name-or-path $base `
        --adapter-name-or-path $adapter

    $exitCode = $LASTEXITCODE
    $elapsed = (Get-Date) - $start
    if ($exitCode -eq 0) {
        Write-Host "=== [$(Get-Date -Format HH:mm:ss)] DONE $name in $($elapsed.ToString('mm\:ss')) ===" -ForegroundColor Green
    } else {
        Write-Host "=== [$(Get-Date -Format HH:mm:ss)] FAILED $name (exit=$exitCode, elapsed=$($elapsed.ToString('mm\:ss'))) ===" -ForegroundColor Red
        Write-Host "Continuing to next adapter. Re-run this script to retry; --resume is on." -ForegroundColor Yellow
    }
}

$totalElapsed = (Get-Date) - $totalStart
Write-Host ""
Write-Host "=== ALL JOBS DONE in $($totalElapsed.ToString('hh\:mm\:ss')) ===" -ForegroundColor Cyan
Write-Host "Next: aggregate with scripts/17_evaluate_on_evergreen.py"

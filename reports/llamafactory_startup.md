# LLaMA-Factory Startup Notes

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | Manual operations note |
| Report type | Environment / startup note |
| Project stage | Local training operations |
| Report status | Reference note |

## Experiment Context

| Field | Value |
| --- | --- |
| Model | N/A |
| Data version | v3 binary scorer ready for training |
| Tooling | LLaMA-Factory, conda environment `llamafactory` |
| Script | `scripts/start_llamafactory_webui.ps1` |
| Current use | Start local LLaMA-Factory WebUI safely on this machine |

Use this note when starting LLaMA-Factory for the SFT-DataJudge scorer training.

## One-Command Startup

From any PowerShell terminal:

```powershell
& '\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\scripts\start_llamafactory_webui.ps1'
```

The script will:

1. Switch to the local LLaMA-Factory repo.
2. Prefer the existing conda environment CLI.
3. Fall back to `uv run llamafactory-cli webui` if needed.

## Paths Found

Preferred launcher:

```text
C:\Users\haoran27\miniconda3\envs\llamafactory\Scripts\llamafactory-cli.exe
```

Fallback `uv`:

```text
C:\Users\haoran27\AppData\Roaming\Python\Python314\Scripts\uv.exe
```

LLaMA-Factory repo:

```text
\\ad.uillinois.edu\engr-ews\haoran27\微调\LLaMA-Factory
```

## Manual Startup

If the script is not available:

```powershell
Set-Location '\\ad.uillinois.edu\engr-ews\haoran27\微调\LLaMA-Factory'
& 'C:\Users\haoran27\miniconda3\envs\llamafactory\Scripts\llamafactory-cli.exe' webui
```

## Current Scorer Dataset

Dataset directory:

```text
\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\labeled\scorer_binary_sft_v3
```

Conservative train/validation/test datasets:

```text
scorer_binary_v3_conservative_train
scorer_binary_v3_conservative_valid
scorer_binary_v3_conservative_test
```

Confident train/validation/test datasets:

```text
scorer_binary_v3_confident_train
scorer_binary_v3_confident_valid
scorer_binary_v3_confident_test
```

## Current Training Commands

Run from the LLaMA-Factory repo:

```powershell
Set-Location '\\ad.uillinois.edu\engr-ews\haoran27\微调\LLaMA-Factory'
& 'C:\Users\haoran27\miniconda3\envs\llamafactory\Scripts\llamafactory-cli.exe' train '\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\configs\llamafactory\scorer_binary_v3_conservative_qwen3_8b_lora_e3.yaml'
```

After conservative finishes, train the companion confident variant:

```powershell
Set-Location '\\ad.uillinois.edu\engr-ews\haoran27\微调\LLaMA-Factory'
& 'C:\Users\haoran27\miniconda3\envs\llamafactory\Scripts\llamafactory-cli.exe' train '\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\configs\llamafactory\scorer_binary_v3_confident_qwen3_8b_lora_e3.yaml'
```

## Current Prediction And Evaluation Commands

After a training run finishes, run greedy prediction through the matching
`*_predict_valid.yaml` and `*_predict_test.yaml` configs. Example for v3
conservative valid:

```powershell
Set-Location '\\ad.uillinois.edu\engr-ews\haoran27\微调\LLaMA-Factory'
& 'C:\Users\haoran27\miniconda3\envs\llamafactory\Scripts\llamafactory-cli.exe' train '\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\configs\llamafactory\scorer_binary_v3_conservative_qwen3_8b_lora_predict_valid.yaml'
```

Then evaluate the generated predictions from the SFT-DataJudge repo:

```powershell
Set-Location '\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge'
python .\scripts\10_evaluate_binary_scorer_predictions.py --predictions 'C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_conservative_qwen3_8b_lora_e3_predict_valid_greedy\generated_predictions.jsonl' --reference '.\data\labeled\scorer_binary_sft_v3\scorer_binary_v3_conservative_valid.jsonl' --split valid --run-name scorer_binary_v3_conservative_qwen3_8b --output-md '.\reports\scorer_binary_v3_conservative_eval_valid_report.md' --output-json '.\data\eval\scorer_binary_v3_conservative_eval_valid_metrics.json'
```

Use the same pattern for v3 conservative test and both v3 confident splits.

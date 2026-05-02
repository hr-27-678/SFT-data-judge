# LLaMA-Factory Startup Notes

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

## Scorer Dataset

Dataset directory:

```text
\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\labeled\scorer_sft
```

Train dataset:

```text
scorer_sft_1000_train
```

Validation dataset:

```text
scorer_sft_1000_valid
```

Test dataset:

```text
scorer_sft_1000_test
```

$ErrorActionPreference = "Stop"

$LF = "C:\Users\haoran27\miniconda3\envs\llamafactory\Scripts\llamafactory-cli.exe"
$Root = "U:\微调\SFT-DataJudge"

$Configs = @(
  "configs\llamafactory\phase_e_unfiltered_clean_15k_qwen3_8b_lora_e1.yaml",
  "configs\llamafactory\phase_e_v4_conservative_keep_clean_15k_qwen3_8b_lora_e1.yaml",
  "configs\llamafactory\phase_e_v4_confident_keep_clean_15k_qwen3_8b_lora_e1.yaml",
  "configs\llamafactory\phase_e_v4_both_keep_clean_15k_qwen3_8b_lora_e1.yaml"
)

Set-Location $Root

foreach ($Config in $Configs) {
  $Path = Join-Path $Root $Config
  Write-Host "=== Training $Config ==="
  & $LF train $Path
}

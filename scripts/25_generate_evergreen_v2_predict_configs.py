"""Generate 12 predict YAMLs for evergreen v2.

Reads the existing 6 v1 evergreen predict YAMLs (one per adapter) and
emits 12 v2 variants, identical except for dataset_dir, eval_dataset,
and output_dir. Two flavors per adapter:

- flagged prompt (uses evergreen_lf_v2)
- noflag prompt (uses evergreen_lf_v2_noflag)

Outputs to configs/llamafactory/:
- evergreen_v2_predict_<name>.yaml          (6)
- evergreen_v2_noflag_predict_<name>.yaml   (6)
"""

from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CFG_DIR = PROJECT_ROOT / "configs" / "llamafactory"

ADAPTERS = [
    "v3_conservative",
    "v3_confident",
    "v2_conservative",
    "v2_confident",
    "v1_8B_confident",
    "v1_4B_confident",
]

V1_DATASET_DIR_LITERAL = r"\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\labeled\evergreen_lf"
V2_DATASET_DIR_LITERAL = r"\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\labeled\evergreen_lf_v2"
V2_NOFLAG_DATASET_DIR_LITERAL = r"\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\labeled\evergreen_lf_v2_noflag"


def patch(yaml_text: str, *, dataset_dir: str, eval_dataset: str, output_dir_suffix: str) -> str:
    out = yaml_text
    out = re.sub(r"dataset_dir:\s*.*", lambda _m: f"dataset_dir: {dataset_dir}", out)
    out = re.sub(r"eval_dataset:\s*.*", lambda _m: f"eval_dataset: {eval_dataset}", out)
    out = re.sub(
        r"(output_dir:\s*.*?_lora_e3)_predict_evergreen.*",
        lambda m: f"{m.group(1)}_predict_{output_dir_suffix}",
        out,
    )
    return out


def main() -> None:
    written: list[str] = []
    for name in ADAPTERS:
        v1_path = CFG_DIR / f"evergreen_predict_{name}.yaml"
        if not v1_path.exists():
            print(f"SKIP {name}: source YAML missing ({v1_path})")
            continue
        text = v1_path.read_text(encoding="utf-8")

        # flagged v2
        v2_text = patch(
            text,
            dataset_dir=V2_DATASET_DIR_LITERAL,
            eval_dataset="evergreen_test_v2",
            output_dir_suffix="evergreen_v2",
        )
        v2_path = CFG_DIR / f"evergreen_v2_predict_{name}.yaml"
        v2_path.write_text(v2_text, encoding="utf-8")
        written.append(v2_path.name)

        # noflag v2
        nf_text = patch(
            text,
            dataset_dir=V2_NOFLAG_DATASET_DIR_LITERAL,
            eval_dataset="evergreen_test_v2_noflag",
            output_dir_suffix="evergreen_v2_noflag",
        )
        nf_path = CFG_DIR / f"evergreen_v2_noflag_predict_{name}.yaml"
        nf_path.write_text(nf_text, encoding="utf-8")
        written.append(nf_path.name)

    print(f"wrote {len(written)} YAML files:")
    for w in written:
        print(f"  {w}")


if __name__ == "__main__":
    main()

# SFT Data Scorer 训练心得与实验观察

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-02, refreshed 2026-05-05 |
| Report type | Training notes / lessons learned |
| Project stage | Cross-experiment learning |
| Report status | Living reference note |

## Experiment Context

| Field | Value |
| --- | --- |
| Model | Qwen3-4B and Qwen3-8B scorer experiments |
| Data version | v1 binary, v2 conservative/confident, v3 data ready, original 1-5 scorer |
| Current use | Explain training tricks, early stopping, observed behavior, v3 training readiness, and next learning experiments |

这份笔记把目前项目里已经踩过的坑、有效的训练设置、观察到的模型现象、以及后续实验判断方式整理到一起。它不是某一次实验报告，而是给后面继续学习和迭代用的总笔记。

## 1. 任务定义比模型大小更重要

最早的目标是让小模型直接预测 teacher 的 1-5 分，但这个目标实践下来不太适合当前数据量。

主要原因：

- 1/2/4/5 相对清楚，3 很模糊。
- 很多错误是 off-by-one，比如 4 和 5、1 和 2 的差异不一定真的重要。
- `maybe` / score 3 的召回很差，模型很难稳定学到中间状态。
- 评分标尺越细，teacher 自身的不确定性越容易变成 student 的噪声。

所以二分类是更好的第一阶段目标：

- 4/5 -> `keep`
- 1/2 -> `not_keep`
- 3 要么跳过，要么按质量优先策略放进 `not_keep`

这个转换的核心价值不是“降低任务难度”这么简单，而是把模型训练目标对齐到真正的业务目标：筛 SFT 数据时，最重要的是知道哪些样本明显可用、哪些样本不该直接进训练集。

## 2. score 3 的处理策略

目前有两个合理版本。

### Confident

score 3 直接跳过：

- 4/5 -> `keep`
- 1/2 -> `not_keep`
- 3 -> skip

优点：

- 训练标签更干净。
- keep 和 not_keep 的边界更明确。
- 适合训练一个“高置信二分类器”。

缺点：

- 模型不一定知道真实世界里那些模糊样本应该怎么处理。
- 部署时遇到边界样本，可能更容易误判成 keep。

### Conservative

score 3 放进 `not_keep`：

- 4/5 -> `keep`
- 1/2/3 -> `not_keep`

优点：

- 更符合 SFT 质量优先的策略。
- 模型会更谨慎，不容易把模糊样本直接放进 keep。
- 对“不能盲目加入训练集”的数据治理更友好。

缺点：

- task 更难，因为 not_keep 内部混合了坏样本和模糊样本。
- keep F1 可能下降。
- 指标不能和 confident 版本做完全同分布比较。

当前判断：

- 如果目标是“尽量别把垃圾数据放进 SFT”，conservative 更符合策略。
- 如果目标是“训练一个边界最干净的二分类器”，confident 值得作为 ablation。
- 最终可以两者结合：confident 模型负责高置信 keep/not_keep，conservative 策略负责 review routing。

## 3. 数据质量比数据量更关键

这几轮实验里，一个很明显的结论是：单纯加数据不一定提升，关键是补什么数据。

有效补数据方向：

- 当前模型容易误判的来源，如 `cot_zh`。
- not_keep 样本，尤其是看起来像 keep 但实际不适合训练的样本。
- 4/5 和 1/2 的边界样本。
- score 3 类模糊样本，用来学习保守过滤策略。
- rule flags 与模型判断冲突的样本。

不建议盲目补的数据：

- 大量明显 keep 的简单样本。
- 重复模板、重复来源、重复长度区间的数据。
- teacher 也明显犹豫的样本，除非目标就是训练 review/uncertain。

这就是为什么 targeted 1200 比随机再采 1200 更有价值。它不是为了让数据集变大，而是为了补模型弱点。

## 4. 目前跑过的关键实验现象

### 原始 1-5 scorer

技术上能训练，JSON 格式也稳定，但任务目标太细。

观察：

- score exact accuracy 不够高。
- score within +/-1 比 exact 好很多，说明很多错误其实是等级边界模糊。
- `maybe` 几乎学不好。
- 模型倾向预测 keep/drop，难以稳定预测中间档。

结论：

- 不适合作为当前主线。
- 可以保留为错误分析参考。

### Qwen3-4B v1 binary confident

这是第一个真正可用的 baseline。

指标：

| Split | Accuracy | Keep F1 | Not-keep F1 |
| --- | ---: | ---: | ---: |
| Valid | 82.11% | 0.872 | 0.702 |
| Test | 76.04% | 0.824 | 0.623 |

观察：

- 格式稳定，JSON/schema 100% 有效。
- 比 1-5 scorer 更适合当前任务。
- not_keep 还不够强，不能直接自动删除数据。

结论：

- 适合作为 compact baseline。
- 后续更大的模型或更多数据，都应该和它比较。

### Qwen3-8B v1 binary confident

换成 8B 后，模型能力确实变强，但不是所有指标都变好。

指标：

| Split | Accuracy | Keep F1 | Not-keep F1 |
| --- | ---: | ---: | ---: |
| Valid | 77.89% | 0.851 | 0.571 |
| Test | 84.38% | 0.899 | 0.651 |

观察：

- test accuracy 和 keep recall 明显提升。
- 但 valid not_keep 更差。
- test not_keep recall 只有 51.85%，说明它更偏向 keep。

结论：

- 8B 容量更强，但会放大数据分布里的 keep bias。
- 只换更大模型不够，必须补 not_keep 和边界数据。

### Qwen3-8B v2 conservative

加入 targeted 1200 并把 score 3 放进 not_keep 后，拒绝边界改善。

指标：

| Split | Accuracy | Keep F1 | Not-keep F1 |
| --- | ---: | ---: | ---: |
| Valid | 74.55% | 0.799 | 0.655 |
| Test | 79.91% | 0.844 | 0.717 |

观察：

- test not_keep F1 从 v1 8B 的 0.651 提升到 0.717。
- test not_keep recall 从 51.85% 提升到 64.04%。
- keep F1 下降，这是预期内的，因为 v2 conservative 任务更难。
- `cot_zh` 仍然是最弱来源。

结论：

- 这是目前最好的 quality-first candidate。
- 适合做优先级排序、review routing、teacher relabeling 采样。
- 仍不适合盲目自动删除。

### Qwen3-8B v2 confident

跳过 score 3 后，模型更适合做 high-confidence keep filter，但拒绝边界弱于 conservative。

指标：

| Split | Accuracy | Keep F1 | Not-keep F1 |
| --- | ---: | ---: | ---: |
| Valid | 76.14% | 0.832 | 0.591 |
| Test | 82.41% | 0.879 | 0.679 |

训练观察：

- 总步数：297
- 最优 checkpoint：`checkpoint-150`
- best valid eval loss：`0.050177909433841705`
- 训练总时长约 30 分钟
- JSON/schema 仍是 100% 有效

和 v2 conservative 对比：

- test accuracy 更高：82.41% vs 79.91%。
- test keep F1 更高：0.879 vs 0.844。
- test not_keep F1 更低：0.679 vs 0.717。
- test not_keep recall 更低：57.81% vs 64.04%。

结论：

- confident 适合挑选更确定的 keep 样本。
- conservative 仍然更适合 review routing 和找可疑样本。
- 两个模型意见不一致的样本，比继续盲目训练更值得发给 teacher。

## 5. 模型大小的经验

Qwen3-8B 不是无脑优于 Qwen3-4B。

更大模型的优势：

- 对 keep 样本理解更强。
- 泛化能力可能更好。
- 能从 targeted 数据中学到更复杂边界。

更大模型的问题：

- 如果训练集 keep 偏多，它可能更自信地预测 keep。
- 对 not_keep 的召回不一定自然变好。
- 如果标签策略不清楚，8B 可能学得更“圆滑”，反而不够保守。

当前建议：

- 4B 保留为 compact baseline。
- 8B 作为主力候选，但必须配合 targeted negatives 和 conservative policy。
- 模型升级本身不是答案，数据分布和标签定义更重要。
- 现在暂时不优先跑 4B v2 confident/conservative。除非需要部署低成本模型，
  否则下一步更应该先用两个 8B v2 模型挖 hard cases，再决定是否训练 4B v2。

## 6. LoRA 训练设置心得

目前稳定可用的设置：

| Setting | Value |
| --- | --- |
| finetuning | LoRA |
| LoRA rank | 8 |
| LoRA target | all |
| epochs | 3 |
| learning rate | 1e-4 |
| effective batch | 16 |
| per-device batch | 1 |
| gradient accumulation | 16 |
| cutoff len | 4096 |
| scheduler | cosine |
| warmup steps | 20 |
| bf16 | true |
| gradient checkpointing | true |
| dataloader workers | 0 |

为什么这些设置合理：

- rank 8 对这种 JSON 分类任务已经够用，先不急着加 rank。
- learning rate 1e-4 对 LoRA 小数据集比较常见，也没有观察到明显崩坏。
- 3 epochs 目前能收敛，继续加 epoch 可能提升有限，并增加过拟合风险。
- effective batch 16 稳定，显存压力也可控。
- cutoff len 4096 保证长样本不容易被过度截断。

暂时不优先调整：

- LoRA rank 16/32：除非现有模型明显欠拟合。
- 5+ epochs：容易记住 teacher labels，而不是真正泛化。
- 过低 temperature 的训练无关，预测阶段才需要控制 generation。

可以后续尝试：

- 2 epoch vs 3 epoch，看是否更稳。
- learning rate 5e-5，看是否减少 keep bias。
- class-balanced sampling 或 loss weighting，增强 not_keep recall。
- 单独做 cot_zh-focused 数据增强。

## 7. 早停、checkpoint 和训练 trick

这一节专门记录训练过程里的操作细节。前面的实验里用了一些“稳态设置”，但还没有启用真正的 early-stopping callback。

### 当前实际使用过的策略

已经使用：

- `load_best_model_at_end: true`
- `metric_for_best_model: eval_loss`
- `greater_is_better: false`
- `eval_strategy: steps`
- `eval_steps: 50`
- `save_steps: 50`
- 训练固定跑 3 epochs，然后选择 best checkpoint，而不是直接用 final checkpoint。

这意味着目前的做法更准确地说是“best-checkpoint selection”，不是真正的“满足条件就提前中止训练”。

这个策略目前是合理的，因为数据集还比较小，一轮完整训练成本不高，而且我们更需要稳定可比较的实验结果。

### 什么时候应该早停

可以考虑早停的情况：

- `eval_loss` 连续 2 次评估不再下降，甚至开始上升。
- 同时 `train_loss` 还在下降，说明模型可能在记训练集而不是泛化。
- valid/test 的 not_keep F1 没有提升，prediction distribution 却越来越偏 keep。
- JSON/schema valid rate 开始下降。
- 生成结果开始出现解释文本、markdown、多余字段，说明格式能力被训练破坏。
- per-source 指标里某一类来源明显崩掉，比如 `cot_zh` 大幅下降。

不建议只因为 `eval_loss` 有一点点抖动就停。小数据 LoRA 的 eval loss 轻微波动很正常，要结合 F1、confusion matrix 和预测分布看。

### 当前实验里的具体观察

Qwen3-8B v2 conservative：

- 总步数：330
- 最优 checkpoint：`checkpoint-250`
- best valid eval loss：`0.055845100432634354`
- step 300 的 eval loss 只比 step 250 略差

这个现象说明：3 epochs 没有明显崩坏，但最后一段收益已经很小。后面继续加到 4-5 epochs 不一定值得，可能会增加过拟合 teacher label 的风险。

Qwen3-8B v1 confident：

- best checkpoint 出现在中段，而不是最终一定最好。
- test keep recall 很高，但 not_keep recall 很低。

这说明不能只看 eval loss 或 accuracy。模型越训越会输出“格式正确的答案”，但不代表 reject boundary 更好。

### 下一轮可以怎么设置早停

如果继续训练 v2 confident 或后续 v3，可以这样做：

- 仍然保留 `load_best_model_at_end: true`。
- `eval_steps` 保持 50，数据更大时可以改成 100。
- 如果观察到连续 2-3 次 eval loss 没有改善，就可以手动停止。
- 早停判断必须同时看：
  - eval loss
  - valid not_keep F1
  - valid not_keep recall
  - prediction keep/not_keep distribution
  - JSON/schema valid rate

对这个任务来说，最重要的早停信号不是“loss 是否最低”，而是“拒绝边界有没有开始变差”。

### 已经用过且有效的训练 trick

有效：

- 把 1-5 评分改成二分类，任务定义立刻更稳。
- 使用 `qwen3_nothink` template，避免模型输出思考过程。
- response 只保留极短 JSON，减少格式漂移。
- greedy predict，保证评估可复现。
- `dataloader_num_workers: 0`，解决 Windows 上多进程 dataloader 和 CUDA 共享问题。
- `gradient_checkpointing: true`，让 8B LoRA 更稳地跑在当前机器上。
- `bf16: true`，速度和显存都更合适。
- targeted sampling，比随机扩数据更有效。
- score 3 conservative mapping，让模型更谨慎。
- source-wise evaluation，及时发现 `cot_zh` 是弱项。

这些 trick 里，最重要的不是某个训练参数，而是“任务定义 + 数据采样 + 评估口径”三件事一起对齐。

### 还没用、但值得尝试的 trick

优先级高：

- class-balanced sampling：让每个 batch 里 keep/not_keep 更均衡，减少 keep bias。
- loss weighting：提高 not_keep 的损失权重，专门拉 not_keep recall。
- v2 confident ablation：跳过 score 3，看看 keep precision 是否明显恢复。
- conservative/confident 双模型分歧采样：只把两个模型意见不一致的样本发给 teacher。
- hard-negative mining：收集模型预测 keep 但 teacher 判 not_keep 的样本。

优先级中：

- learning rate 从 `1e-4` 降到 `5e-5`，看是否更稳、更少 keep bias。
- 2 epochs vs 3 epochs，对比是否 3 epochs 已经过拟合。
- LoRA rank 16，只在 rank 8 明显欠拟合时尝试。
- cutoff len 分析，确认长样本有没有因为截断导致误判。
- 按 source 做采样权重，给 `cot_zh` 更多训练权重。

暂时不优先：

- 大幅增加 epoch，比如 5-10 epochs。
- 盲目把 LoRA rank 提到 32/64。
- 继续扩大随机数据，而不看 hard cases。
- 用 sampling decoding 做评估。
- 重新回到 1-5 score 主线。

### 训练中要盯的日志和文件

训练时重点看：

- `eval_loss`
- `loss`
- `learning_rate`
- best checkpoint 是哪一步
- 是否保存了 expected checkpoints
- stdout/stderr 里有没有 CUDA OOM、dataloader、路径、encoding 报错

训练完必须记录：

- config path
- dataset 名称和 split 数量
- output_dir
- best checkpoint
- best eval loss
- train runtime
- valid/test prediction output path
- valid/test metrics report path

如果这些没记清楚，后面实验多起来会很难判断哪一个模型真的可用。

### 不要用 final checkpoint 的原因

小数据 LoRA 很容易出现 final checkpoint 不如 best checkpoint。

原因：

- 后期可能开始记 teacher label 的局部偏好。
- keep/not_keep 边界可能被训练集比例带偏。
- eval loss 的微小改善不一定对应 not_keep F1 改善。

所以当前原则是：

- 训练可以跑完 3 epochs。
- 最终评估必须用 best checkpoint 对应的 adapter。
- 如果 LLaMA-Factory 已经 `load_best_model_at_end`，预测配置指向整个 output_dir 即可，但报告里仍要记录 best checkpoint。

### 什么时候该停掉一个实验

可以直接停的情况：

- 训练配置指向了错误 dataset。
- output_dir 写错，可能覆盖重要实验。
- JSON valid rate 不再是 100%，且不是评估脚本问题。
- valid not_keep recall 明显崩掉，同时预测几乎全是 keep。
- CUDA/OOM 后继续异常慢或反复报错。
- 发现当前实验的对照意义不成立，比如数据 split 不一致。

这类情况下不要硬跑完。停掉比得到一个不可解释的结果更好。

## 8. Windows 和 LLaMA-Factory 的坑

### dataloader workers

Windows 上用 `dataloader_num_workers: 4` 时，Qwen3-8B 训练曾经因为 CUDA tensor sharing / out-of-memory 失败。

稳定做法：

```yaml
dataloader_num_workers: 0
```

代价是可能慢一点，但稳定性更重要。

### 网络盘路径

项目在学校网络盘上，PowerShell 有时会出现相对路径漂移，甚至落到 `System32` 下面。

稳定做法：

```powershell
Set-Location -LiteralPath "\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge"
```

脚本和评估尽量用显式 UNC 路径，不要依赖当前 shell 的相对路径。

### 中文路径显示

PowerShell 输出里有时会把 `微调` 显示成乱码，但文件实际可以正常读写。判断是否真的有问题，要看脚本是否能读取数据，而不是只看终端显示。

### 后台日志编码

Windows 后台训练如果把 stdout/stderr 重定向到文件，默认编码可能不是 UTF-8。
v2 confident 8B 重跑时，LLaMA-Factory 打印中文 training example 曾经触发：

```text
UnicodeEncodeError: 'charmap' codec can't encode character
```

稳定做法是在启动训练/预测前设置：

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONUTF8='1'
[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new()
```

这不是数据问题，也不是显存问题；只是 Windows 控制台编码和中文样本不匹配。

### 后台训练

长时间训练适合后台启动并写日志，但要记录清楚：

- config path
- output_dir
- stdout/stderr log path
- 是否完成
- best checkpoint

否则容易忘记哪个实验是真的跑完了。

## 9. 预测和评估心得

### 预测必须 greedy

分类任务不应该采样。

推荐：

```yaml
do_sample: false
temperature: 1.0
top_p: 1.0
max_new_tokens: 64
```

原因：

- 输出只有 `{"verdict": "keep"}` 或 `{"verdict": "not_keep"}`。
- sampling 会引入随机误差，让 valid/test 指标不稳定。
- greedy 更适合比较实验。

### JSON 有效率是硬门槛

这个项目里 JSON/schema valid 一直是 100%，这是好现象。

如果以后下降，优先排查：

- prompt 是否改坏了。
- max_new_tokens 是否太短。
- template 是否换了。
- 训练数据 response 是否混入解释文本。

### 不要看 BLEU/ROUGE

LLaMA-Factory 会输出 BLEU/ROUGE，但这个任务不该用它们判断好坏。

真正重要的是：

- accuracy
- keep precision/recall/F1
- not_keep precision/recall/F1
- confusion matrix
- per-source accuracy
- prediction distribution

尤其是 not_keep recall，很能反映模型能不能找出坏样本。

## 10. 指标怎么解读

### Accuracy

有用，但不够。

如果 keep 占比高，模型一直预测 keep 也可能 accuracy 不难看。

### Keep precision

高 keep precision 表示模型说 keep 的样本大多真的能保留。

这对“自动加入训练集”很重要。

### Keep recall

高 keep recall 表示好样本不容易被错杀。

这对“不要浪费好数据”很重要。

### Not-keep precision

高 not_keep precision 表示模型说不保留的样本大多真的不该保留。

这对“人工 review 排序”很有用。

### Not-keep recall

高 not_keep recall 表示坏样本不容易漏掉。

这是自动过滤最关键的指标之一。当前还没高到可以盲删。

### Prediction distribution

一定要看模型预测了多少 keep / not_keep。

例如 v1 8B test 只预测了 16 个 not_keep，说明它非常 keep-biased。即使 accuracy 高，也不能说明它是好的 reject model。

## 11. 什么时候能自动删数据

目前还不能。

原因：

- v2 conservative test 中仍有 32/89 个 not_keep 被预测成 keep。
- not_keep recall 64.04%，还不够做不可逆删除。
- teacher labels 本身也可能有噪声，不能把 student 当绝对真理。

更安全的用法：

- predicted keep：优先进入候选训练池。
- predicted not_keep：进入人工 review 或 teacher relabel。
- 高不确定样本：优先发给 teacher。
- 来源弱、规则异常、模型高置信不保留：重点抽查。

真正可以自动删除的前提：

- not_keep precision 和 recall 都明显更高。
- 在更大的 held-out test 上稳定。
- 对 `cot_zh`、`finetome`、`openmath_reasoning` 都不过分偏科。
- 误删样本人工检查后可以接受。

## 12. 灾难性遗忘和副作用

这个项目不是在训练通用聊天模型，而是在训练一个 data-quality scorer，所以“灾难性遗忘”的含义不同。

主要风险不是模型忘记通用能力，而是：

- 过拟合 teacher 的局部偏好。
- 只学会当前三个来源的表面特征。
- 对某种格式、长度、语言产生偏见。
- 看到边界样本时过度保守或过度 keep。

降低风险的方法：

- 保留 valid/test，不要用它们训练。
- source-wise 评估。
- 不要只补一种来源的数据。
- 不要无限重复相似 negative。
- 每次加数据后都和旧 baseline 对比。
- 保留 compact baseline，避免只相信最新模型。

## 13. 下一步最有价值的学习实验

### v2 confident 8B ablation

已经完成。当前结论：

- 跳过 score 3 后，keep 侧指标明显更好。
- not_keep F1 和 not_keep recall 低于 conservative。
- 它不是 conservative 的替代品，更适合作为 companion model。

判断：

- 如果 confident keep precision 高很多，可以用它做 high-confidence keep filter。
- 如果 conservative not_keep 更强，可以用它做 review routing。
- 两者不一定非要二选一。
- 实际下一步应该看两个模型在未标注大池子上的分歧，而不是只看 held-out 指标。

### 推理脚本和 3,600 条 pilot

比继续盲目训练更值得做。`scripts/12_infer_binary_scorer.py` 已经实现，
并且已经用两个 8B v2 adapter 跑完了
`data/splits/teacher_judge/teacher_candidates_all.jsonl` 这 3,600 条 pilot。

目标：

- 对大池子 JSONL 批量打分。
- 支持 resume。
- 输出 keep/not_keep 分布。
- 按 source、长度、rule flag 聚合。
- 抽样 high-confidence keep / not_keep / uncertain。

这样可以知道模型真实部署时会怎么筛数据。当前 3,600 条 pilot 的四桶结果：

- confident keep + conservative keep
  - 2,681
- confident keep + conservative not_keep
  - 272
- confident not_keep + conservative keep
  - 1
- confident not_keep + conservative not_keep
  - 646

结论：

- 两个 8B v2 scorer 一致率是 92.42%，说明不是完全乱打架。
- 273 条 disagreement 是最紧凑的边界样本池。
- 646 条 both-not-keep 是最值得 teacher 确认的 hard negative 候选。
- 这一步已经完成：pilot priority queue 先 dedupe，再生成 `v2active001`，
  最后由 teacher label 回填。
- 现在已经不用再纠结 v3 数据怎么配；v3 数据已经生成，下一步是训练。

### v3 数据和下一轮训练

v3 已经把 starter、targeted 1200、`v2active001` 三批 teacher labels 合并成
新的二分类 scorer 数据。

当前可训练数据：

| Dataset | Records | Train | Valid | Test | Keep | Not_keep | Score 3 policy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `scorer_binary_v3_conservative` | 2,588 | 2,057 | 267 | 264 | 1,438 | 1,150 | score 3 -> `not_keep` |
| `scorer_binary_v3_confident` | 2,326 | 1,855 | 234 | 237 | 1,438 | 888 | score 3 skipped |

当前判断已经更新：

- `scorer_binary_v3_conservative` 和 `scorer_binary_v3_confident` 都已经训练并
  跑完 greedy valid/test evaluation。
- v3 conservative test：accuracy 76.89%，keep F1 0.796，not_keep F1 0.734，
  not_keep recall 77.06%。
- v3 confident test：accuracy 78.90%，keep F1 0.851，not_keep F1 0.638，
  not_keep recall 53.66%。
- 所以当前主线应该换成 v3 conservative：它是更好的 quality-first / review
  routing 模型。
- v3 confident 仍然是 companion：它 keep recall 高，但 not_keep recall 不够，
  不适合替代 conservative 做 reject model。
- 下一步不是继续盲训，而是用两个 v3 scorer 跑更大的 unlabeled pool，
  再从 disagreement、predicted not_keep、rule/model conflict、`cot_zh` 弱点里
  选下一批 teacher labels。

### teacher relabeling loop

下一轮 teacher label 不应该随机采。

应该优先：

- 模型自信但规则冲突的样本。
- `cot_zh` 中模型易错的样本。
- predicted not_keep 高置信样本。
- predicted keep 但 rule flags 异常的样本。
- conservative/confident 两个模型分歧的样本。

这个 loop 不等于 self-training。关键区别是：

- student 只负责选题，不负责给最终标签。
- teacher label 才进入训练集。
- valid/test 不动。
- retrain 时混合旧数据、teacher-confirmed hard cases、正常 keep 样本，
  不要只用模型挖出来的 negative。

这样做不会天然导致过拟合；真正的风险是采样分布变窄，所以需要 source-wise
balance、dedupe、固定 held-out 对比和少量正常样本校准。

## 14. 当前实践原则

可以把现在的经验浓缩成几条原则：

1. 先把任务定义做干净，再谈模型大小。
2. score 3 不适合直接当普通 keep 训练。
3. 二分类比 1-5 评分更适合作为第一阶段 scorer。
4. 8B 有潜力，但会放大数据偏差。
5. targeted 数据比随机加数据更有价值。
6. JSON 分类任务必须用 greedy 评估。
7. 不要只看 accuracy，必须看 not_keep recall/F1。
8. 当前模型适合辅助筛选，不适合盲目删除。
9. 每个实验都要记录 config、数据版本、输出目录、best checkpoint 和指标。
10. 后续最重要的是形成 scorer -> sample hard cases -> teacher relabel -> retrain 的闭环。

# `All-train-model` 与 `first-train` 训练结果对比审查报告

审查日期：`2026-04-06`

## 1. 审查目标

本文档用于回答一个明确问题：

- `backend-train-model/All-train-model/artifacts` 下本次合并数据训练与评估导出结果，是否优于 `backend-train-model/first-train` 的单套数据训练结果？

本次审查基于仓库内已经导出的训练、评估、可视化和导出模型产物进行，不重新训练模型。

---

## 2. 先给结论

结论非常明确：

- **当前证据不足以支持 `All-train-model` 优于 `first-train`。**
- 更准确地说，`All-train-model` 在 `test` 集上的结果与 `first-train` **基本打平**，但在 `val` 集上的结果**明显落后**。
- 如果今天必须从这两套结果里选一套更稳的模型作为当前阶段候选，我会选：
  - `backend-train-model/first-train/artifacts/runs/clothes_fullframe_baseline/weights/best.pt`
- 不会优先选：
  - `backend-train-model/All-train-model/artifacts/runs/clothes_merged_v1_fullframe/weights/best.pt`

一句话总结就是：

- **`first-train` 目前仍然是更稳、更可信的基线。**
- **`All-train-model` 更像一个“测试集精度不错，但验证集稳定性不足”的候选方案。**

---

## 3. 本次实际审查了哪些产物

### 3.1 `All-train-model` 侧

本次审查的主路径：

- `backend-train-model/All-train-model/artifacts/runs/clothes_merged_v1_fullframe/`
- `backend-train-model/All-train-model/artifacts/reports/clothes_merged_v1_fullframe_train.json`
- `backend-train-model/All-train-model/artifacts/reports/clothes_merged_v1_fullframe_eval.json`
- `backend-train-model/All-train-model/artifacts/reports/clothes_merged_v1_fullframe_export.json`
- `backend-train-model/All-train-model/artifacts/export/workwear_detect_yolov8.metadata.json`
- `backend-train-model/All-train-model/datasets/merged_clothes_v1_positive_only/dataset.yaml`

该目录下只发现 **1 套完整 run**：

- `clothes_merged_v1_fullframe`

### 3.2 `first-train` 侧

本次审查的主路径：

- `backend-train-model/first-train/artifacts/runs/clothes_fullframe_baseline/`
- `backend-train-model/first-train/artifacts/reports/clothes_fullframe_baseline_train.json`
- `backend-train-model/first-train/artifacts/reports/clothes_fullframe_baseline_eval.json`
- `backend-train-model/first-train/artifacts/reports/clothes_fullframe_baseline_export.json`
- `backend-train-model/first-train/artifacts/export/workwear_detect_yolov8.metadata.json`
- `backend-train-model/first-train/artifacts/prepared/fullframe/sequence_contiguous/prepare_report.json`

该目录下也只发现 **1 套完整 run**：

- `clothes_fullframe_baseline`

---

## 4. 基本训练配置对比

两边共同点：

- 都是单类检测：`clothes`
- 都使用 `yolov8n.pt` 作为基座模型
- 都是 `imgsz=640`
- 都是 `batch=4`
- 都是 `device=cpu`
- 都把训练计划配置为 `epochs=180`

不同点主要在数据集规模和数据组织方式。

### 4.1 `All-train-model` 数据规模

- `train=330`
- `val=62`
- `test=62`

按标签文件实际统计的框数约为：

- `train=728`
- `val=74`
- `test=178`

### 4.2 `first-train` 数据规模

- `train=66`
- `val=15`
- `test=14`

按 `prepare_report.json` 中的统计，框数为：

- `train=246`
- `val=43`
- `test=30`

### 4.3 初步判断

从样本量角度看，`All-train-model` 的数据量明显更大，本来应该更有机会优于基线。

但最终结果没有体现出“更大数据量带来更好验证表现”，这说明问题不在“有没有更多图”，而更可能在以下方面之一：

- 合并后数据分布不均衡
- 合并后的标注质量不一致
- `val/test` 划分口径与难度分布不一致
- 模型在更大数据集上训练稳定性不足

---

## 5. 核心指标对比

以下对比以两边各自导出的 `best.pt` 对应 `eval.json` 为准。

### 5.1 验证集 `val` 对比

| 指标 | All-train-model | first-train | 谁更好 |
| --- | ---: | ---: | --- |
| Precision | 0.6447 | 0.9349 | `first-train` |
| Recall | 0.6622 | 0.9535 | `first-train` |
| mAP50 | 0.7317 | 0.9879 | `first-train` |
| mAP50-95 | 0.3419 | 0.7485 | `first-train` |

结论：

- **验证集上 `first-train` 全面领先。**
- 尤其是 `mAP50-95`，`first-train` 比 `All-train-model` 高约 `0.4066`，这是决定性差距。

### 5.2 测试集 `test` 对比

| 指标 | All-train-model | first-train | 谁更好 |
| --- | ---: | ---: | --- |
| Precision | 0.9649 | 0.9112 | `All-train-model` |
| Recall | 0.8933 | 0.9667 | `first-train` |
| mAP50 | 0.9458 | 0.9759 | `first-train` |
| mAP50-95 | 0.6987 | 0.6994 | 基本持平，`first-train` 略高 |

结论：

- `All-train-model` 在 `test` 上的 **precision 更高**，说明它更倾向于“少报”。
- 但 `first-train` 在 `recall`、`mAP50` 和 `mAP50-95` 上并没有输。
- 特别是 `mAP50-95`，两者几乎一样，`first-train` 仅略高约 `0.0007`。

### 5.3 综合判断

如果把 `val` 与 `test` 一起看：

- `All-train-model` **没有形成稳定的全面优势**
- `first-train` **综合表现更均衡**
- 从“模型是否更稳、更可信”而不是“某个 split 上单项 precision 是否更高”的角度看，`first-train` 更值得继续作为当前基线

---

## 6. 训练过程稳定性对比

### 6.1 `All-train-model`

从 `results.csv` 可见：

- 最优 `val mAP50-95` 出现在 **第 75 轮**
- 最优值约为 `0.3423`
- 训练记录只到 **第 115 轮**
- 最后一轮的 `val mAP50-95` 已回落到约 `0.2043`

这说明两件事：

1. 该模型后期训练存在明显退化
2. `best.pt` 与 `last.pt` 差距较大，说明训练后段并不稳定

因此，`All-train-model` 当前更像是：

- “有一段时间达到过尚可水平”
- 但“整体训练过程不够平稳，后段退化明显”

### 6.2 `first-train`

从 `results.csv` 可见：

- 最优 `val mAP50-95` 出现在 **第 172 轮**
- 最优值约为 `0.7486`
- 训练记录完整跑到 **第 180 轮**
- 最后一轮仍保持约 `0.7362`

这说明：

- `first-train` 不仅最好成绩更高
- 而且在训练末段仍保持较高水平
- 曲线整体比 `All-train-model` 稳定得多

### 6.3 稳定性结论

- **`first-train` 明显更稳**
- **`All-train-model` 存在“训练后期退化 + 验证效果偏弱”的双重问题**

---

## 7. 可视化与直观效果观察

本次同时抽看了以下可视化产物：

- `results.png`
- `confusion_matrix_normalized.png`
- `val_batch*_labels.jpg`
- `val_batch*_pred.jpg`

### 7.1 `All-train-model` 的直观现象

从验证图和混淆矩阵看，`All-train-model` 的主要问题不是“疯狂乱报”，而是：

- 某些目标会漏掉
- 某些目标置信度偏低
- 验证集上的检出稳定性明显不够

这和它的：

- `precision` 中等
- `recall` 中等
- `mAP50-95` 偏低

是一致的。

### 7.2 `first-train` 的直观现象

`first-train` 的验证图与曲线更匹配其数值表现：

- 目标覆盖更完整
- 漏检更少
- 曲线更稳定

也就是说，它的“图上看起来更稳”与“指标上更稳”是相互印证的。

---

## 8. 一个必须说明的比较 caveat

虽然当前结论已经足够支持“`All-train-model` 没有赢过基线”，但这里仍然必须明确一个比较边界：

- **两边当前的 `val/test` 并不是完全同口径的公共 holdout 集。**

其中：

- `first-train` 的 `val/test` 是在同一批原始序列上做的连续切分
- `All-train-model` 的 `val/test` 来自 merged 数据集的另一套组织结果

另外，基于文件名做的统计，**这是我的推断**：

- `All-train-model` 的 `val` 基本集中在 `g33__D02_20260123070624`
- `All-train-model` 的 `test` 则来自 `g31__D15_20260123074848` 和 `g31__D04_20260123074846`

这意味着：

- `All-train-model` 的 `val` 和 `test` 很可能难度并不一致
- 其 `val mAP50-95 = 0.3419` 与 `test mAP50-95 = 0.6987` 的巨大落差，不能简单理解为“模型突然在 test 上更神”
- 更合理的解释通常是：**split 难度不同、数据分布不同，或者验证集代表性不足**

因此，本报告的结论应理解为：

- **在当前仓库内现有导出结果口径下，`All-train-model` 没有证明自己优于 `first-train`。**

而不是：

- “在绝对公平同口径基准下，`All-train-model` 永久不可能优于 `first-train`”

---

## 9. 现阶段业务判断

如果目标是：

- 先选一套当前阶段更稳的模型做内部联调
- 先保留一个可信 baseline 作为后续升级参照
- 不希望因为新数据合并带来额外不确定性

那么建议如下：

### 9.1 当前优先保留的模型

优先保留：

- `backend-train-model/first-train/artifacts/runs/clothes_fullframe_baseline/weights/best.pt`

理由：

- `val` 明显更强
- `test` 不输
- 训练过程更稳
- 当前更适合作为“基线版本”

### 9.2 `All-train-model` 的定位

建议将 `All-train-model` 当前结果定位为：

- merged 方案的一次阶段性试训结果
- 不是正式替代 `first-train` 的升级版
- 可以保留继续分析，但不建议直接宣称“已优于 baseline”

---

## 10. 建议的下一步动作

### 10.1 最优先动作

用**同一套公共 holdout 集**重评两边的 `best.pt`。

只有在同口径评估下，才能真正回答：

- merged 数据方案到底有没有超过单套数据方案

### 10.2 次优先动作

复查 `All-train-model` 的 merged 数据问题，重点看：

- `val/test` 划分是否失衡
- `val` 是否过难或代表性异常
- 合并样本标注质量是否不一致
- 是否存在某些序列风格差异过大、把验证集拉崩的情况

### 10.3 训练策略侧建议

如果后续继续跑 merged 方案，建议优先考虑：

- 缩短 patience 或更早停止，避免后段继续退化
- 重新审查 split 规则，不要让 `val` 和 `test` 的难度差距过大
- 在同口径固定验证集上反复比较，而不是只看某次 merged 数据的单独结果

---

## 11. 本次审查的最终结论

最终结论保持不变：

- **`backend-train-model/All-train-model/artifacts` 当前结果不优于 `backend-train-model/first-train`。**
- 它在 `test` 上可以说“没有明显输”，甚至 precision 更高，但这不足以支撑“整体更好”。
- 从验证集表现、训练稳定性、当前可信度三方面综合判断，**`first-train` 仍然是目前更稳的基线结果。**

---

## 12. 附：本次判断主要依据的文件

- `backend-train-model/All-train-model/artifacts/reports/clothes_merged_v1_fullframe_train.json`
- `backend-train-model/All-train-model/artifacts/reports/clothes_merged_v1_fullframe_eval.json`
- `backend-train-model/All-train-model/artifacts/runs/clothes_merged_v1_fullframe/results.csv`
- `backend-train-model/All-train-model/artifacts/runs/clothes_merged_v1_fullframe/results.png`
- `backend-train-model/All-train-model/artifacts/runs/clothes_merged_v1_fullframe/confusion_matrix_normalized.png`
- `backend-train-model/All-train-model/artifacts/runs/clothes_merged_v1_fullframe/val_batch0_pred.jpg`
- `backend-train-model/All-train-model/datasets/merged_clothes_v1_positive_only/dataset.yaml`
- `backend-train-model/first-train/artifacts/reports/clothes_fullframe_baseline_train.json`
- `backend-train-model/first-train/artifacts/reports/clothes_fullframe_baseline_eval.json`
- `backend-train-model/first-train/artifacts/prepared/fullframe/sequence_contiguous/prepare_report.json`
- `backend-train-model/first-train/artifacts/runs/clothes_fullframe_baseline/results.csv`
- `backend-train-model/first-train/artifacts/runs/clothes_fullframe_baseline/results.png`
- `backend-train-model/first-train/artifacts/runs/clothes_fullframe_baseline/confusion_matrix_normalized.png`
- `backend-train-model/first-train/artifacts/runs/clothes_fullframe_baseline/val_batch0_pred.jpg`

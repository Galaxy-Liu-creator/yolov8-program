# `backend-train-model`

本目录用于维护当前项目的后端训练主线，重点覆盖：

- `clothes` / `workwear` 检测训练与评估
- unified holdout 对照训练
- merged 路线 baseline 固化
- 后续 `person` / `personcrop` / 离线链路衔接

如果你现在只想快速知道“项目训练到了哪一步、当前该看哪份文档、现在哪个模型是基线”，优先看这份 README。

---

## 1. 当前训练进度

### 1.1 当前主线状态

当前主线已经从“`first-train` 是否优于 merged”切换到“在统一 holdout 下固定 merged fullframe baseline，并为后续 `person` / `personcrop` 做准备”。

| 阶段 | 状态 | 当前判断 |
| --- | --- | --- |
| P0 `clothes` fullframe baseline | **已完成** | unified holdout 对照、strict holdout、route verification 已跑通，当前 baseline 已固定到 `00_CURRENT_BASELINE` |
| P1 `person` 数据资产 | **基本完成** | `person` 数据准备入口与训练文档已存在，prepared `dataset.yaml` 已生成，但 `person` 模型权重尚未产出 |
| P2 `person` 模型训练 | **未完成** | `backend-train-model/weights/person_detect_yolov8.pt` 仍不存在 |
| P3 `personcrop` clothes 对照 | **未开始** | 依赖稳定的 `person` 权重 |
| P4 离线完整链路 | **未开始** | 还未进入 `person + clothes + ROI + temporal` 联调 |
| P5 摄像头接入 | **未开始** | 尚未进入真实摄像头灰度阶段 |

### 1.2 统一 holdout 当前结论

当前统一对照集为：

- 数据集：`backend-train-model/All-train-model/datasets/unified_holdout_v1/dataset.yaml`
- 样本规模：`75` 张图、`150` 个 GT 框

当前三组最关键结果如下：

| 口径 | 模型 | Precision | Recall | mAP50 | mAP75 | mAP50-95 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| strict holdout | `clothes_first_train_holdout_v1` | `0.8784` | `0.8200` | `0.8581` | `0.7233` | `0.6367` |
| strict holdout | `clothes_merged_v2_balanced_holdout_v1` | `0.9780` | `0.9533` | `0.9859` | `0.8678` | `0.8040` |
| route verification | `clothes_merged_v2_balanced_from_first_holdout_v1` | `0.9797` | `0.9653` | `0.9875` | `0.8773` | `0.8042` |

结论：

- 在当前统一 holdout 下，`merged` 已明显优于本轮公平重训的 `first-train`。
- `route verification` 版本相对 strict holdout 版本仍有小幅正向提升。
- 因此，当前 clothes 主线 baseline 选为 `clothes_merged_v2_balanced_from_first_holdout_v1`，并保留 strict holdout merged 版本作为 rollback。

---

## 2. 当前 clothes merged baseline

当前 baseline 入口目录：

- `backend-train-model/All-train-model/00_CURRENT_BASELINE/README.md`

直接使用这些路径：

- baseline 权重：`backend-train-model/All-train-model/artifacts/runs/clothes_merged_v2_balanced_from_first_holdout_v1/weights/best.pt`
- baseline 评估：`backend-train-model/All-train-model/artifacts/reports/merged_v2_balanced_from_first_holdout_v1_route_eval.json`
- rollback 权重：`backend-train-model/All-train-model/artifacts/runs/clothes_merged_v2_balanced_holdout_v1/weights/best.pt`
- rollback 评估：`backend-train-model/All-train-model/artifacts/reports/merged_v2_balanced_holdout_v1_strict_eval.json`

### 2.1 baseline 指标

- Precision：`0.9797021124620489`
- Recall：`0.9653314638318569`
- mAP50：`0.987533931068667`
- mAP75：`0.8772503022289657`
- mAP50-95：`0.804191182807975`

### 2.2 baseline 单帧 FP/FN 复盘口径

- 复盘明细：`backend-train-model/All-train-model/00_CURRENT_BASELINE/baseline_fpfn_per_image.json`
- 摘要文档：`backend-train-model/All-train-model/00_CURRENT_BASELINE/baseline_fpfn_summary.md`
- 预测阈值：`conf=0.45`
- NMS IoU：`0.7`
- GT 匹配 IoU：`0.5`

单帧统计结果：

- 图片数：`75`
- GT 框数：`150`
- 预测框数：`147`
- TP：`144`
- FP：`3`
- FN：`6`
- 单帧 Precision：`0.9795918367346939`
- 单帧 Recall：`0.96`
- 有误报图片：`3`
- 有漏报图片：`5`

---

## 3. `docs/` 审查结果

这次已把 `backend-train-model/docs/` 中最容易和当前阶段冲突的内容做了同步整理：

- 已更新 `backend-train-model/docs/后端训练完成进度.md`
  - 改为当前真实阶段状态；
  - 明确当前 baseline 已切到 merged；
  - 明确 `person` 是“数据入口已具备、权重未完成”的状态。
- 已更新 `backend-train-model/docs/Problem-Solution.md`
  - 新增一次针对文档与当前 baseline 状态的审查记录；
  - 把旧阶段的“待执行 / 未解决”改为历史记录口径。
- 已更新 `backend-train-model/docs/total-run-method.md`
  - 明确这份文档现在是“统一 holdout 重跑手册”；
  - 说明它对应的阶段已经至少完整执行过一轮。
- 已更新 `backend-train-model/docs/all_vs_first_train_review.md`
  - 明确标注为 **历史报告**；
  - 防止它继续被误用为当前 baseline 结论。
- 已更新 `backend-train-model/docs/README.md`
  - 增加当前主线入口说明，避免一进文档目录就从旧命令说明读起。

当前建议这样理解 `docs/`：

- `docs/todo_list.md`、`docs/total-run-method.md`、`All-train-model/00_CURRENT_BASELINE/README.md` 是**当前主线文档**
- `docs/all_vs_first_train_review.md`、`docs/all_train_docs/*`、`docs/first_train_docs/*` 是**历史阶段文档**

---

## 4. `docs/` 建议阅读顺序

如果你要重新接手项目，建议按这个顺序看：

1. `backend-train-model/docs/README.md`
   - 先了解 `train_workwear.py` 的主入口、命令结构和基础约束。
2. `backend-train-model/docs/todo_list.md`
   - 看当前主线做到哪里、下一步该做什么。
3. `backend-train-model/docs/total-run-method.md`
   - 看统一 holdout 对照怎么复现、怎么重跑。
4. `backend-train-model/All-train-model/00_CURRENT_BASELINE/README.md`
   - 看当前 baseline 具体指向哪个 run、各项指标是多少。
5. `backend-train-model/docs/后端训练完成进度.md`
   - 看阶段性完成度和当前真实能力边界。
6. `backend-train-model/docs/Problem-Solution.md`
   - 看最近几次审查和修订的理由。
7. `backend-train-model/docs/pipeline_roadmap.md`
   - 看中长期生产路线和为什么后面要走 `person` / `personcrop`。
8. `backend-train-model/docs/run_logic.md`
   - 看训练脚本和链路逻辑的实现侧说明。
9. `backend-train-model/docs/all_vs_first_train_review.md`
   - 只在需要回溯 2026-04-06 阶段结论时再看。
10. `backend-train-model/docs/all_train_docs/` 与 `backend-train-model/docs/first_train_docs/`
   - 仅作历史阶段归档，不再作为当前 baseline 判断依据。

---

## 5. 现在最应该做什么

当前最合理的下一步不是继续回头纠结 `first-train`，而是：

1. 以当前 merged baseline 作为 fullframe 主基线继续保留；
2. 训练并固化 `person` 模型，产出 `backend-train-model/weights/person_detect_yolov8.pt`；
3. 再基于 `personcrop` 重训 clothes，和当前 fullframe baseline 做公平对照；
4. 最后再进入离线完整链路与摄像头接入。

一句话总结：

> 当前 `backend-train-model` 已经完成 clothes 主线 baseline 固化；接下来该把重心转到 `person`，而不是继续回到旧的 `first-train` 基线。

# 00_CURRENT_BASELINE

这个目录用于**醒目地固定当前 clothes fullframe 主基线入口**。

注意：

- 这里默认**不复制** `best.pt`，避免同一份权重出现两份物理副本后被误用。
- 真实可训练 / 可评估 / 可导出的权重仍保留在原始 `artifacts/runs/` 目录。
- 如果后续 `personcrop` 对照或真实链路验证推翻当前结论，可以直接回滚到下方记录的 rollback 候选。

## 当前结论

- baseline 状态：`tentative`
- 任务：`clothes fullframe`
- 当前暂定 baseline run：`clothes_merged_v2_balanced_from_first_holdout_v1`
- 选择原因：在相同 `unified_holdout_v1` 上，`route verification` 结果相比 `clothes_merged_v2_balanced_holdout_v1` 略优，且更接近后续真实业务“先有 clothes 基线，再沿链路继续推进”的使用路径
- 统一对照集：`backend-train-model/All-train-model/datasets/unified_holdout_v1/dataset.yaml`
- 对照范围：`75` 张图，`150` 个框

## 直接使用这些路径

- 当前暂定 baseline 权重：`backend-train-model/All-train-model/artifacts/runs/clothes_merged_v2_balanced_from_first_holdout_v1/weights/best.pt`
- 当前暂定 baseline 评估：`backend-train-model/All-train-model/artifacts/reports/merged_v2_balanced_from_first_holdout_v1_route_eval.json`
- 回滚候选权重：`backend-train-model/All-train-model/artifacts/runs/clothes_merged_v2_balanced_holdout_v1/weights/best.pt`
- 回滚候选评估：`backend-train-model/All-train-model/artifacts/reports/merged_v2_balanced_holdout_v1_strict_eval.json`
- 当前 baseline 逐图误报 / 漏报明细：`backend-train-model/All-train-model/00_CURRENT_BASELINE/baseline_fpfn_per_image.json`
- 当前 baseline 误报 / 漏报摘要：`backend-train-model/All-train-model/00_CURRENT_BASELINE/baseline_fpfn_summary.md`

## 关键指标

- 当前暂定 baseline
  - Precision：`0.9797021124620489`
  - Recall：`0.9653314638318569`
  - mAP50：`0.987533931068667`
  - mAP75：`0.8772503022289657`
  - mAP50-95：`0.804191182807975`
- 回滚候选
  - Precision：`0.9779928494282899`
  - Recall：`0.9533333333333334`
  - mAP50：`0.9859170602082232`
  - mAP75：`0.8677885110776686`
  - mAP50-95：`0.8040445872853204`

## 当前判断

- 当前暂定 baseline 比回滚候选：
  - Precision `+0.0017092630337590`
  - Recall `+0.0119981304985235`
  - mAP50 `+0.0016168708604438`
  - mAP75 `+0.0094617911512971`
  - mAP50-95 `+0.0001465955226546`
- 提升幅度不大，但方向为正。
- 因此当前建议：**先用它作为暂定 baseline 继续往后推进**，同时保留回滚路径，不把旧 `first-train` 再当主线基线。

## 误报 / 漏报清单

- 清单口径：`unified_holdout_v1` 的 `test` split 单帧 GT 对照。
- 预测阈值：`conf=0.45`，对齐当前 `inspection-flask` 中 workwear 推理默认置信度；不是 `mAP` 曲线用的低阈值候选清单。
- 匹配规则：同类框 `IoU >= 0.5` 计为 TP；未匹配预测计 FP；未匹配 GT 计 FN。
- 逐图明细：`baseline_fpfn_per_image.json`
- 人类摘要：`baseline_fpfn_summary.md`
- 本轮统计：
  - 图片数：`75`
  - GT 框数：`150`
  - 预测框数：`147`
  - TP：`144`
  - FP：`3`
  - FN：`6`
  - Precision：`0.9795918367346939`
  - Recall：`0.96`
  - 有误报图片数：`3`
  - 有漏报图片数：`5`

## 下一步

- 使用当前 baseline 的误报 / 漏报清单作为后续 `fullframe` 对照参考
- 训练并固定 `person` 模型
- 再进入 `personcrop clothes` 对照训练

# personcrop首轮A_B阶段结论

## 1. 结论摘要

当前 `personcrop` 首轮双上游 A/B 已完成，结论如下：

1. **路线成立**：A 与 B 都证明 `personcrop -> clothes` 路线已经能稳定训练并取得很强结果；
2. **B 略优于 A**：B 在 prepared 统计与下游评估指标上都保持稳定小幅领先；
3. **当前默认 candidate**：后续 `personcrop` 主推进对象暂定为 `pred_pc_clo_hardv1`；
4. **当前稳定对照**：保留 `pred_pc_clo_base` 作为稳健对照，不建议现在删除或忽略；
5. **当前不下最终主线切换结论**：下一步先补原图级 / 业务级复盘，再决定是否把 `personcrop` 升级为默认主线。

---

## 2. 本轮统一口径

### 2.1 下游 source dataset

- 正式 source dataset：
  `backend-train-model/new_clothes_train/train-result/datasets/clothes_merged_with_new_labels_v1/dataset.yaml`
- 当前实际纳入构建的有效样本：
  - `images=2961`
  - `labels=2961`
  - `boxes=5265`
- 说明：名义总图数仍可写作 `3009`，但当前实际参与 `personcrop` 生成的是 `2961` 张有效样本；另有 `48` 张缺 clothes 标签样本按当前 build 口径 skip。

### 2.2 上游 person 权重

- 上游 A：
  `backend-train-model/person-train-model/train-result/export/person_detect_yolov8_with_new_labels.pt`
- 上游 B：
  `backend-train-model/person-train-model/train-result/export/person_detect_yolov8_with_new_labels_and_hard_examples_v1.pt`

### 2.3 下游 clothes 初始化权重

- 初始化来源：
  `backend-train-model/new_clothes_train/train-result/artifacts/runs/clothes_merged_with_new_labels_v1_baseline/weights/best.pt`

---

## 3. prepared 统计对比

| 项目 | 上游 A `pred_pc_person_base` | 上游 B `pred_pc_person_hardv1` | 结论 |
| --- | ---: | ---: | --- |
| source images | 2961 | 2961 | 一致 |
| source boxes | 5265 | 5265 | 一致 |
| train images | 3645 | 3651 | B 略多 |
| val images | 792 | 789 | 接近 |
| test images | 799 | 799 | 一致 |
| positive_crops | 5151 | 5177 | B 略优 |
| fallback_fullframes | 85 | 62 | B 略优 |
| unmatched_boxes | 86 | 62 | B 略优 |
| images_without_person_detection | 13 | 11 | B 略优 |

### 3.1 prepared 阶段结论

当前 prepared 统计说明：

1. A / B 都已经能稳定生成正式可训练的 `personcrop` 数据集；
2. B 的优势主要体现在：
   - 有效 crop 更多；
   - fallback 更少；
   - unmatched 更少；
   - 无 person 检出图更少；
3. 因此从“上游 person 是否更有利于生成下游可训练样本”这一点看，B 已经领先于 A。

---

## 4. 下游训练评估对比

### 4.1 上游 A 对应 run：`pred_pc_clo_base`

| split | Precision | Recall | mAP50 | mAP75 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| val | 0.9890 | 0.9767 | 0.9893 | 0.9010 | 0.7444 |
| test | 0.9861 | 0.9804 | 0.9920 | 0.8744 | 0.7416 |

### 4.2 上游 B 对应 run：`pred_pc_clo_hardv1`

| split | Precision | Recall | mAP50 | mAP75 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| val | 0.9899 | 0.9826 | 0.9942 | 0.9120 | 0.7516 |
| test | 0.9982 | 0.9816 | 0.9943 | 0.8764 | 0.7471 |

### 4.3 评估阶段结论

1. A 与 B 都说明 `personcrop` 路线已经能稳定跑通，且结果都很强；
2. B 在 val / test 两侧都保持稳定小幅领先，不是只在单一 split 上偶然更高；
3. 因此当前更合理的阶段结论是：

> **保留 `pred_pc_clo_hardv1` 作为当前默认 candidate，保留 `pred_pc_clo_base` 作为稳定对照。**

---

## 5. 当前不直接下“主线切换完成”结论的原因

虽然 B 当前领先，但还不建议现在就把结论写成“`personcrop` 已正式完全替代 fullframe clothes 主线”。原因如下：

1. 当前 A / B 的评估样本空间已经是 `personcrop` 样本，不再与原始 fullframe 的“每张原图一个样本”严格同口径；
2. 还需要补做原图级 / 业务级复盘，确认收益是否真的集中体现在更贴近业务的 crowded / overlap / dense scenes；
3. 只有当“指标优势 + 原图业务收益”同时成立时，才更适合把 `personcrop` 升级为默认主线。

---

## 6. P0 执行状态

### 已完成

- [x] 确认 B 为当前默认 candidate；
- [x] 保留 A 为稳定对照；
- [x] 输出首轮 A/B 阶段结论表；
- [x] 启动原图级 / 业务级复盘清单（见下一份文档）。

对应复盘清单文档：

`backend-train-model/personcrop-train/train-result/review/personcrop原图级业务级复盘清单.md`

---

## 7. 下一步只做什么

下一阶段只建议优先做以下工作：

1. 原图级 / 业务级复盘；
2. 验证 B 的优势是否主要集中在 crowded / overlap / dense scenes；
3. 决定是否把 `pred_pc_clo_hardv1` 升级为默认 `personcrop` 主推进对象；
4. 暂不扩更多实验变量；
5. 暂不把 person hard examples 直接并入 clothes 训练。

---

## 8. 一句话阶段口径

> **当前 `personcrop` 首轮双上游 A/B 已完成，A 与 B 都证明路线成立；其中 B 在 prepared 统计与下游评估指标上均略优，因此当前保留 B 作为默认 candidate、A 作为稳定对照。下一阶段重点转向原图级 / 业务级复盘，而不是继续扩更多实验变量。**

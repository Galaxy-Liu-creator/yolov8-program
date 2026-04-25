# ROI-aware person 结果对比

## 文档维护约束

- 本文档专门用于记录 `person_fullframe`、`person_roi_aware`、`person_roi_aware_v2` 及后续新版本的训练 / 评估对比结果。
- **以后每次完成新的训练与评估后，都必须在本文档中新增一条新的对比记录。**
- 记录顺序固定为：**最新在前，历史在后**。
- 每条对比记录至少应包含：
  - 对比对象与对应 `dataset.yaml`
  - 初始化方式 / base model
  - `val` 与 `test` 的 Precision、Recall、mAP50、mAP75、mAP50-95
  - 必要的数据集统计差异
  - 最终结论与解读边界
- 如果不同版本使用的不是同一个 `dataset.yaml`，必须明确写出“不是严格同数据集公平对照”，避免把跨数据集结果误写成严格消融结论。

## 2026-04-25 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` 对比

### 1. 对比对象

| 版本 | run 名称 | 数据集 | 初始化方式 |
| --- | --- | --- | --- |
| `person_roi_aware_v3_mask_then_crop_margin64` | `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` | `train-result/prepared/person_roi_aware_v3_mask_then_crop_margin64/sequence_contiguous/dataset.yaml` | `person_fullframe_baseline/weights/best.pt` |
| `person_roi_aware_v2` | `person_roi_aware_v2_from_fullframe` | `train-result/prepared/person_roi_aware_v2/sequence_contiguous/dataset.yaml` | `person_fullframe_baseline/weights/best.pt` |
| `person_roi_aware` | `person_roi_aware_baseline` | `train-result/prepared/person_roi_aware/sequence_contiguous/dataset.yaml` | `backend-train-model/weights/yolov8n.pt` |
| `person_fullframe` | `person_fullframe_baseline` | `train-result/prepared/person_fullframe/sequence_contiguous/dataset.yaml` | 当前 train report 记录为 `resume_checkpoint`，`initial_base_model` 指向同 run 的 `last.pt` |

对应报告入口：

- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_train.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_eval.json`
- `backend-train-model/person-train-model/train-result/prepared/person_roi_aware_v3_mask_then_crop_margin64/sequence_contiguous/prepare_report.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_v2_from_fullframe_eval.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_baseline_eval.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_fullframe_baseline_eval.json`

### 2. 结果解读边界

- `person_fullframe` 与三版 ROI-aware 使用的不是同一个 `dataset.yaml`，因此 **fullframe vs ROI-aware** 仍然只能写成“当前分支级结果对比”，不能写成严格同数据集消融。
- `person_roi_aware_v3_mask_then_crop_margin64` 与 `person_roi_aware_v2` 也不是完全相同的 `dataset.yaml`；二者是不同 prepared 输出目录。
- 但 v3 与 v2 的 keep rule 相同、初始化方式相同、split 结构相同，核心变化主要是：
  - `mask_then_crop + crop_margin_px=64`
  - 对应的裁剪边界与 remap 后标签
- 因此 **v3 vs v2** 更接近“近似单因子工程对比”，但依然不应误写成绝对严格的同数据集公平消融。

### 3. Test 指标对比

| 版本 | Precision | Recall | mAP50 | mAP75 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `person_roi_aware_v3_mask_then_crop_margin64` | `0.9208` | `0.7075` | `0.7779` | `0.4578` | `0.4607` |
| `person_roi_aware_v2` | `0.9364` | `0.6957` | `0.7774` | `0.4414` | `0.4555` |
| `person_roi_aware` | `0.9390` | `0.5950` | `0.6738` | `0.4005` | `0.3867` |
| `person_fullframe` | `0.9228` | `0.6740` | `0.7606` | `0.4064` | `0.4102` |

### 4. Val 指标对比

| 版本 | Precision | Recall | mAP50 | mAP75 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `person_roi_aware_v3_mask_then_crop_margin64` | `0.9440` | `0.8011` | `0.8811` | `0.6133` | `0.5717` |
| `person_roi_aware_v2` | `0.8939` | `0.7912` | `0.8649` | `0.6493` | `0.5739` |
| `person_roi_aware` | `0.9831` | `0.7865` | `0.8725` | `0.5955` | `0.5509` |
| `person_fullframe` | `0.9677` | `0.8215` | `0.9134` | `0.6222` | `0.5691` |

### 5. ROI-aware 数据集统计对比

| 版本 | mode | crop margin | keep rule | 保留框 | 丢弃框 | 裁剪框 | 空负样本 |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| `person_roi_aware` | `mask_then_crop` | `0` | `center_inside == true` | `1343` | `315` | `49` | `12` |
| `person_roi_aware_v2` | `mask_then_crop` | `0` | `bottom_center_inside OR box_ioa >= 0.25` | `1342` | `316` | `54` | `14` |
| `person_roi_aware_v3_mask_then_crop_margin64` | `mask_then_crop` | `64` | `bottom_center_inside OR box_ioa >= 0.25` | `1335` | `316` | `23` | `15` |

可以看到：

- v3 最直接的工程效果是：`cropped_boxes` 从 `54` 明显下降到 `23`，减少了 `31` 个，降幅约 `57.4%`。
- v3 并不是通过“更多保留框”来换指标；它的保留框反而从 `1342` 变成 `1335`，空负样本从 `14` 增加到 `15`。
- 因此这次提升如果成立，更合理的解释是：**边界 crop 过紧问题被明显缓解了**，而不是简单放宽样本数量。

### 6. 增量对比

#### 6.1 `person_roi_aware_v3_mask_then_crop_margin64` 相比 `person_roi_aware_v2`（Test）

| 指标 | 增量 |
| --- | ---: |
| Precision | `-0.0156` |
| Recall | `+0.0119` |
| mAP50 | `+0.0004` |
| mAP75 | `+0.0164` |
| mAP50-95 | `+0.0052` |

相对变化：

- Precision：约 `-1.7%`
- Recall：约 `+1.7%`
- mAP50：约 `+0.1%`
- mAP75：约 `+3.7%`
- mAP50-95：约 `+1.1%`

这一组结果说明：**v3 相比 v2 是小幅改进，不是显著跃升。**

#### 6.2 `person_roi_aware_v3_mask_then_crop_margin64` 相比 `person_fullframe`（Test）

| 指标 | 增量 |
| --- | ---: |
| Precision | `-0.0020` |
| Recall | `+0.0335` |
| mAP50 | `+0.0172` |
| mAP75 | `+0.0514` |
| mAP50-95 | `+0.0505` |

相对变化：

- Precision：约 `-0.2%`
- Recall：约 `+5.0%`
- mAP50：约 `+2.3%`
- mAP75：约 `+12.6%`
- mAP50-95：约 `+12.3%`

说明当前 v3 在 native test 结果上依然明显强于 `person_fullframe_baseline`。

### 7. 训练过程补充信息

- `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe`
  - `results.csv` 中按 val `mAP50-95` 统计的 best epoch 约为 `168`
  - best val `mAP50-95` 约为 `0.5726`
  - 最终第 `180` 轮 val `mAP50-95` 约为 `0.5659`
- 这说明 v3 不是“前几轮偶然高点后快速崩掉”的 run，而是训练后期仍维持在和 v2 接近的稳定水平。

### 8. 最终结论

当前阶段更准确的结论建议写成下面这版：

1. `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` 在当前 native test 上拿到了四者中最高的 Recall 与 mAP50-95，因此可以视为**当前 test 领先的 ROI-aware 候选版本**。
2. 但它相对 `person_roi_aware_v2_from_fullframe` 的提升幅度很小：`mAP50-95` 仅提升 `0.0052`，Precision 还下降了 `0.0156`，因此**不能写成“显著优于 v2”**。
3. v3 最确定的正向收益，不是指标大幅跃升，而是它确实把 ROI-aware 边界正样本的 crop 截断问题显著缓解了：`cropped_boxes` 从 `54` 降到 `23`。
4. 因此当前最稳妥的工程口径应写成：
   - `person_fullframe_baseline` 继续保留为稳定上游初始化来源；
   - `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` 可以暂列为**当前 native test 领先但优势很小的 ROI-aware 候选版本**；
   - `person_roi_aware_v2_from_fullframe` 仍应保留为稳定备选，不建议直接删除或覆盖；
   - 如果后续还要确认这次 margin 的收益是否可靠，优先补做 `person_roi_aware_v3_crop_only_margin64` 对照，或只对 v2 / v3 里更优的一条再试 `imgsz=768`。

## 2026-04-24 `person_fullframe` / `person_roi_aware` / `person_roi_aware_v2` 对比

### 1. 对比对象

| 版本 | run 名称 | 数据集 | 初始化方式 |
| --- | --- | --- | --- |
| `person_fullframe` | `person_fullframe_baseline` | `train-result/prepared/person_fullframe/sequence_contiguous/dataset.yaml` | 当前 train report 记录为 `resume_checkpoint`，`initial_base_model` 指向同 run 的 `last.pt` |
| `person_roi_aware` | `person_roi_aware_baseline` | `train-result/prepared/person_roi_aware/sequence_contiguous/dataset.yaml` | `backend-train-model/weights/yolov8n.pt` |
| `person_roi_aware_v2` | `person_roi_aware_v2_from_fullframe` | `train-result/prepared/person_roi_aware_v2/sequence_contiguous/dataset.yaml` | `person_fullframe_baseline/weights/best.pt` |

对应报告入口：

- `backend-train-model/person-train-model/train-result/artifacts/reports/person_fullframe_baseline_eval.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_baseline_eval.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_v2_from_fullframe_eval.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_baseline_train.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_v2_from_fullframe_train.json`

### 2. 结果解读边界

- `person_fullframe` 与两版 ROI-aware 使用的不是同一个 `dataset.yaml`，因此 **fullframe vs ROI-aware** 只能作为“当前分支级结果对比”，不能直接当作严格同数据集消融。
- `person_roi_aware_v2` 相比 `person_roi_aware`，同时变化了两件事：
  - 数据规则从 v1 的 `center_inside` 变成 v2 的 `bottom_center_inside OR box_ioa >= 0.25`
  - 初始化方式从 `yolov8n.pt` 变成 `person_fullframe_baseline/weights/best.pt`
- 因此本次更准确的结论应写成：**“ROI-aware v2 数据集 + from_fullframe 初始化”这套组合目前效果最好。**

### 3. Test 指标对比

| 版本 | Precision | Recall | mAP50 | mAP75 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `person_fullframe` | `0.9228` | `0.6740` | `0.7606` | `0.4064` | `0.4102` |
| `person_roi_aware` | `0.9390` | `0.5950` | `0.6738` | `0.4005` | `0.3867` |
| `person_roi_aware_v2` | `0.9364` | `0.6957` | `0.7774` | `0.4414` | `0.4555` |

### 4. Val 指标对比

| 版本 | Precision | Recall | mAP50 | mAP75 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `person_fullframe` | `0.9677` | `0.8215` | `0.9134` | `0.6222` | `0.5691` |
| `person_roi_aware` | `0.9831` | `0.7865` | `0.8725` | `0.5955` | `0.5509` |
| `person_roi_aware_v2` | `0.8939` | `0.7912` | `0.8649` | `0.6493` | `0.5739` |

### 5. ROI-aware 数据集统计对比

| 版本 | keep rule | 保留框 | 丢弃框 | 裁剪框 | 空负样本 |
| --- | --- | ---: | ---: | ---: | ---: |
| `person_roi_aware` | `center_inside == true` | `1343` | `315` | `49` | `12` |
| `person_roi_aware_v2` | `bottom_center_inside OR box_ioa >= 0.25` | `1342` | `316` | `54` | `14` |

可以看到：

- v2 并没有通过“大量放宽样本数量”来换指标；它和 v1 的保留框数量非常接近。
- v2 空负样本从 `12` 增加到 `14`，裁剪框从 `49` 增加到 `54`，说明它更多是在边界处理与训练初始化上发生了变化，而不是把 ROI-aware 分支彻底变回 fullframe。

### 6. 增量对比

#### 6.1 `person_roi_aware_v2` 相比 `person_roi_aware`

| 指标 | 增量 |
| --- | ---: |
| Precision | `-0.0026` |
| Recall | `+0.1006` |
| mAP50 | `+0.1036` |
| mAP75 | `+0.0408` |
| mAP50-95 | `+0.0688` |

相对提升：

- Recall：约 `+16.9%`
- mAP50：约 `+15.4%`
- mAP50-95：约 `+17.8%`

这一组提升已经可以视为**明显改进**，其中最关键的是 recall 回升很明显，不再像 v1 ROI-aware 那样主要卡在漏检。

#### 6.2 `person_roi_aware_v2` 相比 `person_fullframe`

| 指标 | 增量 |
| --- | ---: |
| Precision | `+0.0136` |
| Recall | `+0.0216` |
| mAP50 | `+0.0168` |
| mAP75 | `+0.0349` |
| mAP50-95 | `+0.0453` |

相对提升：

- Recall：约 `+3.2%`
- mAP50：约 `+2.2%`
- mAP50-95：约 `+11.1%`

说明当前 `person_roi_aware_v2_from_fullframe` 在自己的 native 结果上，已经不仅优于旧版 ROI-aware，也优于当前 fullframe baseline。

### 7. 训练过程补充信息

- `person_fullframe_baseline`
  - 当前 best epoch（按 `results.csv` 中 val `mAP50-95` 最大）约为 `151`
- `person_roi_aware_baseline`
  - 当前 best epoch 约为 `83`
  - 初始化为 `backend-train-model/weights/yolov8n.pt`
- `person_roi_aware_v2_from_fullframe`
  - 当前 best epoch 约为 `135`
  - 初始化为 `person_fullframe_baseline/weights/best.pt`

这说明 v2 不是“更早过拟合后偶然撞上 test 集”，而是在较长训练过程中稳定收敛到更高的最终质量。

### 8. 最终结论

当前阶段的结论建议写成下面这版：

1. `person_roi_aware_baseline` 明显弱于 `person_fullframe_baseline`，其主要问题是 recall 过低。
2. `person_roi_aware_v2_from_fullframe` 明显优于历史 `person_roi_aware_baseline`，尤其体现在 recall、mAP50、mAP50-95 的同步提升。
3. 从当前 native 结果看，`person_roi_aware_v2_from_fullframe` 也是三者中效果最好的版本。
4. 但由于 `person_fullframe` 与 ROI-aware 分支不共用同一个 `dataset.yaml`，因此“v2 优于 fullframe”应表述为**当前分支级结果领先**，而不是严格同数据集公平对照。
5. 当前最稳妥的工程结论是：
   - `person_fullframe_baseline` 继续保留为稳定上游初始化来源；
   - `person_roi_aware_v2_from_fullframe` 作为当前最佳 ROI-aware person 模型；
   - `person_roi_aware_baseline` 保留为历史对照，不再建议作为默认 ROI-aware 上游。

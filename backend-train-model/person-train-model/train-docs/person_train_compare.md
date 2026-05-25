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

## 2026-05-04 `person_fullframe_with_new_labels_baseline` 对比

### 1. 对比对象

| 版本 | run 名称 | 数据集 | 初始化方式 |
| --- | --- | --- | --- |
| `person_fullframe_with_new_labels` | `person_fullframe_with_new_labels_baseline` | `train-result/prepared/person_fullframe_with_new_labels/sequence_contiguous/dataset.yaml` | 当前 train report 记录为 `resume_checkpoint`；`initial_base_model` 指向同 run 的 `last.pt` |
| `person_fullframe` | `person_fullframe_baseline` | `train-result/prepared/person_fullframe/sequence_contiguous/dataset.yaml` | 当前 train report 记录为 `resume_checkpoint`，`initial_base_model` 指向同 run 的 `last.pt` |

对应报告入口：

- `backend-train-model/person-train-model/train-result/artifacts/reports/person_fullframe_with_new_labels_baseline/person_fullframe_with_new_labels_baseline_train.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_fullframe_with_new_labels_baseline/person_fullframe_with_new_labels_baseline_eval.json`
- `backend-train-model/person-train-model/train-result/prepared/person_fullframe_with_new_labels/sequence_contiguous/prepare_report.json`
- `backend-train-model/person-train-model/train-result/person_source_dataset_summary_fullframe_with_new_labels.json`

### 2. 结果解读边界

- `person_fullframe_with_new_labels` 与旧 `person_fullframe` 不是同一个 `dataset.yaml`，因此这组对比不是严格同数据集公平消融，更适合写成“扩样前后 fullframe 分支的实际收益”。
- 本次新样本合并后，训练集规模从 `502` 张扩展到 `3009` 张，`person` 框从 `1658` 个扩展到 `8861` 个；因此指标变化既包含数据扩样收益，也包含新样本域带来的难度变化。
- 当前 report 里出现的 `E:\...` 绝对路径，是训练机器上的历史元数据，不影响已经保存的 metric 数值；跨机器复跑时应改用当前机器路径或仓库内配置入口。

### 3. Test 指标对比

| 版本 | Precision | Recall | mAP50 | mAP75 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `person_fullframe_with_new_labels` | `0.9304` | `0.8552` | `0.9054` | `0.4527` | `0.4802` |
| `person_fullframe` | `0.9228` | `0.6740` | `0.7606` | `0.4064` | `0.4102` |

### 4. Val 指标对比

| 版本 | Precision | Recall | mAP50 | mAP75 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `person_fullframe_with_new_labels` | `0.9554` | `0.9067` | `0.9517` | `0.4910` | `0.5095` |
| `person_fullframe` | `0.9677` | `0.8215` | `0.9134` | `0.6222` | `0.5691` |

### 5. 数据集统计对比

| 版本 | images | boxes | train | val | test | empty labels |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `person_fullframe_with_new_labels` | `3009` | `8861` | `2105` | `453` | `451` | `13` |
| `person_fullframe` | `502` | `1658` | `350` | `77` | `75` | `8` |

可以看到：

- 新增样本带来的数据量提升非常明显，图像数增加了 `2507` 张，框数增加了 `7203` 个。
- 这次提升最直接体现在 `test Recall`、`mAP50`、`mAP50-95`，说明扩样后模型对更多 person 形态有了更强覆盖。
- 但 `test mAP50-95 = 0.4802` 仍然不算高，`mAP75 = 0.4527` 也偏低，说明**高 IoU 下的定位精度仍是当前短板**，尤其是小目标、远景、遮挡与边界框贴合度。

### 6. 增量对比

#### 6.1 `person_fullframe_with_new_labels` 相比 `person_fullframe`（Test）

| 指标 | 增量 |
| --- | ---: |
| Precision | `+0.0076` |
| Recall | `+0.1812` |
| mAP50 | `+0.1448` |
| mAP75 | `+0.0463` |
| mAP50-95 | `+0.0700` |

相对变化：

- Precision：约 `+0.8%`
- Recall：约 `+26.9%`
- mAP50：约 `+19.0%`
- mAP75：约 `+11.4%`
- mAP50-95：约 `+17.1%`

这说明这次扩样不是“只提升一点点”，而是确实把 fullframe 分支的整体覆盖能力拉上来了；但如果把重点放在小目标和高 IoU 框质量上，当前结果仍然属于“有明显进步，但离很强还有距离”。

### 7. 当前对小目标的迭代建议

当前这个结果最值得继续追的不是单纯再堆训练轮数，而是围绕 **高 IoU 定位误差** 做单因子实验，优先顺序建议如下：

1. **先提输入分辨率**：在同一数据集上做 `imgsz=640 -> 768 -> 960` 的单因子对照；小目标最直接的收益通常来自更多像素。
2. **再做难样本补齐**：把远景、遮挡、逆光、半身、密集人群、极小框序列单独做 hard set，优先补 `D15_20260119061405`、`D15_20260119203927`、`D02_20260123074836`、`D02_20260123070624` 这类难序列。
3. **提高定位能力而不是只堆 recall**：训练后期适当减弱过强的数据增强，尽量保留更多局部细节；必要时用更高容量模型做第二阶段对照。
4. **如果小目标集中在固定区域，考虑局部裁切 / 切片分支**：对超小人或密集区，局部 crop + 保留上下文通常比继续放大全图更有效。

### 8. 最终结论

1. `person_fullframe_with_new_labels_baseline` 相比旧 `person_fullframe_baseline` 是一次**明确有效的扩样提升**，尤其在 `Recall` 和 `mAP50-95` 上有明显进步。
2. 但 `mAP50-95 = 0.4802` 还没有到“很强”的程度；如果你的重点是小目标和高 IoU 框质量，当前瓶颈已经从“有没有检测到”转向“框是否足够准”。
3. 所以下一轮不建议继续只看总指标，而应优先围绕 **分辨率、难样本、定位能力、局部裁切** 这四个方向做单因子对照。

## 2026-04-28 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768` 对比

### 1. 对比对象

| 版本 | run 名称 | 数据集 | 初始化方式 |
| --- | --- | --- | --- |
| `person_roi_aware_v3_mask_then_crop_margin64_img768` | `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768` | `train-result/prepared/person_roi_aware_v3_mask_then_crop_margin64/sequence_contiguous/dataset.yaml` | 当前 train report 记录为 `resume_checkpoint`；同一 run 的 `last.pt` 严格续训完成 |
| `person_roi_aware_v3_mask_then_crop_margin64` | `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` | `train-result/prepared/person_roi_aware_v3_mask_then_crop_margin64/sequence_contiguous/dataset.yaml` | `person_fullframe_baseline/weights/best.pt` |
| `person_roi_aware_v2` | `person_roi_aware_v2_from_fullframe` | `train-result/prepared/person_roi_aware_v2/sequence_contiguous/dataset.yaml` | `person_fullframe_baseline/weights/best.pt` |
| `person_roi_aware_v3_crop_only_margin64` | `person_roi_aware_v3_crop_only_margin64_from_fullframe` | `train-result/prepared/person_roi_aware_v3_crop_only_margin64/sequence_contiguous/dataset.yaml` | `person_fullframe_baseline/weights/best.pt` |
| `person_fullframe` | `person_fullframe_baseline` | `train-result/prepared/person_fullframe/sequence_contiguous/dataset.yaml` | 当前 train report 记录为 `resume_checkpoint`，`initial_base_model` 指向同 run 的 `last.pt` |

对应报告入口：

- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768_train.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768_eval.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_eval.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_v2_from_fullframe/person_roi_aware_v2_from_fullframe_eval.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_v3_crop_only_margin64_from_fullframe/person_roi_aware_v3_crop_only_margin64_from_fullframe_eval.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_fullframe_baseline/person_fullframe_baseline_eval.json`
- `backend-train-model/person-train-model/train-result/prepared/person_roi_aware_v3_mask_then_crop_margin64/sequence_contiguous/prepare_report.json`

### 2. 结果解读边界

- `person_fullframe` 与 ROI-aware 各分支仍然不是同一个 `dataset.yaml`，因此 **fullframe vs ROI-aware** 仍然只能写成“当前分支级结果对比”，不能写成严格同数据集公平消融。
- `person_roi_aware_v3_mask_then_crop_margin64_img768` 与 `person_roi_aware_v3_mask_then_crop_margin64` 使用的是**同一个** prepared 数据集、同一个 keep rule、同一个 `crop_margin_px=64`、同一个 split 结构，因此这组对比已经很接近“训练配置单因子对比”。
- 但它依然不是绝对纯净的单因子消融，因为这轮变化同时包含：
  - train `imgsz: 640 -> 768`
  - train `batch: 4 -> 2`
  - 训练中途被打断后，又从同一 run 的 `last.pt` 严格续训到完成
- 本节 `val / test` 指标表统一来自各 run 的 `_eval.json`，因此遵循同一套 native eval 口径；`results.csv` 只放到“训练过程补充信息”中，不直接替代表格里的对比指标。

### 3. Test 指标对比

| 版本 | Precision | Recall | mAP50 | mAP75 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `person_roi_aware_v3_mask_then_crop_margin64_img768` | `0.9663` | `0.6435` | `0.7535` | `0.4119` | `0.4399` |
| `person_roi_aware_v3_mask_then_crop_margin64` | `0.9208` | `0.7075` | `0.7779` | `0.4578` | `0.4607` |
| `person_roi_aware_v2` | `0.9364` | `0.6957` | `0.7774` | `0.4414` | `0.4555` |
| `person_roi_aware_v3_crop_only_margin64` | `0.7955` | `0.6766` | `0.7432` | `0.4589` | `0.4521` |
| `person_fullframe` | `0.9228` | `0.6740` | `0.7606` | `0.4064` | `0.4102` |

### 4. Val 指标对比

| 版本 | Precision | Recall | mAP50 | mAP75 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `person_roi_aware_v3_mask_then_crop_margin64_img768` | `0.9195` | `0.8205` | `0.8672` | `0.6055` | `0.5527` |
| `person_roi_aware_v3_mask_then_crop_margin64` | `0.9440` | `0.8011` | `0.8811` | `0.6133` | `0.5717` |
| `person_roi_aware_v2` | `0.8939` | `0.7912` | `0.8649` | `0.6493` | `0.5739` |
| `person_roi_aware_v3_crop_only_margin64` | `0.9557` | `0.7956` | `0.8737` | `0.6368` | `0.5746` |
| `person_fullframe` | `0.9677` | `0.8215` | `0.9134` | `0.6222` | `0.5691` |

### 5. ROI-aware 数据集统计对比

| 版本 | mode | crop margin | keep rule | 保留框 | 丢弃框 | 裁剪框 | 空负样本 |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| `person_roi_aware_v2` | `mask_then_crop` | `0` | `bottom_center_inside OR box_ioa >= 0.25` | `1342` | `316` | `54` | `14` |
| `person_roi_aware_v3_mask_then_crop_margin64` | `mask_then_crop` | `64` | `bottom_center_inside OR box_ioa >= 0.25` | `1335` | `316` | `23` | `15` |
| `person_roi_aware_v3_mask_then_crop_margin64_img768` | `mask_then_crop` | `64` | `bottom_center_inside OR box_ioa >= 0.25` | `1335` | `316` | `23` | `15` |
| `person_roi_aware_v3_crop_only_margin64` | `crop_only` | `64` | `bottom_center_inside OR box_ioa >= 0.25` | `1335` | `316` | `23` | `15` |

可以看到：

- `img768` 与当前 `640` 主线在数据集统计上完全一致，因此这一轮差异主要来自**训练配置变化**，而不是样本数量变化。
- `img768` 与 `640` 主线共享同一套 `mask_then_crop + margin64` 数据集，所以这轮结果不能解释为“边界 crop 又变差了”；它更像是**更高训练输入尺寸没有转化成更好的 native test 泛化**。
- 相比 v2，`img768` 这轮并没有带来新的数据侧收益；`cropped_boxes` 仍然是 `23`，说明 `margin64` 本身的工程收益已经保留了下来。

### 6. 增量对比

#### 6.1 `person_roi_aware_v3_mask_then_crop_margin64_img768` 相比 `person_roi_aware_v3_mask_then_crop_margin64`（Test）

| 指标 | 增量 |
| --- | ---: |
| Precision | `+0.0455` |
| Recall | `-0.0640` |
| mAP50 | `-0.0244` |
| mAP75 | `-0.0459` |
| mAP50-95 | `-0.0208` |

相对变化：

- Precision：约 `+4.9%`
- Recall：约 `-9.0%`
- mAP50：约 `-3.1%`
- mAP75：约 `-10.0%`
- mAP50-95：约 `-4.5%`

这说明 `imgsz=768, batch=2` 并没有打赢当前 `640 / batch=4` 主线；它只把 Precision 顶高了，但 Recall 和各段 mAP 都掉了。

#### 6.2 `person_roi_aware_v3_mask_then_crop_margin64_img768` 相比 `person_roi_aware_v2`（Test）

| 指标 | 增量 |
| --- | ---: |
| Precision | `+0.0299` |
| Recall | `-0.0522` |
| mAP50 | `-0.0239` |
| mAP75 | `-0.0295` |
| mAP50-95 | `-0.0156` |

相对变化：

- Precision：约 `+3.2%`
- Recall：约 `-7.5%`
- mAP50：约 `-3.1%`
- mAP75：约 `-6.7%`
- mAP50-95：约 `-3.4%`

这说明 `img768` 也没有优于 `person_roi_aware_v2_from_fullframe`；因此“放大训练输入尺寸”这一步并没有带来比当前 v2 / v3 更好的 native test 收益。

#### 6.3 `person_roi_aware_v3_mask_then_crop_margin64_img768` 相比 `person_fullframe`（Test）

| 指标 | 增量 |
| --- | ---: |
| Precision | `+0.0435` |
| Recall | `-0.0305` |
| mAP50 | `-0.0071` |
| mAP75 | `+0.0055` |
| mAP50-95 | `+0.0297` |

相对变化：

- Precision：约 `+4.7%`
- Recall：约 `-4.5%`
- mAP50：约 `-0.9%`
- mAP75：约 `+1.4%`
- mAP50-95：约 `+7.2%`

因此 `img768` 仍然不能写成“全面不如 fullframe”；它在 Precision 和 mAP50-95 上仍有分支级收益，但相较当前最佳 ROI-aware 主线并没有形成更优结论。

### 7. 训练过程补充信息

- `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768`
  - 当前 train report 记录为：从同一 run 的 `last.pt` 严格续训完成
  - `results.csv` 中按 train-time val `mAP50-95` 统计的 best epoch 约为 `139`
  - best val `mAP50-95` 约为 `0.5773`
  - 最终第 `180` 轮 val `mAP50-95` 约为 `0.5607`
- `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe`
  - `results.csv` 中按 val `mAP50-95` 统计的 best epoch 约为 `168`
  - best val `mAP50-95` 约为 `0.5726`

这说明：

- `img768` 在 train-time val 的最高点并不低，甚至略高于当前 `640` 主线的 `0.5726`。
- 但这个更高的 train-time val 最高点，并没有转化成更好的统一 native eval `val / test` 结果；尤其 native test `mAP50-95` 从 `0.4607` 回落到了 `0.4399`。
- 因此这轮实验更支持这样一个判断：**当前这条 ROI-aware 分支的瓶颈并不在于“把训练输入尺寸继续放大”本身。**

### 8. 最终结论

当前阶段更准确的结论建议写成下面这版：

1. `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768` 没有成为当前最佳 ROI-aware 路线；它的 native test Precision 更高，但 Recall、mAP50、mAP75、mAP50-95 都低于当前 `640 / batch=4` 主线。
2. 它也没有优于 `person_roi_aware_v2_from_fullframe`，因此“先对更优版本试 `imgsz=768, batch=2`”这一步已经完成，而且结果**不支持**把更大输入尺寸升级为默认主线。
3. 由于 `img768` 与当前 `640` 主线的数据集统计完全一致，这轮结论更偏向训练配置层面：**更高训练输入尺寸没有转化成更好的 native test 泛化。**
4. 当前更稳妥的工程口径应写成：
   - `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe`：当前默认主线 ROI-aware 候选版本；
   - `person_roi_aware_v2_from_fullframe`：稳定备选；
   - `person_roi_aware_v3_crop_only_margin64_from_fullframe`：已完成的对照实验，不建议作为默认主线；
   - `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768`：已完成的训练配置对照实验，不建议作为默认主线。

## 2026-04-27 `person_roi_aware_v3_crop_only_margin64_from_fullframe` 对比

### 1. 对比对象

| 版本 | run 名称 | 数据集 | 初始化方式 |
| --- | --- | --- | --- |
| `person_roi_aware_v3_crop_only_margin64` | `person_roi_aware_v3_crop_only_margin64_from_fullframe` | `train-result/prepared/person_roi_aware_v3_crop_only_margin64/sequence_contiguous/dataset.yaml` | `person_fullframe_baseline/weights/best.pt` |
| `person_roi_aware_v3_mask_then_crop_margin64` | `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` | `train-result/prepared/person_roi_aware_v3_mask_then_crop_margin64/sequence_contiguous/dataset.yaml` | `person_fullframe_baseline/weights/best.pt` |
| `person_roi_aware_v2` | `person_roi_aware_v2_from_fullframe` | `train-result/prepared/person_roi_aware_v2/sequence_contiguous/dataset.yaml` | `person_fullframe_baseline/weights/best.pt` |
| `person_roi_aware` | `person_roi_aware_baseline` | `train-result/prepared/person_roi_aware/sequence_contiguous/dataset.yaml` | `backend-train-model/weights/yolov8n.pt` |
| `person_fullframe` | `person_fullframe_baseline` | `train-result/prepared/person_fullframe/sequence_contiguous/dataset.yaml` | 当前 train report 记录为 `resume_checkpoint`，`initial_base_model` 指向同 run 的 `last.pt` |

对应报告入口：

- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_v3_crop_only_margin64_from_fullframe/person_roi_aware_v3_crop_only_margin64_from_fullframe_train.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_v3_crop_only_margin64_from_fullframe/person_roi_aware_v3_crop_only_margin64_from_fullframe_eval.json`
- `backend-train-model/person-train-model/train-result/prepared/person_roi_aware_v3_crop_only_margin64/sequence_contiguous/prepare_report.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_eval.json`
- `backend-train-model/person-train-model/train-result/prepared/person_roi_aware_v3_mask_then_crop_margin64/sequence_contiguous/prepare_report.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_v2_from_fullframe/person_roi_aware_v2_from_fullframe_eval.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_baseline/person_roi_aware_baseline_eval.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_fullframe_baseline/person_fullframe_baseline_eval.json`

### 2. 结果解读边界

- `person_fullframe` 与各版 ROI-aware 仍然不是同一个 `dataset.yaml`，因此 **fullframe vs ROI-aware** 仍然只能写成“当前分支级结果对比”，不能写成严格同数据集消融。
- `person_roi_aware_v3_crop_only_margin64` 与 `person_roi_aware_v3_mask_then_crop_margin64` 的 prepared 输出目录不同，但两者：
  - keep rule 相同
  - crop margin 相同
  - split 结构相同
  - 保留框 / 丢弃框 / 裁剪框 / 空负样本统计完全相同
- 因此 **crop_only vs mask_then_crop** 是当前最接近“单因子图像处理流程对比”的一组实验；主要变化不是标签数量，而是 ROI 外像素是否置黑。
- `person_roi_aware_v3_crop_only_margin64` 相比 `person_roi_aware_v2` 则同时变化了两件事：
  - `crop_only` 替代 `mask_then_crop`
  - `crop_margin_px=64` 替代 `0`

### 3. Test 指标对比

| 版本 | Precision | Recall | mAP50 | mAP75 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `person_roi_aware_v3_crop_only_margin64` | `0.7955` | `0.6766` | `0.7432` | `0.4589` | `0.4521` |
| `person_roi_aware_v3_mask_then_crop_margin64` | `0.9208` | `0.7075` | `0.7779` | `0.4578` | `0.4607` |
| `person_roi_aware_v2` | `0.9364` | `0.6957` | `0.7774` | `0.4414` | `0.4555` |
| `person_roi_aware` | `0.9390` | `0.5950` | `0.6738` | `0.4005` | `0.3867` |
| `person_fullframe` | `0.9228` | `0.6740` | `0.7606` | `0.4064` | `0.4102` |

### 4. Val 指标对比

| 版本 | Precision | Recall | mAP50 | mAP75 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `person_roi_aware_v3_crop_only_margin64` | `0.9557` | `0.7956` | `0.8737` | `0.6368` | `0.5746` |
| `person_roi_aware_v3_mask_then_crop_margin64` | `0.9440` | `0.8011` | `0.8811` | `0.6133` | `0.5717` |
| `person_roi_aware_v2` | `0.8939` | `0.7912` | `0.8649` | `0.6493` | `0.5739` |
| `person_roi_aware` | `0.9831` | `0.7865` | `0.8725` | `0.5955` | `0.5509` |
| `person_fullframe` | `0.9677` | `0.8215` | `0.9134` | `0.6222` | `0.5691` |

### 5. ROI-aware 数据集统计对比

| 版本 | mode | crop margin | keep rule | 保留框 | 丢弃框 | 裁剪框 | 空负样本 |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| `person_roi_aware_v2` | `mask_then_crop` | `0` | `bottom_center_inside OR box_ioa >= 0.25` | `1342` | `316` | `54` | `14` |
| `person_roi_aware_v3_mask_then_crop_margin64` | `mask_then_crop` | `64` | `bottom_center_inside OR box_ioa >= 0.25` | `1335` | `316` | `23` | `15` |
| `person_roi_aware_v3_crop_only_margin64` | `crop_only` | `64` | `bottom_center_inside OR box_ioa >= 0.25` | `1335` | `316` | `23` | `15` |

可以看到：

- `crop_only` 与 `mask_then_crop` 这两条 v3 路线在标签统计上完全一致，因此它们的结果差异主要来自**图像像素内容**，而不是样本数量变化。
- 相比 v2，两条 v3 路线都把 `cropped_boxes` 从 `54` 降到 `23`；这说明 `margin64` 对缓解边界裁剪问题本身是有效的。
- 但 `crop_only` 并没有把这种工程收益转化成更好的最终 test 指标。

### 6. 增量对比

#### 6.1 `person_roi_aware_v3_crop_only_margin64` 相比 `person_roi_aware_v3_mask_then_crop_margin64`（Test）

| 指标 | 增量 |
| --- | ---: |
| Precision | `-0.1253` |
| Recall | `-0.0309` |
| mAP50 | `-0.0347` |
| mAP75 | `+0.0011` |
| mAP50-95 | `-0.0086` |

相对变化：

- Precision：约 `-13.6%`
- Recall：约 `-4.4%`
- mAP50：约 `-4.5%`
- mAP75：约 `+0.2%`
- mAP50-95：约 `-1.9%`

这说明在**几乎相同的标签 / crop 边界条件**下，`crop_only` 并没有优于 `mask_then_crop`；它只在 `mAP75` 上有极小优势，其余关键 test 指标都落后。

#### 6.2 `person_roi_aware_v3_crop_only_margin64` 相比 `person_roi_aware_v2`（Test）

| 指标 | 增量 |
| --- | ---: |
| Precision | `-0.1408` |
| Recall | `-0.0191` |
| mAP50 | `-0.0342` |
| mAP75 | `+0.0175` |
| mAP50-95 | `-0.0034` |

相对变化：

- Precision：约 `-15.0%`
- Recall：约 `-2.7%`
- mAP50：约 `-4.4%`
- mAP75：约 `+4.0%`
- mAP50-95：约 `-0.8%`

这说明 `crop_only + margin64` 也没有打赢 `person_roi_aware_v2_from_fullframe`。

#### 6.3 `person_roi_aware_v3_crop_only_margin64` 相比 `person_fullframe`（Test）

| 指标 | 增量 |
| --- | ---: |
| Precision | `-0.1272` |
| Recall | `+0.0025` |
| mAP50 | `-0.0174` |
| mAP75 | `+0.0525` |
| mAP50-95 | `+0.0419` |

相对变化：

- Precision：约 `-13.8%`
- Recall：约 `+0.4%`
- mAP50：约 `-2.3%`
- mAP75：约 `+12.9%`
- mAP50-95：约 `+10.2%`

因此 `crop_only` 不能写成“全面优于 fullframe”；它更像是在高 IoU 段仍有一定收益，但 Precision 和 mAP50 明显掉得更多。

### 7. 训练过程补充信息

- `person_roi_aware_v3_crop_only_margin64_from_fullframe`
  - `results.csv` 中按 val `mAP50-95` 统计的 best epoch 约为 `72`
  - best val `mAP50-95` 约为 `0.5734`
  - 最终停在第 `132` 轮，最后一轮 val `mAP50-95` 约为 `0.5638`
- `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe`
  - best epoch 约为 `168`
  - best val `mAP50-95` 约为 `0.5726`

这说明 `crop_only` 在 val 上并没有明显崩掉，甚至 val `mAP50-95` 略高于 `mask_then_crop`；但这种优势并没有转化成更好的 native test 结果。

### 8. 最终结论

当前阶段更准确的结论建议写成下面这版：

1. `crop_only + margin64` 没有成为当前最佳 ROI-aware 路线；在 test 上它落后于 `mask_then_crop + margin64`，也略落后于 `person_roi_aware_v2_from_fullframe`。
2. 因为 `crop_only` 与 `mask_then_crop` 这组对照几乎只差 ROI 外像素是否置黑，所以这轮结果更支持这样一个判断：**在当前数据与业务语义下，保留 ROI 外真实像素并没有带来收益，反而更可能引入可见干扰。**
3. `margin64` 本身仍然是有价值的，因为两条 v3 路线都把裁剪框从 `54` 降到了 `23`；但更优的落地形式是：`mask_then_crop + margin64`，而不是 `crop_only + margin64`。
4. 因此当前最稳妥的工程排序应写成：
   - `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe`：当前首选 ROI-aware 候选版本；
   - `person_roi_aware_v2_from_fullframe`：稳定备选；
   - `person_roi_aware_v3_crop_only_margin64_from_fullframe`：已完成的对照实验版本，不建议作为默认主线。

## 2026-04-25 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` 对比

### 1. 对比对象

| 版本 | run 名称 | 数据集 | 初始化方式 |
| --- | --- | --- | --- |
| `person_roi_aware_v3_mask_then_crop_margin64` | `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` | `train-result/prepared/person_roi_aware_v3_mask_then_crop_margin64/sequence_contiguous/dataset.yaml` | `person_fullframe_baseline/weights/best.pt` |
| `person_roi_aware_v2` | `person_roi_aware_v2_from_fullframe` | `train-result/prepared/person_roi_aware_v2/sequence_contiguous/dataset.yaml` | `person_fullframe_baseline/weights/best.pt` |
| `person_roi_aware` | `person_roi_aware_baseline` | `train-result/prepared/person_roi_aware/sequence_contiguous/dataset.yaml` | `backend-train-model/weights/yolov8n.pt` |
| `person_fullframe` | `person_fullframe_baseline` | `train-result/prepared/person_fullframe/sequence_contiguous/dataset.yaml` | 当前 train report 记录为 `resume_checkpoint`，`initial_base_model` 指向同 run 的 `last.pt` |

对应报告入口：

- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_train.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_eval.json`
- `backend-train-model/person-train-model/train-result/prepared/person_roi_aware_v3_mask_then_crop_margin64/sequence_contiguous/prepare_report.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_v2_from_fullframe/person_roi_aware_v2_from_fullframe_eval.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_baseline/person_roi_aware_baseline_eval.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_fullframe_baseline/person_fullframe_baseline_eval.json`

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

- `backend-train-model/person-train-model/train-result/artifacts/reports/person_fullframe_baseline/person_fullframe_baseline_eval.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_baseline/person_roi_aware_baseline_eval.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_v2_from_fullframe/person_roi_aware_v2_from_fullframe_eval.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_baseline/person_roi_aware_baseline_train.json`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_v2_from_fullframe/person_roi_aware_v2_from_fullframe_train.json`

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


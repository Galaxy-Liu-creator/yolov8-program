# 阶段 PPT 汇报素材

## 使用说明

- 本文按 `backend-train-model/docs/大创PPT汇报.pptx` 当前的 10 页结构整理，方便直接对照现有 PPT 改稿。
- **上一阶段汇报已经覆盖了 `person_fullframe_baseline` 与 `ROI-aware person` 初版跑通。** 因此本轮文档只写承接后的增量进展，默认从 `person_roi_aware_v2_from_fullframe` 开始讲。
- 现有 `大创PPT汇报.pptx` 里很多 person 文案还停留在“ROI-aware 初版刚跑通”的阶段，下面内容的核心任务，就是把它改成“接着上次继续汇报”的版本。
- 如果时间有限，优先改 `Slide 4 / Slide 5 / Slide 7 / Slide 8 / Slide 10`。

## Slide 1 封面页

- 标题继续使用：`工服穿戴阶段汇报`
- 副标题建议改成：
  - `本阶段重点：ROI-aware v2/v3迭代、关键FN复盘、下一轮优化方向确认`

## Slide 2 目录页

- 目录结构继续保留三段式：
  - `本阶段进展`
  - `问题与缺陷`
  - `改进方案`
- 这一页不需要大改，主要改后面的具体内容。

## Slide 3 过渡页

- 标题保留：`本阶段进展`

## Slide 4 后端模型训练进展

这一页要体现“承接上次”的关系，不要再把 ROI-aware 初版跑通写成这次新进展。

### 建议正文

- 承接上次已经完成的 `person_fullframe_baseline` 与 `ROI-aware person` 初版验证，本阶段主要从 `person_roi_aware_v2_from_fullframe` 继续推进。
- `person_roi_aware_v2_from_fullframe` test 指标为：
  - Precision `0.9364`
  - Recall `0.6957`
  - mAP50 `0.7774`
  - mAP50-95 `0.4555`
- 在 v2 基础上，本阶段进一步完成了 `ROI-aware v3 mask_then_crop + crop_margin_px=64`：
  - test Precision `0.9208`
  - test Recall `0.7075`
  - test mAP50 `0.7779`
  - test mAP50-95 `0.4607`
- 同时完成两条对照实验：
  - `person_roi_aware_v3_crop_only_margin64_from_fullframe`
  - `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768`
- 本阶段还补齐了逐图诊断能力：
  - `analyze_person_fpfn.py`
  - `review_person_roi_failures.py`
  - ROI keep-positive 裁边复盘
  - hard FN 分桶复盘

### 这一页口播建议

- 上次我们已经证明 ROI-aware 路线是能跑通的，这次不再重复讲“能不能做”，而是继续讲“在 v2 之后怎么优化、优化后问题还剩什么”。
- 所以这一阶段的重点不是从零搭建，而是围绕 v2 往后做版本迭代、对照实验和问题诊断。

### 推荐配图

- `../person-train-model/train-result/artifacts/runs/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe/results.png`
- 如果还想保留 clothes 线，只补一张：
  - `../All-train-model/artifacts/runs/clothes_merged_v2_balanced_from_first_holdout_v1/results.png`

## Slide 5 训练成果展示

这一页建议明确写成“本阶段从 v2 到 v3 的结果变化”，而不是再写早期 ROI-aware 初版成果。

### 建议正文

- 本阶段最核心的结果，不是再次完成 ROI-aware 路线跑通，而是确认了 `v2 -> v3` 的升级收益和边界。
- `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` 相比 `v2`：
  - test Recall：`0.6957 -> 0.7075`
  - test mAP50-95：`0.4555 -> 0.4607`
  - keep-positive 裁边框：`54 -> 23`
- 这说明 `margin64` 在工程上明显缓解了裁边问题，但指标提升幅度并不大，当前已经进入“小步优化”阶段。
- 另外两条本阶段已完成的对照实验没有优于当前主线：
  - `crop_only + margin64` 未优于 `mask_then_crop + margin64`
  - `imgsz=768` 虽然 Precision 更高，但 Recall 和 mAP 回落
- 因此，当前默认主线仍是：
  - `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe`
  - `person_roi_aware_v2_from_fullframe` 保留为稳定备选

### 这一页口播建议

- 这次最重要的不是把数值拉高很多，而是把“当前最优版本是谁、哪些路不值得继续试”这件事讲清楚了。
- 换句话说，本阶段已经把后续优化空间从一大堆可能性，收敛到了少数真正值得投入的方向。

### 推荐配图

- `../person-train-model/train-result/artifacts/runs/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe/BoxPR_curve.png`
- `../person-train-model/train-result/review/roi_cropped_keep_positive_v3_margin64/overlays/D04_20260123074846_frame_0000_cropped_keep_overlay.jpg`

## Slide 6 过渡页

- 标题保留：`问题与缺陷`

## Slide 7 当前存在的问题

这页要体现“v2 往后继续优化后，真正剩下的问题是什么”，而不是继续沿用上次“ROI 初版刚跑通时”的问题定义。

### 建议改成的三个问题框

- `v2到v3提升幅度较小`
- `小人召回仍是主瓶颈`
- `训练稳定性仍需确认`

### 建议正文

- 本阶段虽然完成了 `v2 -> v3` 的升级，但 test 指标只体现为**小幅领先**，说明当前版本已经进入更细粒度的优化阶段。
- 当前主线 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` 在 test split、`conf=0.25 / nms_iou=0.7 / match_iou=0.5` 口径下逐图复盘结果为：
  - `TP=80 / FP=7 / FN=35`
- FN 分桶结果显示，当前主问题已经不是“ROI-aware 没跑通”，也不是“继续加 margin 就能解决”，而是小人 hard FN：
  - `small_boundary_person`: `13 / 35`，占 `37.1%`
  - `small_interior_person`: `16 / 35`，占 `45.7%`
  - `medium_large_pose_or_appearance`: `4 / 35`，占 `11.4%`
  - `crowded_or_localization`: `2 / 35`，占 `5.7%`
- 也就是说，`82.9%` 的 FN 都集中在小人召回问题上，说明当前模型对远处小人、半身小人、复杂姿态小人的学习仍然不够。
- ROI 裁边问题虽然是 v2 之后重点排查的一项，但复盘已经确认：
  - 原本 `54` 个会裁边的 keep-positive 框里，`margin64` 已完整救回 `31` 个
  - 剩余 `23` 个大多只是贴原图边界的残留裁边
  - 因此 ROI crop 已不再是当前主瓶颈
- 另外，当前还需要补做 `seed=7 / seed=13` 稳定性确认，所以更准确的表达应是“训练稳定性待确认”，而不是简单说模型稳定性差。

### 这一页口播建议

- 如果说上次的问题是“ROI-aware 能不能做出来”，那这次的问题已经变成“做出来之后，到底是哪类样本拖住了指标”。
- 最新复盘给出的答案很明确：现在的主要压力来自小人召回，而不是继续调 ROI 边界。

## Slide 8 问题样例展示

这一页不建议继续叫 `ROI边界过硬示例`，因为这会把问题过度归因到旧结论上。建议改成：

- `关键FN样例展示`

### 推荐放图方案

- 左图：`../person-train-model/train-result/review/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_key_fn_review/D02_20260123074836_frame_0023_roi_failure_review.jpg`
  - 用来说明：`small_boundary_person`，边界附近小人仍然容易漏检。
- 右图：`../person-train-model/train-result/review/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_key_fn_review/D15_20260119061405_frame_0346_roi_failure_review.jpg`
  - 用来说明：即使不是纯边界问题，远处小人、姿态变化、外观复杂度也会导致漏检。

### 图片下方建议配文

- 这一阶段 hardest sequences 的主要矛盾，已经从“有没有进入 ROI-aware 数据集”转向“模型有没有真正学会识别这些 hard sample”。

### 如果你想再补一张图

- `../person-train-model/train-result/review/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_key_fn_review/D15_20260119203927_frame_0162_roi_failure_review.jpg`
  - 用来说明连续困难序列里的 FN 不是偶发单帧现象。

## Slide 9 过渡页

- 标题保留：`解决方案`

## Slide 10 对应的解决方案

这一页要体现“承接 v2/v3 后，本阶段已经知道下一步该做什么”，而不是回到更早期的 keep rule 调整口径。

### 建议正文

- 默认主线继续保持为 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe`，不把 `imgsz=768`、`crop_only` 或直接切换 `yolov8s` 作为第一优先级。
- 下一步先做 `seed=7 / seed=13` 稳定性确认，判断当前 `v3` 相对 `v2` 的小幅领先是否稳定可复现。
- 重点围绕 hardest sequences 做人工 FN 复盘，并补充小人 hard sample，优先提升 Recall 和 mAP50-95。
- 只有在“逐图 FN 复盘 + 原图 ROI filter 复盘”共同证明：确实存在一批接近 ROI 边界、且因 `min_box_ioa=0.25` 被过滤的样本时，才尝试 `min_box_ioa: 0.25 -> 0.20` 的单因子实验。
- 已完成的 `crop_only + margin64` 和 `imgsz=768` 对照实验都没有优于当前主线，因此本阶段已经明确把这两条路降级，不再作为默认优先方向。

### 这一页要替换掉的旧口径

- 不建议再写“下一步把规则从 `center_inside` 调成 `bottom-center` 或 `box_ioA>=0.25`”，因为这不是本阶段之后的下一步，而是当前已经落地并验证过的规则。
- 不建议再把“放宽 ROI 边界”写成默认首选方案，因为本阶段复盘已经说明它不是当前最有效的提分方向。

### 这一页口播建议

- 现在的优化重点不再是继续把 ROI 参数往外拧，而是做更有针对性的 hard sample 补样和训练稳定性验证。

## 可直接复制到 PPT 的总结页口径

- 上一阶段已经完成 ROI-aware person 初版跑通，本阶段则继续从 `v2` 往后推进，完成了 `v3` 升级、对照实验和问题复盘闭环。
- 当前 person 指标提升变慢的主要原因，不再是 ROI 裁边，而是小人 hard FN 导致的 Recall 不足。
- 下一阶段的重点会从“继续改 ROI 参数”转向“补 hard sample、确认 seed 稳定性、提升 Recall 和 mAP50-95”。

## 建议优先替换的图片清单

### 用于 Slide 4 / Slide 5

- `../person-train-model/train-result/artifacts/runs/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe/results.png`
- `../person-train-model/train-result/artifacts/runs/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe/BoxPR_curve.png`
- `../person-train-model/train-result/review/roi_cropped_keep_positive_v3_margin64/overlays/D04_20260123074846_frame_0000_cropped_keep_overlay.jpg`

### 用于 Slide 7 / Slide 8

- `../person-train-model/train-result/review/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_key_fn_review/D02_20260123074836_frame_0023_roi_failure_review.jpg`
- `../person-train-model/train-result/review/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_key_fn_review/D02_20260123070624_frame_0071_roi_failure_review.jpg`
- `../person-train-model/train-result/review/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_key_fn_review/D15_20260119061405_frame_0346_roi_failure_review.jpg`
- `../person-train-model/train-result/review/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_key_fn_review/D15_20260119203927_frame_0162_roi_failure_review.jpg`
- `../person-train-model/train-result/review/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_fn_buckets/fn_bucket_summary.md`

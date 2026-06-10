# 自动分桶结果跳转清单

## 1. 本文件作用

这个文件不是用来写最终结论的，而是用来做“快速跳转目录”。

当你准备做人工复核时，通常需要反复在以下内容之间来回切换：

- `person分桶.md` 中的整体结论；
- 4 个 run 的 `fpfn_summary.md`；
- `person_fullframe_with_new_labels_prescreen_summary.json` 里的自动预筛统计；
- 当前激活阶段目录下对应序列的 `5-xnotes.md`。

把这些入口统一整理在这里，可以减少到处翻路径的时间。

## 2. 先看哪些文件

建议优先按下面顺序打开：

1. 总体结论：`../../../train-docs/person分桶.md`
2. 人工步骤：`../../../train-docs/人工复核.md`
3. 自动预筛结构化汇总：`../person_fullframe_with_new_labels_prescreen_summary.json`
4. 实际待复核素材清单：`by_source/review_asset_manifest.json`
5. 四个 run 的 `fpfn_summary.md`
6. `review_stage_index.md` + `active_stage.json`
7. 当前激活阶段对应序列的 `stage_reviews/stage_*/sequence_notes/sequence_*/5-xnotes.md`

## 3. 核心文档链接

### 3.1 总体文档

- `../../../train-docs/person分桶.md`
  - 当前这轮 hardest FN 分桶分析的主文档。
- `../../../train-docs/人工复核.md`
  - 人工复核的详细操作手册。

### 3.2 自动预筛汇总

- `../person_fullframe_with_new_labels_prescreen_summary.json`
  - 记录 `size_bin / pred_mode / crowd_bin / edge / repeated frames` 等自动统计结果。

### 3.3 实际待复核素材

- `by_source/README.md`
  - 说明按 8 个来源整理素材后的目录结构。
- `by_source/review_asset_manifest.json`
  - 记录这轮实际已经拷出的待复核图片、对应标签和 overlay 文件。

### 3.4 四个 run 的单独复盘摘要

- `../person_fullframe_with_new_labels_baseline_fpfn_val_conf025/fpfn_summary.md`
- `../person_fullframe_with_new_labels_baseline_fpfn_test_conf025/fpfn_summary.md`
- `../person_fullframe_with_new_labels_img768_fpfn_val_conf025/fpfn_summary.md`
- `../person_fullframe_with_new_labels_img768_fpfn_test_conf025/fpfn_summary.md`

### 3.5 当前 review 目录下需要持续维护的文件

- `README.md`
  - 总入口说明。
- `review_stage_index.md`
  - 多轮人工复核阶段总索引。
- `active_stage.json`
  - 当前激活阶段入口。
- `stage_reviews/stage_*/semantic_bucket_manifest.json`
  - 当前阶段的结构化人工复核记录。
- `stage_reviews/stage_*/semantic_bucket_summary.md`
  - 当前阶段的人工复核可读总结。

## 4. 当前建议优先看的序列

根据自动分桶与预筛结果，当前建议按下面顺序进入各序列目录：

1. `stage_reviews/stage_2026-05-07_crowded_overlap_dual_lines/sequence_notes/sequence_D15_20260119061405/5-7notes.md`
2. `stage_reviews/stage_2026-05-07_crowded_overlap_dual_lines/sequence_notes/sequence_D15_20260119203927/5-7notes.md`
3. `stage_reviews/stage_2026-05-07_crowded_overlap_dual_lines/sequence_notes/sequence_D02_20260123070624/5-7notes.md`
4. `stage_reviews/stage_2026-05-07_crowded_overlap_dual_lines/sequence_notes/sequence_D02_20260123074836/5-7notes.md`
5. `stage_reviews/stage_2026-05-07_crowded_overlap_dual_lines/sequence_notes/sequence_D05_20260123074841/5-7notes.md`

## 5. 使用提醒

- 这个文件只做“跳转索引”，不承担最终分析结论的职责；
- 结论请回写到当前激活阶段目录下的 `semantic_bucket_summary.md`；
- 单帧 / 单序列观察请写到当前激活阶段目录下对应序列的 `5-xnotes.md`；
- 结构化字段请写到当前激活阶段目录下的 `semantic_bucket_manifest.json`。

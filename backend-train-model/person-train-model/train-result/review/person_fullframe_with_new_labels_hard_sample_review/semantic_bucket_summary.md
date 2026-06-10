# 人工语义细分桶汇总（兼容入口）

## 1. 本文件作用

本文件现在只作为 `person_fullframe_with_new_labels_hard_sample_review/` 根目录下的**兼容入口**。

从 2026-05-08 起，真实的多轮人工复核总结不再继续直接堆叠在本文件中，而是统一拆到：

- `stage_reviews/stage_*/semantic_bucket_summary.md`

也就是说：

- 本文件负责告诉你“当前该看哪一轮 summary”；
- 真正的阶段总结请进入对应 stage 目录查看。

## 2. 当前激活阶段

- 阶段标题：`5.7 crowded/overlap机械复盘及双主线推进`
- 阶段目录：`stage_reviews/stage_2026-05-07_crowded_overlap_dual_lines/`
- 当前 summary：`stage_reviews/stage_2026-05-07_crowded_overlap_dual_lines/semantic_bucket_summary.md`

## 3. 历史阶段（最新在前）

1. `5.7 crowded/overlap机械复盘及双主线推进`
   - `stage_reviews/stage_2026-05-07_crowded_overlap_dual_lines/semantic_bucket_summary.md`
2. `5.6 第一轮代表帧语义复核与结构化回填`
   - `stage_reviews/stage_2026-05-06_first_semantic_review/semantic_bucket_summary.md`

## 4. 使用提醒

- 后续新增人工复核阶段时，不要再把新结论直接写回本文件；
- 先看 `review_stage_index.md` 和 `active_stage.json`，再进入具体阶段目录；
- 如果需要修改当前阶段总结，请直接修改当前激活阶段目录中的 `semantic_bucket_summary.md`。

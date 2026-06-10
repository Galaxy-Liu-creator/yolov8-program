# person_fullframe_with_new_labels 人工复核总入口

## 1. 本文件作用

这是 `person_fullframe_with_new_labels_hard_sample_review/` 目录的总入口文件，用来说明：

- 这轮人工复核的目标是什么；
- 当前目录下哪些文件是**总索引**，哪些目录才是**分阶段真实产物**；
- 实际复核时建议按什么顺序使用这些文件。

如果后续有人只打开这个目录，不看聊天记录，也应该能先通过本文件快速理解这轮 hard sample review 的用途。

## 2. 本轮人工复核范围

本目录服务于 `person_fullframe_with_new_labels` 这条 fullframe 扩样线的 hardest FN 复核。

当前主线口径已经固定为：

1. 先基于 4 个 run 的 `fpfn_per_image.json` 做自动分桶；
2. 再从 hardest sequences / repeated frames 中抽取代表帧；
3. 最后对这些代表帧做分阶段人工语义复核。

当前默认优先看的主序列是：

- `D15_20260119061405`
- `D15_20260119203927`
- `D02_20260123070624`
- `D02_20260123074836`
- `D05_20260123074841`

## 3. 当前目录结构说明

本目录下建议重点使用以下文件和目录：

- `README.md`
  - 当前这个总入口文件。
- `review_stage_index.md`
  - 多轮人工复核阶段总索引，最新在前、历史在后。
- `active_stage.json`
  - 当前激活阶段的机器可读入口，后续如果脚本或人工要定位“当前该改哪一轮文件”，优先看这里。
- `stage_reviews/`
  - **正式的分阶段人工复核产物目录**。每一轮人工复核单独一个子目录，内部再分别存放该轮的：
    - `semantic_bucket_summary.md`
    - `semantic_bucket_manifest.json`
    - `sequence_notes/sequence_*/5-xnotes.md`
- `bucket_summary_links.md`
  - 汇总跳转入口，方便快速打开已有自动分桶结论与复盘产物。
- `by_source/`
  - 按 `prepare_report.json` 的 8 个来源整理好的实际人工复核素材目录，里面已经放入待复核原图、对应 txt 和按 run 生成的 overlay 图。
- 顶层 `semantic_bucket_summary.md`
  - **兼容入口 / 索引文件**，不再承担多轮历史总结归档职责。
- 顶层 `semantic_bucket_manifest.json`
  - **兼容入口 / 机器可读索引文件**，不再承担多轮历史 records 的唯一存放职责。

补充判断：

- 顶层 `sequence_*` 索引目录已经完成历史过渡任务，当前正式结构中不再需要它们；
- 从现在开始，序列级正文只保留在 `stage_reviews/stage_*/sequence_notes/` 下；
- 如果后续有人继续按旧路径找 `sequence_*/notes.md`，应统一改为先看 `review_stage_index.md` 与 `active_stage.json`，再进入对应阶段目录。

也就是说：

- **实际复核素材**统一放在 `by_source/`；
- **每轮人工复核的真实文字产物**统一放在 `stage_reviews/stage_*/`；
- **根级 summary、根级 manifest** 现在只作为入口 / 兼容层，不再继续反复覆盖历史内容。

## 4. 推荐使用顺序

建议按下面顺序使用本目录：

1. 先看 `../../../train-docs/person分桶.md`
   - 了解自动分桶结论和当前推荐推进顺序。
2. 再看 `../../../train-docs/人工复核.md`
   - 确认“当前阶段到底要复核什么、怎么做、用什么工具”。
3. 再看 `review_stage_index.md`
   - 了解已经存在的阶段、先后顺序以及每轮产物位置。
4. 再看 `active_stage.json`
   - 确认当前激活阶段目录。
5. 再到 `by_source/` 中按来源或序列领取实际复核素材
   - 组员优先从 `by_source/README.md` 和 `by_source/review_asset_manifest.json` 开始。
6. 再进入当前阶段目录，例如：`stage_reviews/stage_*/`
   - 在该轮 `sequence_notes/sequence_*/5-xnotes.md` 中写序列观察；
   - 在该轮 `semantic_bucket_manifest.json` 中写结构化记录；
   - 在该轮 `semantic_bucket_summary.md` 中写全局总结。

## 5. 当前状态

当前目录已经从“单例文件持续覆盖”调整为“按阶段归档”的结构：

- 自动预筛和代表帧筛选已经完成；
- 多轮人工复核开始按阶段拆分；
- 最新阶段在前，历史阶段在后；
- 共享素材仍只维护一份，不按阶段重复复制图片、标签和 overlay。

## 6. 维护建议

- 每新增一轮人工复核，先在 `人工复核.md` 中增加新的阶段 H2，再在 `stage_reviews/` 下新建对应阶段目录；
- 同一轮内部，先写该轮的 `sequence_notes/.../5-xnotes.md`，再更新该轮 `semantic_bucket_manifest.json`，最后更新该轮 `semantic_bucket_summary.md`；
- 根级 summary、根级 manifest 现在只保留为入口 / 兼容层，不要再把新的阶段结论直接写回这些单例文件里；
- 顶层 `sequence_*` 索引目录现已不再作为正式结构的一部分，后续如需查看序列记录，请直接进入对应阶段目录下的 `sequence_notes/`。

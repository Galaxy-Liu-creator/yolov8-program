 # 人工复核阶段索引

 ## 1. 本文件作用

 这个文件用于统一管理 `person_fullframe_with_new_labels_hard_sample_review/` 下已经存在的多轮人工复核阶段。

 约定如下：

 - 最新阶段在前，历史阶段在后；
 - 每一轮人工复核都单独建一个 `stage_reviews/stage_*/` 目录；
 - 真实的阶段性 notes / summary / manifest 都只放在各自阶段目录里；
 - 根级 `semantic_bucket_summary.md`、`semantic_bucket_manifest.json` 只作为入口 / 兼容层；
 - 顶层 `sequence_*` 索引目录已完成历史过渡任务，不再作为正式写入入口。

 ## 2. 当前激活阶段

 - 阶段标题：`5.13 crowded/overlap正式收口与下一阶段任务确认`
 - 阶段目录：`stage_reviews/stage_2026-05-13_crowded_overlap_formal_closeout/`
 - 该轮 summary：`stage_reviews/stage_2026-05-13_crowded_overlap_formal_closeout/semantic_bucket_summary.md`
 - 该轮 manifest：`stage_reviews/stage_2026-05-13_crowded_overlap_formal_closeout/semantic_bucket_manifest.json`
 - 该轮 sequence notes 根目录：`stage_reviews/stage_2026-05-13_crowded_overlap_formal_closeout/sequence_notes/`

 机器可读入口请同步查看：`active_stage.json`

 ## 3. 历史阶段列表（最新在前）

 ### 3.1 `5.13 crowded/overlap正式收口与下一阶段任务确认`

 - 目录：`stage_reviews/stage_2026-05-13_crowded_overlap_formal_closeout/`
 - 说明：当前 active stage，重点是承接 `5.10` 已填 notes，把 crowded / overlap 主线的正式结论、已发现问题和下一阶段任务独立沉淀为新阶段，而不是继续写回 `5.10` 当天的阶段正文。

 ---

 ### 3.2 `5.10 crowded/overlap机制收口与下一阶段启动准备`

 - 目录：`stage_reviews/stage_2026-05-10_crowded_overlap_mechanism_closeout/`
 - 说明：`2026-05-10` 当天的历史阶段，重点是承接 `5.7` 结论，把 crowded / overlap 从语义层推进到机制级判断入口，并完成当日 notes 填写与初步机制收口准备。

 ---

 ### 3.3 `5.7 crowded/overlap机制复盘及双主线推进`

 - 目录：`stage_reviews/stage_2026-05-07_crowded_overlap_dual_lines/`
 - 说明：`2026-05-07` 当天的历史阶段，重点是完成 hardest FN 的第一层语义归类，并把主问题拆成“可见性弱型”和“crowded / overlap 型”两条主线。

 ---

 ### 3.4 `5.6 第一轮代表帧语义复核与结构化回填`

 - 目录：`stage_reviews/stage_2026-05-06_first_semantic_review/`
 - 说明：第一轮代表帧语义复核阶段，重点是把算法桶翻译成基础人工语义桶，并完成首版结构化回填。

 ## 4. 使用建议

 1. 先看 `../../../train-docs/人工复核.md`，确认当前阶段目标和做法；
 2. 再看 `active_stage.json`，确定今天应该修改哪一轮日期阶段目录；
 3. 真正写记录时，只改对应阶段目录中的：
    - `sequence_notes/sequence_*/5-xnotes.md`
    - `semantic_bucket_manifest.json`
    - `semantic_bucket_summary.md`
 4. 不要再把新阶段的正文直接回写到顶层单例文件。

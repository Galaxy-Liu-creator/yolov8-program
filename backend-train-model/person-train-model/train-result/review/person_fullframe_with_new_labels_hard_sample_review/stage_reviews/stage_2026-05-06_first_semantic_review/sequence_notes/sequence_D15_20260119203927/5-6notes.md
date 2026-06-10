 # D15_20260119203927 人工复核记录（5.6 阶段）

 ## 1. 本文件作用

 这个文件用于记录 `D15_20260119203927` 这条序列在 5.6 阶段的人工语义复核结论。

 它的角色更像“与 D15_20260119061405 对照”的第二优先级主序列：

 - 用来判断两条 D15 序列是不是同一类失败模式；
 - 也用来判断当前 person 模型对中等尺度难例是不是存在系统性表征不足。

 ## 2. 当前为什么优先看这条序列

 当前自动分桶显示，这条序列在 val / test 两边都稳定进入 hardest sequences。

 它主要覆盖：

 - `medium_large_pose_or_appearance`
 - `small_interior_person`

 因此它很适合回答：

 - 当前 hardest FN 是不是一类稳定复现的问题；
 - 与另一条 D15 主序列相比，难点是不是同质；
 - 是否存在不同于光照的另一类姿态 / 外观 / 构图问题。

 ## 3. 当前建议优先看的内容

 当前这条序列建议优先看下面 3 张已经导出的代表帧：

 - `D15_20260119203927_frame_0142`
 - `D15_20260119203927_frame_0143`
 - `D15_20260119203927_frame_0180`

 并重点关注：

 - `../../../../by_source/` 下对应来源目录中的 `overlays/` 里，是否能找到 GT 已明显可见但模型响应弱的样本；
 - `../../../../by_source/` 下对应来源目录中的 `images/` 里，优先查看与 `D15_20260119061405` 不同类型的代表图；
 - 若发现 `crowded_or_localization`，单独记清是否只是少量子问题。

 ## 4. 建议记录模板

 | frame | algorithm_bucket | semantic_primary | semantic_secondary | need_relabel | notes |
 | --- | --- | --- | --- | --- | --- |
 | D15_20260119203927_frame_0142 | crowded_or_localization / medium_large_pose_or_appearance |  |  |  |  |
 | D15_20260119203927_frame_0143 | medium_large_pose_or_appearance / small_interior_person |  |  |  |  |
 | D15_20260119203927_frame_0180 | medium_large_pose_or_appearance / small_interior_person |  |  |  |  |

 ## 5. 当前待回答的问题

 1. 这条序列的主问题是否与 `D15_20260119061405` 同质？
 2. 是否更偏姿态异常、人体外观不完整或对比度不足？
 3. 是否存在少量边界小人，但并不是主问题？

 ## 6. 复核后建议补写的位置

 - 逐 GT 结构化记录 -> `../../semantic_bucket_manifest.json`
 - 这条序列的观察总结 -> 当前文件
 - 全局可读总结 -> `../../semantic_bucket_summary.md`

 # D02_20260123070624 人工复核记录（5.6 阶段）

 ## 1. 本文件作用

 这个文件用于记录 `D02_20260123070624` 在 5.6 阶段的人工复核观察。

 这条序列的价值在于：

 - 它同时覆盖 `small_interior_person` 和 `small_boundary_person`；
 - 很适合判断“内部远景小人”和“边界远景小人”到底是不是同一类问题。

 当前实际复核素材统一放在 `../../../../by_source/` 下的对应来源 / 序列目录中；本文件只负责写结论和备注，不再重复存放图片与 overlay。

 ## 2. 当前为什么优先看这条序列

 当前自动分桶显示：

 - 在多个 run 中都持续出现；
 - `D02_20260123070624_frame_0060 / 0061` 是跨 run 反复出现的高价值代表帧；
 - `small_boundary_person` 与 `small_interior_person` 同时明显存在。

 因此这条序列适合回答：

 - 远景内部小人与边界小人是否都源于像素不足；
 - 是否有一部分看上去不算太小，但因为构图或视角压缩而被漏掉；
 - `img768` 对这条序列为什么没有根本改善。

 ## 3. 当前建议优先看的代表帧

 - `D02_20260123070624_frame_0060`
 - `D02_20260123070624_frame_0061`

 ## 4. 建议记录模板

 | frame | algorithm_bucket | semantic_primary | semantic_secondary | need_relabel | notes |
 | --- | --- | --- | --- | --- | --- |
 | D02_20260123070624_frame_0060 | mixed (medium_large / small_interior / small_boundary) | occluded | small_far_interior | false | 车辆遮挡+远景+部分出线 |
 | D02_20260123070624_frame_0061 | small_interior_person | occluded | small_far_interior | false | 车辆遮挡+远景 |

 ## 5. 当前待回答的问题

 1. 这些人到底是“纯远景太小”，还是“构图 + 远景”叠加导致更难？构图+远景
 2. 边界人是不是只占少数，但更容易让人误以为它是主因？占少数，不是主因
 3. 是否存在需要单独补样的远景内部小人场景？不存在

 ## 6. 复核后建议补写的位置

 - 逐 GT 结构化记录 -> `../../semantic_bucket_manifest.json`
 - 这条序列的观察总结 -> 当前文件
 - 全局可读总结 -> `../../semantic_bucket_summary.md`

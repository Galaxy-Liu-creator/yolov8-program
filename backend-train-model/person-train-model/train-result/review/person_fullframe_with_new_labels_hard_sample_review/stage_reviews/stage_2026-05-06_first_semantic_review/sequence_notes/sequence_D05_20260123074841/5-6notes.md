 # D05_20260123074841 人工复核记录（5.6 阶段）

 ## 1. 本文件作用

 这个文件用于记录 `D05_20260123074841` 这条序列在 5.6 阶段的人工复核结论。

 它的特殊价值在于：

 - 这条序列不是 hardest FN 的主体来源；
 - 但它是当前少数能稳定代表 `crowded_or_localization` 子问题的序列之一。

 当前实际复核素材统一放在 `../../../../by_source/` 下的对应来源 / 序列目录中；本文件只负责写结论和备注，不再重复存放图片与 overlay。

 ## 2. 当前为什么优先看这条序列

 当前自动分桶显示：

 - `D05_20260123074841_frame_0026` 在 val 侧跨 run 重复出现；
 - `D05_20260123074841_frame_0029 / 0030` 还代表了拥挤 / 定位类子问题；
 - 这条序列适合专门判断“当前 hardest FN 里到底有多少是真正的拥挤定位问题”。

 因此它最适合回答：

 - `crowded_or_localization` 是不是只是少量子问题；
 - 多人近邻时，模型到底是没看见、框偏了，还是匹配不过线；
 - 是否需要单独去怀疑 NMS / 定位稳定性，而不是样本语义本身。

 ## 3. 当前建议优先看的代表帧

 - `D05_20260123074841_frame_0026`
 - `D05_20260123074841_frame_0029`
 - `D05_20260123074841_frame_0030`

 ## 4. 建议记录模板

 | frame | algorithm_bucket | semantic_primary | semantic_secondary | need_relabel | notes |
 | --- | --- | --- | --- | --- | --- |
 | D05_20260123074841_frame_0026 | crowded_or_localization / mixed | crowded_or_overlap |  | false | 两个框相互干扰 |
 | D05_20260123074841_frame_0029 | crowded_or_localization | crowded_or_overlap |  | false | 两个框相互干扰 |
 | D05_20260123074841_frame_0030 | crowded_or_localization | crowded_or_overlap | occluded | false | 两个框相互干扰+遮挡 |

 ## 5. 当前待回答的问题

 1. 这条序列里 GT 是否本来就近邻重叠明显？是
 2. 漏检是否更像局部遮挡、框偏移还是纯粹匹配不过线？局部遮挡
 3. 这类问题规模是否足够大到值得单独开实验分支？否

 ## 6. 复核后建议补写的位置

 - 逐 GT 结构化记录 -> `../../semantic_bucket_manifest.json`
 - 这条序列的观察总结 -> 当前文件
 - 全局可读总结 -> `../../semantic_bucket_summary.md`

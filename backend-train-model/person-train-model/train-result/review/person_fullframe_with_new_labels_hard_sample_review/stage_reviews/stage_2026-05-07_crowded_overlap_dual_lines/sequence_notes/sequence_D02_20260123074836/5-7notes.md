 # D02_20260123074836 人工复核记录（5.7 阶段）

 ## 1. 本文件作用

 这个文件用于记录 `D02_20260123074836` 这条序列在 5.7 阶段的人工复核结论。

 这条序列的角色比较明确：

 - 它不是当前 hardest FN 的绝对主体；
 - 但它是验证“边界远景小人到底是不是主因”的重要对照序列。

 当前实际复核素材统一放在 `../../../../by_source/` 下的对应来源 / 序列目录中；本文件只负责写结论和备注，不再重复存放图片与 overlay。

 ## 2. 当前为什么优先看这条序列

 当前自动分桶显示：

 - `small_boundary_person` 在这条序列中比较集中；
 - `D02_20260123074836_frame_0022 / 0023 / 0024` 是边界类代表帧；
 - 适合作为“边界问题是否需要单独开分支”的判断依据。

 因此这条序列最适合回答：

 - 边界人到底占多大比重；
 - 这些人是不是已经小到超出当前 fullframe person 的稳定检测范围；
 - 是否值得专门为边界远景小人单独补样或做策略分支。

 ## 3. 当前建议优先看的代表帧

 - `D02_20260123074836_frame_0022`
 - `D02_20260123074836_frame_0023`
 - `D02_20260123074836_frame_0024`

 ## 4. 建议记录模板

 | frame | algorithm_bucket | semantic_primary | semantic_secondary | need_relabel | notes |
 | --- | --- | --- | --- | --- | --- |
 | D02_20260123074836_frame_0022 | small_boundary_person | partial_body | occluded | false | 只露出半身+遮挡+远景 |
 | D02_20260123074836_frame_0023 | small_boundary_person | partial_body | occluded | false | 只露出半身+遮挡+远景 |
 | D02_20260123074836_frame_0024 | small_boundary_person | partial_body | occluded | false | 只露出半身+遮挡+远景 |

 ## 5. 当前待回答的问题

 1. 这条序列的边界人到底是“贴边导致难”，还是“本质就是远景太小”？贴边+远景
 2. 这些样本是否已经接近当前 fullframe 模型的可检测极限？否
 3. 是否存在少量可以通过补样或增强显著改善的边界小人？否

 ## 6. 复核后建议补写的位置

 - 逐 GT 结构化记录 -> `../../semantic_bucket_manifest.json`
 - 这条序列的观察总结 -> 当前文件
 - 全局可读总结 -> `../../semantic_bucket_summary.md`

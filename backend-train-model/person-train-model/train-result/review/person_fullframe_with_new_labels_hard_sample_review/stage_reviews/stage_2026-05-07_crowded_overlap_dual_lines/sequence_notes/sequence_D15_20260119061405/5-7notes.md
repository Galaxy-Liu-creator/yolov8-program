 # D15_20260119061405 人工复核记录（5.7 阶段）

 ## 1. 本文件作用

 这个文件专门记录 `D15_20260119061405` 在 5.7 阶段的人眼观察结论。

 建议在这里写：

 - 这条序列为什么难；
 - 代表帧分别难在哪；
 - 更偏暗光 / 背光 / 遮挡 / 半身 / 姿态异常中的哪一类；
 - 是否怀疑存在标注问题；
 - 下一步最值得做的动作。

 当前实际复核素材统一放在 `../../../../by_source/` 下的对应来源 / 序列目录中；本文件只负责写 5.7 阶段结论和备注，不再重复存放图片与 overlay。

 ## 2. 当前为什么优先看这条序列

 这条序列是当前 hardest FN 的第一优先级来源之一。

 当前自动分桶显示：

 - 在 `baseline_test` 中 `fn = 29`
 - 在 `img768_test` 中 `fn = 33`
 - 主要集中在：
   - `medium_large_pose_or_appearance`
   - `small_interior_person`

 它最适合回答的问题是：

 - 为什么中等尺度 person 仍然会持续漏检；
 - 漏检是否更偏暗光、背光、半身、姿态异常；
 - `img768` 为什么没有改变这类难例的结构。

 ## 3. 当前建议优先看的代表帧

 - `D15_20260119061405_frame_0345`
 - `D15_20260119061405_frame_0346`
 - `D15_20260119061405_frame_0348`
 - `D15_20260119061405_frame_0355`

 ## 4. 建议记录模板

 | frame | algorithm_bucket | semantic_primary | semantic_secondary | need_relabel | notes |
 | --- | --- | --- | --- | --- | --- |
 | D15_20260119061405_frame_0345 | medium_large_pose_or_appearance | occluded | dark_or_backlit | false | 摩托车遮挡+背景昏暗 |
 | D15_20260119061405_frame_0346 | medium_large_pose_or_appearance / small_interior_person | pose_or_shape_unusual | occluded | false | 弯腰+遮挡 |
 | D15_20260119061405_frame_0348 | medium_large_pose_or_appearance / small_interior_person | pose_or_shape_unusual | occluded | false | 弯腰+遮挡 |
 | D15_20260119061405_frame_0355 | medium_large_pose_or_appearance / small_interior_person | occluded | dark_or_backlit | false | 摩托车遮挡+背景昏暗 |

 ## 5. 当前待回答的问题

 1. 这条序列的主问题更偏光照、姿态还是可见性不足？可见性偏多
 2. 这些 person 是否真的不小，但视觉判别线索弱？是
 3. 是否存在一小批“其实应该能学会，但标注或构图让它难度异常升高”的样本？是

 ## 6. 复核后建议补写的位置

 - 逐 GT 结构化记录 -> `../../semantic_bucket_manifest.json`
 - 这条序列的观察总结 -> 当前文件
 - 全局可读总结 -> `../../semantic_bucket_summary.md`

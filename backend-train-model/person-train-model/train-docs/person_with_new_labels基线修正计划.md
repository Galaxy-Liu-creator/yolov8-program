 # person_with_new_labels fullframe 修正方案

 ## 1. 本文档解决什么问题

 本文档用于把 `person_fullframe_with_new_labels` 当前这条线，按照 `人工复核.md` 已经沉淀出的 hardest FN 结论，转换成**真正可执行的 fullframe 修正动作**。

 它重点回答下面几个问题：

 1. 当前 fullframe 上游的主要问题到底是什么；
 2. “修改训练方式”具体应先改什么、不先改什么；
 3. 是先修数据、先补样本，还是先改大配方；
 4. 下一轮 fullframe 应该怎样训练，才能更适合作为后续 new labels ROI-aware 的初始化来源。

 本文默认配合以下文档一起看：

 - 当前决策口径：`backend-train-model/person-train-model/train-docs/person_with_new_labels_decision.md`
 - 当前运行入口：`backend-train-model/person-train-model/train-docs/person_with_new_labels_run.md`
 - hardest FN 人工复核结论：`backend-train-model/person-train-model/train-docs/人工复核.md`

 ---

 ## 2. 当前阶段一句话结论

 当前不建议把“训练方式修改”理解成：

 - 立刻切 ROI-aware；
 - 立刻放大 `imgsz`；
 - 立刻换更大模型；
 - 立刻改 `min_box_ioa`、NMS 或其他规则参数。

 当前更合理的理解是：

 > **先根据人工复核结果，把 crowded / overlap、second_person_no_response、visibility weak、annotation_problem 转成数据治理动作，再用 640 单因子 fullframe 继续修正上游 person 主线。**

 这条线修正到足够稳后，再把其 best 权重作为 new labels ROI-aware 的初始化来源。

 ---

 ## 3. 当前 fullframe 上游真正需要修什么

 根据 `人工复核.md` 当前 `5.13` 阶段口径，当前更值得优先处理的不是 ROI 边界，而是下面四类问题：

 1. `crowded / overlap`
 2. `second_person_no_response`
 3. `visibility weak` / 可见性弱型
 4. `annotation_problem`

 更准确地说：

 - 当前 crowded 主线已经稳定落在 `D15_20260119203927` 与 `D05_20260123074841`；
 - 当前更稳的主失败机制偏 `second_person_no_response`；
 - `merge_two_people` 仍保留为伴随分支，但当前不应把整条主线直接改写成它；
 - `D15_20260119061405` 继续主要承担“可见性弱型”对照角色。

 因此，当前 fullframe 修正优先级应理解为：

 > **先修 crowded / overlap 与可见性弱型这些上游检测本身的问题，再决定是否值得把 ROI-aware 升级成下一步正式主动作。**

 ---

 ## 4. 训练方式到底改什么

 ## 4.1 当前优先改的是“数据治理和实验顺序”

 当前最应该先改的是：

 - 标签问题是否需要修框 / 重标；
 - crowded / overlap hardest 正样本是否需要扩充邻近帧；
 - 当前 mixed 数据中 hardest 主问题是否已经被稳定纳入训练集；
 - 下一轮实验是不是继续保持单因子 `640 fullframe`。

 当前不建议优先改的是：

 - 更大输入尺寸；
 - 更大模型；
 - ROI keep rule；
 - `min_box_ioa 0.25 -> 0.20`；
 - NMS 调参；
 - 直接切 ROI-aware 正式训练。

## 4.2 当前真正要改的是“实验顺序”

 当前更正确的顺序，不是：

 - 先改 `imgsz`；
 - 先换更大模型；
 - 先切 ROI-aware；
 - 或者一边修数据一边同时改很多训练变量。

 当前真正应该做的是：

 ```text
 先把人工复核结论转成三张动作清单
 -> 先回到源标签目录修框 / 重标
 -> 再围绕 crowded / overlap、second_person_no_response、visibility weak 补邻近帧或同问题样本
 -> 再检查标签语义与框风格是否一致
 -> 再重跑 prepare-labels / prepare，刷新 fullframe prepared 数据集
 -> 再根据这轮数据改动大小，决定是从 seed7 best 继续 fine-tune，还是按 640 稳健配方干净重训
 -> 再评估上游是否真的改善
 -> 只有这时才决定是否进入 new labels ROI-aware 正式训练
 ```

 ### 4.2.1 把上面这条顺序翻成真正可执行的阶段

 #### 阶段 A：先把人工复核结果变成训练前动作

 这一阶段先不要急着训练，先把 `人工复核.md` 当前 active stage 的结论整理成：

 - `must_relabel_list`
 - `hard_positive_expand_list`
 - `defer_list`

 对应目标分别是：

 - 哪些图片必须先修标签；
 - 哪些 hardest 正样本要补邻近帧；
 - 哪些问题先不抢当前主线节奏。

 这一阶段的最小交付是：

 1. 关键 `annotation_problem` 样本已列清；
 2. crowded / overlap 与可见性弱型的补样目标序列已列清；
 3. 明确当前哪些问题先不做。

 #### 阶段 B：先修源标签、再补 hardest 样本

 这一阶段所有修改都应回到原始标签入口，而不是改 prepared 中间产物。

 优先处理：

 - crowded / overlap 主线；
 - `second_person_no_response` 主线；
 - 明确的 `annotation_problem`。

 然后按 hardest 序列补邻近帧或同问题样本，重点不是“泛泛扩图”，而是：

 > **提高当前主失败机制在训练数据中的密度。**

 这一阶段的最小交付是：

 1. 源标签修正完成；
 2. 邻近帧 / hardest 样本补齐完成；
 3. 新旧样本框语义没有继续漂移。

 #### 阶段 C：刷新 fullframe prepared 数据集

 只有在阶段 B 做完后，才建议刷新 fullframe prepared 数据。

 先重跑：

 - `prepare-labels`
 - `prepare`

 这一阶段的目标是：

 - 让新的修标与补样正式进入训练数据；
 - 保证后续训练不是在旧 prepared 数据上继续跑。

 #### 阶段 D：再决定 fine-tune 还是重训

 这一阶段不要凭感觉选。

 建议按下面口径判断：

 - **如果改动小**：
  - 只修了一批关键标签；
  - 只补了一批 hardest 邻近帧；
  - 数据分布没有明显重构；
  - 则优先从 `person_fullframe_with_new_labels_baseline_seed7/weights/best.pt` 继续 fine-tune。
- **如果改动大**：
  - 修了较多标签；
  - 补了较多 hardest 样本；
  - 数据分布已经明显变化；
  - 则优先按 `640` 稳健配方从 `yolov8n.pt` 干净重训。

 这一步的核心目标不是“立刻追更高分”，而是：

 > **让修正后的 fullframe 成为下一步最可信的上游基线。**

 #### 阶段 E：先判断上游是否改善，再谈 ROI-aware

 当前评估重点应放在：

 1. Recall；
 2. mAP50；
 3. crowded / overlap 代表序列的漏人是否下降；
 4. 可见性弱型对照序列是否仍明显漏人；
 5. 后续用于 person crop 的人框是否更完整。

 也就是说，先确认：

 > **上游 person 对 downstream 最致命的“没框 / 框不稳”问题是否真的改善了。**

 #### 阶段 F：最后才进入 new labels ROI-aware

 只有下面三个条件都成立时，才建议正式进入 new labels ROI-aware：

 1. hardest FN 的主机制已经转成数据治理动作，并完成一轮 fullframe 修正训练；
 2. 修正后的 fullframe 结果证明：上游没有明显退化，或已经改善；
 3. `new_person_labels` 的 ROI 已补齐到可独立 prepare ROI-aware 数据集的程度。

 这一步的目的，不是“因为 ROI-aware 听起来更高级就先切过去”，而是：

 > **在一个更稳的 fullframe 上游基础上，正式比较 ROI-aware 是否值得升级。**

 ---

 ## 5. 先把人工复核结论整理成三张动作清单

 在开始任何新训练之前，建议先把当前人工复核结果拆成下面三张清单。

 ## 5.1 清单 A：必须修框 / 重标清单

 放进这张清单的样本，满足下面任一条件即可：

 - `annotation_problem` 证据已经足够明确；
 - crowded 情况下 GT 明显漏人；
 - 一框吃两人且当前 GT 表达明显不合理；
 - 框明显偏到会影响后续 person crop 完整性；
 - 原始标签语义和当前其余数据风格明显不一致。

 这批样本的动作不是“继续训练看看”，而是：

 > **先修原始标签，再继续训练。**

 建议至少记录下面字段：

 - `source_id`
 - `sequence_name`
 - `image_stem`
 - `problem_type`
 - `need_relabel`
 - `relabel_status`
 - `comment`

 ## 5.2 清单 B：hard positive 扩充清单

 这批样本标签本身大体没错，但模型容易漏。典型包括：

 - crowded / overlap
 - `second_person_no_response`
 - visibility weak
 - 远景小人
 - 半身 / 截断

 这批样本当前更应该做的是：

 > **补充同 sequence 的邻近帧或同场景同问题样本，让模型更密集地见到这些 hardest positive。**

 建议优先围绕：

 - `D15_20260119203927`
 - `D05_20260123074841`
 - `D15_20260119061405`（作为可见性弱型对照）

 ## 5.3 清单 C：暂不优先处理清单

 放进这张清单的典型情况是：

 - 证据还不稳定；
 - 机制还没完全收口；
 - 不是当前最主要的失败机制；
 - 继续处理会打断主线节奏。

 当前典型例子：

 - 还不能一口气把 crowded 主线统一改写成 `merge_two_people`；
 - `weak_box_match_fail` 还没强到必须升级成当前第一入口；
 - 对照序列不应抢 crowded 主线节奏。

 ---

 ## 6. 数据治理动作怎么落地

 ## 6.1 先修“源标签”，不要修 prepared 产物

 所有修框 / 重标都应优先回到原始标签入口完成，例如：

 - `D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\person_labels\...`
 - `D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\new_person_labels\person_labels`

 不要把修正直接打在：

 - `train-result/prepared/...`
 - `train-result/working/aggregated_labels_...`

 这些目录只应被视为中间产物。

 ## 6.2 对 hard positive 优先补邻近帧，而不是泛泛加更多图

 当前建议的补样方式不是盲目扩图，而是：

 - 先围绕 hardest sequence；
 - 再围绕 hardest frame 的短时间窗口；
 - 优先补具有同类失败机制的邻近帧。

 这样做的目的是：

 - 让 crowded / overlap 这类主失败机制在训练里更密集；
 - 避免新增很多与当前主矛盾无关的普通样本，把 hardest 信号冲淡。

 ## 6.3 保持框语义一致

 这一步非常重要。

 无论是修标还是补样，都要保证：

 - 同类场景中的框松紧一致；
 - 不要这批只框头肩、另一批框全身；
 - 不要旧数据宽松、新数据极紧；
 - crowded 情况下不要一部分帧保守标、一部分帧直接漏标。

 如果标签风格继续漂移，模型很容易把“修正训练”学成“标签冲突”。

 ---

 ## 7. 什么时候用 fine-tune，什么时候重训

 ## 7.1 如果这轮修正改动不大：优先从当前较稳 fullframe 权重继续 fine-tune

 适用场景：

 - 只修了一批关键错误标签；
 - 只补了一批 hardest 邻近帧；
 - 数据分布没有实质重构。

 当前更推荐的初始化来源是：

 - `person_fullframe_with_new_labels_baseline_seed7/weights/best.pt`

 原因：

 - 这轮是干净的 fresh-start seed 对照；
 - test 指标没有崩，且比当前历史 baseline 略优；
 - 它更像当前 640 fullframe 的强候选。

 ## 7.2 如果这轮修正改动较大：优先重新按 640 稳健配方干净重训

 适用场景：

 - 修了较多源标签；
 - 补了较多 hardest 样本；
 - 数据分布已经发生明显变化；
 - 你希望让下一轮 fullframe 重新成为最干净的对照基线。

 这时更适合：

 - 继续保持 `imgsz=640`
 - 继续保持 `batch=4`
 - 继续保持 `epochs=180`
 - 从 `backend-train-model/weights/yolov8n.pt` 重新起训

 ---

 ## 8. 推荐执行顺序

 ## 8.1 第一步：整理动作清单

 先从 `人工复核.md` 当前 active stage 提取：

 - `must_relabel_list`
 - `hard_positive_expand_list`
 - `defer_list`

 即使先用 Excel 或 Markdown 记录，也比直接闷头继续训练更好。

 ## 8.2 第二步：修标 / 补样

 优先处理：

 - crowded / overlap 主线；
 - `second_person_no_response` 主线；
 - 明确的 `annotation_problem`。

 ## 8.3 第三步：刷新 fullframe prepared 数据集

 先重跑聚合标签：

 ```powershell
 D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py prepare-labels --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --overwrite
 ```

 再重跑 fullframe prepared 数据集：

 ```powershell
 D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py prepare --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --overwrite
 ```

 ## 8.4 第四步：训练修正后的 fullframe

 ### 方案 A：改动较小，建议从 seed7 best 继续 fine-tune

 ```powershell
 D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe_with_new_labels\sequence_contiguous\dataset.yaml --run-name person_fullframe_with_new_labels_hardfix_v1_from_seed7 --device 0 --workers 4 --batch 4 --imgsz 640 --epochs 120 --patience 30 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_with_new_labels_baseline_seed7\weights\best.pt
 ```

 ### 方案 B：改动较大，建议从 yolov8n.pt 干净重训

 ```powershell
 D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe_with_new_labels\sequence_contiguous\dataset.yaml --run-name person_fullframe_with_new_labels_hardfix_v1_baseline --device 0 --workers 4 --batch 4 --imgsz 640 --epochs 180 --patience 40 --base-model backend-train-model\weights\yolov8n.pt
 ```

 ## 8.5 第五步：评估时重点看什么

 当前建议优先看：

 1. Recall
 2. mAP50
 3. crowded / overlap 代表序列的漏人是否下降
 4. 可见性弱型对照序列是否仍然大量漏人
 5. 后续用于 person crop 的人框是否更完整

 当前不建议只盯：

 - 单个 `mAP50-95`

 原因是：

 - 上游 person 对 downstream 最致命的问题，通常先是“没框”；
 - 然后才是“框不够准”。

 ---

 ## 9. 当前明确不建议优先做什么

 1. 不建议现在就把 `img768` 升为默认主线；
 2. 不建议现在就切 `yolov8s`；
 3. 不建议现在就围绕 ROI keep rule 做主动作；
 4. 不建议现在就切 `min_box_ioa 0.25 -> 0.20`；
 5. 不建议把 fullframe 修正和 ROI-aware 正式训练混成一轮做；
 6. 不建议在 crowded / overlap 主机制还没转成数据治理动作前，就继续主要纠结大配方。

 ---

 ## 10. 什么时候可以进入 new labels ROI-aware 正式训练

 建议至少满足下面三个条件：

 1. 当前 hardest FN 的主机制已经转成数据治理动作，并完成一轮 fullframe 修正训练；
 2. 修正后的 fullframe 结果证明：上游在 crowded / overlap、visibility weak 等关键场景没有明显退化，或已经改善；
 3. `new_person_labels` 的 ROI 已经补齐到可独立 prepare ROI-aware 数据集的程度。

 只有这时，才更适合把修正后的 fullframe best 权重作为 new labels ROI-aware 的初始化来源，正式比较：

 - fullframe 修正版本
 - ROI-aware new labels 版本

 这时的比较才更有解释力。

 ---

 ## 11. 一句话执行口径

 > **先把人工复核结果转成“修标 + 补 hardest 邻近帧”的 fullframe 数据治理动作，再用 640 单因子 fullframe 修正上游 person 主线；不要把当前 hardest FN 还没转成训练动作的状态，直接跳进 new labels ROI-aware 正式训练。**


 # person_with_new_labels 下一步训练决策

 ## 1. 本文档回答什么问题

 本文档专门回答 `person_with_new_labels` 这条线当前最实际的决策问题：

 1. 现在应不应该继续训练；
 2. 是先继续 fullframe，还是先等 ROI 补齐后再训练；
 3. 当前旧 ROI-aware 主线和 new labels 主线是什么关系；
 4. 接下来训练方式到底该怎么改，哪些事情不该优先做。

 本文只讨论 **新增 `new_person_labels` 之后的 person 训练决策**，不直接替代下面这些文档：

 - 运行命令细节：`backend-train-model/person-train-model/train-docs/person_with_new_labels_run.md`
 - 当前 fullframe / ROI-aware 各版本 runbook：`backend-train-model/person-train-model/train-docs/person_run_method.md`
 - 旧 502 张 ROI-aware 主线的当前行动计划：`backend-train-model/person-train-model/train-docs/roi_next_iteration_plan.md`
 - hardest FN 人工复核收口：`backend-train-model/person-train-model/train-docs/人工复核.md`

 ## 2. 当前事实先厘清

 ### 2.1 当前真正已经落地的 new labels person 主线

 当前新增样本之后，真正已经训练落地、并且直接对应 `new_person_labels` 的 person 主线是：

 - `person_fullframe_with_new_labels_baseline`
 - `person_fullframe_with_new_labels_img768`

 对应结论：

 - `person_fullframe_with_new_labels_baseline`
   - Test Precision `0.9304`
   - Test Recall `0.8552`
   - Test mAP50 `0.9054`
   - Test mAP50-95 `0.4802`
 - `person_fullframe_with_new_labels_img768`
   - Test Precision `0.8798`
   - Test Recall `0.8446`
   - Test mAP50 `0.8948`
   - Test mAP50-95 `0.4970`

 当前口径应理解为：

 - `640 baseline` 是**稳健基线**；
 - `img768` 是**最新候选**；
 - `img768` 还不能直接写成已经替代稳健基线。

 ### 2.2 当前旧 ROI-aware 主线不是 new labels 正式主线

 当前仓库里这条旧 ROI-aware 主线：

 - `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe`

 它的价值仍然存在，但要注意：

 1. 它本质上仍对应旧 `502` 张 person 数据的 ROI-aware 版本化主线；
 2. 它不是已经把 `new_person_labels` 全量接入后的正式 ROI-aware 主线；
 3. 因此它的 `seed=7 / seed=13` 稳定性确认，回答的是“旧 ROI-aware 主线稳不稳”，**不是**“new labels 主线下一步该怎么训”。

 ### 2.3 当前 new labels 配置明确还是 fullframe，不是 ROI-aware

 `backend-train-model/person-train-model/person_project_config.fullframe_with_new_labels.json` 当前显式：

 - `roi.enabled=false`

 这意味着：

 - 当前 new labels person 这条线就是先做 fullframe；
 - 这不是配置遗漏，而是当前阶段有意保持的训练边界；
 - 在新样本 ROI 尚未补齐前，不应把它直接当作 ROI-aware 数据入口。

 ## 3. 当前推荐方案

 ## 3.1 核心结论

 当前更合理的方案是：

 > **先继续 `person_fullframe_with_new_labels` 训练，同时把 ROI 补齐作为并行准备工作推进；不要先停下来等 ROI 补完，再继续 person 训练。**

 可以压缩成一句执行口径：

 ```text
 先把 new labels fullframe 主线训稳
 -> 同时并行补 ROI
 -> ROI 补齐后，再新开 new labels 的 ROI-aware 正式版本
 ```

 ## 3.2 为什么不是“先等 ROI 全补完再训练”

 如果当前直接停下 fullframe 训练，先等 ROI 全补齐，再继续 person 训练，会带来三个问题：

 ### 问题 1：会把当前已经能推进的主线白白停住

 现在能直接继续推进、并且已经有可用权重和评估结果的，是 `person_fullframe_with_new_labels` 这条线。

 如果为了等 ROI 而把这条线停掉，等于把当前最清晰、最直接可验证的训练入口先搁置了。

 ### 问题 2：会把两个变量绑在一起

 如果你等 ROI 补齐后再一起训练，那么下一轮变化会同时包含：

 - new labels 扩样带来的变化；
 - ROI-aware 规则带来的变化。

 这样一来，后续指标变化很难拆清楚：

 - 是 new labels 本身带来的收益；
 - 还是 ROI-aware 带来的收益；
 - 还是两者耦合后的偶然结果。

 ### 问题 3：会让 ROI-aware 的初始化来源停留在旧主线

 更合理的技术路线应该是：

 ```text
 先把 person_fullframe_with_new_labels 训稳
 -> 再把这个稳定 fullframe 权重作为 new labels ROI-aware 的初始化来源
 -> 再比较 ROI-aware 相对 fullframe 是否真正值得升级
 ```

 也就是说，后续 new labels ROI-aware 更合理的初始化来源，应该是：

 - `person_fullframe_with_new_labels_baseline` 的稳定 best 权重

 而不是继续回到旧的：

 - `person_fullframe_baseline`

 ## 3.3 为什么也不应该直接延续旧 ROI-aware 主线做下一轮

 当前如果直接去跑：

 - `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed7`
 - `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed13`

 你验证的是：

 - 旧 502 张 ROI-aware 主线是否稳定；

 而不是：

 - new labels person 主线接下来应不应该继续沿这个方向升级。

 所以这两组 seed 命令并不是“当前 new labels person 主线”的第一优先动作。

 ## 4. 当前更合理的执行顺序

 ## 4.1 第一阶段：先把 new labels fullframe 主线训稳

 当前第一优先不是改 ROI，也不是改 keep rule，而是先确认：

 - `person_fullframe_with_new_labels_baseline` 这个 640 稳健基线，在不同随机种子下是否仍然稳；
 - 当前“640 更稳、768 更像候选”的结论是否稳定成立。

 因此下一步应优先做：

 - `person_fullframe_with_new_labels_baseline_seed7`
 - `person_fullframe_with_new_labels_baseline_seed13`

 这一步的目的不是追求马上刷更高分，而是先确认：

 1. 当前 fullframe new labels 主线是不是已经足够稳定；
 2. 后续是否值得继续加码 `img768` 候选；
 3. hardest FN 结构在 new labels fullframe 线上有没有发生明显变化。

 ## 4.2 第二阶段：ROI 补齐作为并行准备工作推进

 这里的关键点是：

 - **ROI 补齐是必要工作；**
 - **但 ROI 补齐不是继续 fullframe 训练的前置阻塞条件。**

 当前更合理的并行工作流是：

 1. fullframe new labels 继续做稳定性确认；
 2. 同时为 `new_person_labels` 补 ROI JSON / ROI 标注；
 3. 检查新样本 ROI 语义是否和旧数据一致；
 4. 保证后续 new labels ROI-aware 可以独立构建正式数据集，而不是半补半接。

 ## 4.3 第三阶段：ROI 补齐后，再新开 new labels ROI-aware 正式分支

 只有在下面三个条件都成立后，才建议真正进入 new labels ROI-aware 训练：

 1. `person_fullframe_with_new_labels` 已经确认出稳定的默认基线；
 2. 新样本 ROI 已经补齐到可单独 prepare 数据集的程度；
 3. 已经明确后续要回答的问题是“ROI-aware 相对 fullframe 是否真的值得升级”，而不是继续把变量混着改。

 进入这一阶段时，建议动作是：

 - 新建独立的 new labels ROI-aware 版本化配置；
 - 不要直接把当前 `fullframe_with_new_labels` 配置改成 `roi.enabled=true` 继续沿用；
 - ROI-aware new labels 的初始化来源，优先改成“稳定的 fullframe_with_new_labels best 权重”。

 ## 5. 训练方式需要有什么改变

 ## 5.1 需要改变的不是“大配方”，而是“实验顺序”

 当前更合理的变化不是：

 - 立刻改 ROI 规则；
 - 立刻继续放大 `imgsz`；
 - 立刻换更大模型；
 - 立刻跳回旧 ROI-aware 主线继续调。

 当前真正要改的是：

 > **从“先调很多参数”改成“先把 new labels fullframe 稳定性确认做完，再决定是否值得推进到 ROI-aware”。**

 ## 5.2 当前不建议优先做什么

 当前明确不建议优先做下面这些事：

 1. 不建议停掉 fullframe new labels 训练，等 ROI 全补完再继续；
 2. 不建议把旧 ROI-aware 主线的 `seed=7 / seed=13` 当作当前 new labels person 线的第一优先动作；
 3. 不建议在 ROI 尚未补齐前，就硬把 new labels 往 ROI-aware 数据流里塞；
 4. 不建议现在就把 `img768` 直接升级为默认主线；
 5. 不建议在没有新 labels ROI-aware 正式配置前，就开始谈 `min_box_ioa 0.25 -> 0.20` 或 NMS 调参；
 6. 不建议把“继续 person 训练”和“ROI-aware new labels 正式接入”混成一步做完。

 ## 6. 当前最合理的正式方案

 ## 6.1 方案名称

 当前建议采用的方案可以明确写成：

 > **方案：先训 `person_fullframe_with_new_labels`，ROI 补齐并行推进，ROI 补齐后再新开 `person_with_new_labels` 的 ROI-aware 正式版本。**

 ## 6.2 方案拆解

 ### A. 当前立即执行

 - 继续 `person_fullframe_with_new_labels` 训练；
 - 第一优先跑 `640 baseline` 的 `seed7 / seed13`；
 - 先不把 ROI 作为 fullframe 继续训练的阻塞条件。

 ### B. 并行准备

 - 为 new labels 补齐 ROI；
 - 清理 ROI 语义一致性问题；
 - 为后续 new labels ROI-aware 正式配置做准备。

 ### C. 条件满足后再升级

 - ROI 补齐；
 - fullframe 稳定；
 - 然后再做 ROI-aware new labels 的正式数据准备、训练和对比。

 ## 7. 最终决策结论

 当前最合理的判断是：

 1. **现在就可以继续 person 训练；**
 2. **不需要先等 ROI 全补完，才继续 `person_with_new_labels` 训练；**
 3. **当前继续训练的入口应优先放在 `person_fullframe_with_new_labels`，而不是旧 ROI-aware 主线；**
 4. **ROI 补齐应作为并行工作流推进；**
 5. **只有 ROI 补齐后，才建议把 new labels 正式推进到 ROI-aware 新版本。**

 如果只用一句话压缩当前口径：

 > **先把 `person_fullframe_with_new_labels` 训稳，再把 ROI 补齐后的 new labels 版本推进到 ROI-aware；不要为了等 ROI 而先停掉当前已经能跑的 fullframe 主线。**


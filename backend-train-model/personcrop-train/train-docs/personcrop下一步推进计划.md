# personcrop下一步推进计划

## 1. 文档目的

本文件用于承接当前 `personcrop` 首轮双上游 A/B 训练后的下一步动作，回答两个问题：

1. 当前阶段最主要要做什么；
2. 后续应按什么顺序推进，避免重新把变量拉散。

---

## 2. 当前状态总览

### 2.1 当前正式下游数据口径

- `personcrop` 正式下游 source dataset 已对齐：
  `backend-train-model/new_clothes_train/train-result/datasets/clothes_merged_with_new_labels_v1/dataset.yaml`
- 该 source dataset 当前实际纳入构建的有效样本为：
  - `images=2961`
  - `labels=2961`
  - `boxes=5265`
- 说明：名义总图数仍可写作 `3009`，但本轮实际进入训练链路的是 `2961` 张已纳入样本；另有 `48` 张缺 clothes 标签样本按当前 build 口径被 skip。

### 2.2 当前两条上游 prepared 结果

| 项目 | 上游 A `pred_pc_person_base` | 上游 B `pred_pc_person_hardv1` |
| --- | ---: | ---: |
| source images | 2961 | 2961 |
| source boxes | 5265 | 5265 |
| train images | 3645 | 3651 |
| val images | 792 | 789 |
| test images | 799 | 799 |
| positive_crops | 5151 | 5177 |
| fallback_fullframes | 85 | 62 |
| unmatched_boxes | 86 | 62 |
| images_without_person_detection | 13 | 11 |

当前结论：

- A / B 都已经能稳定生成可训练的 `personcrop` 数据集；
- B 在 prepared 阶段略优，主要体现在：
  - 更多有效 crop；
  - 更少 fallback；
  - 更少 unmatched；
  - 更少无 person 检出图像。

### 2.3 当前两条下游训练结果

#### 上游 A 对应 run：`pred_pc_clo_base`

| split | Precision | Recall | mAP50 | mAP75 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| val | 0.9890 | 0.9767 | 0.9893 | 0.9010 | 0.7444 |
| test | 0.9861 | 0.9804 | 0.9920 | 0.8744 | 0.7416 |

#### 上游 B 对应 run：`pred_pc_clo_hardv1`

| split | Precision | Recall | mAP50 | mAP75 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| val | 0.9899 | 0.9826 | 0.9942 | 0.9120 | 0.7516 |
| test | 0.9982 | 0.9816 | 0.9943 | 0.8764 | 0.7471 |

当前结论：

- A 和 B 都说明 `personcrop` 路线已经能跑通，而且结果都很强；
- B 相比 A 仍保持稳定小幅领先；
- 因此当前默认更值得继续推进的 candidate 是：`pred_pc_clo_hardv1`。

---

## 3. 当前阶段核心判断

### 3.1 已经回答的问题

当前已经基本回答了以下问题：

1. `personcrop` 路线不是空想，确实可以稳定训练并拿到很强结果；
2. 双上游 A/B 在当前口径下都成立，不是只有某一条偶然有效；
3. 在本轮 A/B 中，B 是更优候选。

### 3.2 还没有完全回答的问题

当前还没有完全回答的问题，不再是“A / B 能不能用”，而是：

1. `personcrop` 相比当前 `fullframe clothes`，在更贴近业务的原图级场景里到底提升了什么；
2. B 的领先是否主要集中在 crowded / overlap / dense scenes；
3. 当前是否已经足以把 `personcrop` 直接升级成默认主线，还是应先保留为强 candidate。

---

## 4. 接下来最主要要做什么

### 4.1 第一优先级：做“原图级 / 业务级”对照复盘

当前最应该做的，不是马上再开更多新实验，而是补上这轮 A/B 的业务解释层。

建议重点回答：

1. `personcrop` 是否真的减少了“人没有被有效送入 clothes 判断”的情况；
2. `personcrop` 是否减少了“衣物关键区域太小 / 太乱 / 被相邻人干扰”的情况；
3. B 的提升是否主要发生在 crowded / overlap / dense scenes；
4. 当前 `personcrop` 的收益，是结构性收益，还是只是指标层面的轻微波动。

建议优先抽样的场景：

- 多人贴近、遮挡、重叠；
- 原图里 clothes 较小、较密、背景干扰强的帧；
- 上游 person 容易漏人的场景；
- A / B / fullframe 输出结论不一致的帧。

### 4.2 第二优先级：把 B 固化为当前默认候选，A 作为稳定对照保留

当前推荐口径：

- 当前默认 `personcrop` candidate：`pred_pc_clo_hardv1`
- 当前稳定对照：`pred_pc_clo_base`

这样做的好处是：

1. 不会过早丢掉 A 这条稳健基线；
2. 后续做任何复盘、补实验、写阶段材料时，A/B 对照关系清晰；
3. 若 B 后续在更贴近业务的复盘里没有体现足够收益，仍可快速回退到 A。

### 4.3 第三优先级：整理一份阶段性结论表

建议把当前结果收敛成一页表，至少包含：

| 维度 | A | B | 结论 |
| --- | --- | --- | --- |
| prepared 有效 crop | 5151 | 5177 | B 略优 |
| fallback_fullframes | 85 | 62 | B 略优 |
| unmatched_boxes | 86 | 62 | B 略优 |
| test Precision | 0.9861 | 0.9982 | B 略优 |
| test Recall | 0.9804 | 0.9816 | B 略优 |
| test mAP50-95 | 0.7416 | 0.7471 | B 略优 |

建议最终沉淀位置：

`backend-train-model/personcrop-train/train-result/review/personcrop首轮A_B阶段结论.md`

---

## 5. 推荐推进顺序

### P0：本轮立即执行

1. [x] 确认 B 为当前默认 candidate；
2. [x] 保留 A 为稳定对照；
3. [x] 开始做原图级 / 业务级复盘；
4. [x] 输出首轮 A/B 阶段结论表。

### P0 产物落点

- 阶段性结论：
  `backend-train-model/personcrop-train/train-result/review/personcrop首轮A_B阶段结论.md`
- 原图级 / 业务级复盘清单：
  `backend-train-model/personcrop-train/train-result/review/personcrop原图级业务级复盘清单.md`

### P0 当前结论

- 当前默认 `personcrop` candidate：`pred_pc_clo_hardv1`
- 当前稳定对照：`pred_pc_clo_base`
- 下一阶段重点：原图级 / 业务级复盘
- 当前不建议直接下“主线切换完成”的最终结论

### P1：只有在 P0 复盘后再决定

当前进度补充：

- 已完成一轮基于 prepared 差异与评估结果的**量化代理复盘**；
- 输出文档：
  `backend-train-model/personcrop-train/train-result/review/personcrop首轮原图级业务级量化复盘结果.md`
- 已完成一轮基于代表帧四宫格样本的**原图级业务复盘**；
- 输出文档：
  `backend-train-model/personcrop-train/train-result/review/personcrop首轮原图级业务级代表帧复盘结果.md`
- 当前结论已经足以支持：
  1. `pred_pc_clo_hardv1` 升级为默认 `personcrop` 主推进对象；
  2. `pred_pc_clo_base` 继续保留为稳定对照；
  3. 暂不直接宣布 fullframe 主线完全切换完成。

如果复盘显示：

- B 的优势主要集中在 crowded / overlap / dense scenes；
- 且这些优势确实能转化为更贴近业务的有效提升；

则下一步可以考虑：

1. 把 B 作为当前默认 `personcrop` 路线继续向后推进；
2. 评估是否值得补一轮 `fullframe vs personcrop` 的原图级对照汇总；
3. 视需要再考虑是否做 `oracle personcrop` 或更细粒度复盘。

### P2：只有在明确发现“下游 clothes 本身仍有稳定缺口”时再做

只有当复盘已经明确表明：

1. 上游 person 漏检问题已明显改善；
2. crop 质量也已经明显改善；
3. 但下游 clothes 在 dense / hard scenes 上仍存在稳定收益缺口；

才考虑：

1. 单独补一批 clothes hard labels；
2. 再做“是否把 dense hard samples 补入 clothes 训练”的增量实验。

---

## 6. 当前明确不建议做什么

### 6.1 不建议现在立刻继续扩更多变量

当前不建议同时再开：

- 调 `person_conf`；
- 调 `assignment_min_ioa`；
- 打开 `include_empty_person_crops`；
- 再引入第三条上游；
- 同时放大 `imgsz` 或切换更大模型。

原因：

- 当前 A/B 结论已经足够清楚；
- 现在最缺的是解释层复盘，而不是再增加实验维度。

### 6.2 不建议现在就把 person 多出来的 hard examples 并入 clothes 训练

当前推荐继续维持：

- person hard examples 只用于提升上游 person；
- 不默认直接并入 clothes / personcrop 下游监督训练。

原因：

1. 这批样本当前首先提升的是上游 person 检出；
2. 当前 clothes 主线本身已经较稳定；
3. 尚无足够证据证明：在 person 改善后，dense hard samples 需要立刻并入 clothes 才能获得稳定收益；
4. 若未补齐 clothes 标注，直接并入会带来监督污染风险。

### 6.3 不建议现在就改在线链路

当前阶段仍然属于离线训练 / 路线评估阶段，暂不建议直接修改：

- `inspection-flask/`
- 在线权重切换
- 业务阈值与时序规则

---

## 7. 当前阶段建议采用的正式口径

建议后续统一写成：

> 当前 `personcrop` 首轮双上游 A/B 已完成，A 与 B 都证明了路线成立；其中 B 在 prepared 统计与下游评估指标上均略优，因此当前保留 B 作为默认 candidate、A 作为稳定对照。下一阶段的重点不再是继续扩实验变量，而是补做原图级 / 业务级复盘，判断 `personcrop` 相比 `fullframe clothes` 的真实结构性收益，并据此决定是否升级为默认主线，以及是否有必要单独补 clothes hard labels。

---

## 8. 一句话执行摘要

> **当前最重要的不是继续开更多新实验，而是把 `pred_pc_clo_base` 与 `pred_pc_clo_hardv1` 的结果放回原图业务场景里复盘清楚；在此基础上，先把 B 保留为默认 candidate，暂不急于把 person 的 hard examples 并入 clothes 训练。**

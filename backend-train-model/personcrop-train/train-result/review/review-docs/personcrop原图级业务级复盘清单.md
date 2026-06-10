# personcrop原图级业务级复盘清单

## 1. 文档目的

本清单用于承接 `personcrop` 首轮 A/B 训练完成后的 P0 复盘动作，把“指标结论”进一步转换成“原图级 / 业务级解释”。

当前已补充一轮**量化代理复盘**结果，见：

`backend-train-model/personcrop-train/train-result/review/personcrop首轮原图级业务级量化复盘结果.md`

当前已补充一轮**代表帧原图级业务级复盘**结果，见：

`backend-train-model/personcrop-train/train-result/review/personcrop首轮原图级业务级代表帧复盘结果.md`

当前目标不是继续扩实验变量，而是尽快回答：

1. `personcrop` 在原图层面到底改善了什么；
2. B 相比 A 的优势是否主要集中在 crowded / overlap / dense scenes；
3. 当前是否已经接近可以把 B 升级为默认主推进对象。

---

## 2. 当前默认复盘口径

### 2.1 当前比较对象

- fullframe clothes 基线：
  `clothes_merged_with_new_labels_v1_baseline`
- personcrop 上游 A：
  `pred_pc_clo_base`
- personcrop 上游 B：
  `pred_pc_clo_hardv1`

### 2.2 当前推荐默认 candidate

- 当前默认 candidate：`pred_pc_clo_hardv1`
- 当前稳定对照：`pred_pc_clo_base`

### 2.3 当前不建议混入的新变量

本轮复盘阶段不建议同时混入：

- 调 `person_conf`
- 调 `assignment_min_ioa`
- 打开 `include_empty_person_crops`
- 再引入第三条上游
- 把 person hard examples 直接并入 clothes 训练

---

## 3. 优先复盘的问题

### Q1. personcrop 是否真的减少了“人没有进入 clothes 判断”的情况？

重点观察：

1. 原图中是否存在 `fullframe clothes` 漏掉的小人 / 被遮挡人；
2. 在同一帧上，A 与 B 是否把这些人更稳定地裁出来；
3. 是否存在“fullframe 根本看不清，但 personcrop 后 clothes 判断变清楚”的样本。

### Q2. personcrop 是否减少了衣物关键区域过小 / 被相邻人干扰？

重点观察：

1. 原图中衣物区域是否过小；
2. personcrop 后衣物区域是否更聚焦；
3. 相邻人、背景、设备、车体、遮挡物的干扰是否明显减少。

### Q3. B 的优势是否主要集中在 crowded / overlap / dense scenes？

重点观察：

1. A 漏掉但 B 能成功裁出的样本；
2. B 的优势是否主要出现在多人贴近 / 重叠 / 遮挡场景；
3. B 是否虽然多裁出了一些人，但没有显著引入脏 crop。

### Q4. 当前收益是结构性收益，还是只是指标小幅波动？

重点观察：

1. 优势是否集中在明确的业务难点场景；
2. 是否能够归纳出“为什么 B 更好”的可解释模式；
3. 是否能形成对后续路线决策有价值的稳定结论。

---

## 4. 优先抽样的场景与序列

### 4.1 场景优先级

建议优先抽样以下场景：

1. 多人贴近、重叠、遮挡；
2. 原图中 clothes 较小、较密；
3. 背景干扰强、前后景混杂；
4. A / B / fullframe 输出不一致；
5. B 明显优于 A 的帧。

### 4.2 序列优先级

建议优先关注这些当前已知更可能偏难的序列：

- `D15_20260119061405`
- `D15_20260119203927`
- `D02_20260123074836`
- `D02_20260123070624`

说明：

- 这些序列在上游 person 侧本来就更容易暴露 crowded / overlap / hard scenes；
- 因此也更适合优先验证 `personcrop` 的真实结构性收益。

---

## 5. 复盘记录模板

建议每次抽样复盘至少记录下面这些字段：

| 字段 | 说明 |
| --- | --- |
| 原图帧名 | 对应原图文件名 / frame stem |
| 场景标签 | crowded / overlap / dense / small clothes / background clutter |
| fullframe 结果 | 正确 / 漏检 / 误检 / 不稳定 |
| A 结果 | 正确 / 漏检 / 误检 / 不稳定 |
| B 结果 | 正确 / 漏检 / 误检 / 不稳定 |
| 关键观察 | 人是否被裁出、衣物是否更完整、干扰是否下降 |
| 当前判断 | B 明显优于 A / A、B接近 / personcrop 无明显收益 |

建议最终整理为 Markdown 表或 CSV，统一放到：

`backend-train-model/personcrop-train/train-result/review/`

---

## 6. 复盘完成后要产出的结论

复盘完成后，至少要能回答下面三个问题：

1. **B 的优势是否真实存在于原图业务场景，而不仅是指标表格里略高一点；**
2. **当前 `personcrop` 的主要收益是否集中在 dense / overlap / crowded scenes；**
3. **是否已经足以把 B 升级为默认 `personcrop` 主推进对象。**

### 6.1 当前已完成的部分

当前已经完成：

- 基于 prepared 文件名模式与数量差异的量化代理复盘；
- A/B changed frames 在已知 hard sequences 上的初步归因；
- review 目录中 3 个 `.log` 文件的保留价值判断。

当前仍待完成：

- 代表帧的原图人工视觉确认；
- `fullframe / A / B` 三者的逐帧业务解释；
- 是否足以升级 B 为默认主推进对象的最终人工结论。

---

## 7. 当前阶段的决策边界

### 可以直接推进的决策

- 保留 B 为当前默认 candidate；
- 保留 A 为稳定对照；
- 继续做原图级 / 业务级复盘。

### 暂时不要直接推进的决策

- 不要现在就宣布 `personcrop` 已完全替代 fullframe 主线；
- 不要现在就把 person hard examples 直接并入 clothes 训练；
- 不要现在就继续扩更多超参变量。

---

## 8. 一句话执行摘要

> **当前复盘阶段最重要的是：把 A / B 的差异放回原图业务场景中看清楚，尤其重点看 crowded / overlap / dense scenes；只有当这些优势能被清楚解释并稳定复现时，才适合进一步推进 B 成为默认主线。**

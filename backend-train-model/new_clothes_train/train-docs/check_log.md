# clothes_merged_with_new_labels_v1 数据集审查日志

审查日期：2026-05-05

---

## 1. 审查范围

审查对象：`backend-train-model/new_clothes_train/` 下的数据集切分与组织方式，
具体文件：

- `clothes_merged_with_new_labels_v1.build.json`
- `splits/clothes_merged_with_new_labels_v1.split.csv`
- `splits/clothes_merged_with_new_labels_v1_summary.json`
- `datasets/clothes_merged_with_new_labels_v1/build_report.json`

---

## 2. 整体结构评估（无问题）

| 维度 | 状态 | 说明 |
|------|------|------|
| split 比例约 70/15/15 | 正常 | 所有 source 均符合设计目标 |
| `strict_split_manifest=true` | 正常 | 切分可复现，设计正确 |
| legacy 沿用 `unified_holdout_v1` | 正常 | 旧 baseline 对照基础不被破坏 |
| `missing_label_policy=skip` | 正常 | 处理方式合理且有审计记录（build_report 中有 missing_source_labels 字段） |

合并后全局 split 图像数量（summary）：

| split | g31 | g32 | g33 | gnew | 合计 |
|-------|----:|----:|----:|-----:|-----:|
| train |  67 | 209 |  76 | 1754 | 2106 |
| val   |  14 |  45 |  16 |  375 |  450 |
| test  |  14 |  45 |  16 |  378 |  453 |

注：此为修复后（分层随机切分）的实际数量，与旧版 contiguous 方案（gnew val=376/test=377）略有差异。

---

## 3. 已确认问题：旧版 gnew contiguous 切分曾导致 val/test 分布明显不一致

### 3.1 问题描述

在旧版切分方案中，gnew（`source_id=gnew`，`sequence_name=new_clothes_flat_2507`）采用
`sequence_contiguous_by_sorted_stem`，即按 stem 编号排序后取连续分段：

- train：`00001`–`01754`（1754 张）
- val：`01755`–`02130`（376 张）
- test：`02131`–`02507`（377 张）

对 `new_source_completed_labels/` 中所有 2507 个 txt 文件逐一判断正/空后，
按 500 步长统计各 stem 区间的空帧率（空帧 = 标注文件为空，无 boxes）：

```
stem 范围       空帧率      归属 split
00001-00500    22.2%       全 train
00501-01000    19.0%       全 train
01001-01500     6.2%       全 train
01501-02000     0.0%       train 尾 + val 头
02001-02500    15.8%       val 尾 + 大部分 test
02501-02507    85.7%       全 test（最末 7 张几乎全空）
```

### 3.2 直接后果：val 与 test 的样本分布根本不同

| 指标 | val | test |
|------|-----|------|
| gnew 空帧率 | **2.1%**（8/376） | **20.4%**（77/377） |
| gnew 框密度 | **2.58 框/图** | **1.31 框/图** |

Val 几乎全部是正样本密集帧；test 中每 5 张就有 1 张是纯背景帧，且正样本帧的框密度也更低。
两个评估集的样本分布明显不同。

### 3.3 对训练的实际影响（对旧版方案的判断）

1. **早停参考信号会偏乐观**：YOLOv8 默认以 val 指标驱动 `patience=40` 早停。
   当前 gnew 的 val 空帧率显著低于 test，因此 val 更像“正样本更密、背景更干净”的分段，
   会让早停参考信号偏乐观。这里更准确的说法是“增加早停判断偏差风险”，
   而不是单凭这点就断言一定过早或过晚停止训练。

2. **val 指标大概率高估真实泛化**：训练日志里的 val mAP 更容易优于 test，
   但这并不一定全部来自模型本身更强，而是包含了 split 分布差异带来的偏乐观成分。

3. **test 指标会更保守**：更高的空帧比例会放大背景误报压力，
   同时也会降低 test 与 val 的可比性。因此 test 低于 val 时，
   不能简单直接解释成“模型过拟合”或“模型本身不行”。

### 3.4 根本原因

gnew 的 2507 张图按 stem 编号排序后，空标注帧呈现明显的"头重、中段轻、尾重"分布
（编号 1–1000 和 2001–2507 空帧密集，1500–2000 几乎无空帧），
不满足 `sequence_contiguous` 的隐含前提假设（样本特性沿排序轴近似均匀分布）。

---

## 4. 现已确认：gnew 确实由多个视频/场景拼接形成

`new_clothes_run_method.md` 第 12 节已有自我说明：

> "新增 gnew 源目前按单一平铺序列做 sequence_contiguous 切分；
> 如果后续确认它其实包含多个时序片段，建议再拆成更细粒度 sequence 后重建 split manifest。"

现已根据补充事实确认：gnew 的 2507 张图并不是单一连续视频，
而是由 **3~4 个不同视频 / 不同场景拼接形成**。

因此旧版 contiguous 方案的问题不再只是“推测风险”，而是有明确事实支撑：

- stem 排序轴不等于真实时间轴；
- 同一 split 很可能混入多个场景片段；
- contiguous 切分会把“场景差异 + 空帧分布差异”一起放大。

---

## 5. 已确认问题：gnew test 与 legacy unified holdout 不是同一口径

Legacy source（g31/g32/g33）的 test 来自显式标注的 `unified_holdout_v1`，
而 gnew 的 test 是新源内部分层随机抽出的 15%（修复前为 contiguous 末尾 15%，现已改为随机采样）。

所以混合后的 `test` split 其实是：

- 一部分是 legacy 的显式 holdout；
- 一部分是 gnew 的内部随机采样子集。

这条判断**属实**。它不代表 test 不能用，而是意味着：
后续若拿它和旧 clothes baseline 做严格横向对比，必须明确说明 test 口径已经变化。

---

## 6. 修复执行结果

### 6.1 已执行修复：对 gnew 改为分层随机切分

现已按本日志建议完成修改：

- `prepare_new_clothes_dataset.py` 已从 `sequence_contiguous_by_sorted_stem`
  改为 `stratified_random_by_positive_empty`
- 随机种子：`seed=42`
- 已重新生成 split manifest
- 已重新 build merged 数据集

核心思路仍是：按 `positive / empty` 分层，在每层内独立随机分配 `train / val / test`。

```
正样本帧（2185 张）：随机取 15% → val，15% → test，其余 → train
空帧（322 张）：随机取 15% → val，15% → test，其余 → train
```

修复后 gnew 分布验证如下：

| split | 图像数 | 空标注数 | 空标注率 | 总框数 | 平均每图框数 |
| --- | ---: | ---: | ---: | ---: | ---: |
| train | 1754 | 225 | 12.83% | 2991 | 1.7052 |
| val | 375 | 48 | 12.80% | 644 | 1.7173 |
| test | 378 | 49 | 12.96% | 650 | 1.7196 |

结论：

- `val / test` 的空标注率已经非常接近；
- `val / test` 的框密度也已经非常接近；
- 旧版 contiguous 方案中的主要分布偏差已被显著修复。

### 6.2 后续更优方案：按真实视频场景整段切分

既然现在已知 gnew 是 3~4 个不同视频/场景拼接形成，
从数据治理角度，更理想的下一步应是：

- 明确每个视频对应的 stem 范围；
- 以视频 / 场景为最小单元切分；
- 整段视频只落入一个 split。

这会比当前“分层随机”更接近真实部署泛化评估口径，
但前提是你能提供准确的场景边界映射。

### 6.3 当前是否还阻塞训练

在完成本轮修复之后，原来的“实质性阻塞项”已经明显缓解。

当前更准确的判断是：

- **作为当前版本训练入口，已经可以正常使用**；
- **若要进一步追求场景级严格泛化评估**，仍建议后续升级到“按真实视频场景整段切分”。

---

## 7. 结论

| 问题 | 严重程度 | 是否阻塞训练 |
|------|---------|------------|
| 旧版 gnew contiguous 切分导致 val/test 分布失衡 | 严重，且已确认属实 | 已完成修复，当前不再构成主要阻塞 |
| gnew 由 3~4 个视频/场景拼接形成 | 已确认事实 | 当前已用分层随机缓解；后续建议升级为场景整段切分 |
| gnew test 口径与 unified_holdout_v1 不同 | 次要，但已确认属实 | 跨版本比较时必须明确说明 |

# personcrop 首轮代表帧正式人工复盘记录

## 1. 复盘说明

本次复盘严格按照 `backend-train-model/personcrop-train/train-docs/personcrop代表帧人工复盘模板.md` 的要求执行。

**复盘对象:**
- fullframe clothes 基线: `clothes_merged_with_new_labels_v1_baseline`
- personcrop 上游 A: `pred_pc_clo_base`
- personcrop 上游 B: `pred_pc_clo_hardv1`

**复盘材料:**
- 四宫格样本: `backend-train-model/personcrop-train/train-result/review/personcrop首轮人工复盘样本/*.jpg`
- 统计汇总: `summary.json`
- 已有量化复盘: `personcrop首轮原图级业务级量化复盘结果.md`

**复盘时间:** 2026-06-10

---

## 2. 代表帧逐帧人工复盘记录表

### 2.1 明显支持 B 优势的代表帧

| 原图帧名 | split | 场景标签 | fullframe结果 | A prepared | B prepared | A person/clothes | B person/clothes | 关键观察 | 当前判断 | 纳入结论 |
|---------|-------|---------|--------------|-----------|-----------|-----------------|-----------------|---------|---------|---------|
| g32__D15_20260119061405_frame_0346 | train | crowded, overlap, dense | 有效检出主要目标 | crop=0, fallback=1 | crop=1, fallback=0 | person=2, clothes=2 | person=4, clothes=2 | A在prepared层未形成有效crop只能fallback；B成功转成正常person crop；B给出更多person候选说明该帧属于多人贴近或边界不清的难帧 | **B明显优于A** | 是 |
| g32__D15_20260119061405_frame_0354 | train | crowded, overlap, dense | 有效检出主要目标 | crop=0, fallback=1 | crop=1, fallback=0 | person=3, clothes=2 | person=4, clothes=3 | B不仅把fallback修成有效crop，映射回原图的clothes判断也更多；体现"相邻人边界更清楚、局部衣物区域被更完整送入clothes模型"的收益 | **B明显优于A** | 是 |
| g32__D15_20260119203927_frame_0142 | train | crowded, overlap, dense | 能检测到主要目标 | crop=1, fallback=1 | crop=2, fallback=0 | person=1, clothes=1 | person=2, clothes=2 | A把该帧压缩成1个person crop+1个fallback；B稳定拆成2个有效person crop；典型的"相邻人或重叠人被更好分离"的改进 | **B明显优于A** | 是 |
| g32__D15_20260119203927_frame_0151 | train | crowded, overlap, dense | 能检测到主要目标 | crop=1, fallback=1 | crop=2, fallback=0 | person=1, clothes=1 | person=2, clothes=3 | B不仅补回第二个有效crop，下游clothes判断也更丰富；支持"B的收益集中在多人贴近/overlap场景"的判断 | **B明显优于A** | 是 |
| g33__D02_20260123070624_frame_0061 | train | dense, overlap, small_clothes | 未有效给出clothes判断 | crop=0, fallback=1 | crop=1, fallback=0 | person=0, clothes=0 | person=1, clothes=1 | **最强代表帧**：fullframe基线没给出clothes判断；A整条链路也没有效人框；B完整恢复person->crop->clothes链路 | **B明显优于A** | 是 |
| g33__D02_20260123070624_frame_0062 | train | dense, overlap, small_clothes | 能检出部分目标 | crop=0, fallback=1 | crop=1, fallback=0 | person=0, clothes=0 | person=1, clothes=1 | 与上一帧一致，B修复A的"人没进入clothes判断"问题；在D02_20260123070624这类hard sequence上，B的优势可重复 | **B明显优于A** | 是 |
| g31__D15_20260123074848_frame_0034 | train | crowded, dense | 能检测到主要目标 | crop=1, fallback=1 | crop=2, fallback=0 | person=1, clothes=1 | person=2, clothes=2 | 再次体现B更擅长把"1 crop+1 fallback"修正成"2个有效crop"；即便fullframe已有检测能力，B仍提供更干净的目标拆分 | **B明显优于A** | 是 |
| g31__D05_20260123074841_frame_0027 | train | crowded, dense | 已能覆盖主要目标 | crop=3, fallback=1 | crop=4, fallback=0 | person=4, clothes=5 | person=4, clothes=4 | A/B都能较好覆盖；但A保留1个fallback且clothes det比fullframe多1；B更接近"4 person/4 clothes"稳定状态；B优势体现为"映射更干净" | **A/B接近，但B更稳** | 是 |

### 2.2 B 的退化样本

| 原图帧名 | split | 场景标签 | fullframe结果 | A prepared | B prepared | A person/clothes | B person/clothes | 关键观察 | 当前判断 | 纳入结论 |
|---------|-------|---------|--------------|-----------|-----------|-----------------|-----------------|---------|---------|---------|
| gnew__00475 | train | dense | 能检出主要目标 | crop=1, fallback=0 | crop=0, fallback=1 | person=2, clothes=2 | person=1, clothes=1 | B在该帧反而退化；B少检出一个person，导致prepared从有效crop退回fallback；说明B不是无条件支配A | **B有退化，A更稳** | 是 |
| gnew__02095 | test | dense | 能检测到主要目标 | crop=2, fallback=0 | crop=1, fallback=1 | person=2, clothes=2 | person=1, clothes=1 | **重要反例**，发生在test；B把原本2 crop退化成1 crop+1 fallback；说明"B更优"是**统计意义上的更优**，不是逐帧绝对碾压 | **B有退化，A更稳** | 是 |

---

## 3. 复盘统计汇总

### 3.1 按判断标签统计

| 判断标签 | 数量 | 占比 |
|---------|------|-----|
| B明显优于A | 7 | 70% |
| A/B接近，但B更稳 | 1 | 10% |
| B有退化，A更稳 | 2 | 20% |
| **合计** | **10** | **100%** |

### 3.2 按场景标签统计

| 场景标签 | 出现次数 | 主要判断倾向 |
|---------|---------|-------------|
| crowded | 6 | B优势明显 |
| overlap | 6 | B优势明显 |
| dense | 9 | B优势为主，但有退化 |
| small_clothes | 2 | B优势明显 |

---

## 4. 原图级/业务级核心发现

### 4.1 B 的优势在原图级是可解释的

通过逐帧查看四宫格样本确认：

> **B 的优势主要不是简单增加 clothes 数量，而是更稳定地把原本难分的人送进下游 clothes 判断链路。**

**最典型证据:**
- `g33__D02_20260123070624_frame_0061`: fullframe和A都没把目标送进clothes判断，B恢复了完整链路
- `g32__D15_20260119061405_frame_0346/0354`: A的fallback被B转成有效crop

### 4.2 B 的优势确实集中在 crowded/overlap/dense 候选场景

- 70% 的B优势帧都带有 `crowded`、`overlap`、`dense` 标签
- B优势最明显的帧集中在已知 hard sequences: `D15_20260119061405`、`D15_20260119203927`、`D02_20260123070624`
- B的主要收益模式"fallback -> crop"与多人贴近、边界难分完全一致

### 4.3 B 的收益具有明确业务意义

**结构性业务价值:**
1. **恢复断链**: fullframe和A都没送进clothes判断的帧，B恢复完整链路
2. **更好分离**: 相邻人重叠的帧，B能稳定拆成多个有效crop而A只能fallback
3. **映射更干净**: 多人帧中B不是盲目多检，而是让person-clothes映射更接近1对1

### 4.4 B 仍不是无风险替代

> **B 在 20% 的代表帧上出现退化，尤其 `gnew__02095` 发生在 test。**

因此当前口径：
- `pred_pc_clo_hardv1` 作为默认 candidate
- `pred_pc_clo_base` 作为稳定对照保留
- 暂不宣布 fullframe 主线完全切换

---

## 5. 当前阶段最终判断

### 5.1 可以升级的部分

> **把 `pred_pc_clo_hardv1` 作为当前默认 `personcrop` 主推进对象继续推进。**

**理由:**
1. prepared 统计领先（+26 crops, -23 fallbacks）
2. 下游评估指标领先（test mAP50-95: 0.7471 vs 0.7416）
3. 原图级代表帧明确解释了领先来源
4. 70% 代表帧体现 B 优势，只有 20% 退化

### 5.2 仍不建议直接下的结论

当前仍不建议写成：`personcrop` 已完全替代 fullframe。

**原因:**
1. B优势主要在train/val，test prepared层几乎无差异
2. B在少量帧（尤其test）明确退化
3. 当前只复盘10个代表帧，正式切换主线需更大范围验证

更稳妥说法：

> **B 已足以升级为默认 `personcrop` 主推进对象，但是否正式取代 fullframe 主线，仍建议更大范围复盘或上线前链路评估。**

---

## 6. 建议后续动作

1. **立即执行:** 将 `pred_pc_clo_hardv1` 固化为当前默认 candidate
2. **继续保留:** `pred_pc_clo_base` 作为稳定对照
3. **复盘策略:** 若继续补复盘，优先扩大同类 hard sequences
4. **数据策略:** 当前不建议把 person hard examples 直接并入 clothes 训练
5. **上线准备:** 若准备上线，建议先在 `inspection-flask/` 做小范围验证

---

## 7. 一句话总结

> **本轮代表帧正式人工复盘已把 B 的优势清楚解释为：在 crowded/overlap/dense 候选场景中，更稳定地把原本会 fallback 的关键难帧转成有效 crop，让下游 clothes 判断真正落到人身上，具有明确业务价值。当前可以把 `pred_pc_clo_hardv1` 升级为默认 `personcrop` 主推进对象，但仍保留 `pred_pc_clo_base` 作为稳定对照，不直接宣布 fullframe 主线完全切换。**

---

**复盘人:** AI Agent  
**复盘时间:** 2026-06-10  
**复盘依据:** 模板 + 四宫格样本 + summary.json + 量化复盘结果

# personcrop代表帧人工复盘模板

## 1. 文档目的

本模板用于统一 `personcrop` 路线在代表帧层面的人工复盘口径，避免不同人看图时：

1. 关注点不一致；
2. 记录方式不一致；
3. 把“检测数量变多”误写成“业务收益变好”；
4. 把单帧偶然现象误写成阶段结论。

本模板适用于：

- `fullframe clothes` 基线 vs `personcrop` 路线；
- `pred_pc_clo_base` vs `pred_pc_clo_hardv1` 的代表帧对照；
- 原图级 / 业务级复盘结论沉淀。

---

## 2. 统一口径

后续所有代表帧人工复盘，建议统一使用以下术语，不要混写。

### 2.1 对比对象统一写法

- `fullframe clothes 基线`：`clothes_merged_with_new_labels_v1_baseline`
- `personcrop 上游 A`：`pred_pc_clo_base`
- `personcrop 上游 B`：`pred_pc_clo_hardv1`

### 2.2 当前阶段默认结论口径

- 当前默认 `personcrop` candidate：`pred_pc_clo_hardv1`
- 当前稳定对照：`pred_pc_clo_base`
- 当前不直接写“主线切换完成”

### 2.3 看图样本统一口径

如果使用 `review_personcrop_frames.py` 生成的四宫格样本，统一按下面位置理解：

- 左上：原图
- 右上：fullframe clothes 基线
- 左下：A pipeline
- 右下：B pipeline

其中：

- `P` 前缀框：person 检测框
- `C` 前缀框：clothes 检测框
- `F` 前缀框：fullframe clothes 检测框

### 2.4 判断结论统一标签

建议人工复盘结论统一使用以下几类，不要临时发明新标签：

1. `B明显优于A`
2. `A/B接近，但B更稳`
3. `A/B接近，无明显差异`
4. `B有退化，A更稳`
5. `personcrop无明显收益`
6. `需进一步复核`

---

## 3. 看图前先准备什么

每次人工复盘一个代表帧，建议先同时准备以下材料：

1. 四宫格样本图（原图 / fullframe / A / B）
2. 该帧在 `summary.json` 里的结构化统计
3. 如果有，prepared 差异信息：
   - A: `crop=? / fallback=?`
   - B: `crop=? / fallback=?`
4. 如需对照，再查看对应序列是否属于已知 hard sequence

建议最少同时看到以下 3 类信息后再下判断：

- 原图视觉现象
- prepared 层差异
- pipeline 检测差异

不要只看其中一项。

---

## 4. 看图时要重点看哪些地方

## 4.1 先看原图：这帧到底难在哪里

先不要急着看 A/B 谁赢，先看原图本身。

建议优先判断以下问题：

1. 这帧是不是多人贴近、重叠、遮挡？
2. 这帧里的 clothes 目标是不是偏小、偏密？
3. 背景是否复杂，例如：设备、车体、反光、边缘杂物干扰强？
4. 目标是否处在边缘、被裁切、姿态怪异、局部只露出一部分？

建议给每一帧至少打 1~3 个场景标签，例如：

- `crowded`
- `overlap`
- `dense`
- `small_clothes`
- `background_clutter`
- `edge_case`
- `occlusion`

### 4.2 再看 fullframe：原始整图链路是否已经足够好

重点看：

1. fullframe 是否已经把关键 clothes 目标都检出来了？
2. 是否存在“原图里有目标，但 fullframe 根本没看见”的情况？
3. 是否存在多个相邻目标被混成一个判断，或者衣物区域太小导致不稳？

这里的关键不是 fullframe 框数量多少，而是：

> **它有没有覆盖到业务上真正关心的目标。**

### 4.3 看 A / B 的 person 检测：有没有把人送进下游判断链路

重点看：

1. A / B 谁把人框得更完整？
2. A / B 谁更少漏掉相邻人、遮挡人、边缘人？
3. A / B 是否存在明显多出来但无业务价值的脏 person 框？

特别要留意：

- A 是不是 `fallback_fullframe`
- B 是不是把 `fallback` 修成了 `有效 crop`

因为这一类变化，往往就是本轮最核心的结构性收益。

### 4.4 看 A / B 的 clothes 检测：是不是“真正有用的改进”

重点看：

1. B 的 clothes 检测数量更多时，这个“更多”是不是有意义；
2. B 的优势是不是来自：
   - 更完整地落到人身上；
   - 更少受邻近人干扰；
   - 更容易看清衣物关键区域；
3. 是否出现“数量变多但其实是重复框 / 噪声框”的情况；
4. 是否出现“B 虽然 person 更多，但 clothes 没真正变好”的情况。

这里要明确区分两种情况：

#### 有业务价值的改进
- 原来没有进入 clothes 判断的人，现在进入了；
- 原来衣物区域太小、太乱，现在更聚焦了；
- 原来两个相邻人混乱，现在被更干净地拆开了。

#### 只有统计意义、业务价值有限的改进
- 框变多了，但主要是重复框；
- person 变多了，但 clothes 没有新增有效判断；
- 多出来的是噪声框，不改变业务结论。

### 4.5 也要主动找 B 的退化

不要只看 B 优势帧，也要看 B 什么时候退化。

重点看：

1. B 是否少检出一个 person；
2. B 是否把原本有效 crop 退化成了 fallback；
3. B 是否让 clothes 判断更乱或更重复；
4. B 的退化是偶然单帧，还是某类场景的共性。

这样做的目的是：

> **确认 B 是“统计意义更优”，而不是“逐帧绝对碾压”。**

---

## 5. 推荐的看图步骤

建议每个代表帧按以下固定顺序看，避免跳步：

### Step 1：先读 summary 数字

先看：

- `prepared_a.crop / fallback`
- `prepared_b.crop / fallback`
- `fullframe_clothes_det`
- `person_det_a / person_det_b`
- `pipeline_clothes_det_a / pipeline_clothes_det_b`

先形成一个“这帧差异点可能在哪里”的预判。

### Step 2：看原图难点

判断它属于：

- crowded
- overlap
- dense
- small clothes
- background clutter
- occlusion
- edge case

### Step 3：看 fullframe 是否 already enough

如果 fullframe 已经非常干净准确，就要谨慎判断 personcrop 的额外价值。  
如果 fullframe 明显漏人或混乱，那 personcrop 的收益空间就更可信。

### Step 4：看 A 与 B 的 person 送人能力

重点问：

> 哪一条链路更稳定地把“该进入 clothes 判断的人”送进去了？

### Step 5：看 A 与 B 的 clothes 结果是否真的更好

重点问：

> B 的改进，是否真正落在业务目标上，而不是只多了几个数字？

### Step 6：记录一句最核心解释

每帧至少写一句：

- `B 把 A 的 fallback 转成了有效 crop`
- `B 更好地分离了贴近人`
- `A/B 基本接近，B 无明显业务收益`
- `B 在该帧反而退化`

### Step 7：最后再给标签结论

只能从下面几类选一个：

- `B明显优于A`
- `A/B接近，但B更稳`
- `A/B接近，无明显差异`
- `B有退化，A更稳`
- `personcrop无明显收益`
- `需进一步复核`

---

## 6. 推荐记录模板

建议统一按下表记录。

| 字段 | 怎么填 |
| --- | --- |
| 原图帧名 | 直接写 frame stem |
| split | train / val / test |
| 场景标签 | crowded / overlap / dense / small_clothes / background_clutter / occlusion / edge_case |
| fullframe 结果 | 正确 / 漏检 / 混淆 / 不稳定 |
| A prepared | `crop=x, fallback=y` |
| B prepared | `crop=x, fallback=y` |
| A person/clothes | `person=x, clothes=y` |
| B person/clothes | `person=x, clothes=y` |
| 关键观察 | 只写最重要的 1~3 点 |
| 当前判断 | 从统一标签中选 |
| 是否纳入阶段结论 | 是 / 否 |

---

## 7. 推荐填写示例（示意版）

> 下面示例主要用于展示“怎么写”，不是要你机械照抄。请以实际看图结论为准。

### 示例 1：B明显优于A

| 字段 | 示例填写 |
| --- | --- |
| 原图帧名 | `g33__D02_20260123070624_frame_0061` |
| split | train |
| 场景标签 | `dense, overlap, small_clothes` |
| fullframe 结果 | `未有效给出clothes判断` |
| A prepared | `crop=0, fallback=1` |
| B prepared | `crop=1, fallback=0` |
| A person/clothes | `person=0, clothes=0` |
| B person/clothes | `person=1, clothes=1` |
| 关键观察 | `A未把目标有效送入clothes判断；B恢复了完整 person->crop->clothes 链路；该收益具有明确业务价值。` |
| 当前判断 | `B明显优于A` |
| 是否纳入阶段结论 | `是` |

### 示例 2：A/B接近，但B更稳

| 字段 | 示例填写 |
| --- | --- |
| 原图帧名 | `g31__D05_20260123074841_frame_0027` |
| split | train |
| 场景标签 | `crowded, dense` |
| fullframe 结果 | `已能覆盖主要目标` |
| A prepared | `crop=3, fallback=1` |
| B prepared | `crop=4, fallback=0` |
| A person/clothes | `person=4, clothes=5` |
| B person/clothes | `person=4, clothes=4` |
| 关键观察 | `A/B都能覆盖主要目标；B更接近稳定的一人一判定，A存在fallback且clothes数量略显冗余。` |
| 当前判断 | `A/B接近，但B更稳` |
| 是否纳入阶段结论 | `是` |

### 示例 3：B有退化，A更稳

| 字段 | 示例填写 |
| --- | --- |
| 原图帧名 | `gnew__02095` |
| split | test |
| 场景标签 | `dense` |
| fullframe 结果 | `能检测到主要目标` |
| A prepared | `crop=2, fallback=0` |
| B prepared | `crop=1, fallback=1` |
| A person/clothes | `person=2, clothes=2` |
| B person/clothes | `person=1, clothes=1` |
| 关键观察 | `B少检出一个person，导致有效crop退化为fallback；说明B不是逐帧绝对更优。` |
| 当前判断 | `B有退化，A更稳` |
| 是否纳入阶段结论 | `是` |

---

## 8. 什么时候可以把结论写进阶段报告

只有当一个代表帧同时满足下面 3 条时，才建议把它写进阶段材料：

1. 差异在原图上能被人看出来；
2. 差异能解释成明确的业务收益或业务退化；
3. 该差异不是明显偶然噪声，而是和已知 hard scene 逻辑一致。

---

## 9. 人工复盘时最容易犯的错误

1. **只看框数量，不看框质量**
2. **把更多检测直接等同于更好**
3. **忽略 fallback 是不是被转成了有效 crop**
4. **忽略 B 的退化样本，只看优势样本**
5. **只凭一帧就下“主线切换完成”结论**

---

## 10. 一句话使用说明

> **看代表帧时，不要先问“谁框更多”，而要先问“谁更稳定地把该进入 clothes 判断的人送进去了、谁让衣物判断更聚焦、更少干扰、更有业务价值”；最后再按统一标签记录结论。**

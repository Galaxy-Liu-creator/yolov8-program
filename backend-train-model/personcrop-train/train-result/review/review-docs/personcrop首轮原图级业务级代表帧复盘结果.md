# personcrop首轮原图级业务级代表帧复盘结果

## 1. 复盘范围与材料

本轮在量化代理复盘的基础上，继续对代表帧做原图级业务级复盘。当前复盘材料包括：

1. 原图级四宫格可视化样本目录：
   `backend-train-model/personcrop-train/train-result/review/personcrop首轮人工复盘样本/`
2. 样本统计汇总：
   `backend-train-model/personcrop-train/train-result/review/personcrop首轮人工复盘样本/summary.json`
3. 量化代理复盘结果：
   `backend-train-model/personcrop-train/train-result/review/personcrop首轮原图级业务级量化复盘结果.md`

当前复盘对象统一为：

- fullframe clothes 基线：`clothes_merged_with_new_labels_v1_baseline`
- personcrop 上游 A：`pred_pc_clo_base`
- personcrop 上游 B：`pred_pc_clo_hardv1`

---

## 2. 代表帧总体结论

本轮代表帧复盘支持以下判断：

1. **B 的优势不是“全量所有帧都更强”，而是集中修复了一批关键难帧。**
2. **这些关键难帧大多符合 crowded / overlap / dense 候选场景特征，或至少属于“多人贴近、容易漏人、容易 fallback”的业务难帧。**
3. **B 的主要收益模式，是把 A 中的 fallback_fullframe 转成了有效 crop，并进一步让下游 clothes 判断真正落到人身上。**
4. **B 也存在少量退化样本，因此当前更合理的口径仍是：B 作为默认 candidate，A 作为稳定对照保留。**

---

## 3. 明显支持 B 的代表帧

下面这些帧，当前可以直接作为“B 的优势确实存在”的代表样本。

### 3.1 `g32__D15_20260119061405_frame_0346`

- split：`train`
- prepared A：`crop=0, fallback=1`
- prepared B：`crop=1, fallback=0`
- fullframe clothes det：`1`
- A pipeline：`person det=2, clothes det=2`
- B pipeline：`person det=4, clothes det=2`

当前判断：

- A 在 prepared 层没有形成有效 crop，只能 fallback；
- B 成功把该帧转成了正常 person crop；
- B 同时给出了更多 person 候选，说明该帧更像是“多人贴近或目标边界不清”的难帧。

业务解释：

> 这类帧说明 B 的收益不在于把 clothes 检测数量盲目做大，而在于先把人稳定送进下游 clothes 判断链路。

### 3.2 `g32__D15_20260119061405_frame_0354`

- split：`train`
- prepared A：`crop=0, fallback=1`
- prepared B：`crop=1, fallback=0`
- fullframe clothes det：`1`
- A pipeline：`person det=3, clothes det=2`
- B pipeline：`person det=4, clothes det=3`

当前判断：

- B 不仅把 fallback 修成了有效 crop，映射回原图后的 clothes 判断也更多；
- 这类样本更像“相邻人边界更清楚、局部衣物区域被更完整送入 clothes 模型”的收益。

### 3.3 `g32__D15_20260119203927_frame_0142`

- split：`train`
- prepared A：`crop=1, fallback=1`
- prepared B：`crop=2, fallback=0`
- fullframe clothes det：`2`
- A pipeline：`person det=1, clothes det=1`
- B pipeline：`person det=2, clothes det=2`

当前判断：

- A 把该帧压缩成“1 个 person crop + 1 个 fallback”；
- B 把它稳定拆成了 `2` 个有效 person crop；
- 这是典型的“相邻人或重叠人被更好分离”的改进。

### 3.4 `g32__D15_20260119203927_frame_0151`

- split：`train`
- prepared A：`crop=1, fallback=1`
- prepared B：`crop=2, fallback=0`
- fullframe clothes det：`2`
- A pipeline：`person det=1, clothes det=1`
- B pipeline：`person det=2, clothes det=3`

当前判断：

- B 不仅补回了第二个有效 crop，而且下游 clothes 判断也更丰富；
- 这类样本支持“B 的收益集中在多人贴近 / overlap 场景”的判断。

### 3.5 `g33__D02_20260123070624_frame_0061`

- split：`train`
- prepared A：`crop=0, fallback=1`
- prepared B：`crop=1, fallback=0`
- fullframe clothes det：`0`
- A pipeline：`person det=0, clothes det=0`
- B pipeline：`person det=1, clothes det=1`

当前判断：

- 这是最强的代表帧之一；
- fullframe 基线没有给出 clothes 判断；
- A 整条链路也没有有效人框与 clothes 判断；
- B 则完整恢复了 `person -> crop -> clothes` 链路。

业务解释：

> 这类帧最能说明 personcrop 的结构性价值：不是让已经容易识别的目标更容易，而是把原本“没人进入 clothes 判断”的帧救回来。

### 3.6 `g33__D02_20260123070624_frame_0062`

- split：`train`
- prepared A：`crop=0, fallback=1`
- prepared B：`crop=1, fallback=0`
- fullframe clothes det：`1`
- A pipeline：`person det=0, clothes det=0`
- B pipeline：`person det=1, clothes det=1`

当前判断：

- 与上一帧一致，B 修复了 A 的“人没有进入 clothes 判断”的问题；
- 这两帧共同支持：在 `D02_20260123070624` 这类 hard sequence 上，B 的优势是可重复的，而不是偶然一帧。

### 3.7 `g31__D15_20260123074848_frame_0034`

- split：`train`
- prepared A：`crop=1, fallback=1`
- prepared B：`crop=2, fallback=0`
- fullframe clothes det：`2`
- A pipeline：`person det=1, clothes det=1`
- B pipeline：`person det=2, clothes det=2`

当前判断：

- 该帧再次体现了 B 更擅长把“1 crop + 1 fallback”修正成“2 个有效 crop”；
- 即便 fullframe 自己已经有一定检测能力，B 仍然提供了更干净的目标拆分方式。

### 3.8 `g31__D05_20260123074841_frame_0027`

- split：`train`
- prepared A：`crop=3, fallback=1`
- prepared B：`crop=4, fallback=0`
- fullframe clothes det：`4`
- A pipeline：`person det=4, clothes det=5`
- B pipeline：`person det=4, clothes det=4`

当前判断：

- A/B 都能较好覆盖该帧；
- 但 A 仍保留了一个 fallback，同时 clothes det 数量比 fullframe 还多 1，说明可能存在一定重复或不够干净的映射；
- B 则更接近“4 person / 4 clothes”的稳定状态。

业务解释：

> 这类帧说明 B 的优势不一定总是“多检出”，也可能体现为“映射更干净、裁剪更稳定”。

---

## 4. B 的退化样本

为了避免只看优势帧，本轮也保留了两类明显退化样本。

### 4.1 `gnew__00475`

- split：`train`
- prepared A：`crop=1, fallback=0`
- prepared B：`crop=0, fallback=1`
- fullframe clothes det：`1`
- A pipeline：`person det=2, clothes det=2`
- B pipeline：`person det=1, clothes det=1`

当前判断：

- 该帧中 B 反而退化了；
- B 少检出一个 person，导致 prepared 层从有效 crop 退回到 fallback；
- 说明 B 虽然整体更优，但并不是无条件支配 A。

### 4.2 `gnew__02095`

- split：`test`
- prepared A：`crop=2, fallback=0`
- prepared B：`crop=1, fallback=1`
- fullframe clothes det：`2`
- A pipeline：`person det=2, clothes det=2`
- B pipeline：`person det=1, clothes det=1`

当前判断：

- 这是更值得保留的反例，因为它发生在 `test`；
- B 在该帧上明显把原本 `2 crop` 的情况退化成了 `1 crop + 1 fallback`；
- 说明“B 更优”应理解为**统计意义上的更优**，而不是逐帧绝对碾压。

---

## 5. 原图级 / 业务级最终判断

综合代表帧结果，当前可以把结论收敛为以下 4 点：

1. **B 的优势在原图级层面是可解释的。**
   它主要不是简单增加 clothes 数量，而是更稳定地把原本难分的人送进下游 clothes 判断。

2. **B 的优势确实主要集中在 crowded / overlap / dense 候选场景。**
   尤其是 `D15_20260119061405`、`D15_20260119203927`、`D02_20260123070624` 这些已知 hard sequences，上游 B 都体现出更明显的“fallback -> crop”修复收益。

3. **B 的收益具有明确业务意义。**
   像 `g33__D02_20260123070624_frame_0061` 这种帧中，fullframe 和 A 都没把目标有效送进 clothes 判断，而 B 恢复了完整链路，这类收益比单纯 mAP 小数点提升更有业务解释价值。

4. **B 仍不是无风险替代。**
   `gnew__00475`、`gnew__02095` 说明 B 也会在少量帧上退化，因此当前更稳妥的口径仍应是：
   - `pred_pc_clo_hardv1` 作为默认 candidate；
   - `pred_pc_clo_base` 作为稳定对照保留；
   - 暂不直接宣布 fullframe 主线完全切换完成。

---

## 6. 当前是否可以把 B 升级为默认主推进对象

### 可以升级的部分

当前已经有足够证据支持：

> **把 `pred_pc_clo_hardv1` 作为当前默认 `personcrop` 主推进对象继续向后推进。**

理由：

1. prepared 统计领先；
2. 下游评估领先；
3. 原图级代表帧复盘也能解释这种领先来自哪里；
4. 优势与已知 hard sequences 的业务难点相匹配。

### 仍不建议直接下的结论

当前仍不建议直接写成：

> `personcrop` 已经完全正式替代 fullframe clothes 主线。

更稳妥的说法是：

> **B 已经足以升级为默认 `personcrop` 主推进对象，但是否正式取代 fullframe 主线，仍建议以后续更大范围原图业务复盘与上线前链路评估再做最终确认。**

---

## 7. 建议后续动作

1. 将 `pred_pc_clo_hardv1` 固化为当前默认 `personcrop` candidate；
2. 保留 `pred_pc_clo_base` 作为稳定对照；
3. 若继续补复盘，优先扩大到同类 hard sequences，而不是重新发散更多新超参变量；
4. 当前仍不建议把 person hard examples 直接并入 clothes 训练。

---

## 8. 一句话结论

> **本轮代表帧复盘已经把 B 的优势解释清楚了：它的主要收益不是“全量都更强”，而是在 crowded / overlap / dense 候选场景中，更稳定地把原本会 fallback 的关键难帧转成有效 crop，并让下游 clothes 判断真正落到人身上。因此当前可以把 `pred_pc_clo_hardv1` 升级为默认 `personcrop` 主推进对象，但仍建议保留 `pred_pc_clo_base` 作为稳定对照，不直接宣布 fullframe 主线完全切换完成。**

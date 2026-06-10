# personcrop首轮原图级业务级量化复盘结果

## 1. 复盘目的与范围

本轮复盘用于承接 `personcrop` 首轮双上游 A/B 训练后的原图级 / 业务级检查，但当前先完成**量化代理复盘**，暂不把本结论直接写成最终人工视觉定论。

本轮复盘主要依据：

- `pred_pc_person_base` / `pred_pc_person_hardv1` prepared 目录中的样本文件名模式与数量差异；
- `pred_pc_clo_base` / `pred_pc_clo_hardv1` 的评估 JSON；
- review 目录中的 prepare 日志文件。

当前目标是先回答：

1. A / B 差异主要集中在哪些 split、哪些序列、哪些原图帧；
2. 这些差异是否主要指向 crowded / overlap / dense 候选场景；
3. 是否已经有足够证据支持保留 B 作为当前默认 candidate。

---

## 2. 量化复盘的核心结论

### 2.1 B 的优势真实存在，但不是“大面积普遍提升”

prepared 统计层面，B 相比 A 的总差异为：

- `positive_crops`: `5151 -> 5177`（`+26`）
- `fallback_fullframes`: `85 -> 62`（`-23`）
- `unmatched_boxes`: `86 -> 62`（`-24`）
- `images_without_person_detection`: `13 -> 11`（`-2`）

说明：

> **B 的优势是真实存在的，但收益集中在少量关键难帧，不是整个数据集被大面积重构。**

### 2.2 差异主要集中在 train，其次是 val，test prepared 层几乎无差异

按 split 观察 A/B prepared 文件差异：

- **train**：B 相比 A 净增加 `22` 个 crop，同时减少 `16` 个 fallback；
- **val**：B 相比 A 净增加 `4` 个 crop，同时减少 `7` 个 fallback；
- **test**：A/B 在 prepared 层的 crop / fallback 总量几乎一致。

这意味着：

> **B 的 test 指标略优，更可能来自 train / val prepared 质量改善后的泛化收益，而不是 test 样本本身被大幅重构。**

### 2.3 B 的主收益模式是“把 fallback 转成正常 crop”

按 changed frames 的变化模式观察，最常见情况是：

- `crop +1`
- `fallback -1`

这说明 B 的收益更像是：

1. A 原本在某些难帧上没把人稳定裁出来，只能 fallback；
2. B 把这类 fallback 帧转成了正常 person crop；
3. 只有少量样本表现为“纯新增一个人 crop”。

因此当前不能把 B 的优势简单概括为“切得更多”，更准确的说法应是：

> **B 更擅长把原本不稳定的难帧裁成可训练样本。**

---

## 3. 差异集中在哪些序列与原图帧

### 3.1 命中已知 hard sequences 的情况

本轮 A/B changed frames 明确命中了以下已知更难的序列：

- `D15_20260119061405`
- `D15_20260119203927`
- `D02_20260123070624`

说明当前 B 的收益并非完全随机，而是**确实部分延续到了已知 hard sequences**。

### 3.2 优先复盘的代表帧（B 把 fallback 变成 crop）

建议优先人工查看以下帧：

- `D15_20260119061405_frame_0346`
- `D15_20260119061405_frame_0354`
- `D15_20260119061405_frame_0356`
- `D15_20260119203927_frame_0142`
- `D15_20260119203927_frame_0151`
- `D02_20260123070624_frame_0061`
- `D02_20260123070624_frame_0062`
- `D15_20260123074848_frame_0034`
- `D15_20260123074848_frame_0035`
- `D05_20260123074841_frame_0027`

这些帧更值得优先看：

1. A 中存在 fallback 或少一个有效 crop；
2. B 中对应样本被成功转成了正常 crop；
3. 更有可能体现上游 person 的结构性改善。

### 3.3 也要保留少量“B 退化”样本做平衡复盘

为避免只看优势帧，建议同步保留以下样本作为平衡检查：

- `gnew__00475`
- `gnew__00874`
- `gnew__01009`
- `gnew__02095`
- `gnew__02252`

这些帧中，B 出现了“少一个 crop”或“多一个 fallback”的退化现象，可用于判断 B 是否引入了新问题。

---

## 4. 差异是否主要集中在 crowded / overlap / dense 候选场景

## 4.1 当前判断

当前可以下的判断是：

> **现有证据较强支持：B 的收益倾向于集中在 crowded / overlap / dense 候选场景，但仍建议保留为“强倾向”而非最终人工定论。**

### 4.2 支持该判断的证据

1. 差异反复命中已知 hard sequences；
2. changed frames 中，多目标密集候选帧占比不低；
3. 最常见改进模式是“fallback 转正常 crop”，与多人贴近、遮挡、相邻人边界难分的业务机制一致。

### 4.3 当前仍需保留的谨慎点

当前证据仍是：

- 文件名级差异；
- crop / fallback 数量模式；
- 已知难序列重合；
- 训练指标同步领先。

它还**不是逐帧人工视觉确认后的最终业务结论**。因此当前更稳妥的写法是：

> **B 的优势明显倾向于集中在已知 hard sequences 与多目标密集候选帧，和 crowded / overlap / dense scenes 的预期一致；但若要把结论写成“主要就是 crowded / overlap 场景收益”，仍建议对上述代表帧做一轮原图人工抽样确认。**

---

## 5. 对“是否继续推进 B” 的当前结论

结合 prepared 统计、changed frames 结构和下游评估指标，当前更合理的阶段判断是：

1. `pred_pc_clo_hardv1` 继续保留为当前默认 candidate；
2. `pred_pc_clo_base` 保留为稳定对照；
3. 下一步不再优先扩更多实验变量，而是优先做这些代表帧的原图人工复盘；
4. 在人工复盘完成前，不建议直接宣布 `personcrop` 已经正式替代 fullframe 主线。

---

## 6. review 目录下 3 个 .log 文件的处理结论

本轮同时检查了 review 目录中的 3 个日志文件：

- `pred_pc_person_base.stderr.log`
- `pred_pc_person_base.stdout.log`
- `pred_pc_person_base_prepare.log`

### 6.1 删除建议

- `pred_pc_person_base.stderr.log`：空文件，**已删除**；
- `pred_pc_person_base.stdout.log`：仅为 `prepare_report.json` 的 stdout 镜像，**已删除**；
- `pred_pc_person_base_prepare.log`：保留。

### 6.2 保留 `pred_pc_person_base_prepare.log` 的原因

该日志包含一次真实 prepare 失败的 traceback，说明 fallback copy 阶段曾出现目录不存在问题，仍有排障参考价值，因此不建议与空日志等同处理。

---

## 7. 建议立即执行的下一步

1. 按本文件列出的代表帧，补做一轮原图人工复盘；
2. 对每个代表帧至少记录：
   - fullframe / A / B 的差异；
   - 是否属于 crowded / overlap / dense；
   - B 的优势是否来自更稳定地把人裁出来；
3. 将人工结论补入业务级复盘记录，再决定是否把 B 升级为默认主推进对象。

---

## 8. 一句话结论

> **首轮量化复盘已经支持“B 的收益是真实存在的，而且主要来自把少量关键难帧的 fallback 转成有效 crop；这些收益明显倾向于集中在已知 hard sequences 与 crowded / overlap / dense 候选场景”。因此当前继续保留 B 作为默认 candidate 是合理的，但在正式宣布主线切换前，仍建议补做一轮这些代表帧的原图人工复盘。**

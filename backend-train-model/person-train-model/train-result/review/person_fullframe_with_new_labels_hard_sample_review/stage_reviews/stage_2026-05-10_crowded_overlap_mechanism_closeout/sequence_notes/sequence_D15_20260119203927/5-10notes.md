# D15_20260119203927 人工复核记录（5.10 阶段）

## 1. 本轮定位

这一轮不再重新判断它是不是 crowded / overlap，而是承接 `5.7` 已有结论，继续补主失败机制。

## 2. 今天优先看的帧

- `D15_20260119203927_frame_0143`
- `D15_20260119203927_frame_0180`

## 3. 今天要回答的问题

1. 更像一框合两人，还是第二人无响应；
2. 是否存在弱框但匹配不过线；
3. 是否伴随明显标注问题；
4. 是否已经足以支撑后续实验分流。

## 4. 记录提醒

- `semantic_primary / semantic_secondary` 直接承接 `5.7` 已有结论；
- 今天重点补 `mechanism_primary / mechanism_secondary / mechanism_confidence`；
- 如果没有明确证据，不要把边界问题硬写成主因。

## 5. 字段总览表（中文解释 + 应该怎么填 + 示例）

> 下面的“示例值”只是**示范写法**，不代表本序列当前已经得出的真实结论。

| 字段 | 中文意思 | 这一栏要填什么 | 常见取值 / 写法 | 示例（仅示范格式） |
| --- | --- | --- | --- | --- |
| `semantic_primary` | 主语义标签 | 写这张图在语义层首先属于哪类难例。这里直接承接 `5.7`。 | `crowded_or_overlap` | `crowded_or_overlap` |
| `semantic_secondary` | 次语义标签 | 写补充语义现象；没有就留空。 | `occluded` / 留空 | `occluded` |
| `mechanism_primary` | 主失败机制 | 写模型这次**最核心怎么错**，只能优先选一个最主的。 | `merge_two_people` / `second_person_no_response` / `weak_box_match_fail` / `annotation_problem` / `uncertain` | `merge_two_people` |
| `mechanism_secondary` | 次失败机制 | 写伴随问题；没有稳定次机制就留空。 | 同主机制候选集 | `weak_box_match_fail` |
| `mechanism_confidence` | 主机制判断把握度 | 根据原图、overlay、GT 三者证据一致程度填写。 | `high` / `medium` / `low` | `medium` |
| `need_relabel` | 是否怀疑需要修框 / 重标 | 只判断“要不要进一步修标”，不要和 `relabel_status` 混写。 | `true` / `false` / `null` | `false` |
| `relabel_status` | 重标状态 | 写当前标注处理状态。 | `not_needed` / `suspected` / `pending` / `fixed` | `not_needed` |
| `主要依据` | 判断证据 | 必须拆成原图、`baseline_val`、`img768_val`、GT/标签四块来写。 | 短句，1~3 句每块 | `baseline_val 中一个大框覆盖两人，img768 仍未分开` |
| `当前一句话结论` | 压缩结论 | 用一句中文概括这张图最终主判断，后续好抄到 manifest / summary。 | 1 句中文 | `更偏一框合两人，同时伴随轻微弱框匹配不足。` |

## 6. 推荐填写顺序（避免组员乱填）

| 步骤 | 先看什么 | 要解决的问题 | 输出到哪里 |
| --- | --- | --- | --- |
| 1 | 原图 | 两个人靠得多近、谁挡谁、第二个人可见度如何 | `主要依据 -> 原图观察` |
| 2 | `baseline_val` overlay | 有没有大框吃两人、第二个人附近有没有独立预测框 | `主要依据 -> baseline_val overlay` |
| 3 | `img768_val` overlay | 放大后有没有改善、是否出现新弱框 | `主要依据 -> img768_val overlay` |
| 4 | `labels/` GT | GT 是否合理、是否漏标、是否过松过紧 | `主要依据 -> GT / 标签检查` |
| 5 | 汇总结论 | 主机制是什么、把握度多高、是否需要 relabel | 各字段 + 一句话结论 |

## 7. 逐帧记录模版（表格版，先填这里，再同步 manifest）

> 建议顺序：先看原图 -> 再看 `baseline_val` / `img768_val` overlay -> 再对照 `labels/` 中 GT -> 最后回填这里。

### D15_20260119203927_frame_0143

#### 7.1 字段填写表

| 项目 | 这一格要填什么 | 你的填写 |
| --- | --- | --- |
| `semantic_primary` | 主语义标签；这里通常直接承接 `5.7` | `crowded_or_overlap` |
| `semantic_secondary` | 次语义标签；没有可留空 |  |
| `mechanism_primary` | 主失败机制；五选一 | second_person_no_response |
| `mechanism_secondary` | 次失败机制；没有可留空 |  |
| `mechanism_confidence` | `low` / `medium` / `high` | high |
| `need_relabel` | `true` / `false` / `null` | false |
| `relabel_status` | `not_needed` / `suspected` / `pending` / `fixed` | not_needed |
| `当前一句话结论` | 一句中文压缩结论 | 第二人无响应 |

#### 7.2 主要依据填写表

| 证据来源 | 这一格建议怎么写 | 你的填写 |
| --- | --- | --- |
| 原图观察 | 写两个人的相对位置、遮挡关系、第二人可见度、是否真的很拥挤 | 第二人几乎不可见 |
| `baseline_val` overlay | 写有没有一个大预测框吃两人、第二个人附近有没有独立框 | 没有 |
| `img768_val` overlay | 写相比 baseline 更好还是更差，是否出现弱框或更接近 GT 的框 | 无变化 |
| GT / 标签检查 | 写 GT 是否合理、是否漏标、是否有明显框过松 / 过紧 | 合理 |

#### 7.3 示例（仅示范写法，不代表本帧真实结论）
hl
| 项目 | 示例填写 |
| --- | --- |
| `semantic_primary` | `crowded_or_overlap` |
| `semantic_secondary` | `occluded` |
| `mechanism_primary` | `merge_two_people` |
| `mechanism_secondary` | `weak_box_match_fail` |
| `mechanism_confidence` | `medium` |
| `need_relabel` | `false` |
| `relabel_status` | `not_needed` |
| 原图观察 | 两人肩部和上半身明显贴近，后侧人仅露出部分轮廓。 |
| `baseline_val` overlay | 只看到一个偏大的预测框覆盖两个人，第二人附近没有稳定独立框。 |
| `img768_val` overlay | 放大后框位置略有改善，但仍未把两人清楚分开。 |
| GT / 标签检查 | GT 为两个独立框，范围基本合理，暂未见明确漏标。 |
| `当前一句话结论` | 更偏一框合两人，同时伴随一定弱框匹配不足，但当前不支持先走修标。 |

### D15_20260119203927_frame_0180

#### 7.4 字段填写表

| 项目 | 这一格要填什么 | 你的填写 |
| --- | --- | --- |
| `semantic_primary` | 主语义标签；这里通常直接承接 `5.7` | `crowded_or_overlap` |
| `semantic_secondary` | 次语义标签；没有可留空 |  |
| `mechanism_primary` | 主失败机制；五选一 | second_person_no_response |
| `mechanism_secondary` | 次失败机制；没有可留空 |  |
| `mechanism_confidence` | `low` / `medium` / `high` | low |
| `need_relabel` | `true` / `false` / `null` | false |
| `relabel_status` | `not_needed` / `suspected` / `pending` / `fixed` | not_needed |
| `当前一句话结论` | 一句中文压缩结论 | 车门遮挡+围栏遮挡 |

#### 7.5 主要依据填写表

| 证据来源 | 这一格建议怎么写 | 你的填写 |
| --- | --- | --- |
| 原图观察 | 写两个人是否更紧贴、局部遮挡是否更严重、第二人是否只剩局部可见 | 不贴近，分别被车门和围栏遮挡 |
| `baseline_val` overlay | 写是否只有一个大框、还是完全没给第二人附近反应 | 否 |
| `img768_val` overlay | 写放大后有没有出现弱框、是否只是 IoU 不够 | 没有 |
| GT / 标签检查 | 写 GT 是否仍然合理、是否出现需要单独怀疑的标注问题 | 合理 |

#### 7.6 示例（仅示范写法，不代表本帧真实结论）

| 项目 | 示例填写 |
| --- | --- |
| `semantic_primary` | `crowded_or_overlap` |
| `semantic_secondary` |  |
| `mechanism_primary` | `second_person_no_response` |
| `mechanism_secondary` | `occluded` |
| `mechanism_confidence` | `medium` |
| `need_relabel` | `null` |
| `relabel_status` | `suspected` |
| 原图观察 | 第二人被前景人遮掉大半，仅剩窄条可见区域。 |
| `baseline_val` overlay | 第一人附近有框，第二人附近几乎没有单独可用框。 |
| `img768_val` overlay | 放大后出现轻微响应，但位置仍不稳定，暂不足以下定论。 |
| GT / 标签检查 | GT 看起来基本合理，但第二人框边界仍需再核一次。 |
| `当前一句话结论` | 当前更偏第二人无响应，但还要继续核查是否同时伴随轻微标注问题。 |

## 8. sequence 级结论（两帧都填完后再写）

### 8.1 sequence 级结论表

| 项目 | 这一格要填什么 | 你的填写 |
| --- | --- | --- |
| 是否稳定属于 crowded / overlap 主线 | 写“是 / 否 / 暂不确定” | 是 |
| 本 sequence 主机制更偏 | 写主机制名称，并补一句中文解释 | `second_person_no_response`；分别被车门围栏遮挡。 |
| 是否存在“有弱框但匹配不过线”的稳定证据 | 写“有 / 没有 / 不确定”，并说明原因 | 没有；当前未见稳定证据支持这一机制。 |
| 是否存在明确标注问题 | 写“有 / 没有 / 不确定”，并说明是否需要 relabel | 没有；当前没有先进入修标流程的直接证据。 |
| 与 `D05_20260123074841` 是否可稳定归入同一条机制主线 | 写“能 / 不能 / 暂不确定” | 能；可与 `D05` 一起归入 crowded / overlap 主线，但 `D05` 更像辅助对照序列。 |
| 当前更建议的下一步 | `hard sample 治理` / `补 ROI 证据` / `修框后复验` / `暂缓`，并补一句原因 | `hard sample 治理`；当前已足以支撑后续实验分流，且暂不支持优先走修标。 |
| 当前一句 sequence 级总结 | 面向 `summary` 的压缩结论 | 本 sequence 当前更偏 crowded / overlap 被物体遮挡，而非两人重叠。 |

### 8.2 sequence 级示例（仅示范格式）

| 项目 | 示例填写 |
| --- | --- |
| 是否稳定属于 crowded / overlap 主线 | 是 |
| 本 sequence 主机制更偏 | `merge_two_people`；两帧都更像近邻目标未被有效拆分。 |
| 是否存在“有弱框但匹配不过线”的稳定证据 | 有，但不是最主导，更多是伴随现象。 |
| 是否存在明确标注问题 | 暂不确定，目前不足以直接进入修标。 |
| 与 `D05_20260123074841` 是否可稳定归入同一条机制主线 | 能，二者都属于 crowded / overlap 主线，但 D05 可能更强调遮挡叠加。 |
| 当前更建议的下一步 | `hard sample 治理`；先围绕 crowded / overlap 样本继续补机制证据，不宜直接跳 NMS。 |
| 当前一句 sequence 级总结 | 本 sequence 已较稳定指向 crowded / overlap 主线，主机制更偏近邻目标分离失败。 |

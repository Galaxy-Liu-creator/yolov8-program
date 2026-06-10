# D05_20260123074841 人工复核记录（5.10 阶段）

## 1. 本轮定位

本轮把这条序列作为 `D15_20260119203927` 的 crowded / overlap 辅助对照序列，不再只当成孤立异常点。

## 2. 今天优先看的帧

- `D05_20260123074841_frame_0026`
- `D05_20260123074841_frame_0029`
- `D05_20260123074841_frame_0030`

## 3. 今天要回答的问题

1. 更像一框合两人，还是第二人无响应；一框合两人
2. 是否存在遮挡叠加后导致的匹配失败；是
3. 是否伴随明显 GT 问题；否
4. 能否与 `D15_20260119203927` 稳定归入同一条机制主线。能

## 4. 记录提醒

- 本轮目标是补主机制，不是重写语义桶；
- 如果只能得到偏向性判断，也要把理由写清楚；
- 不要提前把结论直接翻译成 NMS 调参动作。

## 5. 字段总览表（中文解释 + 应该怎么填 + 示例）

> 下面的“示例值”只是**示范写法**，不代表本序列当前已经得出的真实结论。

| 字段 | 中文意思 | 这一栏要填什么 | 常见取值 / 写法 | 示例（仅示范格式） |
| --- | --- | --- | --- | --- |
| `semantic_primary` | 主语义标签 | 写这张图在语义层首先属于哪类难例。这里直接承接 `5.7`。 | `crowded_or_overlap` | `crowded_or_overlap` |
| `semantic_secondary` | 次语义标签 | 写补充语义现象；没有就留空。 | `occluded` / 留空 | `occluded` |
| `mechanism_primary` | 主失败机制 | 写模型这次**最核心怎么错**，只能优先选一个最主的。 | `merge_two_people` / `second_person_no_response` / `weak_box_match_fail` / `annotation_problem` / `uncertain` | `second_person_no_response` |
| `mechanism_secondary` | 次失败机制 | 写伴随问题；没有稳定次机制就留空。 | 同主机制候选集 | `weak_box_match_fail` |
| `mechanism_confidence` | 主机制判断把握度 | 根据原图、overlay、GT 三者证据一致程度填写。 | `high` / `medium` / `low` | `medium` |
| `need_relabel` | 是否怀疑需要修框 / 重标 | 只判断“要不要进一步修标”，不要和 `relabel_status` 混写。 | `true` / `false` / `null` | `null` |
| `relabel_status` | 重标状态 | 写当前标注处理状态。 | `not_needed` / `suspected` / `pending` / `fixed` | `suspected` |
| `主要依据` | 判断证据 | 必须拆成原图、`baseline_val`、`img768_val`、GT/标签四块来写。 | 短句，1~3 句每块 | `baseline_val 未见第二人独立框，img768 仅出现轻微弱响应` |
| `当前一句话结论` | 压缩结论 | 用一句中文概括这张图最终主判断，后续好抄到 manifest / summary。 | 1 句中文 | `更偏第二人无响应，但仍伴随遮挡叠加后的弱框匹配困难。` |

## 6. 推荐填写顺序（避免组员乱填）

| 步骤 | 先看什么 | 要解决的问题 | 输出到哪里 |
| --- | --- | --- | --- |
| 1 | 原图 | 人与人是否贴近、遮挡方向、第二人还能看到多少 | `主要依据 -> 原图观察` |
| 2 | `baseline_val` overlay | 第二人附近有没有独立框、还是只有第一人框 / 大框 | `主要依据 -> baseline_val overlay` |
| 3 | `img768_val` overlay | 放大后是否多出弱框、改善有没有实质性 | `主要依据 -> img768_val overlay` |
| 4 | `labels/` GT | GT 是否合理、是否存在漏标或框异常 | `主要依据 -> GT / 标签检查` |
| 5 | 汇总结论 | 主机制是什么、把握度多高、是否需要 relabel | 各字段 + 一句话结论 |

## 7. 逐帧记录模版（表格版，先填这里，再同步 manifest）

> 建议顺序：先看原图 -> 再看 `baseline_val` / `img768_val` overlay -> 再对照 `labels/` 中 GT -> 最后回填这里。

### D05_20260123074841_frame_0026

#### 7.1 字段填写表

| 项目 | 这一格要填什么 | 你的填写 |
| --- | --- | --- |
| `semantic_primary` | 主语义标签；这里通常直接承接 `5.7` | `crowded_or_overlap` |
| `semantic_secondary` | 次语义标签；没有可留空 |  |
| `mechanism_primary` | 主失败机制；五选一 | second_person_no_response`|
| `mechanism_secondary` | 次失败机制；没有可留空 |  |
| `mechanism_confidence` | `low` / `medium` / `high` | high |
| `need_relabel` | `true` / `false` / `null` | false |
| `relabel_status` | `not_needed` / `suspected` / `pending` / `fixed` | not_needed |
| `当前一句话结论` | 一句中文压缩结论 | 第二人无响应 |

#### 7.2 主要依据填写表

| 证据来源 | 这一格建议怎么写 | 你的填写 |
| --- | --- | --- |
| 原图观察 | 写两个人贴得多近、谁挡谁、第二人还剩多少可见区域 | 贴得很近，前面的人挡后面的人，第二人几乎不可见 |
| `baseline_val` overlay | 写有没有一个大框吃两人、第二人附近有没有单独框 | 没有 |
| `img768_val` overlay | 写相比 baseline 有没有改善、是否出现弱框 | 没有 |
| GT / 标签检查 | 写 GT 是否合理、是否存在漏标 / 框过松过紧 | 合理 |

#### 7.3 示例（仅示范写法，不代表本帧真实结论）

| 项目 | 示例填写 |
| --- | --- |
| `semantic_primary` | `crowded_or_overlap` |
| `semantic_secondary` | `occluded` |
| `mechanism_primary` | `second_person_no_response` |
| `mechanism_secondary` | `weak_box_match_fail` |
| `mechanism_confidence` | `medium` |
| `need_relabel` | `false` |
| `relabel_status` | `not_needed` |
| 原图观察 | 第二人与前景人距离很近，头肩区域有明显遮挡，但仍能辨认出是两个独立人。 |
| `baseline_val` overlay | 只匹配到前景人附近响应，第二人附近没有稳定独立预测框。 |
| `img768_val` overlay | 放大后出现轻微改善，但仍不足以形成稳定匹配。 |
| GT / 标签检查 | GT 为两个独立框，暂未见明显漏标或框异常。 |
| `当前一句话结论` | 当前更偏第二人无响应，同时伴随一定弱框匹配不足，但不支持先走修标。 |

### D05_20260123074841_frame_0029

#### 7.4 字段填写表

| 项目 | 这一格要填什么 | 你的填写 |
| --- | --- | --- |
| `semantic_primary` | 主语义标签；这里通常直接承接 `5.7` | `crowded_or_overlap` |
| `semantic_secondary` | 次语义标签；没有可留空 | second_person_no_response |
| `mechanism_primary` | 主失败机制；五选一 |  |
| `mechanism_secondary` | 次失败机制；没有可留空 |  |
| `mechanism_confidence` | `low` / `medium` / `high` | high |
| `need_relabel` | `true` / `false` / `null` | false |
| `relabel_status` | `not_needed` / `suspected` / `pending` / `fixed` | not_needed |
| `当前一句话结论` | 一句中文压缩结论 | 第二人无响应 |

#### 7.5 主要依据填写表

| 证据来源 | 这一格建议怎么写 | 你的填写 |
| --- | --- | --- |
| 原图观察 | 写局部重叠是更偏横向并排、还是前后遮挡 | 前后遮挡 |
| `baseline_val` overlay | 写第二人附近是否完全无框，还是存在疑似弱框 | 完全无框 |
| `img768_val` overlay | 写放大后是更像改善了召回，还是仍旧没有有效响应 | 没有有效响应 |
| GT / 标签检查 | 写 GT 是否合理、是否有必要怀疑标注问题 | 合理 |

#### 7.6 示例（仅示范写法，不代表本帧真实结论）

| 项目 | 示例填写 |
| --- | --- |
| `semantic_primary` | `crowded_or_overlap` |
| `semantic_secondary` |  |
| `mechanism_primary` | `weak_box_match_fail` |
| `mechanism_secondary` | `occluded` |
| `mechanism_confidence` | `low` |
| `need_relabel` | `null` |
| `relabel_status` | `suspected` |
| 原图观察 | 两人有较强遮挡，但第二人的局部边界仍能看到。 |
| `baseline_val` overlay | 第二人附近似乎有响应，但位置偏得比较厉害。 |
| `img768_val` overlay | 放大后弱框更明显，但仍未达到稳定匹配。 |
| GT / 标签检查 | GT 可能合理，但局部边界仍值得再核。 |
| `当前一句话结论` | 当前更偏弱框存在但匹配不过线，不过证据还不够硬，需要继续核。 |

### D05_20260123074841_frame_0030

#### 7.7 字段填写表

| 项目 | 这一格要填什么 | 你的填写 |
| --- | --- | --- |
| `semantic_primary` | 主语义标签；这里通常直接承接 `5.7` | `crowded_or_overlap` |
| `semantic_secondary` | 次语义标签；没有可留空 |  |
| `mechanism_primary` | 主失败机制；五选一 | second_person_no_response |
| `mechanism_secondary` | 次失败机制；没有可留空 |  |
| `mechanism_confidence` | `low` / `medium` / `high` | high |
| `need_relabel` | `true` / `false` / `null` | false |
| `relabel_status` | `not_needed` / `suspected` / `pending` / `fixed` |  not_needed|
| `当前一句话结论` | 一句中文压缩结论 | 第二人无响应 |

#### 7.8 主要依据填写表

| 证据来源 | 这一格建议怎么写 | 你的填写 |
| --- | --- | --- |
| 原图观察 | 写遮挡是否比 0026 / 0029 更重，第二人轮廓是否更弱 | 否 |
| `baseline_val` overlay | 写有没有更明显的大框合并，或者第二人彻底没响应 | 第二人彻底没响应 |
| `img768_val` overlay | 写放大后有没有从“无响应”变成“弱响应” | 没有 |
| GT / 标签检查 | 写 GT 是否合理，是否出现明确需要修标的证据 | 合理 |

#### 7.9 示例（仅示范写法，不代表本帧真实结论）

| 项目 | 示例填写 |
| --- | --- |
| `semantic_primary` | `crowded_or_overlap` |
| `semantic_secondary` | `occluded` |
| `mechanism_primary` | `merge_two_people` |
| `mechanism_secondary` | `second_person_no_response` |
| `mechanism_confidence` | `medium` |
| `need_relabel` | `false` |
| `relabel_status` | `not_needed` |
| 原图观察 | 两人几乎并成一团，第二人轮廓只剩局部边缘。 |
| `baseline_val` overlay | 更像一个较大的预测框覆盖拥挤区域，没有清晰拆成两人。 |
| `img768_val` overlay | 放大后分离能力仍有限，但相较 baseline 略有改善。 |
| GT / 标签检查 | GT 仍为两个独立框，暂未见明显标注错误。 |
| `当前一句话结论` | 当前更偏一框合两人，但还伴随第二人局部无响应，属于拥挤重叠主线样本。 |

## 8. sequence 级结论（三帧都填完后再写）

### 8.1 sequence 级结论表

| 项目 | 这一格要填什么 | 你的填写 |
| --- | --- | --- |
| 是否稳定属于 crowded / overlap 主线 | 写“是 / 否 / 暂不确定” | 是 |
| 本 sequence 主机制更偏 | 写主机制名称，并补一句中文解释 | second_person_no_response；无法识别第二人。 |
| 是否存在“遮挡叠加 + 匹配失败”的稳定证据 | 写“有 / 没有 / 不确定”，并说明原因 | 不确定。 |
| 是否存在明确标注问题 | 写“有 / 没有 / 不确定”，并说明是否需要 relabel | 没有；当前未见需要优先修标的直接证据。 |
| 与 `D15_20260119203927` 是否可稳定归入同一条机制主线 | 写“能 / 不能 / 暂不确定” | 能；当前已记录可稳定归入同一条 crowded / overlap 机制主线。 |
| 当前更建议的下一步 | `hard sample 治理` / `补 ROI 证据` / `修框后复验` / `暂缓`，并补一句原因 | `hard sample 治理`；主问题更像 crowded / overlap 主线样本本身，需要继续补机制证据而不是先修标。 |
| 当前一句 sequence 级总结 | 面向 `summary` 的压缩结论 | 本 sequence 当前稳定支撑 crowded / overlap 主线，主机制更偏“第二人无响应”，并伴随遮挡叠加后的匹配失败。 |

### 8.2 sequence 级示例（仅示范格式）

| 项目 | 示例填写 |
| --- | --- |
| 是否稳定属于 crowded / overlap 主线 | 是 |
| 本 sequence 主机制更偏 | `second_person_no_response`；遮挡叠加后第二人独立响应普遍不足。 |
| 是否存在“遮挡叠加 + 匹配失败”的稳定证据 | 有，个别帧看起来存在弱框但最终没过匹配线。 |
| 是否存在明确标注问题 | 暂不确定，目前不足以先进入修标。 |
| 与 `D15_20260119203927` 是否可稳定归入同一条机制主线 | 能，二者都属于 crowded / overlap 主线，但 D05 更强调遮挡叠加。 |
| 当前更建议的下一步 | `hard sample 治理`；先继续补 crowded 样本级证据，不宜直接跳 NMS。 |
| 当前一句 sequence 级总结 | 本 sequence 稳定支撑 crowded / overlap 主线，主机制更偏第二人独立响应不足。 |

 # 双上游personcrop执行方案

 本文档用于回答三个具体问题：

 1. 当前是否已经可以推进到 `personcrop`；
 2. 如果推进，为什么第一轮要做“双上游”而不是只押一条 `person`；
 3. 第一轮 `pred-personcrop clothes` 应该怎样执行，才能把“上游 person 差异”和“下游 clothes 差异”尽量拆开看清楚。

 ---

 ## 1. 当前阶段一句话结论

 - **可以推进到 `personcrop` 验证阶段**，但当前更准确的定位仍然是“路线验证”，不是直接把 `pred-personcrop clothes` 升级为默认主线。
 - 第一轮建议采用 **`fullframe clothes` 对照 + 双上游 `pred-personcrop clothes` A/B**。
 - 当前**先不要**把 `new hard examples` 直接并入 `clothes` 训练；先固定下游 `clothes`，只更换上游 `person`，这样更容易判断 hard examples 带来的收益能否真实传导到 `personcrop`。

 ---

 ## 2. 当前双上游为什么成立

 当前推荐进入 `personcrop` A/B 的两条 `person` 上游分别是：

 | 角色 | run / 权重 | 当前定位 | 已知特点 |
 | --- | --- | --- | --- |
 | 上游 A | `person_fullframe_with_new_labels_baseline`  / `backend-train-model/person-train-model/train-result/artifacts/runs/person_fullframe_with_new_labels_baseline/weights/best.pt` | 通用稳健基线 | 常规 fullframe 主测试集更平衡，Precision / mAP 更稳 |
 | 上游 B | `person_fullframe_with_new_labels_and_hard_examples_v1_from_baseline` / `backend-train-model/person-train-model/train-result/artifacts/runs/person_fullframe_with_new_labels_and_hard_examples_v1_from_baseline/weights/best.pt` | 困难样本增强候选 | 在 hard holdout 上明显更强；同口径 fullframe 回评里 Recall 更高，但 Precision / mAP 略回落 |

 当前阶段不直接只押其中一条的原因如下：

 1. **上游 A 更像保守型方案**：常规场景更稳，适合当 `pred-personcrop` 的下限参考；
 2. **上游 B 更像进取型方案**：最值得验证 crowded / overlap / hardest sequences 下是否能少漏人；
 3. 对 `personcrop` 来说，**漏掉一个人往往比多出一个误检更致命**，因为“漏人 = 根本没有 crop”；
 4. 因此当前更合理的做法不是先争论哪条 `person` 已经终局胜出，而是先让它们在同一套 `personcrop clothes` 流程里做一轮干净 A/B。

 ---

 ## 3. 当前阶段的边界和固定前提

 第一轮双上游 `personcrop` 验证，建议固定下面这些前提：

1. **固定 clothes 标签与下游训练口径**，先不把 `new hard examples` 并入 `clothes` 训练；
   - 当前正式 `personcrop` 下游 source dataset 固定对齐 `backend-train-model/new_clothes_train/train-result/datasets/clothes_merged_with_new_labels_v1/dataset.yaml`，即当前 `3009` 图的 clothes 扩样主线；
   - 旧的 `backend-train-model/project_config.json` 单源 `95` 图 clothes 入口只保留为历史轻量验证口径，不再作为当前正式 `personcrop` A/B 的默认 source dataset；
2. **固定 `personcrop` 默认机制**，第一轮不改：
    - `person_conf=0.20`
    - `person_imgsz=640`
    - `assignment_min_ioa=0.35`
    - `include_empty_person_crops=false`
    - `fallback_to_fullframe=true`
3. **固定训练主超参**，建议先沿用当前更稳的 `640 / batch=4 / epochs=180 / patience=40 / workers=4 / device=0`；
4. **固定 clothes 初始化来源**，如果当前是“路线验证优先”，建议继续沿用已有 `clothes fullframe` 权重做初始化，而不是一上来就改成从零训练；
5. 第一轮**不把 ROI-aware person 加入候选**；当前先完成两条 fullframe `person` 上游的 A/B，再决定是否引入第三条上游。
 6. **当前两条原始 fullframe `person` best.pt` 直接读取时类别名都是 `{0: 'item'}`**；为避免继续污染 `personcrop` 口径，现已额外生成两份 **`person` 命名 alias 权重**，后续 `personcrop` 路线统一优先使用 alias 权重，而不是直接使用原始 `best.pt`。

 ---

 ## 4. 第一轮建议实验矩阵

 当前最建议的矩阵不是只跑两组，而是至少保留下面三组：

 | 组别 | 路线 | 作用 |
 | --- | --- | --- |
 | G0 | `fullframe clothes` | 当前 clothes 对照组，不依赖 `person` 上游 |
 | G1 | `pred-personcrop clothes + 上游 A` | 保守型 `person` 上游对照 |
 | G2 | `pred-personcrop clothes + 上游 B` | 困难样本增强型 `person` 上游对照 |

 如果人力允许，建议再补一组：

 | 组别 | 路线 | 作用 |
 | --- | --- | --- |
 | G-1 | `oracle personcrop clothes` | 先验证“路线值不值”，避免一上来就被当前 `person` 上游污染 |

 但就当前“先写双上游具体怎么做”的目标而言，核心主线是：

 - **G1：`pred-personcrop + 上游 A`**
 - **G2：`pred-personcrop + 上游 B`**

 ---

 ## 5. 推荐输出目录约定

 为了避免两条上游互相覆盖，建议在 `personcrop-train/` 下单独维护本轮产物：

 ```text
 backend-train-model/personcrop-train/
   train-docs/
   train-result/
     prepared/
       pred_pc_person_base/
       pred_pc_person_hardv1/
     artifacts/
       runs/
       reports/
     review/
 ```

 推荐命名如下：

- 上游 A prepared 输出：
  `backend-train-model/personcrop-train/train-result/prepared/pred_pc_person_base`
- 上游 B prepared 输出：
  `backend-train-model/personcrop-train/train-result/prepared/pred_pc_person_hardv1`
- 上游 A run 名：
  `pred_pc_clo_base`
- 上游 B run 名：
  `pred_pc_clo_hardv1`

 ---

## 6. 具体执行步骤

本节默认在训练机环境执行，Python 解释器统一使用：

```powershell
E:\Miniconda3\envs\yolo_Code\python.exe
```

### 6.1 先创建本轮产物目录

建议先把本轮双上游 `personcrop` 的目录建好，避免后续产物分散：

```powershell
New-Item -ItemType Directory -Force -Path backend-train-model\personcrop-train\train-result\prepared | Out-Null
New-Item -ItemType Directory -Force -Path backend-train-model\personcrop-train\train-result\artifacts\runs | Out-Null
New-Item -ItemType Directory -Force -Path backend-train-model\personcrop-train\train-result\artifacts\reports | Out-Null
New-Item -ItemType Directory -Force -Path backend-train-model\personcrop-train\train-result\review | Out-Null
```

建议本轮先手工固定下面三个变量，并在你自己的实验记录里写清楚：

1. `person` 上游 A 权重路径；
2. `person` 上游 B 权重路径；
3. 本轮选定的唯一 `clothes` 初始化权重路径。

---

### 6.2 执行前先确认的权重

#### 上游 A 原始 best.pt

```text
backend-train-model/person-train-model/train-result/artifacts/runs/person_fullframe_with_new_labels_baseline/weights/best.pt
```

#### 上游 B 原始 best.pt

```text
backend-train-model/person-train-model/train-result/artifacts/runs/person_fullframe_with_new_labels_and_hard_examples_v1_from_baseline/weights/best.pt
```

#### 上游 A alias 权重（`personcrop` 推荐使用）

```text
backend-train-model/person-train-model/train-result/export/person_detect_yolov8_with_new_labels.pt
```

#### 上游 B alias 权重（`personcrop` 推荐使用）

```text
backend-train-model/person-train-model/train-result/export/person_detect_yolov8_with_new_labels_and_hard_examples_v1.pt
```

#### alias 元数据

```text
backend-train-model/person-train-model/train-result/export/person_detect_yolov8_with_new_labels.metadata.json
backend-train-model/person-train-model/train-result/export/person_detect_yolov8_with_new_labels_and_hard_examples_v1.metadata.json
```

#### 建议的 clothes 初始化权重

如果本轮重点是“先验证 `personcrop` 路线值不值”，建议优先沿用当前可用的 fullframe clothes 权重做初始化。更推荐的两个入口如下：

1. 若你当前要对齐“扩样后的 clothes 训练线”，优先使用：

```text
backend-train-model/new_clothes_train/train-result/artifacts/runs/clothes_merged_with_new_labels_v1_baseline/weights/best.pt
```

2. 若你当前要对齐仓库级既有 fullframe baseline，则使用：

```text
backend-train-model/All-train-model/artifacts/runs/clothes_merged_v2_balanced_from_first_holdout_v1/weights/best.pt
```

第一轮建议**固定只选其中一个**，不要 A 用一条、B 用另一条。

如果你想在命令里直接沿用“扩样后的 clothes 训练线”，那本节后面的 `--base-model` 就保持为：

```text
backend-train-model/new_clothes_train/train-result/artifacts/runs/clothes_merged_with_new_labels_v1_baseline/weights/best.pt
```

#### 当前正式 personcrop 下游 source dataset

```text
backend-train-model/new_clothes_train/train-result/datasets/clothes_merged_with_new_labels_v1/dataset.yaml
```

当前口径不再直接从默认 `backend-train-model/project_config.json` 的 `95` 图单源 clothes 入口生成正式 A/B，而是从这套已经构建好的 `3009` 图 clothes 扩样数据集出发，并保留其既有 `train / val / test` 切分。

---

### 6.3 先准备上游 A 的 `personcrop` 数据集

先说明一个本轮已经确认并已修正的结论：

- 上游 A / B 原始 `best.pt` 本身不是“0 检出”；
- 真正的根因是原始 `best.pt` 当前读出来的类别名是 `item`；
- 现在已经额外生成 `person` 命名 alias 权重，因此本节后续命令统一改用 alias 权重，回到默认 `person` 口径，不再需要显式写 `--monitored-person-labels item`。

```powershell
E:\Miniconda3\envs\yolo_Code\python.exe backend-train-model\personcrop-train\train-code\prepare_personcrop_from_dataset_yaml.py --source-dataset-yaml backend-train-model\new_clothes_train\train-result\datasets\clothes_merged_with_new_labels_v1\dataset.yaml --person-model backend-train-model\person-train-model\train-result\export\person_detect_yolov8_with_new_labels.pt --person-conf 0.20 --person-imgsz 640 --assignment-min-ioa 0.35 --output-root backend-train-model\personcrop-train\train-result\prepared\pred_pc_person_base --device 0 --overwrite
```

第一轮建议**先不要**加下面两个开关：

- `--include-empty-person-crops`
- `--no-fallback-to-fullframe`

原因：

- 先沿用当前默认机制，并保留 `clothes_merged_with_new_labels_v1` 既有 `train / val / test` 切分，避免第一轮把“上游 person 差异”“下游 source dataset 变化”和“personcrop 规则变化”混在一起；
- 当前更需要先知道：只换 `person` 上游后，`pred-personcrop` 本身会发生多大变化。

---

### 6.4 再准备上游 B 的 `personcrop` 数据集

```powershell
E:\Miniconda3\envs\yolo_Code\python.exe backend-train-model\personcrop-train\train-code\prepare_personcrop_from_dataset_yaml.py --source-dataset-yaml backend-train-model\new_clothes_train\train-result\datasets\clothes_merged_with_new_labels_v1\dataset.yaml --person-model backend-train-model\person-train-model\train-result\export\person_detect_yolov8_with_new_labels_and_hard_examples_v1.pt --person-conf 0.20 --person-imgsz 640 --assignment-min-ioa 0.35 --output-root backend-train-model\personcrop-train\train-result\prepared\pred_pc_person_hardv1 --device 0 --overwrite
```

到这一步，建议先人工检查两件事：

1. crowded / overlap 场景下，B 是否比 A 少漏掉一些本该裁出来的人；
2. B 是否明显引入了大量无关人框，导致 crop 质量脏很多。

如果第二点异常严重，再考虑第二轮才改 `person_conf` 或额外清洗，不要在第一轮就同时动多个变量。

---

### 6.5 先核对两套 prepared 产物是否可用

两条 `prepare` 跑完后，建议不要立刻开训，先核对下面这些文件是否都已生成：

#### 上游 A

```text
backend-train-model/personcrop-train/train-result/prepared/pred_pc_person_base/dataset.yaml
backend-train-model/personcrop-train/train-result/prepared/pred_pc_person_base/prepare_report.json
```

#### 上游 B

```text
backend-train-model/personcrop-train/train-result/prepared/pred_pc_person_hardv1/dataset.yaml
backend-train-model/personcrop-train/train-result/prepared/pred_pc_person_hardv1/prepare_report.json
```

这一轮建议至少手工记录：

1. train / val / test 的图片数；
2. A 与 B 的 crop 总量差异；
3. unmatched clothes 回退到 fullframe 的数量差异；
4. hardest sequences 上 A / B 的肉眼差异。

---

### 6.6 训练上游 A 对应的 `personcrop clothes`

假设本轮继续沿用 `clothes_merged_with_new_labels_v1_baseline` 作为初始化来源，则训练命令可以写成：

```powershell
E:\Miniconda3\envs\yolo_Code\python.exe backend-train-model\train_workwear.py train --dataset-yaml backend-train-model\personcrop-train\train-result\prepared\pred_pc_person_base\dataset.yaml --mode personcrop --person-model backend-train-model\person-train-model\train-result\export\person_detect_yolov8_with_new_labels.pt --base-model backend-train-model\new_clothes_train\train-result\artifacts\runs\clothes_merged_with_new_labels_v1_baseline\weights\best.pt --project backend-train-model\personcrop-train\train-result\artifacts\runs --name pred_pc_clo_base --imgsz 640 --epochs 180 --batch 4 --patience 40 --workers 4 --device 0 --seed 42
```

如果你本轮想对齐仓库级旧 baseline，则只替换 `--base-model` 指向的 clothes 权重，不改其他参数。

该命令跑完后，训练权重应位于：

```text
backend-train-model/personcrop-train/train-result/artifacts/runs/pred_pc_clo_base/weights/best.pt
```

---

### 6.7 训练上游 B 对应的 `personcrop clothes`

```powershell
E:\Miniconda3\envs\yolo_Code\python.exe backend-train-model\train_workwear.py train --dataset-yaml backend-train-model\personcrop-train\train-result\prepared\pred_pc_person_hardv1\dataset.yaml --mode personcrop --person-model backend-train-model\person-train-model\train-result\export\person_detect_yolov8_with_new_labels_and_hard_examples_v1.pt --base-model backend-train-model\new_clothes_train\train-result\artifacts\runs\clothes_merged_with_new_labels_v1_baseline\weights\best.pt --project backend-train-model\personcrop-train\train-result\artifacts\runs --name pred_pc_clo_hardv1 --imgsz 640 --epochs 180 --batch 4 --patience 40 --workers 4 --device 0 --seed 42
```

这里建议 **A / B 两条都使用同一个 clothes 初始化来源**，否则最后无法判断改进到底来自：

- 上游 `person` 不同；
- 还是下游 `clothes` 初始化不同。

该命令跑完后，训练权重应位于：

```text
backend-train-model/personcrop-train/train-result/artifacts/runs/pred_pc_clo_hardv1/weights/best.pt
```

---

### 6.8 评估、报告落盘与归档整理

训练完成后，至少补齐两条 `native eval`。命令模板如下：

#### 评估上游 A 对应模型

```powershell
E:\Miniconda3\envs\yolo_Code\python.exe backend-train-model\train_workwear.py evaluate --dataset-yaml backend-train-model\personcrop-train\train-result\prepared\pred_pc_person_base\dataset.yaml --weights backend-train-model\personcrop-train\train-result\artifacts\runs\pred_pc_clo_base\weights\best.pt --report-name pred_pc_clo_base_eval --imgsz 640 --batch 4 --workers 4 --device 0
```

#### 评估上游 B 对应模型

```powershell
E:\Miniconda3\envs\yolo_Code\python.exe backend-train-model\train_workwear.py evaluate --dataset-yaml backend-train-model\personcrop-train\train-result\prepared\pred_pc_person_hardv1\dataset.yaml --weights backend-train-model\personcrop-train\train-result\artifacts\runs\pred_pc_clo_hardv1\weights\best.pt --report-name pred_pc_clo_hardv1_eval --imgsz 640 --batch 4 --workers 4 --device 0
```

按当前 `train_workwear.py` 的默认行为，评估报告会按 run 名写入仓库级报告目录：

#### 上游 A 默认报告路径

```text
backend-train-model/artifacts/reports/pred_pc_clo_base/pred_pc_clo_base_eval.json
```

#### 上游 B 默认报告路径

```text
backend-train-model/artifacts/reports/pred_pc_clo_hardv1/pred_pc_clo_hardv1_eval.json
```

为了后续在 `personcrop-train/` 目录下集中复盘，建议评估后立刻把两份报告复制一份到本轮专用目录：

```powershell
New-Item -ItemType Directory -Force -Path backend-train-model\personcrop-train\train-result\artifacts\reports\pred_pc_clo_base | Out-Null
New-Item -ItemType Directory -Force -Path backend-train-model\personcrop-train\train-result\artifacts\reports\pred_pc_clo_hardv1 | Out-Null

Copy-Item backend-train-model\artifacts\reports\pred_pc_clo_base\pred_pc_clo_base_eval.json backend-train-model\personcrop-train\train-result\artifacts\reports\pred_pc_clo_base\ -Force
Copy-Item backend-train-model\artifacts\reports\pred_pc_clo_hardv1\pred_pc_clo_hardv1_eval.json backend-train-model\personcrop-train\train-result\artifacts\reports\pred_pc_clo_hardv1\ -Force
```

如果你后续还会补 `train` 报告、FP/FN 复盘或可视化样本，也建议统一按 run 名写回 `personcrop-train/train-result/artifacts/reports/<run_name>/` 与 `personcrop-train/train-result/review/<run_name>/`。

---

### 6.9 本轮和 G0 对照时至少要做的整理

当 G1 / G2 都评估完成后，建议立即手工整理一个最小对照表，至少写清楚：

1. `G0 fullframe clothes` 的当前对照指标来源；
2. `G1` 的 Val / Test 指标；
3. `G2` 的 Val / Test 指标；
4. 两条上游各自对应的 prepared 统计摘要；
5. hardest sequences 的主观观察结论。

如果当前 `G0` 还没有同口径写进同一份表，可以先用最简单的 Markdown 表手工补到：

```text
backend-train-model/personcrop-train/train-result/review/双上游personcrop首轮对照结论.md
```

这样后面无论是决定继续补 `oracle personcrop`，还是继续补 `clothes` hard scenes，都不会丢失首轮 A / B 的原始判断依据。

 ---

 ## 7. 第一轮必须记录的对照信息

 第一轮不要只看最后一个 mAP；至少要保留下列信息：

 ### 7.1 `prepare` 阶段

 1. 每个 split 的图片数 / crop 数；
 2. 每图平均 person crop 数；
 3. `clothes -> person` 成功分配数量；
 4. unmatched clothes 回退到 fullframe 的数量；
 5. 被跳过的空 person crop 数量；
 6. hardest sequences 的典型可视化样本。

 ### 7.2 `train / evaluate` 阶段

 1. Val / Test 的 Precision、Recall、mAP50、mAP75、mAP50-95；
 2. 相比当前 `fullframe clothes` 对照，Recall 是否提升；
 3. 相比当前 `fullframe clothes` 对照，Precision 是否明显失控；
 4. hardest sequences 上是否少漏掉“本应进入 clothes 判断的人”；
 5. crop 是否更完整，是否减少“衣服关键区域被裁坏”的问题。

 ---

 ## 8. 如何解读这轮双上游结果

 ### 8.1 如果 B 明显优于 A

 这说明：

 - `new hard examples` 在上游 `person` 端带来的收益，已经开始传导到 `pred-personcrop clothes`；
 - 下一轮可以优先把 **上游 B** 作为 `pred-personcrop` 默认 person 候选；
 - 之后再考虑是否给 clothes 端补 hard scenes 标注。

 ### 8.2 如果 B 只在 hardest sequences 上更好，但整体 mAP 变化不大

 这仍然是**有价值结果**，不应简单判为失败。更合理的解释可能是：

 - 上游 hard examples 的主要收益集中在 crowded / overlap / hardest scenes；
 - 但因为当前 `clothes` 端还没有同步补 hard scenes，整链路总 mAP 不一定立刻大幅提升；
 - 这类结果通常意味着“路线值得继续”，而不是“路线没用”。

 ### 8.3 如果 A / B 都不如 `fullframe clothes`

 这时不要马上下结论说 `personcrop` 没价值，要先分两种情况：

 1. 如果人工复盘显示 `pred-personcrop` 已经因为上游漏人或裁坏衣物而失真，说明当前问题更多还是上游 person；
 2. 如果人工复盘显示 crop 质量其实还行，但 `clothes` 仍没收益，才更像是路线本身收益有限。

 ### 8.4 如果未来补了 `oracle personcrop`，而 oracle 明显优于 fullframe

 那就说明：

 - `personcrop` 路线本身是有价值的；
 - 当前 `pred-personcrop` 没跑出来，更可能是因为上游 person 或当前 crop 规则还不够稳；
 - 这种情况下，不应把失败简单归因到 `clothes` 模型本身。

 ---

 ## 9. 当前阶段对结果的预期

 结合已有 `person` 实验，当前更合理的预期是：

 1. **上游 A** 更像“常规场景稳健型”；
 2. **上游 B** 更像“困难场景增强型”；
 3. 如果只比较 `pred-personcrop` 内部胜负，**B 更有希望胜出**；
 4. 但 `pred-personcrop` 是否已经能全面超过 `fullframe clothes`，当前还不能提前保证；
 5. 第一轮更可能出现的是：
   - hardest scenes 上 `B > A`；
   - 常规场景两者差距不大；
   - 全量总体收益未必“碾压”，但结构性收益值得继续追。

 ---

 ## 10. 当前阶段明确不做什么

 第一轮双上游 `personcrop`，当前明确**不建议**同时做下面这些事：

 1. 不在同一轮里同时引入 ROI-aware `person` 第三上游；
 2. 不在同一轮里同时放大 `person_imgsz`、降低 `person_conf`、修改 `assignment_min_ioa`；
 3. 不在同一轮里同时把 `new hard examples` 并入 `clothes` 监督训练；
 4. 不把第一轮 `pred-personcrop` 结果直接写成“默认主线已经切换”；
 5. 不修改 `inspection-flask/` 在线链路。

 当前最重要的是：

 > 先把“上游 A vs 上游 B”在同一套 `personcrop clothes` 路线里跑清楚，再决定下一轮是补 oracle、补 clothes hard labels，还是引入第三条上游。

 ---

 ## 11. 一句话执行口径

 当前最稳的执行口径应写成：

 > **先固定下游 clothes，不并入 new hard examples；再用 `person_fullframe_with_new_labels_baseline` 与 `person_fullframe_with_new_labels_and_hard_examples_v1_from_baseline` 两条上游，分别生成两套 `pred-personcrop` 数据集与训练 run；最后和当前 `fullframe clothes` 对照，判断 hard examples 带来的上游收益是否已经能传导到 `personcrop`。**

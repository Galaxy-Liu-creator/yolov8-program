# ROI-aware person 首轮训练问题分析

本文档用于记录本轮 `person_roi_aware_baseline` 第一次训练后的现状、问题判断与下一步改进建议，避免后续只凭印象重复试错。

当前结论先写在前面：

- 这次 ROI-aware person **不是没训起来**，而是**正常训练后在第 123 轮因早停结束**；
- 但当前 ROI-aware baseline 的 **test 指标明显弱于 fullframe baseline**；
- 主要问题不是误报，而是 **模型过于保守，Recall 偏低，漏检偏多**；
- 当前阶段**不建议**用这版 ROI-aware 权重替换 `person_fullframe_baseline`；
- 下一步最优先的改法不是继续硬训同一版，而是：**用 fullframe person best 权重作为 ROI-aware 初始化重新微调。**

---

## 1. 本轮训练与评估对象

### 1.1 ROI-aware 训练 run

- run 名称：`person_roi_aware_baseline`
- run 目录：`backend-train-model/person-train-model/train-result/artifacts/runs/person_roi_aware_baseline`
- 训练报告：`backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_baseline_train.json`
- 评估报告：`backend-train-model/person-train-model/train-result/artifacts/reports/person_roi_aware_baseline_eval.json`

### 1.2 Fullframe 对照 run

- run 名称：`person_fullframe_baseline`
- 训练报告：`backend-train-model/person-train-model/train-result/artifacts/reports/person_fullframe_baseline_train.json`
- 评估报告：`backend-train-model/person-train-model/train-result/artifacts/reports/person_fullframe_baseline_eval.json`

### 1.3 ROI-aware 数据集

- 数据集 YAML：`backend-train-model/person-train-model/train-result/prepared/person_roi_aware/sequence_contiguous/dataset.yaml`
- prepare 报告：`backend-train-model/person-train-model/train-result/prepared/person_roi_aware/sequence_contiguous/prepare_report.json`

---

## 2. 训练是否“过早停止”

先说结论：**训练确实比预设的 180 轮早结束，但这属于正常早停，不是异常中断。**

本轮训练参数：

- `epochs=180`
- `patience=40`
- `imgsz=640`
- `batch=4`
- `device=cpu`
- `base-model=backend-train-model/weights/yolov8n.pt`

实际训练情况：

- `results.csv` 最后记录到第 `123` 轮；
- 最佳 `mAP50-95` 出现在第 `83` 轮；
- 从第 `83` 轮开始，后续 `40` 轮没有再刷新最佳 `mAP50-95`；
- 因此在第 `123` 轮触发 early stopping。

也就是说：

- 这不是训练脚本崩掉；
- 也不是 checkpoint 丢失；
- 而是 **当前配置下模型在 val 集上已经较早进入平台期。**

---

## 3. 当前指标结论

### 3.1 ROI-aware baseline

来自 `person_roi_aware_baseline_eval.json`：

#### val

- `Precision = 0.9831`
- `Recall = 0.7865`
- `mAP50 = 0.8725`
- `mAP50-95 = 0.5509`

#### test

- `Precision = 0.9390`
- `Recall = 0.5950`
- `mAP50 = 0.6738`
- `mAP50-95 = 0.3867`

### 3.2 Fullframe baseline

来自 `person_fullframe_baseline_eval.json`：

#### val

- `Precision = 0.9677`
- `Recall = 0.8215`
- `mAP50 = 0.9134`
- `mAP50-95 = 0.5691`

#### test

- `Precision = 0.9228`
- `Recall = 0.6740`
- `mAP50 = 0.7606`
- `mAP50-95 = 0.4102`

### 3.3 对照结论

ROI-aware 当前与 fullframe 相比：

- `Precision` 更高；
- 但 `Recall` 更低；
- `mAP50` 更低；
- `mAP50-95` 也更低；
- **test 集下降比 val 更明显。**

因此当前 ROI-aware baseline 的问题不是“乱报太多”，而是：

**模型变保守了，漏人更多。**

---

## 4. 当前最关键的问题现象

### 4.1 Test Recall 明显掉了

从 fullframe 到 ROI-aware：

- test `Recall`: `0.6740 -> 0.5950`
- test `mAP50`: `0.7606 -> 0.6738`
- test `mAP50-95`: `0.4102 -> 0.3867`

这说明 ROI-aware 第一版并没有把业务关注区域转化成更强的检测效果，反而让 test 侧漏检更严重。

### 4.2 数据集框数量显著减少

ROI-aware prepare 报告显示：

- 输入图片：`502`
- 输出图片：`502`
- 保留框：`1343`
- 丢弃框：`315`
- 边界裁剪框：`49`
- 空 ROI 负样本：`12`

而 fullframe person 原始总框数为：

- `1658`

也就是说，ROI-aware 把约 `19%` 的原 person 框过滤掉了。

尤其 test split：

- fullframe test 框：`181`
- ROI-aware test 框：`121`

test 监督信号减少较多，指标自然更容易波动，也更容易出现 recall 偏低。

### 4.3 某些序列被 ROI 过滤得过多

从 `prepare_report.json` 看，最值得警惕的序列是：

#### `D15_20260119061405`

- 原始框总数：`471`
- ROI-aware 保留：`218`
- ROI-aware 丢弃：`253`

这个序列被过滤掉的框非常多，说明当前 ROI 或当前保留规则对这个机位特别“狠”。

#### `D15_20260119203927`

- ROI-aware test 中有 `28` 张图；
- 其中 `9` 张是空 ROI 负样本；
- test 只剩 `20` 个保留框。

这会让该序列 test 指标对漏检非常敏感。

### 4.4 当前 test 里仍然有很多小目标

尽管 ROI-aware 后平均框面积变大了，但 test 集中仍有很多小框。

粗略统计：

- fullframe test 中，小框比例约 `81.2%`
- ROI-aware test 中，小框比例约 `71.9%`

这说明 ROI-aware 虽然缩小了背景，但并没有把“小目标难题”根本消掉。

因此 `imgsz=640` 可能仍偏保守。

---

## 5. 为什么会这样

### 5.1 ROI-aware 是从 `yolov8n.pt` 重新起训，不是从 fullframe person best 微调

这是当前最重要的问题之一。

现在的 ROI-aware baseline：

- 直接从通用预训练 `yolov8n.pt` 起训；
- 没有继承 fullframe person 已经学到的站内 person 场景知识；
- 同时 ROI-aware 数据比 fullframe 更少、框也更少；
- 所以它在当前阶段更容易学成“高精度、低召回”的保守模型。

### 5.2 当前 ROI 保留规则太硬：`center_inside`

当前 ROI-aware v1 规则是：

- 只要 person 框中心点在 ROI polygon 内，就保留；
- 中心点不在 ROI 内，就丢弃。

这个规则实现简单，但问题也明显：

- ROI 边界附近的人容易被系统性丢掉；
- 半身进入 ROI 的人容易被过滤；
- 一旦这些边界样本在 test 中出现，就会拉低 recall。

### 5.3 ROI 裁剪没有留 margin

当前做法是：

- ROI 外区域置黑；
- 再裁剪到 ROI polygon 的最小外接矩形。

这样有两个问题：

- 对 ROI 边缘的人，裁剪可能过紧；
- 对框贴边或刚进入 ROI 的目标，容易出现训练信号不足。

### 5.4 默认增强可能对 ROI crop 小数据不够友好

当前训练仍使用 Ultralytics 默认增强组合，例如：

- `mosaic=1.0`
- `scale=0.5`
- `translate=0.1`
- `erasing=0.4`

ROI-aware 数据已经是“局部区域 + 更少框”的训练集，再叠较强增强，未必是正收益。

当前 wrapper 还没有把这组参数显式暴露出来，因此这部分目前还没做专门对照。

---

## 6. 当前不建议做的事情

### 6.1 不建议直接拿当前 ROI-aware 权重替换 fullframe baseline

原因很简单：

- 当前 test `Recall`、`mAP50`、`mAP50-95` 都不如 fullframe；
- 还没证明 ROI-aware 这版对后续 `personcrop -> clothes` 整体链路更优。

### 6.2 不建议直接继续 resume 当前 ROI-aware run

因为：

- 当前 best 出现在第 `83` 轮；
- 第 `123` 轮已早停；
- 继续沿用同样配置和同样初始化，收益大概率有限。

### 6.3 不建议只靠调推理阈值解决

虽然当前表现像“高 precision、低 recall”，看起来似乎可以靠调 `conf` 拉召回；
但本轮不只是 recall 低，`mAP50 / mAP50-95` 也比 fullframe 差，说明问题不只是阈值，而是模型本身对 ROI-aware 数据的学习还不够好。

---

## 7. 下一步改进优先级

下面按优先级从高到低列出建议。

### 7.1 第一优先：用 fullframe person best 作为 ROI-aware 初始化重新微调

这是最应该先做的一版对照。

原因：

- fullframe person 已经学到当前站内场景；
- ROI-aware 训练集又是从这套 person 母数据派生出来的；
- 先用 fullframe best 作为初始化，比重新从 `yolov8n.pt` 起训更合理。

建议命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware\sequence_contiguous\dataset.yaml --run-name person_roi_aware_from_fullframe_v1 --device cpu --workers 0 --batch 4 --imgsz 640 --epochs 180 --patience 60 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

评估命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware\sequence_contiguous\dataset.yaml --run-name person_roi_aware_from_fullframe_v1 --device cpu --workers 0
```

### 7.2 第二优先：尝试更高分辨率

因为 ROI-aware test 仍然有很多小目标，建议至少补一版：

- `imgsz=768`
- `batch=2`

推荐命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware\sequence_contiguous\dataset.yaml --run-name person_roi_aware_from_fullframe_img768 --device cpu --workers 0 --batch 2 --imgsz 768 --epochs 180 --patience 60 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

### 7.3 第三优先：给 ROI crop 增加边距

当前 ROI 外接矩形裁剪太紧，建议下一版支持：

- `crop_margin_ratio = 0.05`

或者：

- `crop_margin_px = 32 / 64`

目标：

- 保留一点 ROI 边界上下文；
- 降低边界 person 被裁得太狠的概率；
- 减少“刚进入 ROI 的人”在训练中被系统性弱化。

### 7.4 第四优先：放宽边界目标保留规则

当前 `center_inside` 过于干脆。

建议下一版增加保留规则，例如：

- 中心点在 ROI 内：保留；
- 或者 box 与 ROI 的可见面积占比 `IoA >= 0.2 / 0.3`：也保留。

这样可以更稳地保留 ROI 边缘人。

### 7.5 第五优先：做 ROI 过滤可视化质检

建议专门做 overlay 可视化，画出：

- ROI polygon
- 保留框
- 丢弃框
- 裁剪后框

重点检查：

- `D15_20260119061405`
- `D15_20260119203927`

因为这两个序列当前最可能是 test recall 下降的主要来源。

### 7.6 第六优先：降低训练增强强度

如果做了前几步之后 ROI-aware 仍不稳定，再考虑补充 CLI 参数，把这些增强暴露出来做对照：

- `mosaic`
- `scale`
- `translate`
- `erasing`
- `close_mosaic`

建议的保守方向：

- `mosaic=0.3` 或 `0`
- `scale=0.25`
- `translate=0.05`
- `erasing=0`

---

## 8. 当前推荐路线

建议按下面顺序推进：

1. 先保留 `person_fullframe_baseline` 作为当前可用 baseline；
2. 重新训练一版 `person_roi_aware_from_fullframe_v1`；
3. 若 test recall 仍低，再试 `imgsz=768`；
4. 若仍不理想，再做：
   - ROI margin
   - IoA 保留规则
   - ROI 过滤 overlay 质检；
5. 只有当 ROI-aware 在 test 上至少达到或超过 fullframe，再考虑把它作为后续 `personcrop -> clothes` 的默认上游 person 模型。

---

## 9. 一句话结论

当前 ROI-aware person 第一版的核心问题不是“训练崩了”，而是：

**ROI 数据变少、边界规则偏硬、初始化又从通用预训练起步，导致模型变得保守，test Recall 明显下降。**

因此下一步最优先不是继续硬训同一版，而是：

**用 fullframe person best 权重作为 ROI-aware 初始化重新微调。**

# person hardest val/test 样本分桶复盘

## 1. 文档目的

本文专门记录 `person_fullframe_with_new_labels` 这条 fullframe 扩样线的 hardest val/test 样本分桶结果，用于回答三个问题：

1. 当前 hardest FN 主要集中在哪类目标；
2. `baseline 640` 与 `img768` 的 hardest samples 结构有没有变化；
3. 当前更适合优先推进哪类后续动作。

本文优先记录**已经跑通、可复现**的算法分桶结果；在此基础上，再给出更贴近业务语义的二层归纳结论。

---

## 2. 分桶口径

### 2.1 复盘口径

对以下 4 组结果统一执行逐图 FP/FN 复盘：

- `person_fullframe_with_new_labels_baseline` - val
- `person_fullframe_with_new_labels_baseline` - test
- `person_fullframe_with_new_labels_img768` - val
- `person_fullframe_with_new_labels_img768` - test

统一推理 / 匹配口径：

- `conf = 0.25`
- `nms_iou = 0.7`
- `match_iou = 0.5`

复盘产物目录：

- `train-result/review/person_fullframe_with_new_labels_baseline_fpfn_val_conf025/`
- `train-result/review/person_fullframe_with_new_labels_baseline_fpfn_test_conf025/`
- `train-result/review/person_fullframe_with_new_labels_img768_fpfn_val_conf025/`
- `train-result/review/person_fullframe_with_new_labels_img768_fpfn_test_conf025/`

### 2.2 分桶规则

对每个 **FN 的 GT 框**，计算：

- `best_iou`：该 GT 与同图所有预测框的最大 IoU
- `rel_height`：GT 高度 / 图片高度
- `min_edge_px`：GT 到四条图像边界的最小像素距离

然后按下面规则分桶：

1. `small_boundary_person`
  - `best_iou < 0.5`
  - `rel_height < 0.10`
  - `min_edge_px <= 10`
2. `small_interior_person`
  - `best_iou < 0.5`
  - `rel_height < 0.10`
  - `min_edge_px > 10`
3. `medium_large_pose_or_appearance`
  - `best_iou < 0.5`
  - `rel_height >= 0.10`
4. `crowded_or_localization`
  - `best_iou >= 0.5`

这四类对应的直观语义分别是：

- `small_boundary_person`：贴边远景小人
- `small_interior_person`：画面内部小人
- `medium_large_pose_or_appearance`：并不算特别小，但姿态 / 外观 / 亮度 / 遮挡更难
- `crowded_or_localization`：模型其实看到了附近目标，但定位 / 拥挤匹配没过线

---

## 3. 结果总览

### 3.1 baseline - val

- 总 FN：`116`
- `medium_large_pose_or_appearance`：`53`，`45.7%`
- `small_interior_person`：`49`，`42.2%`
- `small_boundary_person`：`9`，`7.8%`
- `crowded_or_localization`：`5`，`4.3%`

主要序列：

- `medium_large_pose_or_appearance`
  - `D15_20260119203927`: 4
- `small_interior_person`
  - `D15_20260119061405`: 11
  - `D02_20260123070624`: 5
  - `D05_20260123074841`: 5
- `small_boundary_person`
  - `D02_20260123070624`: 6

最难图片：

- `D02_20260123070624_frame_0061`：3 个 FN，全部 `small_interior_person`

### 3.2 baseline - test

- 总 FN：`131`
- `medium_large_pose_or_appearance`：`66`，`50.4%`
- `small_interior_person`：`44`，`33.6%`
- `small_boundary_person`：`13`，`9.9%`
- `crowded_or_localization`：`8`，`6.1%`

主要序列：

- `medium_large_pose_or_appearance`
  - `D15_20260119061405`: 11
  - `D15_20260119203927`: 3
- `small_interior_person`
  - `D15_20260119061405`: 18
  - `D15_20260119203927`: 16
- `small_boundary_person`
  - `D02_20260123070624`: 7
  - `D02_20260123074836`: 5
- `crowded_or_localization`
  - `D05_20260123074841`: 2

最难图片：

- `D15_20260119061405_frame_0346`：3 个 FN（2 个 `medium_large_pose_or_appearance` + 1 个 `small_interior_person`）
- `D15_20260119061405_frame_0348`：3 个 FN（2 个 `medium_large_pose_or_appearance` + 1 个 `small_interior_person`）

### 3.3 img768 - val

- 总 FN：`164`
- `medium_large_pose_or_appearance`：`80`，`48.8%`
- `small_interior_person`：`66`，`40.2%`
- `small_boundary_person`：`14`，`8.5%`
- `crowded_or_localization`：`4`，`2.4%`

主要序列：

- `medium_large_pose_or_appearance`
  - `D15_20260119203927`: 3
  - `D02_20260123070624`: 2
- `small_interior_person`
  - `D15_20260119061405`: 11
  - `D02_20260123070624`: 5
  - `D05_20260123074841`: 5
- `small_boundary_person`
  - `D02_20260123070624`: 8

最难图片：

- `D02_20260123070624_frame_0060`：3 个 FN，混合型
- `D02_20260123070624_frame_0061`：3 个 FN，全部 `small_interior_person`
- `D05_20260123074841_frame_0026`：3 个 FN，混合型

### 3.4 img768 - test

- 总 FN：`149`
- `medium_large_pose_or_appearance`：`88`，`59.1%`
- `small_interior_person`：`45`，`30.2%`
- `small_boundary_person`：`14`，`9.4%`
- `crowded_or_localization`：`2`，`1.3%`

主要序列：

- `medium_large_pose_or_appearance`
  - `D15_20260119061405`: 16
  - `D15_20260119203927`: 4
- `small_interior_person`
  - `D15_20260119061405`: 17
  - `D15_20260119203927`: 16
- `small_boundary_person`
  - `D02_20260123070624`: 7
  - `D02_20260123074836`: 6
- `crowded_or_localization`
  - `D05_20260123074841`: 2

最难图片：

- `D15_20260119061405_frame_0345`：5 个 FN（4 个 `medium_large_pose_or_appearance` + 1 个 `small_interior_person`）
- `D15_20260119061405_frame_0346`：3 个 FN
- `D15_20260119061405_frame_0348`：3 个 FN
- `D15_20260119061405_frame_0355`：3 个 FN

---

## 4. 合并视角对比

### 4.1 baseline 合并视角（val + test）

- 总 FN：`247`
- `medium_large_pose_or_appearance`：`119`，`48.2%`
- `small_interior_person`：`93`，`37.7%`
- `small_boundary_person`：`22`，`8.9%`
- `crowded_or_localization`：`13`，`5.3%`

### 4.2 img768 合并视角（val + test）

- 总 FN：`313`
- `medium_large_pose_or_appearance`：`168`，`53.7%`
- `small_interior_person`：`111`，`35.5%`
- `small_boundary_person`：`28`，`8.9%`
- `crowded_or_localization`：`6`，`1.9%`

### 4.3 直接对比

相对 baseline，`img768` 的 hardest FN 结构没有发生根本性变化：

- 主体仍然是 `medium_large_pose_or_appearance + small_interior_person`
- `small_boundary_person` 占比基本不变（都约 `8.9%`）
- `crowded_or_localization` 反而更少
- 但 `medium_large_pose_or_appearance` 占比更高了

这说明：

> `imgsz=768` 没有把 hardest samples 的失败结构从根本上改掉，反而让 FN 更偏向“并不算特别小、但姿态 / 外观 / 亮度 / 遮挡更难”的样本。

---

## 5. 更贴近业务语义的二层归纳

在算法分桶之上，当前更适合把 hardest FN 先粗归纳成下面 4 类业务语义问题：

### 5.1 中等 / 较大但姿态或外观更难的人

对应算法桶：

- `medium_large_pose_or_appearance`

当前是**第一大类**，尤其在 `img768_test` 中占比达到 `59.1%`。

这类样本更像是：

- 目标并不特别小；
- 但存在暗光、背光、遮挡、半身、姿态异常、画面清晰度差或外观不稳定等因素；
- 问题重点不是“像素太少到完全看不见”，而是“模型没能稳定把它当成标准 person 学会”。

主要序列：

- `D15_20260119061405`
- `D15_20260119203927`

### 5.2 画面内部的小人

对应算法桶：

- `small_interior_person`

这是**第二大类**。它说明 hardest FN 的很大一部分，并不是贴边小人，而是：

- 小；
- 但在画面内部；
- 更像是远景站位、视角压缩、人体像素不足、外观不显著造成的漏检。

主要序列：

- `D15_20260119061405`
- `D15_20260119203927`
- `D02_20260123070624`

### 5.3 贴边远景小人

对应算法桶：

- `small_boundary_person`

这类样本确实存在，但它不是当前 hardest FN 的主体，只占大约 `8%~10%`。

主要序列：

- `D02_20260123070624`
- `D02_20260123074836`

所以：

> 当前不能把 hardest FN 主因简单归因成“都是边界小人”。

### 5.4 拥挤 / 局部定位问题

对应算法桶：

- `crowded_or_localization`

这类问题占比最小，说明当前 hardest FN 主体并不是“其实框到了，只是 IoU 差一点点”。

主要序列：

- `D05_20260123074841`

它更像是：

- 多人近邻
- 局部遮挡
- 框匹配失败
- 定位抖动

而不是全局主导矛盾。

---

## 6. 最终结论

### 6.1 关于 hardest samples 主体

当前 hardest val/test 样本的主体，**不是单纯边界小人**。

真正主导 FN 的是两类：

1. `medium_large_pose_or_appearance`
2. `small_interior_person`

也就是说，当前主矛盾更像是：

> **并不算特别小、但姿态 / 外观 / 亮度更难的人**

> 和

> **小但位于画面内部的人**。

### 6.2 关于 img768 的真实作用

`img768` 并没有把 hardest sample 的失败结构改变掉。

它的问题不在于“完全没收益”，而在于：

- 虽然正式 eval 的 `mAP75 / mAP50-95` 有小幅提升；
- 但按当前 `conf=0.25 / nms_iou=0.7 / match_iou=0.5` 的逐图 FN 复盘口径看，
- hardest FN 仍然主要集中在 `medium_large_pose_or_appearance + small_interior_person`；
- 而且 `img768` 下 `medium_large_pose_or_appearance` 占比更高。

因此：

> 继续单纯放大 `imgsz`，不是当前最优先的推进方向。

### 6.3 关于下一步优先级

当前更适合优先推进的是：

1. **继续围绕 `D15_20260119061405`、`D15_20260119203927` 做人工复核**
  - 重点看 `medium_large_pose_or_appearance`
  - 进一步拆成：暗光 / 背光 / 遮挡 / 半身 / 姿态异常 / 外观不稳定 / 可疑标注问题
2. **再围绕 `D02_20260123070624`、`D02_20260123074836` 看小型内部 / 边界人问题**
  - 判断是否存在更强的远景小人规律
3. **只有当 clothes hard cases 也明显集中在 person 附着小目标场景时，再启动 `oracle person-guided clothes` 路线验证**
  - 不要因为旧 YOLOv5 路线有效，就反过来忽略当前 person 主线 hardest FN 的真实结构

---

## 7. 当前一句话结论

当前 `person_fullframe_with_new_labels` 的 hardest FN 主体不是“边界小人” alone，而是：

> **中等 / 较大但姿态、外观、亮度更难的人**

> 与

> **小但位于画面内部的人**。

`img768` 没有改变这一失败结构，反而让 FN 更偏向 `medium_large_pose_or_appearance`。因此当前最该优先推进的仍然是 `person` 主线的人工 hard sample 复核，而不是直接切到依赖当前 person 上游的 `pred-personcrop clothes`。

---

## 8. 把“算法分桶”继续推进成“语义细分桶”时，应该重点看什么

上面的 4 类算法桶已经足够回答“当前 hardest FN 的几何结构是什么”。

但如果下一步要决定：

- 是优先补暗光样本；
- 还是优先调增强；
- 还是先补遮挡 / 半身类样本；
- 还是先怀疑标注一致性；

那么仅靠 `best_iou / rel_height / min_edge_px` 还不够，需要进一步做一层**人工语义细分桶**。

### 10.1 当前最应该优先人工复核的序列

建议按下面优先级看：

#### 第一优先级：`D15_20260119061405`

原因：

- 在 `baseline_test` 中：
  - `fn = 29`
- 在 `img768_test` 中：
  - `fn = 12`
- 而且在 test hardest 图片里，`0345 / 0346 / 0348 / 0355` 都反复出现。

这条序列最适合重点确认：

- 中等 / 较大目标为什么还漏；
- 是否存在暗光、背光、遮挡、半身、姿态异常；
- 是否有“看起来并不小，但视觉判别信息很弱”的情况。

#### 第二优先级：`D15_20260119203927`

原因：

- 在 val / test 两边都稳定进入 hardest sequences；
- 同时覆盖：
  - `medium_large_pose_or_appearance`
  - `small_interior_person`

这条序列最适合重点确认：

- 与 `D15_20260119061405` 是否属于同一类失败模式；
- 是否是另一类不同的姿态 / 光照 / 遮挡问题；
- 是否说明“当前 person 模型对某类中等尺度难例表征不足”是系统性问题。

#### 第三优先级：`D02_20260123070624`

原因：

- 在 `small_boundary_person` 上持续居前；
- 同时也有明显的 `small_interior_person`。

这条序列最适合重点确认：

- 边界小人和内部小人是否本质上是同一类“远景像素不足”；
- 还是贴边 / 站位 / 裁切构图导致的额外问题；
- 是否存在“看上去不该漏，但因为目标太稀薄而漏掉”的情况。

#### 第四优先级：`D02_20260123074836`

原因：

- 它在 `small_boundary_person` 中稳定出现；
- 是验证“边界小人是否是当前主因”的重要对照序列。

这条序列最适合重点确认：

- 边界人到底占多大比重；
- 这些人是不是已经小到超出当前 fullframe person 的稳定检测范围；
- 是否值得为这一类样本单独做策略分支。

#### 第五优先级：`D05_20260123074841`

原因：

- 它虽然总体量没有 D15 / D02 两组高；
- 但在 `crowded_or_localization` 中最有代表性。

这条序列最适合重点确认：

- 多人近邻重叠是否是主因；
- 是 GT / pred 对不齐，还是局部遮挡；
- 是否存在“预测框已经靠近 GT，但略偏”这种 localization-only 现象。

### 10.2 当前最应该优先人工复核的图片

建议先从下面这些最难帧开始：

#### D15 主线 hardest frames

- `D15_20260119061405_frame_0345`
- `D15_20260119061405_frame_0346`
- `D15_20260119061405_frame_0348`
- `D15_20260119061405_frame_0355`

#### D02 代表帧

- `D02_20260123070624_frame_0060`
- `D02_20260123070624_frame_0061`
- `D02_20260123074836_frame_0022`

#### D05 拥挤代表帧

- `D05_20260123074841_frame_0026`

如果时间有限，先看这 8 张代表帧，通常已经足以判断下一轮应该优先押哪一类问题。

---

## 11. 语义细分桶应该怎么做

这里不建议上来就把全部 FN 全量人工看完，而是建议采用：

> **先自动分桶缩小范围，再对最关键的代表帧做人眼语义复核。**

### 11.1 建议的语义细分桶标签

在当前项目阶段，建议先用下面这 8 个标签，够用且不容易过细：

1. `dark_or_backlit`
  - 暗光、背光、低对比度
2. `occluded`
  - 被设备、车辆、立柱、其他人部分遮挡
3. `partial_body`
  - 半身、截断、只露出局部
4. `pose_or_shape_unusual`
  - 弯腰、转身、蹲姿、人体形态异常
5. `small_far_interior`
  - 小、远景、位于画面内部
6. `small_far_boundary`
  - 小、远景、贴边或贴角
7. `crowded_or_overlap`
  - 多人近邻、框互相干扰、局部重叠
8. `annotation_or_label_suspect`
  - 标注框范围、目标语义、框贴合度存在可疑点

必要时再补一个：

1. `mixed_hard_case`
  - 同时满足 2~3 种难点，不适合硬拆成单一原因

### 11.2 每张图应该怎么标

建议不要对整张图只给 1 个标签，而是：

- 以 **每个 FN GT 框** 为最小单位记录原因；
- 允许 1 个 GT 框打 1~2 个标签；
- 其中第一个标签写“主因”，第二个标签写“次因”。

例如：

- 主因：`small_far_interior`
- 次因：`dark_or_backlit`

或者：

- 主因：`occluded`
- 次因：`pose_or_shape_unusual`

这样后面统计时才不会把真正的难因过度简化。

### 11.3 具体执行步骤

建议按下面流程做：

#### 第 1 步：从算法分桶里抽样

按优先级抽样：

- 先抽 D15
- 再抽 D02
- 最后抽 D05

每条序列先看：

- FN 数最多的前 5~10 张图；
- 对于连续视频段，尽量只保留关键变化帧，避免同一场景重复劳动。

#### 第 2 步：打开原图，看 FN GT 的真实视觉难点

建议重点看：

- 目标有多大；
- 是否明显暗光 / 背光；
- 是否被遮挡；
- 是否只露出半身；
- 是否姿态异常；
- 是否紧贴边界；
- 是否多人重叠；
- GT 本身是否可疑。

#### 第 3 步：给每个 FN GT 打语义标签

每个 FN GT 至少记录：

- `image_stem`
- `sequence_name`
- `gt_index`
- `algorithm_bucket`
- `semantic_primary`
- `semantic_secondary`
- `notes`

其中 `notes` 建议写短句，例如：

- `远景小人，人体对比度很低`
- `半身 + 背光`
- `被立柱遮挡下半身`
- `三人近邻，预测框偏到相邻人`

#### 第 4 步：序列级汇总

每条序列最后统计：

- 哪个语义桶最多；
- 是否存在明显单一主因；
- 是否值得为它单独设计下一轮实验。

#### 第 5 步：形成动作建议

最后不要只停在“这类很多”，而是要落到动作上：

- 如果 `dark_or_backlit` 很多 -> 优先考虑暗光专项补样 / 增强
- 如果 `small_far_interior` 很多 -> 说明远景小人是主问题
- 如果 `crowded_or_overlap` 很多 -> 要看 NMS / 定位 / 框匹配问题
- 如果 `annotation_or_label_suspect` 很多 -> 先回头查标注一致性

---

## 12. 目录结构应该怎么设计

当前不建议再新建一个完全独立、零散的 `person语义细分桶.md`。更推荐把“算法分桶结论”和“语义细分执行结果”保持在同一主题目录下，结构清晰一些。

### 12.1 推荐目录

建议在：

- `backend-train-model/person-train-model/train-result/review/`

下面新增一个统一目录，例如：

```text
backend-train-model/person-train-model/train-result/review/
└─ person_fullframe_with_new_labels_hard_sample_review/
   ├─ README.md
   ├─ bucket_summary_links.md
   ├─ by_source/
   │  ├─ README.md
   │  ├─ review_asset_manifest.json
   │  ├─ source_D15_20260119203927/
   │  │  ├─ README.md
   │  │  └─ sequence_D15_20260119203927/
   │  │     ├─ images/
   │  │     ├─ labels/
   │  │     └─ overlays/
   │  └─ source_.../
   ├─ semantic_bucket_manifest.json
   ├─ semantic_bucket_summary.md
   ├─ sequence_D15_20260119061405/
   │  └─ notes.md
   ├─ sequence_D15_20260119203927/
   │  └─ notes.md
   ├─ sequence_D02_20260123070624/
   │  └─ notes.md
   ├─ sequence_D02_20260123074836/
   │  └─ notes.md
   └─ sequence_D05_20260123074841/
      └─ notes.md
```

### 12.2 每一层的作用

#### `README.md`

写这轮人工复核的范围、目标和口径。

#### `bucket_summary_links.md`

把当前已有：

- `person分桶.md`
- 各个 `fpfn_summary.md`

的链接整理进去，方便跳转。

#### `by_source/`

这是当前建议的**唯一素材工作区**。

这里按 `prepare_report.json` 的 8 个来源整理：

- 待人工复核原图
- 对应 YOLO 标签 txt
- 按不同 run 生成的 overlay 图

如果要把任务分给组员，应该优先从这个目录发素材，而不是在顶层 `sequence_*` 目录里再复制一份。

#### `semantic_bucket_manifest.json`

建议存结构化记录，一条 FN GT 一条记录，例如：

```json



{



  "image_stem": "D15_20260119061405_frame_0345",



  "sequence_name": "D15_20260119061405",



  "split": "test",



  "gt_index": 0,



  "algorithm_bucket": "medium_large_pose_or_appearance",



  "semantic_primary": "dark_or_backlit",



  "semantic_secondary": "partial_body",



  "notes": "中等大小但明显背光，人体边缘与背景反差低"



}



```

#### `semantic_bucket_summary.md`

这是最终给人看的汇总：

- 每个语义桶数量
- 每个序列主因
- 最终建议动作

#### `sequence_*/notes.md`

逐序列的人眼备注，适合写：

- 这条序列整体什么问题最突出
- 哪几张图是典型例子
- 下一轮对它最合适的动作是什么

这里建议只保留 **`notes.md` 这类记录文件**，不要再把同一批原图 / 标签 / overlay 复制第二份到顶层 `sequence_*` 目录里。

也就是说：

- `by_source/` 负责放素材；
- 顶层 `sequence_*` 负责写记录；
- 避免一份素材在两个地方重复维护。

---

## 13. 当前最值得优先做的部分

如果现在时间有限，不要试图一下把全部 hardest FN 都语义细分完。

建议按这个顺序做：

### 第一批必须先看

1. `D15_20260119061405_frame_0345`
2. `D15_20260119061405_frame_0346`
3. `D15_20260119061405_frame_0348`
4. `D15_20260119061405_frame_0355`
5. `D02_20260123070624_frame_0060`
6. `D02_20260123070624_frame_0061`
7. `D02_20260123074836_frame_0022`
8. `D05_20260123074841_frame_0026`

这 8 张基本就能先回答：

- D15 的主因到底偏暗光 / 遮挡 / 半身 / 姿态哪一类；
- D02 的小人到底更偏边界还是更偏纯远景；
- D05 到底是不是真的拥挤定位问题。

### 第二批再补

如果第一批看完已经很明确，就按同序列再各补 3~5 张相邻关键帧，不需要盲目扩大范围。

---

## 14. 当前建议

当前更合理的推进顺序应该是：

1. 保留本文已有的算法分桶结果作为第一层；
2. 在此基础上，围绕 D15 / D02 / D05 的代表帧做第二层人工语义细分桶；
3. 先把 `medium_large_pose_or_appearance` 真正拆开，再决定下一轮优先补哪类样本或增强；
4. 只有当 clothes hardest cases 也明确集中在 person 附着小目标场景时，再启动 `oracle person-guided clothes` 路线验证。

这样做的好处是：

- 不会因为全量人工复核成本太高而卡住；
- 也不会只停留在几何分桶、无法落到具体动作；
- 最终能形成一条从“自动复盘 -> 人工语义细分 -> 下一轮实验设计”的闭环。


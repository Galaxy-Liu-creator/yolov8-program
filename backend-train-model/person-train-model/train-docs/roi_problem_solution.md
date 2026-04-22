# ROI 边界 person 保留规则改进方案

本文档用于记录当前 ROI-aware person 数据集在边界样本上的问题，以及下一版 ROI-aware prepare 规则的建议方案。

当前结论先写在前面：

- 当前 `center_inside` 规则能有效去掉 ROI 外的人，但对边界人偏硬；
- 不建议改成“只要 person 框与 ROI 有一点重叠就保留”，因为那会太松；
- 更推荐使用符合地面业务语义的 **底边中心点 / 脚点规则**；
- 同时引入 **box 与 ROI 的 IoA / 可见比例** 作为补充；
- 后续再配合少量 **crop margin**，降低边界人被裁得过紧的问题。

---

## 1. 当前问题背景

ROI-aware person v1 当前使用的保留规则是：

```text
person 框中心点在 ROI polygon 内 -> 保留
person 框中心点不在 ROI polygon 内 -> 丢弃
```

也就是：

```text
center_inside == true
```

这个规则有优点：

- 简单；
- 可复现；
- 能稳定去掉大部分 ROI 外的人；
- 不会把明显在业务区域外的人轻易放进训练集。

但它也有一个明显问题：

**对 ROI 边界附近的人偏硬。**

例如：

- 人已经部分进入 ROI；
- 人的脚已经踩进业务区域；
- 但 person 框中心点还在 ROI 外；
- 这时当前规则仍会把这个人丢掉。

这会导致一些边界进入样本被错误变成空 ROI 负样本。

---

## 2. 不建议的极端方案

### 2.1 不建议直接使用 any overlap

不要简单改成：

```text
只要 person 框和 ROI 有任意重叠 -> 保留
```

这个规则太松。

可能带来的问题：

- 路边远处的人只擦到 ROI 边缘，也会被保留；
- 业务区域外的人只要框有一点点碰到 ROI，就会被训练成正样本；
- 会削弱 ROI 收紧训练目标的意义；
- 可能重新引入 ROI 外无关人的干扰。

因此：

- `center_inside` 太硬；
- `any overlap` 太松；
- 下一版应该采用中间态的软规则。

---

## 3. 更符合业务语义的判断点：底边中心点

当前 ROI polygon 本质上画的是地面业务区域。

在加油站监控画面中，判断一个人是否进入业务区域，更合理的点通常不是：

```text
person 框中心点
```

而是：

```text
person 框底边中心点
```

也可以理解为：

```text
脚点 / 落地点
```

原因是：

- ROI 对应的是地面区域；
- 人是否进入业务区域，通常取决于脚是否站到该区域；
- 目标框中心点往往位于人体躯干附近，不一定能代表人的落地点；
- 对刚进入 ROI 或半身进入 ROI 的人，中心点可能仍在 ROI 外，但脚点已经在 ROI 内。

因此，下一版规则应优先考虑：

```text
bottom_center_inside
```

即：

```text
person 框底边中心点是否在 ROI polygon 内
```

---

## 4. 用 box IoA 作为补充条件

只看底边中心点也不是完美的。

一些边界样本可能出现：

- 脚点被遮挡；
- 框底边落在 ROI 外一点点；
- 但人体已有相当一部分在 ROI 内。

因此建议增加第二个保留条件：

```text
box_ioa_with_roi >= threshold
```

这里推荐使用 **IoA**，不是 IoU。

---

## 5. 为什么用 IoA 而不是 IoU

### 5.1 IoU 不适合这个场景

IoU 公式是：

```text
area(person_box ∩ ROI) / area(person_box ∪ ROI)
```

但 ROI 通常远大于 person 框。

这会导致：

- 即使 person 大部分已经在 ROI 内；
- 因为 ROI 很大，`person_box ∪ ROI` 也很大；
- IoU 数值仍然会很低；
- 阈值不好解释。

### 5.2 IoA 更符合当前语义

这里真正关心的是：

```text
这个 person 框有多少比例落在 ROI 内
```

所以应该使用：

```text
box_ioa = area(person_box ∩ ROI) / area(person_box)
```

这个指标语义更直接：

- `box_ioa = 1.0`：person 框完全在 ROI 内；
- `box_ioa = 0.5`：person 框约一半在 ROI 内；
- `box_ioa = 0.0`：person 框完全不在 ROI 内。

---

## 6. 推荐保留规则 v2

下一版建议使用如下逻辑：

```text
保留 person 框，当满足：

bottom_center_inside == true
OR
box_ioa_with_roi >= min_box_ioa
```

第一版建议阈值：

```text
min_box_ioa = 0.25
```

也就是说：

- 如果脚点在 ROI 内，直接保留；
- 如果脚点不在 ROI 内，但 person 框至少有 `25%` 面积在 ROI 内，也保留；
- 否则丢弃。

---

## 7. 为什么先用 `min_box_ioa = 0.25`

`0.25` 是一个相对稳妥的第一版阈值。

如果阈值太低，例如：

```text
0.05 / 0.10
```

可能会导致：

- 只是擦到 ROI 边界的人也被保留；
- ROI 外无关人重新进入训练集。

如果阈值太高，例如：

```text
0.40 / 0.50
```

可能会导致：

- 刚进入 ROI 的人仍被丢弃；
- 半身进入 ROI 的边界样本仍然不足。

因此建议先从：

```text
0.25
```

开始。

后续根据 overlay 结果调整：

- 仍然太严：降到 `0.20`
- 太多边界外人被保留：升到 `0.30`

---

## 8. 建议增加 crop margin

保留规则只解决“框是否保留”的问题。

当前 ROI-aware v1 还存在另一个问题：

```text
裁剪到 ROI polygon 的最小外接矩形
```

这个裁剪可能对边界样本过紧。

即使某个边界 person 被新规则保留，如果 crop 很紧，也可能导致：

- 人体可见区域被截断；
- 边界上下文太少；
- 训练时定位更困难。

因此建议下一版增加 margin。

推荐第一版：

```text
crop_margin_px = 64
```

或：

```text
crop_margin_ratio = 0.05
```

两者含义：

- `crop_margin_px`：在 ROI 最小外接矩形上下左右各扩固定像素；
- `crop_margin_ratio`：按 ROI 外接矩形宽高比例扩边。

当前更推荐先用：

```text
crop_margin_px = 64
```

因为：

- 语义直观；
- 便于看 overlay；
- 不同分辨率下也容易调参。

---

## 9. 对当前 4 张问题帧的解释

当前重点复查的 4 张问题帧为：

- `D15_20260119203927_frame_0181`
- `D15_20260119203927_frame_0182`
- `D15_20260119203927_frame_0183`
- `D15_20260119203927_frame_0184`

当前它们的状态是：

```text
boxes=1, kept=0, dropped=1
```

也就是说：

- 每张图 fullframe 中都有 1 个 person 框；
- 当前 ROI-aware v1 都把它们丢弃；
- 丢弃原因是 `center_inside=false`。

重新计算后，4 个框中心点到 ROI 边界的 signed distance 约为：

```text
-118px 到 -133px
```

这说明它们不是“中心点刚好压线”，而是中心点确实在 ROI 外一段距离。

如果业务上希望这些人被保留，需要满足以下任一条件：

- 调整 ROI polygon，让其覆盖到这些人的落地点 / 足够人体区域；
- 或改用 `bottom_center_inside OR box_ioa >= 0.25` 规则；
- 或配合 crop margin 与更宽松的边界保留策略。

如果业务上认为这些人确实在橙色 ROI 外，不应参与检测，那么当前丢弃是合理的。

---

## 10. 推荐实现字段

建议在 `person_project_config.json` 的 `roi.keep_rule` 中逐步扩展，例如：

```json
{
  "roi": {
    "enabled": true,
    "mode": "mask_then_crop",
    "keep_rule": {
      "center_inside": false,
      "bottom_center_inside": true,
      "min_box_ioa": 0.25
    },
    "crop_margin_px": 64,
    "config_path": "train-result/working/roi/roi_config.generated.json"
  }
}
```

说明：

- `center_inside=false`：不再只依赖框中心点；
- `bottom_center_inside=true`：优先使用脚点语义；
- `min_box_ioa=0.25`：允许部分进入 ROI 的 person 被保留；
- `crop_margin_px=64`：裁剪时保留一点边界上下文。

---

## 11. 推荐落地顺序

不要一次改太多，建议分阶段验证。

### 阶段 1：只改保留规则

新增：

```text
bottom_center_inside OR box_ioa >= 0.25
```

然后只重跑：

- ROI-aware prepare；
- 4 张问题帧 overlay；
- 数据集统计报告。

重点看：

- 4 张问题帧是否被保留；
- 总保留框数增加多少；
- `D15_20260119061405` 的丢弃框是否明显减少；
- 是否引入太多明显 ROI 外的人。

### 阶段 2：增加 crop margin

如果阶段 1 方向正确，再加入：

```text
crop_margin_px = 64
```

重点看：

- 边界人是否被裁得更自然；
- 小目标尺寸是否更适合训练；
- 是否引入过多无关背景。

### 阶段 3：重新训练

规则和数据集确认后，再重新训练：

- 优先使用 `person_fullframe_baseline/weights/best.pt` 作为初始化；
- 不建议继续从 `yolov8n.pt` 重新起训。

---

## 12. 推荐训练对照

在完成规则 v2 后，建议训练 run 命名为：

```text
person_roi_aware_v2_from_fullframe
```

建议命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v2_from_fullframe --device cpu --workers 0 --batch 4 --imgsz 640 --epochs 180 --patience 60 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

如果 `640` 仍然不够，再试：

```text
imgsz=768, batch=2
```

---

## 13. 最终建议

当前最推荐的下一版 ROI-aware 规则是：

```text
keep if:
  bottom_center_inside == true
  OR box_ioa_with_roi >= 0.25

crop:
  mask_then_crop + crop_margin_px = 64
```

这套规则的目标是：

- 保留真正进入业务区域的边界 person；
- 仍然过滤明显 ROI 外的人；
- 避免 `center_inside` 过硬导致漏掉边界进入样本；
- 避免 `any overlap` 过松导致 ROI 外无关人重新污染训练。

---

## 14. 一句话结论

下一版不应该继续用“框中心点是否在 ROI 内”作为唯一标准，而应该改成：

**看人的脚点是否进入业务地面区域，或者至少有足够比例的人框已经进入 ROI。**

也就是：

```text
bottom_center_inside OR box_ioa >= 0.25
```

再配合：

```text
crop_margin_px = 64
```

这样更符合当前加油站 ROI person 检测的业务语义。

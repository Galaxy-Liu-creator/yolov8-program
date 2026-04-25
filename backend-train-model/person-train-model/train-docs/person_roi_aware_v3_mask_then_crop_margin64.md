# person_roi_aware_v3_mask_then_crop_margin64

本文档用于定义 `person_roi_aware_v3_mask_then_crop_margin64` 这条 ROI-aware person 数据准备方案，作为当前 `person_roi_aware_v2` 的下一步改进方向说明。**当前仓库代码已支持该方案的 `prepare-roi-aware` 落地；本文同时记录方案定位、风险与验证口径。**

## 1. 当前问题背景

当前 `person_roi_aware_v2` 已经把 keep rule 调整为：

```text
bottom_center_inside == true
OR
box_ioa_with_roi >= 0.25
```

相比历史 v1，这套规则已经更能保留真正进入 ROI 边界的人，但仍然存在两个现实问题：

1. 当前历史 v2 默认配置仍然是 `mask_then_crop + crop_margin_px=0`，如果要跑这一版，需要在版本化 `prepare-roi-aware` 命令里显式指定 `crop_margin_px=64`；
2. 某些边界 person 虽然被 keep rule 保留，但其人体可见区域有一部分在 ROI 外，这部分像素会在 mask 阶段被置为 `0`。

因此，当前 v2 可能出现一种不够理想的正样本：

- 该 person 因为脚点进入 ROI 而被保留；
- 但 person 框内部仍有较大比例像素被置黑；
- 最终训练图中的正样本外观不够自然，尤其是 ROI 边界样本。

## 2. 一个需要先说明清楚的事实

源 `person` 数据中，fullframe 标签本身是对所有已标注 person 都存在的；问题不在“源数据没标注”。

真正需要区分的是：

- **源 fullframe 标注**：所有已标注 person 都有框；
- **ROI-aware prepared 标签**：只保留满足 ROI keep rule 的 person 框；
- **ROI-aware prepared 图像**：根据 prepare 方案，可能会保留或抹掉 ROI 外像素。

因此，讨论 ROI-aware 方案时，要看的是：

```text
哪些 person 像素最终仍然出现在 prepared 图像里
以及
这些 person 是否仍然有对应标签
```

## 3. 方案定义

建议的 v3 `mask_then_crop + margin64` 方案如下：

### 3.1 keep rule

继续沿用当前 v2：

```text
keep if:
  bottom_center_inside == true
  OR box_ioa_with_roi >= 0.25
```

### 3.2 图像处理流程

建议流程：

```text
原图
-> 根据 ROI polygon 生成 mask
-> ROI 外像素置 0
-> 计算 ROI polygon 的最小外接矩形
-> 在外接矩形四周增加 crop_margin_px = 64
-> 按扩边后的矩形进行 crop
```

也就是说，和当前 v2 的差异主要不是 keep rule，而是：

```text
mask_then_crop
-> 改成
mask_then_crop + crop_margin_px = 64
```

### 3.3 标签处理流程

- 保留框的判定仍然在 fullframe 坐标系完成；
- 只输出满足 keep rule 的 person 标签；
- 标签再映射到扩边后的 crop 图坐标系；
- 如有必要，统计被 crop 边界裁剪的框数量。

## 4. 为什么这条方案值得先做

这条方案的核心优势是：**在不把 ROI 外无关可见区域大量重新放回训练图的前提下，先缓解边界样本“裁得太紧”的问题。**

相比当前 v2，它的预期收益主要有：

1. **减轻贴边问题**
   - 当前最小外接矩形过紧，边界 person 容易贴着图像边界；
   - 加 `margin64` 后，person 在 crop 图中的位置会更自然。
2. **保留一点上下文**
   - 即使 ROI 外仍然被置黑，扩边后的 crop 也能给边界目标留出更稳定的局部空间；
   - 训练时更不容易出现“目标紧贴图像边框”的极端样本。
3. **继续控制 ROI 外可见干扰**
   - 和 `crop-only` 不同，这条方案不会把 ROI 外大量真实像素重新带回图中；
   - 对“作业区 person”这一训练目标更保守、更干净。

## 5. 这条方案不能解决什么

这条方案虽然更稳，但**并不能彻底解决“边界正样本被黑掉”的问题**。

因为在 `mask_then_crop` 下：

- 只要 person 框有一部分在 ROI 外；
- 那部分 ROI 外像素仍然会被置黑；
- `crop margin` 只能缓解“裁得太紧”，不能把已经被 mask 掉的真实人体像素恢复回来。

因此，对你当前最关心的这个问题，必须明确回答：

```text
如果一个 person 被保留，但 person 框有较大一部分落在 ROI 外，
那么该框内部确实可能出现大面积黑块。
```

但也要注意，这并不等于“整个 person 框一定是全黑”。

更准确的说法是：

- 只要该 person 仍有一部分位于 ROI 内；
- 那么框中 ROI 内对应的人体像素仍然可见；
- 变黑的是框内那些落在 ROI 外的区域。

真正危险的是另一种情况：

- `bottom_center_inside=true`；
- 但 `box_ioa` 很小；
- 结果这个 person 虽然被保留，却只剩很少一部分可见，形成“**大部分是黑块的正样本框**”。

如果这类样本占比高，确实会明显影响训练效果。

## 6. 对这类风险的判断

因此，这条方案虽然比当前 v2 更好，但它仍然需要重点观察下面这个风险：

```text
低可见面积的 keep-positive 是否过多
```

建议重点抽查两类样本：

1. `bottom_center_inside=true` 但 `box_ioa` 明显很低的样本；
2. crop 后 person 框内黑块比例很高的边界样本。

如果复查后发现这类样本很多，那么说明仅靠 `margin64` 还不够，后续可能需要继续追加约束，例如：

- 给 `bottom_center_inside` 再加一个较低的可见面积下限；
- 或把 `crop-only` 作为专门的对照实验继续比较。

## 7. 与生产语义的关系

如果目标是严格贴近当前线上链路，那么线上实际上更接近：

```text
fullframe person detect
-> ROI filtering
```

而不是训练阶段的 `mask_then_crop`。

但在 ROI-aware 训练分支里，`mask_then_crop + margin64` 仍然有工程意义，因为它更强调：

- 训练目标是 ROI 内 / 作业区 person；
- 尽量降低 ROI 外 person 的可见干扰；
- 同时先把最明显的“crop 太紧”问题修掉。

因此，这条方案更适合作为：

```text
当前 ROI-aware person 的保守改进版
```

而不是“最贴近现网 fullframe 推理”的那一条线。

## 8. 推荐验证方式

建议把这条方案作为 **v3 主推荐实验**，重点验证以下内容：

1. prepared 统计
   - 保留框数
   - 丢弃框数
   - crop 裁剪框数
   - 空负样本数
2. 边界样本可视化
   - 对历史问题帧继续生成 overlay
   - 重点看边界人是否不再紧贴 crop 边界
3. 训练指标
   - `test recall`
   - `test mAP50`
   - `test mAP50-95`
4. 风险观察
   - 低 `box_ioa` keep-positive 是否仍然很多
   - 正样本框内部大面积黑块是否仍然明显

## 9. 当前建议结论

对于下一步实验优先级，当前更推荐：

```text
先做 person_roi_aware_v3_mask_then_crop_margin64
再做 person_roi_aware_v3_crop_only_margin64 作为对照
```

原因是：

- 这条方案改动更小；
- 更容易和当前 v2 做单因素比较；
- 更不容易把 ROI 外 person 可见区域大规模重新引回训练图；
- 更适合作为当前 ROI-aware person 的默认保守升级方向。

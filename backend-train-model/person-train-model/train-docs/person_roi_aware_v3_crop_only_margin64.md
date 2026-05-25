# person_roi_aware_v3_crop_only_margin64

本文档用于定义 `person_roi_aware_v3_crop_only_margin64` 这条候选 ROI-aware person 数据准备方案，作为 `mask_then_crop` 方案的对照实验。**当前仓库代码已支持该方案的 `prepare-roi-aware` 落地；本文同时记录方案定位、风险与验证口径。**

## 1. 方案定位

这条方案的核心目标是：

```text
尽量让被保留的 ROI 边界 person 看起来更自然
```

因此它和当前 `person_roi_aware_v2` 的主要差异不在 keep rule，而在图像处理方式：

- 当前 v2：`mask_then_crop`
- 本方案：`crop_only + margin64`

## 2. 一个必须先说清楚的事实

源 `person` 数据里，fullframe 的 person 都是有标注的；问题不是“原始数据没有标到 ROI 外的人”。

但在 ROI-aware prepare 之后，真正输出到训练集里的标签，并不是所有源 person，而是：

```text
仅保留满足 ROI keep rule 的 person
```

因此，一旦采用 `crop-only`：

- 图像里仍可能看见 ROI 外的人；
- 但这些 ROI 外的人如果没有通过 keep rule；
- 那么它们的标签在 ROI-aware prepared 数据中会被丢弃。

所以这条方案最大的风险，不是“源标签缺失”，而是：

```text
prepared 图像里可能出现可见的、但在 prepared 标签中被丢掉的 person
```

这类样本会形成 ROI-aware 训练里的未保留可见干扰。

## 3. 方案定义

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
-> 计算 ROI polygon 的最小外接矩形
-> 在外接矩形四周增加 crop_margin_px = 64
-> 直接按扩边后的矩形进行 crop
-> 不对 ROI 外像素做置黑
```

### 3.3 标签处理流程

- 保留框的判定仍在 fullframe 坐标系完成；
- 只输出满足 keep rule 的 person 标签；
- 标签再映射到扩边后的 crop 图坐标系；
- 未通过 keep rule 的 person，即使在 crop 图中仍然可见，也不会被输出为最终标签。

## 4. 这条方案的预期优势

相比 `mask_then_crop`，这条方案最直接的优势是：

### 4.1 被保留的边界 person 更自然

如果某个 person 因为脚点进入 ROI 而被保留，那么：

- 在 `mask_then_crop` 下，框内 ROI 外部分像素会被置黑；
- 在 `crop-only` 下，这个人体的完整外观仍可保留。

这意味着：

- 边界正样本更接近真实摄像头画面；
- person 框内部不容易出现大块黑区；
- 对边界人的形状学习可能更自然。

### 4.2 更容易观察 keep rule 本身是否合理

因为没有 mask，这条方案能更纯粹地回答一个问题：

```text
当前 keep rule v2 本身是否足够合理
```

否则在 `mask_then_crop` 下，训练结果往往混合了两种因素：

1. keep rule 的效果；
2. hard mask 对边界正样本外观的影响。

`crop-only` 更适合作为对照实验去分离这两件事。

## 5. 这条方案的核心风险

这条方案最大的问题恰恰也很明确：

```text
ROI 外 person 可能在图像里仍然可见，但在最终 prepared 标签里被丢掉
```

也就是说，虽然源数据对这些人是有标注的，但 ROI-aware prepare 阶段会主动把它们过滤掉。  
如果 crop 后这些人还在画面里，它们就会变成：

```text
可见 person 像素 + 无对应 ROI-aware 标签
```

这会带来几类风险：

1. **训练目标不够干净**
   - 模型输入里混入了更多“不是主要训练对象”的 person 外观。
2. **ROI-aware 语义被稀释**
   - 模型可能重新看到大量 ROI 外的人体纹理、轮廓与背景关系。
3. **边界判断更难解释**
   - 指标变好时，不容易立刻判断是因为边界人更自然，还是因为 ROI 外信息重新回流。

## 6. 对你当前疑问的直接回应

你担心的是：

```text
既然 source person 都标了，
那 crop 后又把 ROI 外 person 带进来，会不会影响训练？
```

更准确的回答是：

- **会有影响风险**；
- 影响不是因为源数据没标，而是因为 ROI-aware 最终输出标签已经把这部分 person 主动过滤掉了；
- 所以这些 person 在 ROI-aware prepared 数据中会变成“可见但未保留”的干扰项。

因此，这条方案不能默认当作主线方案直接替代 `mask_then_crop`，而更适合作为：

```text
针对“边界正样本是否被 mask 得过于不自然”的专项对照实验
```

## 7. 什么时候这条方案才有价值

这条方案不是不能做，而是需要带着约束做。

建议只有在下面几个条件同时满足时，才把它当作认真候选：

1. `crop_margin_px` 控制得比较保守
   - 第一版先固定 `64`，不要一开始就扩太大；
2. ROI polygon 本身质量较稳定
   - 如果 ROI 多边形本来就偏松，`crop-only` 更容易把无关 person 带进来；
3. 有可视化抽查
   - 要抽查 crop 后是否频繁出现明显 ROI 外 person；
4. 有训练后对照
   - 至少和 `mask_then_crop + margin64` 做一轮相同训练参数的对照。

## 8. 推荐验证重点

建议把这条方案作为 **v3 对照实验**，重点看下面几件事：

1. 图像层面
   - 被保留的边界 person 是否明显更自然；
   - crop 图中是否频繁出现 ROI 外可见 person。
2. prepared 统计
   - 保留框数
   - 丢弃框数
   - 裁剪框数
   - 空负样本数
3. 训练指标
   - `test recall`
   - `test mAP50`
   - `test mAP50-95`
4. 误差解释
   - 如果指标上涨，要进一步确认是不是来自真正更好的边界 person 学习；
   - 而不是来自 ROI 外 person 重新被模型“看到”。

## 9. 当前建议结论

当前更合理的工程结论不是“直接改成 crop-only”，而是：

```text
把 person_roi_aware_v3_crop_only_margin64 当成对照实验
而不是默认主线
```

原因是：

- 它确实有机会让边界正样本更自然；
- 但它也更容易让 ROI-aware 训练目标被可见的 ROI 外 person 稀释；
- 如果没有配套可视化复核和对照训练，很容易把结果解释错。

因此，当前推荐顺序仍然是：

```text
先跑 person_roi_aware_v3_mask_then_crop_margin64
再跑 person_roi_aware_v3_crop_only_margin64
```


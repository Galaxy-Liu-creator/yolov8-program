# clothes_merged_with_new_labels_v1_baseline 结果审查

审查日期：2026-05-06

## 1. 审查对象

- 训练报告：`backend-train-model/new_clothes_train/train-result/artifacts/reports/clothes_merged_with_new_labels_v1_baseline_train.json`
- 评估报告：`backend-train-model/new_clothes_train/train-result/artifacts/reports/clothes_merged_with_new_labels_v1_baseline_eval.json`
- 训练曲线：`backend-train-model/new_clothes_train/train-result/artifacts/runs/clothes_merged_with_new_labels_v1_baseline/results.csv`

## 2. 数据口径说明

本次训练使用的数据集为：

- `backend-train-model/new_clothes_train/train-result/datasets/clothes_merged_with_new_labels_v1/dataset.yaml`

其底层 split 口径为：

- legacy `g31/g32/g33` 继续沿用既有 `trainval_balanced_v1 + unified_holdout_v1`
- `gnew` 已从旧版 `sequence_contiguous_by_sorted_stem` 改为 `stratified_random_by_positive_empty`
- 当前 `gnew` 分层随机切分后，`val/test` 的空标注率与框密度已经基本对齐

因此，这次训练结果比旧版 contiguous split 更适合作为当前阶段的训练/评估参考。

## 3. 训练配置回顾

来自训练报告的关键参数：

- `base_model`: `backend-train-model/weights/yolov8n.pt`
- `imgsz`: `640`
- `epochs`: `180`
- `batch`: `4`
- `patience`: `40`
- `workers`: `0`
- `device`: `0`
- `seed`: `42`
- `single_cls`: `true`

说明：

- `workers=0` 说明这次训练是在当前本机稳定性优先口径下完成的；
- 它不影响本次结果可用性，但如果后续迁移到另一台 GPU 训练机复现实验，仍可按项目默认建议回到 `workers=4`。

## 4. 最终评估结果

### 4.1 val 集

- Precision: `0.9769`
- Recall: `0.9594`
- mAP50: `0.9817`
- mAP75: `0.8645`
- mAP50-95: `0.7106`

### 4.2 test 集

- Precision: `0.9835`
- Recall: `0.9683`
- mAP50: `0.9924`
- mAP75: `0.8491`
- mAP50-95: `0.7075`

## 5. 结果解读

### 5.1 整体表现

从当前指标看，这一版 `clothes_merged_with_new_labels_v1_baseline` 的整体表现是比较强的：

- `val/test` 的 Precision、Recall、mAP50 都非常高；
- `test mAP50 = 0.9924`，说明单类 `clothes` 检测在当前数据口径下已经具备较强检出能力；
- `mAP50-95` 稳定在 `0.70+`，说明更严格 IoU 阈值下仍有不错表现，但边界框质量还有继续优化空间。

### 5.2 val 与 test 的关系

这次修复 `gnew` 切分策略之后，一个重要现象是：

- `val mAP50-95 = 0.7106`
- `test mAP50-95 = 0.7075`

二者已经非常接近。

这说明：

- 本轮针对 `gnew` 分布偏差的修复是有效的；
- 当前 `val/test` 的评估信号相比旧版 contiguous 方案更加一致；
- 训练过程中的 val 指标，已经能更可靠地反映 test 集上的大致表现。

### 5.3 一个需要注意的细节

虽然 `test` 的 Precision、Recall、mAP50 都略高于 `val`，但：

- `test mAP75 = 0.8491`
- `val mAP75 = 0.8645`

且：

- `test mAP50-95 = 0.7075`
- `val mAP50-95 = 0.7106`

这说明 test 集上的“是否能检出”表现很好，但在更高 IoU 阈值下，框定位质量并没有全面超过 val。

因此更合理的结论不是“test 全面优于 val”，而是：

- 当前模型在 `val/test` 上的总体水平已经非常接近；
- 但框定位精度仍是比粗检出能力更敏感的短板。

### 5.4 从训练曲线看训练状态

从 `results.csv` 可以看到：

- 训练早期从 `mAP50-95 ~ 0.51` 较快抬升到 `0.63+`
- 中后期逐步提升到 `0.68~0.70`
- 后期进入平台区，提升趋缓

这说明：

- 当前数据集和参数配置是有效的；
- 模型并不是一开始就训练失败，而是正常收敛到较高水平；
- 后期已经进入“边际收益变小”的阶段。

## 6. 当前结论

### 6.1 可以确认的结论

1. **这版模型结果是可用且质量较高的。**
2. **`gnew` 切分修复后，`val/test` 的一致性明显改善。**
3. **当前训练结果已经可以作为 `new_clothes_train` 线的有效 baseline。**

### 6.2 不应过度解读的部分

1. 不能把当前高指标直接写成“已完成未穿工服告警器”。
   它仍然只是 `clothes` 单类检测模型。
2. 不能因为 `test mAP50` 很高，就忽略 `mAP75` / `mAP50-95` 仍然显示框定位还有提升空间。
3. 不能把当前“分层随机切分”误写成最终最严谨的数据治理终态；
   它是当前已知事实下更稳妥的训练入口，而不是场景级切分终局。

## 7. 后续建议

### 7.1 如果当前目标是先固定一个可复现 baseline

建议：

- 直接把 `clothes_merged_with_new_labels_v1_baseline` 作为当前新线 baseline 记录下来；
- 后续评估、对照、导出都统一基于这一版进行。

### 7.2 如果当前目标是继续提高严谨性

建议优先顺序：

1. 明确 `gnew` 中每个视频/场景对应的 stem 范围；
2. 升级为“按视频场景整段切分”；
3. 再观察新 split 下 `val/test` 与本轮 baseline 的指标变化。

### 7.3 如果当前目标是继续提升模型指标

在不破坏当前数据口径稳定性的前提下，优先考虑：

1. 基于当前 run 做逐图 FP/FN 复盘；
2. 重点看高 IoU 下的框偏移问题；
3. 再决定是否要做更大模型、imgsz 调整或更细的数据修订。

## 8. 总结

这次 `clothes_merged_with_new_labels_v1_baseline` 的结果可以评价为：

- **检测能力强**；
- **val/test 一致性较好**；
- **已具备作为当前新线 baseline 的条件**；
- **后续若追求更严格泛化结论，仍建议补视频场景级切分。**

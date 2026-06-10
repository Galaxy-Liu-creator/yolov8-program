# Personcrop 诊断性实验方案

## 1. 背景与问题

### 1.1 当前状态

**已完成工作**：
- Personcrop 双上游 A/B 训练完成
- A（pred_pc_clo_base）：Test mAP50-95 **0.7416**
- B（pred_pc_clo_hardv1）：Test mAP50-95 **0.7471**
- 代表帧复盘显示：70% 代表帧 B 优于 A

**核心问题**：
- Personcrop (0.74) 相比 Fullframe clothes baseline (0.80) **低了 6 个百分点**
- 当前只有 crop 级评估，缺少原图级对比
- 不清楚性能差距来自：person 召回不足 / clothes 模型容量 / 裁剪策略损失

### 1.2 诊断目标

**必须回答的三个关键问题**：

**Q1**：在统一原图级评估空间下，personcrop 是否真的优于 fullframe？

**Q2**：Person 召回是否是当前主要瓶颈？

**Q3**：如果用"理想 person"（GT person 框），personcrop 能达到什么上界？

---

## 2. 诊断实验设计

### 2.1 实验1：原图级 Personcrop vs Fullframe 对比

#### **实验目标**

在统一评估空间（原图级）下，对比三条链路的真实性能。

#### **实验设计**

**测试集**：`clothes_merged_with_new_labels_v1` 的 test split（453 张图）

**对比链路**：
1. **Fullframe baseline**：直接在原图上检测 clothes
2. **Personcrop A**：person A → crop → clothes → 映射回原图
3. **Personcrop B**：person B → crop → clothes → 映射回原图

**关键要求**：
- 所有链路在**同一批原图**上评估
- 使用统一的 GT clothes 标注
- 使用统一的评估阈值（conf / NMS IoU / match IoU）

#### **执行步骤**

```bash
# Step 1: Fullframe baseline 在 test split 上评估
python backend-train-model/train_workwear.py evaluate --mode fullframe --weights All-train-model/artifacts/runs/clothes_merged_v2_balanced_from_first_holdout_v1/weights/best.pt --data new_clothes_train/train-result/datasets/clothes_merged_with_new_labels_v1/dataset.yaml --split test --conf 0.45

# Step 2: Personcrop A/B 映射回原图评估
python backend-train-model/personcrop-train/train-code/evaluate_personcrop_on_original.py --personcrop-data-a personcrop-train/train-result/prepared/pred_pc_person_base/dataset.yaml --personcrop-weights-a personcrop-train/train-result/artifacts/runs/pred_pc_clo_base/weights/best.pt --personcrop-data-b personcrop-train/train-result/prepared/pred_pc_person_hardv1/dataset.yaml --personcrop-weights-b personcrop-train/train-result/artifacts/runs/pred_pc_clo_hardv1/weights/best.pt --source-dataset new_clothes_train/train-result/datasets/clothes_merged_with_new_labels_v1/dataset.yaml --split test --conf 0.45 --output personcrop-train/train-result/review/diag_exp1_original_compare/
```

#### **预期产出**

**产出文件**：
- `original_level_comparison_report.json`：三条链路的原图级指标对比
- `per_image_comparison.json`：逐帧对比，哪些图 personcrop 优于 fullframe
- `comparison_summary.md`：可读性总结报告

**判断标准**：
- 如果 personcrop B 原图级 mAP50-95 **≥ 0.80**：说明 personcrop 确实优于 fullframe
- 如果 personcrop B 原图级 mAP50-95 **< 0.78**：说明存在显著性能损失，需要进入实验2/3

---

### 2.2 实验2：Person 召回瓶颈量化分析

#### **实验目标**

量化：有多少 clothes GT 因为 person 漏检而无法进入下游。

#### **实验设计**

**核心思路**：
1. 对每张 test 图，加载 GT person 框和 GT clothes 框
2. 用 person 检测器预测 person 框
3. 统计被漏检的 person 框数量
4. 分析这些漏检的 person 框对应了多少 clothes GT
5. 计算：因 person 漏检导致无法进入下游的 clothes 目标占比

**关键指标**：
- `missed_person_count`：漏检的 person 框数
- `unassigned_clothes_due_to_missed_person`：因 person 漏检而无法分配的 clothes GT 数
- `bottleneck_ratio = unassigned_clothes_due_to_missed_person / total_clothes_gt`

#### **执行步骤**

```bash
# 实验2：Person 召回瓶颈量化分析
python backend-train-model/personcrop-train/train-code/analyze_person_bottleneck.py --source-dataset new_clothes_train/train-result/datasets/clothes_merged_with_new_labels_v1/dataset.yaml --person-weights-a person-train-model/train-result/export/person_detect_yolov8_with_new_labels.pt --person-weights-b person-train-model/train-result/export/person_detect_yolov8_with_new_labels_and_hard_examples_v1.pt --split test --person-conf 0.20 --assignment-min-ioa 0.35 --output personcrop-train/train-result/review/diag_exp2_person_bottleneck/
```

#### **预期产出**

**产出文件**：
- `person_bottleneck_report.json`：瓶颈量化统计
- `per_image_bottleneck.json`：逐帧分析，哪些图因 person 漏检损失严重
- `bottleneck_summary.md`：可读性总结

**判断标准**：
- 如果 `bottleneck_ratio > 15%`：**person 是主要瓶颈**，应优先优化 person
- 如果 `5% < bottleneck_ratio < 15%`：person 是次要瓶颈，可考虑调整 person_conf 阈值
- 如果 `bottleneck_ratio < 5%`：**person 不是主要瓶颈**，应优化 clothes 模型或裁剪策略

---

### 2.3 实验3：理想 Person 上界实验

#### **实验目标**

如果用"理想 person"（GT person 框），personcrop 能达到什么性能上界。

#### **实验设计**

**核心思路**：
1. 修改 personcrop 数据生成脚本，添加 `--use-gt-person` 模式
2. 使用 GT person 框（而非检测框）生成 personcrop 数据集
3. 训练 clothes 模型
4. 评估性能上界

**关键假设**：
- 如果"理想 person" personcrop 能达到 **0.78-0.80**，说明 person 确实是瓶颈
- 如果"理想 person" personcrop 仍然只有 **0.75** 左右，说明瓶颈在 clothes 端或裁剪策略

#### **执行步骤**

```bash
# Step 1: 生成"理想 person"数据集
python backend-train-model/personcrop-train/train-code/prepare_personcrop_with_gt_person.py --dataset-yaml new_clothes_train/train-result/datasets/clothes_merged_with_new_labels_v1/dataset.yaml --output-root personcrop-train/train-result/prepared/pred_pc_person_ideal_gt --assignment-min-ioa 0.35 --device 0

# Step 2: 训练 clothes 模型
python backend-train-model/train_workwear.py train --mode personcrop --project-config personcrop-train/personcrop_project_config.json --run-name pred_pc_clo_ideal_gt --data personcrop-train/train-result/prepared/pred_pc_person_ideal_gt/dataset.yaml --model yolov8n.pt --device 0

# Step 3: 评估
python backend-train-model/train_workwear.py evaluate --mode personcrop --project-config personcrop-train/personcrop_project_config.json --run-name pred_pc_clo_ideal_gt_eval --weights personcrop-train/train-result/artifacts/runs/pred_pc_clo_ideal_gt/weights/best.pt --data personcrop-train/train-result/prepared/pred_pc_person_ideal_gt/dataset.yaml --split test
```

**注意**：实验3的产出会自动保存到 `personcrop-train/train-result/artifacts/reports/pred_pc_clo_ideal_gt_eval/` 目录。

#### **预期产出**

**产出文件**：
- `pred_pc_clo_ideal_gt_eval.json`：理想 person 上界的评估报告
- `ideal_person_upper_bound_summary.md`：上界分析总结

**判断标准**：
- 如果理想 person 上界 mAP50-95 **≥ 0.78**：person 是瓶颈，优化 person 有显著收益空间
- 如果理想 person 上界 mAP50-95 **< 0.76**：person 不是主要瓶颈，需要优化 clothes 或裁剪

---

## 3. 基于诊断结果的优化方案

### 3.1 分支A：Person 是瓶颈（bottleneck_ratio > 15%）

#### **优化方向A.1：调整 person_conf 阈值**

**当前**：`person_conf = 0.20`
**尝试**：降低到 `0.15` 或 `0.10`

```bash
# 优化方向A.1：降低 person_conf 阈值
python backend-train-model/personcrop-train/train-code/prepare_personcrop_from_dataset_yaml.py --dataset-yaml new_clothes_train/train-result/datasets/clothes_merged_with_new_labels_v1/dataset.yaml --output-root personcrop-train/train-result/prepared/pred_pc_person_hardv1_conf015 --person-weights person-train-model/train-result/export/person_detect_yolov8_with_new_labels_and_hard_examples_v1.pt --person-conf 0.15 --device 0
```

**预期收益**：
- 可能增加 positive_crops，减少 fallback
- 但可能引入更多噪声框

---

#### **优化方向A.2：补标注 person test FN**

**当前已知**：
- Person test FN = 35 个样本
- 主要集中在 `D15_20260119061405`、`D15_20260119203927`、`D02_20260123074836`、`D02_20260123070624`

**执行步骤**：
1. 提取这 35 个 FN 样本的原图
2. 人工检查：是否确实有 person 目标但被漏检
3. 补充标注（如果确实遗漏）
4. 重新训练 person 模型

**预期收益**：
- Person Recall 从 0.70 提升到 0.75-0.80
- Personcrop mAP50-95 可能从 0.74 提升到 0.78-0.80

---

### 3.2 分支B：Person 不是主要瓶颈（bottleneck_ratio < 5%）

#### **优化方向B.1：优化裁剪策略**

**尝试方向**：
- 增大 crop margin（当前隐式为 0）
- 调整 assignment_min_ioa（当前 0.35，可尝试 0.30）

```bash
# 优化方向B.1：优化裁剪策略
python backend-train-model/personcrop-train/train-code/prepare_personcrop_from_dataset_yaml.py --dataset-yaml new_clothes_train/train-result/datasets/clothes_merged_with_new_labels_v1/dataset.yaml --assignment-min-ioa 0.30 --crop-margin 16 --output-root personcrop-train/train-result/prepared/pred_pc_person_hardv1_margin16 --person-weights person-train-model/train-result/export/person_detect_yolov8_with_new_labels_and_hard_examples_v1.pt --device 0
```

---

#### **优化方向B.2：升级 clothes 模型**

**尝试 yolov8s**（更大容量）：

```bash
# 优化方向B.2：升级 clothes 模型（yolov8s）
python backend-train-model/train_workwear.py train --mode personcrop --project-config personcrop-train/personcrop_project_config.json --run-name pred_pc_clo_hardv1_yolov8s --data personcrop-train/train-result/prepared/pred_pc_person_hardv1/dataset.yaml --model yolov8s.pt --device 0
```

---

#### **优化方向B.3：重新评估路线选择**

**如果优化后 personcrop 仍然不如 fullframe**：
- 考虑回到 fullframe + 数据增强方向
- Personcrop 作为对照保留，不作为主线

---

## 4. 任务时间线

### **第1周（诊断期）**

| 时间 | 任务 | 产出 |
|-----|------|------|
| Day 1 | 实验1：原图级对比 | `original_level_comparison_report.json` |
| Day 2 | 实验2：person瓶颈量化 | `person_bottleneck_report.json` |
| Day 3 | 实验3：理想person上界 | `ideal_person_upper_bound_summary.md` |
| Day 4 | 撰写诊断报告初稿 | `诊断实验总结报告.md` |

### **第2周（优化期）**

| 时间 | 任务 | 依据 |
|-----|------|------|
| Day 5-7 | 执行分支A或分支B | 基于实验2的 bottleneck_ratio |
| Day 8-9 | 验证优化效果 | 重新评估原图级指标 |
| Day 10 | 对比实验与结论固化 | 生成最终技术报告 |

### **第3周（文档期，可选）**

| 时间 | 任务 |
|-----|------|
| Day 11-12 | 撰写技术报告 |
| Day 13-14 | 准备汇报材料 |

---

## 5. 关键决策点

### **决策点1（Day 3）**：Person 是否是瓶颈？

**判断依据**：实验2的 `bottleneck_ratio`

- **是**（>15%）→ 进入**分支A**（优化person）
- **否**（<5%）→ 进入**分支B**（优化clothes或裁剪）
- **中间**（5-15%）→ 先尝试调整 person_conf，再决定

---

### **决策点2（Day 9）**：Personcrop 是否优于 Fullframe？

**判断依据**：优化后的原图级对比实验

- **是**（mAP50-95 ≥ 0.80）→ 固化 personcrop 为主线
- **否**（mAP50-95 < 0.78）→ 回到 fullframe 方向

---

## 6. 严谨性要求

### 6.1 实验设计原则

1. **统一评估空间**：所有对比必须在原图级完成
2. **量化瓶颈分析**：不能凭"感觉"，必须有具体百分比
3. **上界实验验证**：通过理想 person 确认优化天花板
4. **独立变量控制**：每次只改一个变量（如只调 person_conf）

### 6.2 结论固化条件

**只有满足以下条件，才能固化 personcrop 为主线**：

1. ✅ 完成三个诊断实验
2. ✅ Personcrop 原图级 mAP50-95 **≥ 0.80**
3. ✅ 在至少 20-30 个代表帧上验证优势
4. ✅ 明确记录优化方向和触发条件

---

## 7. 预期产出物

### 7.1 实验产出

- `original_level_comparison_report.json`
- `person_bottleneck_report.json`
- `ideal_person_upper_bound_summary.md`
- `诊断实验总结报告.md`

### 7.2 代码产出

- `evaluate_personcrop_on_original.py`
- `analyze_person_bottleneck.py`
- `prepare_personcrop_with_gt_person.py`

### 7.3 文档产出

- 诊断实验设计与结果（本文档）
- 瓶颈分析报告
- 优化方向选择依据
- 最终性能对比报告

---

## 8. 注意事项

### 8.1 避免过早优化

❌ **错误做法**：在完成诊断前就开始调参、换模型、补标注

✅ **正确做法**：先明确瓶颈，再针对性优化

### 8.2 避免指标误导

❌ **错误做法**：只看 crop 级 mAP50-95，就认为 personcrop 更好

✅ **正确做法**：必须在原图级统一评估空间对比

### 8.3 避免盲目附和

❌ **错误做法**：用户说"person 够用了"，AI 就默认同意

✅ **正确做法**：基于实验数据独立判断，必要时纠正用户

---

## 9. 后续规划

### 9.1 短期（1-2周）

- 完成三个诊断实验
- 明确优化方向
- 执行针对性优化

### 9.2 中期（3-4周）

- 固化最优路线为 baseline
- 撰写技术报告
- 准备阶段汇报

### 9.3 长期（可选）

- ROI-aware personcrop 探索
- 实时推理优化
- 模型部署与上线

---

## 10. 参考文档

- `backend-train-model/personcrop-train/train-docs/双上游personcrop执行方案.md`
- `backend-train-model/personcrop-train/train-docs/personcrop下一步推进计划.md`
- `backend-train-model/personcrop-train/train-docs/personcrop代表帧人工复盘模板.md`
- `backend-train-model/personcrop-train/train-result/review/review-docs/personcrop首轮代表帧正式人工复盘记录.md`

# ROI-aware person 数据集方案

本文档用于约束后续 `person` 数据集从“全图所有人检测”向“面向业务 ROI 的候选人检测”演进的方式。

当前结论先写在前面：

- 当前 `fullframe + 全图所有人标注` 的 `person` 数据集仍应保留，作为**母数据集**。
- 如果后续真实业务只关心 ROI 内候选人，那么不建议继续只用这套母数据集直接训练业务版 `person`。
- 但也**不能**在完整原图里看到 ROI 外的人却故意不标，因为这会把可见的人错误地当成背景。
- 更合理的做法是：**先做 ROI 约束，再生成派生训练集，再训练 ROI-aware person 模型**。

---

## 1. 背景

当前项目的真实业务链路不是“单模型直接输出未穿工服告警”，而是：

1. `person` 检测；
2. ROI / 区域规则筛选；
3. `personcrop` 或候选人区域裁剪；
4. `clothes / workwear` 检测；
5. 时序与告警逻辑。

因此，`person` 模型的职责不一定是“把画面中所有人都尽可能检测完整”，而更接近：

- 在业务关心的区域内，尽量稳定地召回候选人；
- 减少与业务无关的小远人、边缘路人、ROI 外背景行人对训练目标的干扰。

当前 `person_fullframe_baseline` 已经说明：

- val 指标尚可；
- test 的 `Recall` 与 `mAP50-95` 下降明显；
- 说明现阶段更像是“业务相关难例泛化不足”，而不是简单阈值问题。

所以，下一阶段更适合引入 **ROI-aware person 数据集**，而不是在原图上继续扩大“全图通用行人检测”的学习目标。

---

## 2. 方案目标

ROI-aware person 数据集的目标不是替代当前母数据集，而是新增一条更贴合业务的训练分支。

预期达到的效果：

- 把模型注意力集中到业务有效区域；
- 降低 ROI 外远处小人、边缘行人对训练的干扰；
- 提升 ROI 内人员的 `Recall`、`mAP50` 和 `mAP50-95`；
- 为后续 `personcrop -> clothes` 对照实验提供更合理的上游 `person` 检测器。

---

## 3. 核心原则

### 3.1 保留母标注，不直接推翻当前标法

当前“图中出现的人都标出来”的做法是合理的，应该保留为母数据集，因为它完整记录了原始画面的真实情况。

建议长期同时保留两类数据资产：

- `fullframe-all-person`：母数据集，完整原图 + 全图所有人标注；
- `roi-aware-person`：派生数据集，面向业务 ROI 重新生成。

### 3.2 不要在完整原图里做“局部漏标”

不推荐的做法：

- 原图里 ROI 外的人仍然清晰可见；
- 但标注时只框 ROI 内的人；
- 其余 ROI 外的人故意不标。

这样会导致模型把“看得见但没标注的人”当成背景，污染训练信号。

### 3.3 让“不想学的人”先离开有效训练画面

对于 ROI 外的人，不是简单不标，而是要通过以下任一方式让其不再成为有效训练目标：

1. **优先方案：先按 ROI 做遮罩，再裁到 ROI 最小外接矩形；**
2. 备选方案：直接裁出 ROI 对应矩形区域；
3. 不推荐方案：保留完整原图但局部漏标。

---

## 4. 推荐默认方案

推荐采用：

**多边形 ROI 遮罩 + 最小外接矩形裁剪 + ROI 内人框保留**

对应逻辑如下：

1. 每个序列或摄像头先定义自己的 ROI 多边形；
2. 对原图执行：
   - ROI 外区域置黑或置为统一遮罩色；
   - 再裁成 ROI 多边形的最小外接矩形；
3. 对人框执行：
   - 只保留 ROI 内有效 person 框；
   - 对超出裁剪窗口的框做裁剪重映射；
   - 丢弃 ROI 外目标；
4. 生成新的 `images/` 与 `labels/`，用于单独训练。

这个方案相对平衡了几个目标：

- ROI 外的人不会再作为“可见但未标注目标”污染训练；
- 输入分辨率会更多落在业务区域，有利于提升 ROI 内小目标有效像素占比；
- 后续仍可与当前 `fullframe` 数据分支做公平对照。

---

## 5. 标注与样本保留规则

### 5.1 母数据集规则

母数据集继续保持当前规则：

- 只要图中出现可见的人，就标出来；
- 不因为其是否位于 ROI 内而改变原始标注。

### 5.2 ROI-aware 派生数据集规则

建议默认采用以下保留规则：

#### 正样本保留

一个 person 框满足以下条件时保留为 ROI-aware 正样本：

1. 目标框底边中心点落在 ROI 多边形内；
2. 或目标框与 ROI 的 `box IoA >= 0.25`；
3. 经过裁剪重映射后，目标框仍然有效。

#### 边界目标处理

对于贴近 ROI 边界的人，建议采用 v2 的“软边界保留”策略：

- 若目标框底边中心点在 ROI 内，则直接保留；
- 若底边中心点不在 ROI 内，但 `box IoA >= 0.25`，也保留；
- 否则丢弃。

这样既保留 ROI 地面语义，又能补偿边界样本召回。

#### 负样本保留

若 ROI 画面内没有任何 person：

- 该图仍应保留为空标注负样本；
- 但前提是人工确认或自动审计后，确实不存在漏标 person。

### 5.3 当前阶段不建议直接做的事情

- 不建议在原图里让 ROI 外的人继续清晰可见但不标；
- 不建议一上来就删除所有小人框；
- 不建议把“业务暂时不关心”直接等同于“训练时当背景”。

---

## 6. 建议的数据准备流程

建议在现有 `person` 数据准备链路旁边，新增一条独立的 ROI-aware prepare 流程。

建议输出目录与命名如下：

- `backend-train-model/person-train-model/train-result/prepared/person_roi_aware/sequence_contiguous/`
- `backend-train-model/person-train-model/train-result/prepared/person_roi_aware/sequence_holdout/`

建议执行流程：

1. 读取当前母数据集图片与全量 person 标签；
2. 读取每个序列对应的 ROI 配置；
3. 对原图先做 ROI 外区域遮罩；
4. 再裁成 ROI 最小外接矩形；
5. 对框坐标做重映射；
6. 过滤掉 ROI 外目标；
7. 输出新的 `dataset.yaml`、`images/`、`labels/`；
8. 生成一份 prepare 报告，记录：
   - 输入图片数；
   - 输出图片数；
   - 保留目标数；
   - 丢弃目标数；
   - 空标注数；
   - 边界裁剪目标数；
   - 每个序列的统计信息。

---

## 7. 建议的 ROI 配置方式

实现阶段不应把 ROI 写死在脚本里。

建议在 `backend-train-model/person-train-model/person_project_config.json` 中新增独立配置段，例如：

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
    "per_sequence": {
      "D04_20260123074846": {
        "polygon": [[100, 120], [1100, 120], [1180, 680], [80, 680]]
      }
    }
  }
}
```

说明：

- `polygon` 使用原图坐标；
- 若不同序列来自同一固定机位，也可以后续抽象为“按摄像头模板复用”；
- 当前阶段先支持固定多边形即可，不必一开始就做动态 ROI。

---

## 8. 训练与评估建议

ROI-aware 数据集不应替代当前 fullframe baseline，而应作为**平行对照实验**。

建议至少保留以下实验矩阵：

1. `fullframe-all-person` 当前基线；
2. `roi-aware-person` 同模型、同训练轮数、同 split 的公平对照；
3. `roi-aware-person + 更高 imgsz` 对照；
4. 必要时再加入 `sequence_holdout` 严格评估。

建议重点看以下指标：

- `Recall`
- `mAP50`
- `mAP50-95`
- ROI 内小目标召回率
- 困难序列召回率
- 空 ROI 负样本上的误报数量

建议比较口径：

- 不只看全 test 平均值；
- 还要单独看困难序列；
- 还要单独看“ROI 内业务候选人”的效果。

---

## 9. 风险与边界

### 9.1 ROI 画错会直接误导训练

如果 ROI 定义过紧：

- 业务上真正需要的人可能会被系统性排除；
- 模型会学成“只会检 ROI 里最中间那部分人”。

因此 ROI 配置应先经过业务确认，再进入正式训练。

### 9.2 ROI-aware 模型的泛化范围会变窄

ROI-aware 模型更贴业务，但也更依赖当前机位和当前区域定义。

因此不应删除 fullframe 母数据集与 fullframe baseline。

### 9.3 边界人框要特别小心

ROI 边缘的人最容易出现：

- 框被截断；
- 留框规则前后不一致；
- 训练和评估口径不统一。

建议第一版先使用简单规则，避免过度复杂的边界逻辑。

---

## 10. 推荐落地顺序

建议按以下顺序推进：

1. 保留当前 `fullframe-all-person` 母数据集不动；
2. 为每个序列补齐 ROI 多边形配置；
3. 新增 ROI-aware prepare 流程；
4. 先生成一版 `person_roi_aware/sequence_contiguous` 数据集；
5. 训练 ROI-aware person baseline；
6. 与当前 `person_fullframe_baseline` 做公平评估对照；
7. 如果 ROI-aware person 明显改善，再进入 `personcrop -> clothes` 对照链路。

---

## 11. 当前代码落地状态

截至 `2026-04-24`，当前仓库已将 ROI-aware person 从第一版最小链路升级到 keep rule v2：

- `person_project_config.json` 中新增 `roi.keep_rule.bottom_center_inside` 与 `roi.keep_rule.min_box_ioa`，当前默认使用 `mask_then_crop + (bottom_center_inside OR box_ioa >= 0.25)`；
- `labelme_roi_to_config.py` 负责把 Labelme `roi` polygon 提取为统一 ROI 配置；
- `prepare_roi_aware_person_dataset.py` 负责生成遮罩、裁剪、坐标重映射后的 ROI-aware YOLO 数据集；
- `run_person_flow.py` 新增 `extract-roi-config` 与 `prepare-roi-aware` 两个入口；
- 默认 ROI 配置输出为 `train-result/working/roi/roi_config.generated.json`，不把每条序列的 polygon 直接写死在脚本里；
- 默认 ROI-aware 数据集输出为 `train-result/prepared/person_roi_aware/sequence_contiguous/`。

当前第一版仍刻意保持简单，但已支持两种 ROI 配置粒度：

- 优先支持每张图片一个 ROI polygon，即 `per_image`；
- 兼容每个序列一个 canonical ROI polygon，即 `per_sequence` fallback；
- 只支持单 polygon，不支持多块不连通 ROI 合并；
- 只支持按框中心点是否落在 ROI 内决定保留或丢弃；
- 不直接修改 fullframe 母数据集，也不自动替换现有 person baseline。

当前真实数据已采用逐图 ROI JSON：

- ROI JSON 来源：`D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\roi-json\...\roi-json`
- 已生成逐图 ROI 配置：`train-result/working/roi/roi_config.generated.json`
- 已生成 ROI-aware 数据集：`train-result/prepared/person_roi_aware/sequence_contiguous/`

---

## 12. 当前明确不做的事情

- 不直接废弃当前全图 person 标注；
- 不在完整原图上通过“故意漏标 ROI 外的人”来构造数据集；
- 不把 ROI-aware 数据集直接写成线上最终方案；
- 不在尚未完成 ROI-aware 对照前，就断言 fullframe person 无价值。

---

## 13. 一句话结论

当前 person 标注“图中有人就标”本身没有错，问题不在标注过多，而在于：

**业务只关心 ROI 内候选人时，训练阶段也应该先把有效区域收紧，再让模型学习。**

因此下一步推荐不是“少标一些人”，而是：

**保留母标注，新增 ROI-aware 派生数据集。**


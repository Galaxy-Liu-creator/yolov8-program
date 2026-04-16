# [归档] `All-train-model` 精度提升 TODO 清单

> 归档说明（2026-04-15）：
> - 本文是 merged 早期阶段的专项 TODO，主要服务于 `merged_v1 / merged_v2` 提升分析。
> - 当前项目级 TODO 已切换到 `backend-train-model/docs/todo_list.md`，请优先使用后者。
> - 本文仅保留为历史归档，不再作为当前执行清单。

本文档基于以下审查结论整理：

- `backend-train-model/docs/all_vs_first_train_review_2026-04-06.md`

目标不是泛泛而谈“继续优化”，而是把当前 `All-train-model` 下一步最值得做、最可能带来精度提升的动作拆成可执行清单。

---

## 1. 先给结论

当前 `All-train-model` 想要提升准确性，优先级最高的不是：

- 继续把 `epochs` 拉高
- 关闭 EarlyStopping
- 反复重训当前 `merged_v1`

而是下面三件事：

1. **补齐缺标，先做 `merged_v2_full_reviewed`**
2. **重做更合理的 `train / val / test` split**
3. **用 `first-train` 的 `best.pt` 作为 merged 训练初始化权重继续 fine-tune**

原因很明确：

- 当前 `merged_v1` 仍有 `48` 张缺标样本被直接跳过
- 当前 `val / test` 分布不均，导致 merged 结果不稳定
- 当前 merged 训练并没有利用已有更稳的 `first-train` 基线权重

---

## 2. 当前问题摘要

基于当前仓库内已有结果，`All-train-model` 的主要问题可以概括为四点。

### 2.1 数据仍不完整

当前 `merged_v1_positive_only` 的统计是：

- 源图片：`502`
- 实际纳入：`454`
- 缺失源标注：`48`

其中缺标主要集中在：

- `g32 / D15_20260119203927`：`26`
- `g33 / D02_20260123070624`：`21`
- `g33 / D02_20260123074836`：`1`

这意味着当前 merged 训练集不是“完整 merged 数据集”，而只是“跳过缺标后的正样本版本”。

### 2.2 `val / test` split 代表性不足

当前 `merged_v1` 的 split 近似表现为：

- `val` 主要来自 `g33 / D02_20260123070624`
- `test` 主要来自 `g31 / D04_20260123074846` 与 `g31 / D15_20260123074848`

这会带来两个问题：

- `val` 和 `test` 的难度、风格、来源不一致
- 你看到的“`val` 很差、`test` 还行”不一定说明模型真实泛化更强，可能只是 split 本身不均衡

### 2.3 当前 merged 训练没有站在更强基线上继续训

现在 `All-train-model` 和 `first-train` 都还是基于：

- `yolov8n.pt`

但当前审查结论已经明确：

- `first-train` 仍然是更稳的 baseline

所以更合理的下一轮 merged 训练方式，应该是：

- 以 `first-train` 的 `best.pt` 为初始权重继续 fine-tune

### 2.4 后段训练不是当前主要矛盾

当前 merged 训练：

- 最优结果出现在第 `75` 轮
- 第 `115` 轮触发早停
- 后段存在明显退化

所以现在不应把重点放在：

- 继续拉大 `patience`
- 强行跑满 `180` 轮

这不会解决数据与 split 的根因问题。

---

## 3. 总体推进顺序

建议按下面顺序推进，不要跳步：

### `P0` 固定当前基线与对照关系

目标：

- 保留当前 `first-train` 作为稳定 baseline
- 保留当前 `All-train-model merged_v1` 作为对照组

完成标准：

- 确认两边 `best.pt` 路径可用
- 训练报告、评估报告、导出报告都能追溯

### `P1` 先把 `merged_v2_full_reviewed` 做出来

目标：

- 先补齐 `48` 张缺标样本
- 让 merged 数据不再依赖 “missing_label_policy=skip”

完成标准：

- `review/merged_clothes_v2_full_reviewed/labels/` 补齐
- 成功生成 `merged_v2_full_reviewed/dataset.yaml`

### `P2` 重做 balanced split

目标：

- 让 `val / test` 不再集中在单一来源或单一序列

完成标准：

- 新 split 中 `val / test` 都覆盖多来源序列
- 不再出现某一 split 主要只来自单个 source 的情况

### `P3` 用 `first-train` 权重启动 merged 再训练

目标：

- 不是重新从 `yolov8n.pt` 起步
- 而是站在当前更稳的 `first-train` baseline 上继续学习 merged 数据

完成标准：

- 成功跑出一版 `merged_v2_from_first`
- 指标可与 `merged_v1`、`first-train` 直接比较

### `P4` 最后才考虑模型和参数增强

目标：

- 在数据与 split 已经稳定后，再尝试更高成本优化

完成标准：

- 有明确公共 holdout 或固定验证口径
- 再决定是否上更大模型或更大输入尺寸

---

## 4. 分阶段 TODO

## `P0` 固定对照基线

### 目标

明确后续所有实验都要和以下两套结果对比：

- `first-train/artifacts/runs/clothes_fullframe_baseline/weights/best.pt`
- `All-train-model/artifacts/runs/clothes_merged_v1_fullframe/weights/best.pt`

### TODO

- [ ] 确认 `first-train` 的 `best.pt` 路径固定可用
- [ ] 确认 `All-train-model` 当前 `best.pt` 路径固定可用
- [ ] 统一记录这两份模型的评估报告路径
- [ ] 以后所有 merged 实验都显式写出“相对 `first-train` 的变化”

### 说明

如果对照基线不固定，后续每一版 merged 提升与否都会变得模糊。

---

## `P1` 补齐缺标，做 `merged_v2_full_reviewed`

### 目标

解决当前 `merged_v1_positive_only` 最大的数据缺口：

- `48` 张缺标样本被直接跳过

### 当前重点清单

优先处理：

- [ ] `g32 / D15_20260119203927` 的 `26` 张缺标
- [ ] `g33 / D02_20260123070624` 的 `21` 张缺标
- [ ] `g33 / D02_20260123074836` 的 `1` 张缺标

### 执行要求

- [ ] 打开 `backend-train-model/All-train-model/review/merged_clothes_v1_positive_only/missing_review.csv`
- [ ] 按 `merged_stem` 为文件名补 `.txt`
- [ ] 如果图片确认没有 `clothes`，写空白 `.txt`，不要继续跳过
- [ ] 统一把补标文件放到 `backend-train-model/All-train-model/review/merged_clothes_v2_full_reviewed/labels/`

### 产物

- `backend-train-model/All-train-model/review/merged_clothes_v2_full_reviewed/labels/`

### 构建命令

进入 `backend-train-model/` 后执行：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe build_merged_clothes_dataset.py --config All-train-model\merged_clothes_v2.build.json --overwrite
```

### 完成标准

- [ ] `merged_v2_full_reviewed/dataset.yaml` 成功生成
- [ ] `build_report.json` 中 `require_review_completion=true` 且成功通过
- [ ] 不再依赖 `missing_label_policy=skip`

### 预期收益

- 训练集更完整
- 验证集不再因为缺标跳过而被动扭曲
- `g33` 验证序列的代表性更接近真实数据

---

## `P2` 重新设计 balanced split

### 目标

让 merged 训练结果的 `val / test` 更可信，而不是继续使用当前明显不均衡的 split。

### 问题点

当前 `merged_v1`：

- `val` 基本落在 `g33`
- `test` 基本落在 `g31`

这会让：

- `val` 更像“单域验证”
- `test` 更像“另一域测试”

### TODO

- [ ] 新建一份 balanced 版 build config
- [ ] 让 `val` 至少覆盖 `g31 / g32 / g33` 中的两个来源
- [ ] 让 `test` 至少覆盖 `g31 / g32 / g33` 中的两个来源
- [ ] 避免把某个来源的整套风格全部压到单一 split
- [ ] 重新统计 `split_image_counts` 与 `split_box_counts`

### 推荐原则

- 优先按**序列**切分，不按单张图随机打散
- `val / test` 都要有跨来源代表性
- 如果某条序列过短，不要单独承担整个验证集角色
- 如果做不到三来源同时进入 `val / test`，至少要避免“单一来源独占验证集”

### 建议产物

- `backend-train-model/All-train-model/merged_clothes_v2_balanced.build.json`
- `backend-train-model/All-train-model/datasets/merged_clothes_v2_balanced/`

### 完成标准

- [ ] balanced 版 `dataset.yaml` 生成成功
- [ ] `val / test` 的来源分布明显比当前 `merged_v1` 更均衡
- [ ] 可以把 balanced 版和当前 `merged_v2_full_reviewed` 做同口径对比

### 预期收益

- `val` 指标更有参考价值
- 不再出现“`val` 很差但 `test` 还行”的结构性假象
- 后续模型优劣判断更可靠

---

## `P3` 用 `first-train` 的 `best.pt` 初始化 merged 再训练

### 目标

利用当前更稳的 baseline，而不是每次都从 `yolov8n.pt` 重新起步。

### 核心策略

把：

- `backend-train-model/first-train/artifacts/runs/clothes_fullframe_baseline/weights/best.pt`

作为下一轮 merged 训练的 `--base-model`。

### TODO

- [ ] 固定 `first-train` 的 `best.pt` 路径
- [ ] 用 `merged_v2_full_reviewed` 跑一版 from-first 训练
- [ ] 如果 balanced split 也完成，再跑一版 balanced + from-first
- [ ] 明确记录每次训练的 base model 来源

### 推荐命令

进入 `backend-train-model/` 后执行：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py train --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\merged_clothes_v2_full_reviewed\dataset.yaml --base-model first-train\artifacts\runs\clothes_fullframe_baseline\weights\best.pt --name clothes_merged_v2_from_first
```

如果 balanced 版数据也准备好了，再跑：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py train --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\merged_clothes_v2_balanced\dataset.yaml --base-model first-train\artifacts\runs\clothes_fullframe_baseline\weights\best.pt --name clothes_merged_v2_balanced_from_first
```

### 完成标准

- [ ] 成功产出 `merged_v2_from_first` 的 `best.pt`
- [ ] 评估报告明确记录 `base_model` 来自 `first-train`
- [ ] 指标能和 `merged_v1`、`first-train` 直接对比

### 预期收益

- 更快进入有效收敛区间
- 降低 merged 数据初期训练不稳定的风险
- 更有机会同时保留 baseline 的稳定性和 merged 的覆盖能力

---

## `P4` 数据源一致性复核

### 目标

解决 merged 数据“样本量更大但验证效果没变好”的根因。

### 重点排查对象

- [ ] `g33 / D02_20260123070624`
- [ ] `g32 / D15_20260119203927`

### TODO

- [ ] 抽样检查三套数据的框是否同口径
- [ ] 检查远距离、小目标、遮挡目标的标注标准是否一致
- [ ] 检查 `g33` 的框是否偏松、偏移、漏标更多
- [ ] 检查 `g32` 缺标是不是一部分其实应为正样本
- [ ] 检查空标签是否被一致处理

### 完成标准

- [ ] 明确记录三套数据之间是否存在标注口径差异
- [ ] 如果存在差异，形成一份统一补标/修标规则

### 预期收益

- 解决“更多数据反而不更好”的根因
- 为后续 merged 训练提供更一致的数据基础

---

## `P5` 训练参数与模型增强

### 目标

在数据完整、split 合理、训练策略更稳之后，再做参数层增强。

### 当前不建议优先做的事

- [ ] 不要优先通过增大 `epochs` 来解决问题
- [ ] 不要优先通过关闭 EarlyStopping 来解决问题
- [ ] 不要在当前 `merged_v1` 上盲目反复重训

### 更合理的增强顺序

- [ ] 如果仍是 CPU，先维持 `yolov8n.pt`
- [ ] 如果有稳定 GPU，再考虑试 `yolov8s.pt`
- [ ] 如果 GPU 显存允许，再试更大 `imgsz`，例如 `800`
- [ ] 再视情况微调 `patience`

### 为什么这一步放最后

因为当前主要瓶颈不是“模型容量不够”，而是：

- 数据不完整
- split 不均衡
- 初始化策略没有利用已有更优基线

### 完成标准

- [ ] 只有在 `merged_v2` + balanced split 跑通后，才进入这一步
- [ ] 任何参数调整都要和固定 holdout 或固定 split 结果对比

---

## 5. 推荐实验矩阵

为了避免后续实验混乱，建议按下面矩阵推进。

### 必做

- [ ] `first-train baseline`
- [ ] `merged_v1_positive_only`
- [ ] `merged_v2_full_reviewed`
- [ ] `merged_v2_from_first`

### 建议做

- [ ] `merged_v2_balanced`
- [ ] `merged_v2_balanced_from_first`

### 条件允许再做

- [ ] `merged_v2_balanced_from_first_s`
- [ ] `merged_v2_balanced_from_first_imgsz800`

其中命名约定建议写清：

- 数据版本
- 是否 balanced
- 是否 from-first
- 是否更换模型大小

---

## 6. 每轮实验必须记录的内容

后续每一轮 merged 实验，至少记录：

- [ ] 数据版本
- [ ] split 版本
- [ ] base model 来源
- [ ] `imgsz`
- [ ] `batch`
- [ ] `patience`
- [ ] `best epoch`
- [ ] `val mAP50`
- [ ] `val mAP50-95`
- [ ] `test mAP50`
- [ ] `test mAP50-95`
- [ ] 与 `first-train baseline` 的差异

如果不记录这些，后续比较会重新失真。

---

## 7. 当前最值得先执行的三步

如果只考虑“今天开始先做什么”，按这个顺序执行：

### 第一步

- [ ] 处理 `missing_review.csv`
- [ ] 做出 `merged_v2_full_reviewed`

### 第二步

- [ ] 重做 balanced split
- [ ] 生成一版 balanced merged 数据集

### 第三步

- [ ] 用 `first-train` 的 `best.pt` 作为初始化权重
- [ ] 训练 `merged_v2_from_first`

这三步做完之后，再比较：

- `first-train baseline`
- `merged_v1`
- `merged_v2`
- `merged_v2_from_first`

到那时，`All-train-model` 才真正有资格和 baseline 做一次有效竞争。

---

## 8. 一句话结论

`All-train-model` 现在要想提升准确性，最有效路线不是“继续重训当前版本”，而是：

> **先补齐缺标做 `merged_v2`，再重做更合理的 split，最后用 `first-train` 的稳定 `best.pt` 作为初始化权重继续 fine-tune。**

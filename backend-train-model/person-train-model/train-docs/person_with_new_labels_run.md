# person_with_new_labels 运行方案

## 1. 本文档作用

本文档对应：

- `backend-train-model/person-train-model/train-docs/person_with_new_labels_decision.md`

它不再讨论“该不该先等 ROI”，而是直接给出当前方案下可执行的运行入口。

当前采用的正式方案是：

```text
先继续 person_fullframe_with_new_labels 训练
-> 优先做 640 baseline 的 seed 稳定性确认
-> ROI 补齐作为并行工作流推进
-> ROI 补齐后，再新开 new labels 的 ROI-aware 正式版本
```

这意味着：

1. **当前立即可执行的命令，优先是 fullframe_with_new_labels。**
2. **当前不把旧 502 张 ROI-aware 主线的 seed 命令，作为 new labels 主线的第一优先动作。**
3. **当前不会提供“可直接执行”的 new labels ROI-aware 训练命令**，因为这条线的正式版本化配置与 ROI 数据入口还没有作为仓库当前事实完全落盘；在此之前，硬写死命令容易误跑到旧 ROI-aware 主线。

## 2. 当前执行顺序总览

当前推荐顺序：

1. 检查环境与数据集入口；
2. 如需刷新 new labels fullframe 数据集，先重跑 `prepare-labels / prepare`；
3. 训练 `person_fullframe_with_new_labels_baseline_seed7`；
4. 评估 `person_fullframe_with_new_labels_baseline_seed7`；
5. 训练 `person_fullframe_with_new_labels_baseline_seed13`；
6. 评估 `person_fullframe_with_new_labels_baseline_seed13`；
7. 与已有 `person_fullframe_with_new_labels_baseline`、`person_fullframe_with_new_labels_img768` 做对比；
8. 只有当 640 稳健基线已确认足够稳定后，再决定是否继续给 `img768` 候选补 seed；
9. ROI 补齐并行推进，但当前不把 ROI 作为 fullframe 继续训练的前置阻塞条件。

## 3. 运行前检查

在仓库根目录运行：

```powershell
cd D:\University-Competition\Innovation_Entrepreneurship\MyProgram\yolov8-program
```

检查 Python：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe --version
```

检查基础权重：

```powershell
Test-Path backend-train-model\weights\yolov8n.pt
```

检查 new labels fullframe 数据集 YAML：

```powershell
Test-Path backend-train-model\person-train-model\train-result\prepared\person_fullframe_with_new_labels\sequence_contiguous\dataset.yaml
```

检查当前 fullframe 配置仍保持 `roi.enabled=false`：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe -c "import json, pathlib; p=pathlib.Path(r'backend-train-model/person-train-model/person_project_config.fullframe_with_new_labels.json'); print(json.loads(p.read_text(encoding='utf-8'))['roi']['enabled'])"
```

期望输出：

```text
False
```

## 4. 如需重生成 fullframe_with_new_labels 数据集

如果你已经改了标签接入、空白标签补齐或 split 相关配置，可以先刷新数据集；如果当前数据集入口没有变化，这一步可以跳过。

### 4.1 重跑聚合标签

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py prepare-labels --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --overwrite
```

### 4.2 重跑 fullframe prepared 数据集

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py prepare --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --overwrite
```

## 5. 第一优先：640 稳健基线 seed 稳定性确认

这一阶段只围绕：

- `person_fullframe_with_new_labels_baseline`

做稳定性确认，不改 ROI 规则，不改任务语义，不改模型尺寸。

### 5.1 Seed 7 训练

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe_with_new_labels\sequence_contiguous\dataset.yaml --run-name person_fullframe_with_new_labels_baseline_seed7 --device 0 --workers 4 --batch 4 --imgsz 640 --epochs 180 --patience 40 --seed 7 --base-model backend-train-model\weights\yolov8n.pt
```

### 5.2 Seed 7 评估

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe_with_new_labels\sequence_contiguous\dataset.yaml --run-name person_fullframe_with_new_labels_baseline_seed7 --report-name person_fullframe_with_new_labels_baseline_seed7_eval --imgsz 640 --batch 4 --workers 4 --device 0
```

### 5.3 Seed 13 训练

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe_with_new_labels\sequence_contiguous\dataset.yaml --run-name person_fullframe_with_new_labels_baseline_seed13 --device 0 --workers 4 --batch 4 --imgsz 640 --epochs 180 --patience 40 --seed 13 --base-model backend-train-model\weights\yolov8n.pt
```

### 5.4 Seed 13 评估

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe_with_new_labels\sequence_contiguous\dataset.yaml --run-name person_fullframe_with_new_labels_baseline_seed13 --report-name person_fullframe_with_new_labels_baseline_seed13_eval --imgsz 640 --batch 4 --workers 4 --device 0
```

## 6. 跑完 640 seed 之后怎么判断

至少把下面 4 组结果放在一起看：

- `person_fullframe_with_new_labels_baseline`
- `person_fullframe_with_new_labels_baseline_seed7`
- `person_fullframe_with_new_labels_baseline_seed13`
- `person_fullframe_with_new_labels_img768`（已有候选）

优先观察：

1. Precision
2. Recall
3. mAP50
4. mAP50-95
5. hardest FN 是否仍集中在 crowded / overlap / visibility weak

推荐判断口径：

- 如果 `baseline / seed7 / seed13` 三组都大体稳定，说明 640 稳健基线成立；
- 如果 640 三组之间波动很大，就先不要急着把 768 升级为主线；
- 如果 640 很稳，而 768 只是单次 `mAP50-95` 更高，则 768 继续只保留为候选；
- 只有当 768 在后续补种子后也稳定更优，才值得讨论升级默认主线。

## 7. 第二优先：是否继续补 768 候选的 seed

这一阶段是**条件动作**，不是当前默认必跑项。

只有当你已经确认：

- 640 稳健基线结论足够稳定；
- 仍然希望验证 768 是否值得升级；

才建议继续跑下面这些命令。

### 7.1 `img768` Seed 7 训练

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe_with_new_labels\sequence_contiguous\dataset.yaml --run-name person_fullframe_with_new_labels_img768_seed7 --device 0 --workers 4 --batch 4 --imgsz 768 --epochs 180 --patience 40 --seed 7 --base-model backend-train-model\weights\yolov8n.pt
```

### 7.2 `img768` Seed 7 评估

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe_with_new_labels\sequence_contiguous\dataset.yaml --run-name person_fullframe_with_new_labels_img768_seed7 --report-name person_fullframe_with_new_labels_img768_seed7_eval --imgsz 768 --batch 4 --workers 4 --device 0
```

### 7.3 `img768` Seed 13 训练

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe_with_new_labels\sequence_contiguous\dataset.yaml --run-name person_fullframe_with_new_labels_img768_seed13 --device 0 --workers 4 --batch 4 --imgsz 768 --epochs 180 --patience 40 --seed 13 --base-model backend-train-model\weights\yolov8n.pt
```

### 7.4 `img768` Seed 13 评估

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe_with_new_labels\sequence_contiguous\dataset.yaml --run-name person_fullframe_with_new_labels_img768_seed13 --report-name person_fullframe_with_new_labels_img768_seed13_eval --imgsz 768 --batch 4 --workers 4 --device 0
```

### 7.5 如果 768 在训练机上显存吃紧

可回退到 `batch=2`，并使用独立 run 名，避免和标准 `img768` 对照混淆，例如：

- `person_fullframe_with_new_labels_img768_batch2_seed7`
- `person_fullframe_with_new_labels_img768_batch2_seed13`

回退时要保持：

- 在汇总结论里明确这是“稳定性回退版本”；
- 不要和 `batch=4` 的正式 `img768` 对照结果混写成一条线。

## 8. ROI 并行准备：当前做什么，不做什么

## 8.1 当前可以并行推进的工作

当前可以和 fullframe 训练并行推进：

1. 为 `new_person_labels` 补齐 ROI JSON / ROI 标注；
2. 核对新旧 ROI 语义是否一致；
3. 检查是否有新的机位 / 新场景需要单独留显式 holdout；
4. 为后续 new labels ROI-aware 正式配置准备版本化入口。

## 8.2 当前明确不直接执行的动作

当前**不建议直接执行**下面这些旧 ROI-aware 命令，作为 new labels person 主线的下一步：

- `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed7`
- `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed13`

原因不是这些命令“错了”，而是：

- 它们服务的是旧 502 张 ROI-aware 主线；
- 不能直接回答 new labels 主线下一步该怎么训。

## 9. ROI 补齐后，如何进入 new labels ROI-aware

当前阶段的正确做法不是直接伪造一个“现成可执行”的 new labels ROI-aware 命令，而是先满足下面 3 个条件：

1. `person_fullframe_with_new_labels` 已经确认出稳定默认基线；
2. `new_person_labels` 的 ROI 已经补齐到可单独 prepare 数据集；
3. 已经准备好独立版本化配置，而不是直接覆盖当前 fullframe 配置。

## 9.1 进入 ROI-aware 前的推荐准备

建议你到那时至少新增：

- 一个独立的 new labels ROI-aware project config；
- 一个独立的 ROI config 输出路径；
- 一个独立的 prepared 输出目录；
- 一个明确的 base-model 入口，优先指向稳定的 `person_fullframe_with_new_labels` best 权重。

## 9.2 到那时建议遵守的约束

一旦开始做 new labels ROI-aware，建议保持下面这些原则：

- 不直接复用旧 502 张 ROI-aware 的 run 名；
- 不直接沿用旧 `person_fullframe_baseline` 作为初始化来源；
- 先把 fullframe new labels 稳定 best 权重作为 ROI-aware 初始化来源；
- 第一个 ROI-aware new labels 实验仍应保持单因子，不要一口气同时改 `imgsz / keep_rule / model size`。

## 10. 最终执行口径

当前这份 runbook 对应的正式执行口径是：

1. **现在就继续 `person_fullframe_with_new_labels` 训练；**
2. **当前第一优先先跑 640 baseline 的 `seed7 / seed13`；**
3. **`img768` 只在 640 稳定后，作为条件对照继续补 seed；**
4. **ROI 补齐作为并行工作流推进，而不是继续训练的阻塞条件；**
5. **ROI 补齐并形成独立配置后，再新开 new labels 的 ROI-aware 正式版本。**


# first-train 与 All-train-model 统一 holdout 全流程命令

> 状态更新（2026-04-15）：
> - 本文中的数据集构建、strict holdout、strict eval、route verification 已经完整执行过至少一轮。
> - 当前选中的 clothes fullframe baseline 为 `clothes_merged_v2_balanced_from_first_holdout_v1`。
> - 本文继续保留为“统一 holdout 重跑手册”；如果后续要复现实验，仍按本文命令执行。

本文档记录当前推荐的统一 holdout 对比流程，目标是让 `first-train` 与 `All-train-model` 在同一个 `unified_holdout_v1` 上得到可比较的结果。

## 0. 执行前提

- 当前命令默认在仓库根目录下的 `backend-train-model/` 中执行。
- Python 解释器固定使用：`D:\Miniconda3_python\envs\yolo_code\python.exe`
- 本流程分为三层：
  - `cross-eval`：复评已有历史权重，统一评估口径，但不保证历史权重没见过 holdout。
  - `strict holdout / fair compare`：重新训练后再评估，且两边使用相同初始化，作为当前最严格的主对照。
  - `route verification`：验证“先得到 g31 基线，再并入 merged 数据继续训练”这条业务路线是否成立。
- 训练参数显式固定为：
  - `imgsz = 640`
  - `epochs = 180`
  - `batch = 4`
  - `patience = 40`
  - `workers = 0`
  - `device = cpu`
  - `seed = 42`
- 2026-04-11 起，`train_workwear.py` 已禁用长参数缩写；`--project` 不会再被误判为 `--project-config`，下面命令可以直接照抄执行。

```powershell
Set-Location D:\University-Competition\Innovation_Entrepreneurship\MyProgram\yolov8-program\backend-train-model
```

## 1. 构建三套统一对比数据集

### 1.1 构建 balanced merged 训练集

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe build_merged_clothes_dataset.py --config All-train-model\merged_clothes_v2_balanced.build.json --overwrite
```

预期输出：

- `All-train-model\datasets\merged_clothes_v2_balanced\dataset.yaml`
- `All-train-model\datasets\merged_clothes_v2_balanced\manifest.csv`
- `All-train-model\datasets\merged_clothes_v2_balanced\build_report.json`

### 1.2 构建 unified holdout 评估集

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe build_merged_clothes_dataset.py --config All-train-model\unified_holdout_v1.build.json --overwrite
```

预期输出：

- `All-train-model\datasets\unified_holdout_v1\dataset.yaml`
- `All-train-model\datasets\unified_holdout_v1\manifest.csv`
- `All-train-model\datasets\unified_holdout_v1\build_report.json`

### 1.3 构建 first-train 对照训练集

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe build_merged_clothes_dataset.py --config All-train-model\first_train_holdout_v1.build.json --overwrite
```

预期输出：

- `All-train-model\datasets\first_train_holdout_v1\dataset.yaml`
- `All-train-model\datasets\first_train_holdout_v1\manifest.csv`
- `All-train-model\datasets\first_train_holdout_v1\build_report.json`

## 2. 第一阶段：cross-eval 复评已有历史权重

这一步用于先统一评估口径，不作为严格 holdout 结论。

### 2.1 复评现有 first-train 历史权重

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py evaluate --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\unified_holdout_v1\dataset.yaml --weights first-train\artifacts\runs\clothes_fullframe_baseline\weights\best.pt --imgsz 640 --batch 4 --workers 0 --device cpu --report-name first_train_on_unified_holdout_v1_cross_eval
```

报告输出：

- `All-train-model\artifacts\reports\first_train_on_unified_holdout_v1_cross_eval.json`

### 2.2 复评现有 merged_v2_from_first 历史权重

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py evaluate --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\unified_holdout_v1\dataset.yaml --weights All-train-model\artifacts\runs\clothes_merged_v2_from_first\weights\best.pt --imgsz 640 --batch 4 --workers 0 --device cpu --report-name merged_v2_from_first_on_unified_holdout_v1_cross_eval
```

报告输出：

- `All-train-model\artifacts\reports\merged_v2_from_first_on_unified_holdout_v1_cross_eval.json`

说明：

- 这两条命令使用的是历史产物，主要用来对齐“现有模型在统一 holdout 上到底差多少”。
- 这一步可以保留 `first-train\artifacts\runs\clothes_fullframe_baseline\weights\best.pt`，因为这里做的是历史复评，不是新的严格主对照。

## 3. 第二阶段：strict holdout / fair compare 主对照

这一步才是当前最严格、最推荐优先看的主实验。

设计原则：

- `first-train` 与 `merged_v2_balanced` 都从同一个初始权重起跑；
- 当前统一使用 `weights\yolov8n.pt`；
- 这样可以尽量把差异收敛到“数据集本身”与“统一 holdout 口径”上，而不是混入历史初始化差异。

### 3.1 重训 first-train 对照模型

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py train --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\first_train_holdout_v1\dataset.yaml --base-model weights\yolov8n.pt --project All-train-model\artifacts\runs --name clothes_first_train_holdout_v1 --imgsz 640 --epochs 180 --batch 4 --patience 40 --workers 0 --device cpu --seed 42
```

预期权重：

- `All-train-model\artifacts\runs\clothes_first_train_holdout_v1\weights\best.pt`

### 3.2 重训 balanced merged 公平对照模型

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py train --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\merged_clothes_v2_balanced\dataset.yaml --base-model weights\yolov8n.pt --project All-train-model\artifacts\runs --name clothes_merged_v2_balanced_holdout_v1 --imgsz 640 --epochs 180 --batch 4 --patience 40 --workers 0 --device cpu --seed 42
```

预期权重：

- `All-train-model\artifacts\runs\clothes_merged_v2_balanced_holdout_v1\weights\best.pt`

说明：

- 这两条 strict holdout 主对照命令可以并行跑，因为它们：
  - 输入数据不同；
  - 输出目录不同；
  - 初始化权重都读取固定的 `weights\yolov8n.pt`。
- 不再推荐把历史的 `first-train\artifacts\runs\clothes_fullframe_baseline\weights\best.pt` 作为这一步的 merged 初始化，因为那会把“历史基线训练痕迹”混进当前主对照。

## 4. 第三阶段：strict eval 最终评估

### 4.1 评估 first-train 公平对照模型

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py evaluate --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\unified_holdout_v1\dataset.yaml --weights All-train-model\artifacts\runs\clothes_first_train_holdout_v1\weights\best.pt --imgsz 640 --batch 4 --workers 0 --device cpu --report-name first_train_holdout_v1_strict_eval
```

报告输出：

- `All-train-model\artifacts\reports\first_train_holdout_v1_strict_eval.json`

### 4.2 评估 balanced merged 公平对照模型

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py evaluate --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\unified_holdout_v1\dataset.yaml --weights All-train-model\artifacts\runs\clothes_merged_v2_balanced_holdout_v1\weights\best.pt --imgsz 640 --batch 4 --workers 0 --device cpu --report-name merged_v2_balanced_holdout_v1_strict_eval
```

报告输出：

- `All-train-model\artifacts\reports\merged_v2_balanced_holdout_v1_strict_eval.json`

## 5. 第四阶段：route verification 业务路线验证

这一步不再回答“哪条数据路线本身更好”，而是回答：

- 如果先得到一个干净的 `g31` 基线；
- 再用这次 strict holdout 里新训练出来的 `first-train` 权重去 warm-start merged；
- 这条接近真实业务推进顺序的路线是否值得保留。

### 5.1 用本轮 first-train strict holdout 权重 warm-start merged

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py train --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\merged_clothes_v2_balanced\dataset.yaml --base-model All-train-model\artifacts\runs\clothes_first_train_holdout_v1\weights\best.pt --project All-train-model\artifacts\runs --name clothes_merged_v2_balanced_from_first_holdout_v1 --imgsz 640 --epochs 180 --batch 4 --patience 40 --workers 0 --device cpu --seed 42
```

预期权重：

- `All-train-model\artifacts\runs\clothes_merged_v2_balanced_from_first_holdout_v1\weights\best.pt`

### 5.2 评估 warm-start merged 路线

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py evaluate --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\unified_holdout_v1\dataset.yaml --weights All-train-model\artifacts\runs\clothes_merged_v2_balanced_from_first_holdout_v1\weights\best.pt --imgsz 640 --batch 4 --workers 0 --device cpu --report-name merged_v2_balanced_from_first_holdout_v1_route_eval
```

报告输出：

- `All-train-model\artifacts\reports\merged_v2_balanced_from_first_holdout_v1_route_eval.json`

说明：

- 这一步必须等 `clothes_first_train_holdout_v1` 训练完成后再跑，不能和它并行。
- 这里读取的是本轮新生成的 `All-train-model\artifacts\runs\clothes_first_train_holdout_v1\weights\best.pt`，而不是历史 `first-train\artifacts\runs\clothes_fullframe_baseline\weights\best.pt`。

## 6. 结果判断顺序

建议按以下顺序看结果：

1. 先看 `cross-eval`
   - 确认现有 `first-train` 与现有 `merged_v2_from_first` 在统一 holdout 上的真实差距。
2. 再看 `strict holdout / fair compare`
   - 比较 `clothes_first_train_holdout_v1`
   - 与 `clothes_merged_v2_balanced_holdout_v1`
   - 这是当前最应该依赖的主结论。
3. 最后看 `route verification`
   - 比较 `clothes_merged_v2_balanced_from_first_holdout_v1`
   - 判断“先 first-train 再 merged”这条业务路线有没有额外收益。
4. 如果 balanced merged 仍未明显改善
   - 优先复核 `48` 张 review 空标签；
   - 再复核 `g32 / g33` 标注一致性；
   - 最后再考虑调参。

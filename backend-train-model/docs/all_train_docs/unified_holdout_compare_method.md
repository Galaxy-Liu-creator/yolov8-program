# [归档] unified holdout 与 balanced merged 的使用说明

> 归档说明（2026-04-15）：
> - 本文是 unified holdout 方案刚落地时的说明文档。
> - 当前项目已经将正式复现实验入口统一到 `backend-train-model/docs/total-run-method.md`。
> - 若只是要按当前口径重跑，请直接看 `total-run-method.md`；本文仅保留为历史背景说明。

这份说明文档回答三个问题：

1. 现在仓库里新增了哪些文件，可以直接用于 `merged_v2` 短期提效；
2. 怎样让 `first-train`、现有 merged 历史权重以及下一轮 balanced merged 在统一口径下比较；
3. 严格主对照和“先 first 再 merged”的业务路线验证，应该怎样拆开看。

## 1. 本轮新增的核心文件

- `backend-train-model/generate_split_manifests.py`
  - 从 canonical manifest 生成：
    - `trainval_balanced_v1.split.csv`
    - `unified_holdout_v1.split.csv`
- `backend-train-model/All-train-model/splits/trainval_balanced_v1.split.csv`
  - source-balanced 的 `train / val / skip` 分配表
- `backend-train-model/All-train-model/splits/unified_holdout_v1.split.csv`
  - 统一 holdout 的 `test / skip` 分配表
- `backend-train-model/All-train-model/splits/source_balanced_v1_summary.json`
  - 当前这版 split 的分布摘要
- `backend-train-model/All-train-model/merged_clothes_v2_balanced.build.json`
  - 用于构建新的 balanced merged 数据集
- `backend-train-model/All-train-model/unified_holdout_v1.build.json`
  - 用于构建统一 holdout 数据集
- `backend-train-model/All-train-model/first_train_holdout_v1.build.json`
  - 用于构建 `g31` 基线重训数据集

## 2. 当前这版 split 的默认结果

当前使用：

- `holdout_ratio = 0.15`
- `val_ratio = 0.15`
- `seed = 42`

生成结果见：

- `backend-train-model/All-train-model/splits/source_balanced_v1_summary.json`

关键统计是：

- `trainval`
  - `train = 352`
  - `val = 75`
  - `skip = 75`
- `holdout`
  - `test = 75`

当前这版 `val` 与 `holdout` 都覆盖了：

- `g31`
- `g32`
- `g33`

因此它至少已经避免了旧版 `merged_v2_full_reviewed` 中“`val` 基本只有 `g33`、`test` 基本只有 `g31`”的结构性偏差。

## 3. 重新生成 split manifest

进入 `backend-train-model/` 后执行：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe generate_split_manifests.py --source-manifest All-train-model\datasets\merged_clothes_v2_full_reviewed\manifest.csv --output-dir All-train-model\splits
```

作用：

- 以 `merged_clothes_v2_full_reviewed/manifest.csv` 作为 canonical sample pool；
- 按 `source_id + sample_role` 做 deterministic split；
- 把 `review_empty` 负样本同步分配进 `val / holdout`；
- 输出两份可复用 CSV，而不是把 split 写死在代码里。

## 4. 构建三套对比数据集

这一步仍然使用：

- `build_merged_clothes_dataset.py`

但现在它已经支持：

- `split_manifest_csv`
- `strict_split_manifest`
- 样本级 `split=train / val / test / skip`

### 4.1 构建 balanced merged 训练集

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe build_merged_clothes_dataset.py --config All-train-model\merged_clothes_v2_balanced.build.json --overwrite
```

输出：

- `backend-train-model/All-train-model/datasets/merged_clothes_v2_balanced/`

### 4.2 构建 unified holdout

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe build_merged_clothes_dataset.py --config All-train-model\unified_holdout_v1.build.json --overwrite
```

输出：

- `backend-train-model/All-train-model/datasets/unified_holdout_v1/`

这套数据集的主要用途是：

- 给现有历史权重做统一口径复评；
- 给下一轮重训后的模型做严格 final test。

### 4.3 构建 `first-train` 的对照训练集

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe build_merged_clothes_dataset.py --config All-train-model\first_train_holdout_v1.build.json --overwrite
```

输出：

- `backend-train-model/All-train-model/datasets/first_train_holdout_v1/`

这套数据集只保留 `g31` 样本，但 `val` 的选取规则和 merged 版使用同一份 split manifest。

## 5. 三层比较方式

### 5.1 第一层：cross-eval 历史复评

这一步不要求历史权重“没见过 holdout”，目的只是先把评估口径统一。

#### 现有 `first-train` 历史权重复评

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py evaluate --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\unified_holdout_v1\dataset.yaml --weights first-train\artifacts\runs\clothes_fullframe_baseline\weights\best.pt --report-name first_train_on_unified_holdout_v1_cross_eval
```

#### 现有 `merged_v2_from_first` 历史权重复评

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py evaluate --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\unified_holdout_v1\dataset.yaml --weights All-train-model\artifacts\runs\clothes_merged_v2_from_first\weights\best.pt --report-name merged_v2_from_first_on_unified_holdout_v1_cross_eval
```

注意：

- `train_workwear.py evaluate` 现在支持 `--report-name`
- 这样不同评估口径不会再覆盖同一个 `*_eval.json`

### 5.2 第二层：strict holdout / fair compare 主对照

这一步才是严格意义上的统一 holdout 主实验。

原则：

- `first-train` 与 `merged_v2_balanced` 都从 `weights\yolov8n.pt` 起跑；
- 这样主要比较的是数据集与 holdout 口径，而不是历史初始化权重差异。

#### 重训 `first-train` 基线

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py train --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\first_train_holdout_v1\dataset.yaml --base-model weights\yolov8n.pt --project All-train-model\artifacts\runs --name clothes_first_train_holdout_v1 --imgsz 640 --epochs 180 --batch 4 --patience 40 --workers 0 --device cpu --seed 42
```

#### 重训 balanced merged 公平对照模型

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py train --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\merged_clothes_v2_balanced\dataset.yaml --base-model weights\yolov8n.pt --project All-train-model\artifacts\runs --name clothes_merged_v2_balanced_holdout_v1 --imgsz 640 --epochs 180 --batch 4 --patience 40 --workers 0 --device cpu --seed 42
```

#### strict eval：`first-train`

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py evaluate --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\unified_holdout_v1\dataset.yaml --weights All-train-model\artifacts\runs\clothes_first_train_holdout_v1\weights\best.pt --report-name first_train_holdout_v1_strict_eval
```

#### strict eval：balanced merged

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py evaluate --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\unified_holdout_v1\dataset.yaml --weights All-train-model\artifacts\runs\clothes_merged_v2_balanced_holdout_v1\weights\best.pt --report-name merged_v2_balanced_holdout_v1_strict_eval
```

说明：

- 这一步可以并行跑。
- 不再把历史 `first-train\artifacts\runs\clothes_fullframe_baseline\weights\best.pt` 作为当前主对照的 merged 初始化。

### 5.3 第三层：route verification 业务路线验证

如果你要验证“先做 g31 基线，再把 merged 接到后面”是否有价值，就单独做这一层。

#### 用本轮 `clothes_first_train_holdout_v1` warm-start merged

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py train --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\merged_clothes_v2_balanced\dataset.yaml --base-model All-train-model\artifacts\runs\clothes_first_train_holdout_v1\weights\best.pt --project All-train-model\artifacts\runs --name clothes_merged_v2_balanced_from_first_holdout_v1 --imgsz 640 --epochs 180 --batch 4 --patience 40 --workers 0 --device cpu --seed 42
```

#### route eval：warm-start merged

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py evaluate --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\unified_holdout_v1\dataset.yaml --weights All-train-model\artifacts\runs\clothes_merged_v2_balanced_from_first_holdout_v1\weights\best.pt --report-name merged_v2_balanced_from_first_holdout_v1_route_eval
```

说明：

- 这一步不能和 `clothes_first_train_holdout_v1` 并行，因为它依赖本轮新生成的 `best.pt`。
- 这一层回答的是“业务路线是否成立”，不是“数据集是否公平胜出”。

## 6. 本轮 short-term improvement 的判断方式

如果你要判断这轮改造有没有价值，先看三类结果：

1. `cross-eval`
   - 现有 `first-train` 和现有 `merged_v2_from_first` 在同一 `unified_holdout_v1` 上的对比
2. `strict holdout / fair compare`
   - `clothes_first_train_holdout_v1`
   - `clothes_merged_v2_balanced_holdout_v1`
3. `route verification`
   - `clothes_merged_v2_balanced_from_first_holdout_v1`

如果在统一 holdout 下仍然是：

- `clothes_merged_v2_balanced_holdout_v1` 没有明显改善；
- 或者 `route verification` 也没有明显收益；
- 或者 precision / recall 仍然被 `review_empty` 拖得很厉害；

那么下一步就不应该先调模型，而应继续回到：

- 48 张 review 空标签复核；
- `g32 / g33` 标注口径一致性复核。

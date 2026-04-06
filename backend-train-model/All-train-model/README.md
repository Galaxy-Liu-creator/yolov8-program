# All-train-model

这个目录专门承接“总数据集构建 + 总模型训练”的产物，避免继续把新的 merged 数据、训练 runs、评估报告和导出文件混在默认 `backend-train-model/artifacts/` 里。

如果你要先看“现在已经做到哪一步、下一步该跑什么”，直接打开：

- `backend-train-model/All-train-model/status_and_next_steps.md`

## 固定文件

- `merged_train_project_config.json`
  - 把 `train_workwear.py` 的默认产物根目录切到 `backend-train-model/All-train-model/artifacts/`
- `merged_clothes_v1.build.json`
  - 当前可直接构建的 `merged_v1_positive_only` 配置
- `merged_clothes_v2.build.json`
  - 预留给后续补标后的 `merged_v2_full_reviewed` 配置

## 当前状态

- `merged_v1_positive_only` 已经构建完成
- 关键产物已经生成：
  - `backend-train-model\All-train-model\datasets\merged_clothes_v1_positive_only\dataset.yaml`
  - `backend-train-model\All-train-model\datasets\merged_clothes_v1_positive_only\build_report.json`
  - `backend-train-model\All-train-model\review\merged_clothes_v1_positive_only\missing_review.csv`
- 当前 `backend-train-model\All-train-model\artifacts\` 还不存在，说明 `train / evaluate / export` 还没正式开始

## 当前推荐流程

最稳妥的方式，是**先进入 `backend-train-model/` 目录再执行命令**：

```powershell
Set-Location .\backend-train-model
```

这样下面所有命令都统一使用 `All-train-model\...` 相对路径，不容易再踩 `--project-config` 的解析坑。

如果你不想切目录，也可以直接复制：

- `backend-train-model\All-train-model\datasets\merged_clothes_v1_positive_only\build_report.json`

里 `commands` 字段提供的绝对路径命令。

另外，当前 merged 流程**不建议直接使用** `train_workwear.py all`，因为这条命令会强制把流程带回 `prepare -> train -> evaluate -> export`，而现在 `merged_v1` 已经是准备好的标准 `dataset.yaml` 数据集。

### 1. 先构建 `merged_v1_positive_only`

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe build_merged_clothes_dataset.py --config All-train-model\merged_clothes_v1.build.json --overwrite
```

作用：

- 扫描三套 `clothes` 数据
- 只纳入当前“有同名标注”的样本
- 生成：
  - `backend-train-model\All-train-model\datasets\merged_clothes_v1_positive_only\dataset.yaml`
  - `backend-train-model\All-train-model\datasets\merged_clothes_v1_positive_only\manifest.csv`
  - `backend-train-model\All-train-model\datasets\merged_clothes_v1_positive_only\build_report.json`
  - `backend-train-model\All-train-model\review\merged_clothes_v1_positive_only\missing_review.csv`

### 2. 基于 `merged_v1` 训练

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py train --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\merged_clothes_v1_positive_only\dataset.yaml --name clothes_merged_v1_fullframe
```

作用：

- 使用 `dataset.yaml` 直接训练 merged 总模型
- 默认把训练产物写到 `backend-train-model\All-train-model\artifacts\runs\`
- JSON 报告默认写到 `backend-train-model\All-train-model\artifacts\reports\`

### 3. 评估 `merged_v1`

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py evaluate --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\merged_clothes_v1_positive_only\dataset.yaml --weights All-train-model\artifacts\runs\clothes_merged_v1_fullframe\weights\best.pt
```

### 4. 导出 `merged_v1`

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py export --project-config All-train-model\merged_train_project_config.json --weights All-train-model\artifacts\runs\clothes_merged_v1_fullframe\weights\best.pt --overwrite
```

## `merged_v2` 的补标规则

`merged_v1` 构建后会输出缺标清单：

- `backend-train-model\All-train-model\review\merged_clothes_v1_positive_only\missing_review.csv`

后续补标时：

1. 以 CSV 里的 `merged_stem` 为文件名
2. 把补好的标注放到：
   - `backend-train-model\All-train-model\review\merged_clothes_v2_full_reviewed\labels\`
3. 若该图确认没有 `clothes`，也要创建**空白 txt**
4. 全部补完后再跑：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe build_merged_clothes_dataset.py --config All-train-model\merged_clothes_v2.build.json --overwrite
```

## 目录约定

- `datasets/`
  - merged 后的数据集目录
- `review/`
  - 缺标清单与后续补标文件
- `artifacts/`
  - `train_workwear.py` 的训练、评估、导出产物

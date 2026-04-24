# 运行前置条件

本文档用于统一记录 `person` 三条训练分支的运行方式：`person_fullframe`、`person_roi_aware`、`person_roi_aware_v2`。当前电脑没有独立显卡，默认仅使用 CPU 训练；集成显卡不作为 PyTorch / Ultralytics 的 CUDA 训练设备使用。

## 通用环境检查

在仓库根目录运行命令：

```powershell
cd D:\University-Competition\Innovation_Entrepreneurship\MyProgram\yolov8-program
```

确认使用 Conda 环境 `yolo_code` 的 Python：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe --version
```

确认本地基础权重存在：

```powershell
Test-Path backend-train-model\weights\yolov8n.pt
```

如果要训练 `from_fullframe` 分支，再确认 fullframe best 权重存在：

```powershell
Test-Path backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

## 通用运行约束

- Windows + CPU 下统一使用 `--workers 0`，避免 DataLoader 多进程问题。
- 所有版本的训练与评估命令都建议显式传入 `--dataset-yaml` 与 `--run-name`，避免误用默认数据集或默认 run 名。
- 所有 ROI-aware 派生版本都必须使用独立输出目录，不要把不同版本的 prepared 数据集写到同一路径。
- 如果只是刷新某一版 ROI-aware 数据集，只覆盖该版本自己的 `output-root`，不要顺手覆盖其他版本产物。
- `person_roi_aware_v2` 当前优先使用 `person_fullframe_baseline/weights/best.pt` 做初始化，而不是重新从 `yolov8n.pt` 起训。

## 文档迭代约束

- 以后每新增一个训练版本，直接在本文档中新增一个新的 H1 版本段。
- 版本段顺序固定为：**最新在前，历史在后**。
- 不要把旧版本段直接改写成新版本；新版本应单独新增，旧版本保留为历史对照。
- 每个版本段尽量保持同一结构：`当前定位`、`数据集与产物`、`如需重生成数据集`、`训练命令`、`评估命令`、`备注`。

# person_roi_aware_v2

## 当前定位

- 当前最新 ROI-aware 派生分支。
- 当前 keep rule 为：`bottom_center_inside == true OR box_ioa_with_roi >= 0.25`。
- 当前推荐 run 名：`person_roi_aware_v2_from_fullframe`。

## 数据集与产物

- ROI 配置：
  - `backend-train-model/person-train-model/train-result/working/roi/roi_config.v2.generated.json`
- 数据集 YAML：
  - `backend-train-model/person-train-model/train-result/prepared/person_roi_aware_v2/sequence_contiguous/dataset.yaml`
- 当前 prepare 统计：
  - 图片：`502`
  - 保留框：`1342`
  - 丢弃框：`316`
  - 裁剪框：`54`
  - 空负样本：`14`
- 对应 prepare 报告：
  - `backend-train-model/person-train-model/train-result/prepared/person_roi_aware_v2/sequence_contiguous/prepare_report.json`

## 如需重生成数据集

先重生成独立的 v2 ROI 配置：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py extract-roi-config --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v2.generated.json --overwrite
```

再重生成独立的 v2 ROI-aware 数据集：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py prepare-roi-aware --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v2.generated.json --output-root backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v2\sequence_contiguous --overwrite
```

## 训练命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v2\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v2_from_fullframe --device cpu --workers 0 --batch 4 --imgsz 640 --epochs 180 --patience 60 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

## 评估命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v2\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v2_from_fullframe --device cpu --workers 0
```

## 备注

- 当前版本主要用于和 `person_roi_aware`、`person_fullframe` 做对照。
- 如果 `imgsz=640` 版本仍然 recall 偏低，再尝试 `imgsz=768, batch=2`，其余条件尽量先保持不变。
- 这一版是当前默认优先推进的 ROI-aware 训练分支。

# person_roi_aware

## 当前定位

- 历史 ROI-aware v1 分支。
- 当前 keep rule 为：`center_inside == true`。
- 当前仓库内这套 v1 数据集视为**保留的历史对照产物**。

## 数据集与产物

- ROI 配置：
  - `backend-train-model/person-train-model/train-result/working/roi/roi_config.generated.json`
- 数据集 YAML：
  - `backend-train-model/person-train-model/train-result/prepared/person_roi_aware/sequence_contiguous/dataset.yaml`
- 当前 prepare 统计：
  - 图片：`502`
  - 保留框：`1343`
  - 丢弃框：`315`
  - 裁剪框：`49`
  - 空负样本：`12`
- 对应 prepare 报告：
  - `backend-train-model/person-train-model/train-result/prepared/person_roi_aware/sequence_contiguous/prepare_report.json`

## 如需重生成数据集

- 当前不建议直接在现有 `person_project_config.json` 默认配置上原地重生成 v1。
- 原因是当前项目默认 keep rule 已经切到 v2；如果要严格重建 v1，应单独准备 v1 配置入口或保留专门的 v1 ROI 配置文件，再输出到独立目录。
- 因此，当前更推荐把仓库里现有 `person_roi_aware` 目录作为冻结的历史对照数据集使用。

## 训练命令

如果只是做当前 v1 / v2 的公平对照，优先使用 `from_fullframe` 初始化：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v1_from_fullframe --device cpu --workers 0 --batch 4 --imgsz 640 --epochs 180 --patience 60 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

## 评估命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v1_from_fullframe --device cpu --workers 0
```

## 备注

- 如果要复现最早的历史 baseline，可继续使用历史 run 名 `person_roi_aware_baseline` 与 `backend-train-model\weights\yolov8n.pt` 作为初始化。
- 当前阶段更有价值的用法是：把这一版当成旧规则对照组，与 `person_roi_aware_v2` 比较 recall、mAP50、mAP50-95。

# person_fullframe

## 当前定位

- 当前最稳定的上游 person baseline。
- 当前推荐 run 名：`person_fullframe_baseline`。
- 当前 ROI-aware `from_fullframe` 分支都默认把它作为初始化来源。

## 数据集与产物

- 数据集 YAML：
  - `backend-train-model/person-train-model/train-result/prepared/person_fullframe/sequence_contiguous/dataset.yaml`
- person 项目配置：
  - `backend-train-model/person-train-model/person_project_config.json`
- 数据集统计：
  - train：`350` 张图片，`1258` 个 person 框
  - val：`77` 张图片，`219` 个 person 框
  - test：`75` 张图片，`181` 个 person 框
  - 合计：`502` 张图片，`1658` 个 person 框
- 空标注负样本：
  - 新建空标注：`7`
  - 源标签本身为空：`1`
  - 最终空标注：`8`

## 如需重生成数据集

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py prepare --overwrite
```

## 训练命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe\sequence_contiguous\dataset.yaml --run-name person_fullframe_baseline --device cpu --workers 0 --batch 4 --imgsz 640 --epochs 180 --patience 40 --base-model backend-train-model\weights\yolov8n.pt
```

如果 CPU 压力较大，可先用更保守的 batch：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe\sequence_contiguous\dataset.yaml --run-name person_fullframe_baseline_batch2 --device cpu --workers 0 --batch 2 --imgsz 640 --epochs 180 --patience 40 --base-model backend-train-model\weights\yolov8n.pt
```

## 评估命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe\sequence_contiguous\dataset.yaml --run-name person_fullframe_baseline --device cpu --workers 0
```

## 备注

- 如果训练中断，续训仍建议直接调用 `backend-train-model\train_workwear.py` 的 `--resume`，不要在 wrapper 里混传新的训练参数。
- 如需导出 alias，可执行：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py export --overwrite
```

- 导出后 alias 位置：
  - `backend-train-model/person-train-model/train-result/export/person_detect_yolov8.pt`

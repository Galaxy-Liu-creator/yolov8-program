# 运行前置条件

本文档用于统一记录 `person` 五条训练分支的运行方式：`person_roi_aware_v3_mask_then_crop_margin64`、`person_roi_aware_v3_crop_only_margin64`、`person_roi_aware_v2`、`person_roi_aware`、`person_fullframe`。当前电脑没有独立显卡，默认仅使用 CPU 训练；集成显卡不作为 PyTorch / Ultralytics 的 CUDA 训练设备使用。

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
- 当前所有 ROI-aware `from_fullframe` 分支都默认把 `person_fullframe_baseline/weights/best.pt` 作为初始化来源。
- 现在 `extract-roi-config` 与 `prepare-roi-aware` 都支持显式传 `--roi-mode` 与 `--crop-margin-px`；如果要做版本化 ROI-aware 数据集，两个阶段都建议显式传这两个参数，保证 ROI 配置元数据与 prepare 行为一致。

## 文档迭代约束

- 以后每新增一个训练版本，直接在本文档中新增一个新的 H1 版本段。
- 版本段顺序固定为：**最新在前，历史在后**。
- 不要把旧版本段直接改写成新版本；新版本应单独新增，旧版本保留为历史对照。
- 每个版本段尽量保持同一结构：`当前定位`、`数据集与产物`、`如需重生成数据集`、`训练命令`、`评估命令`、`备注`。
- 如果当前需求不是“如何跑这条命令”，而是“下一轮该优先做什么改进”，优先看 `backend-train-model/person-train-model/train-docs/roi_next_iteration_plan.md`。

# person_roi_aware_v3_mask_then_crop_margin64

## 当前定位

- 当前已落地的 v3 主推荐 ROI-aware 分支。
- keep rule 继续沿用 v2：`bottom_center_inside == true OR box_ioa_with_roi >= 0.25`。
- 图像处理流程为：`mask_then_crop + crop_margin_px=64`。
- 当前推荐 run 名：`person_roi_aware_v3_mask_then_crop_margin64_from_fullframe`。
- 已完成的 `imgsz=768, batch=2` 对照 run 名：`person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768`。

## 数据集与产物

- ROI 配置：
  - `backend-train-model/person-train-model/train-result/working/roi/roi_config.v3.mask_then_crop_margin64.generated.json`
- 数据集 YAML：
  - `backend-train-model/person-train-model/train-result/prepared/person_roi_aware_v3_mask_then_crop_margin64/sequence_contiguous/dataset.yaml`
- 对应 prepare 报告：
  - `backend-train-model/person-train-model/train-result/prepared/person_roi_aware_v3_mask_then_crop_margin64/sequence_contiguous/prepare_report.json`
- 首次执行本节 `prepare-roi-aware` 前，上述数据集目录与统计文件可以还不存在；执行后才会生成。

## 如需重生成数据集

先生成带版本元数据的 ROI 配置：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py extract-roi-config --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v3.mask_then_crop_margin64.generated.json --roi-mode mask_then_crop --crop-margin-px 64 --overwrite
```

再生成独立的 v3 `mask_then_crop + margin64` 数据集：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py prepare-roi-aware --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v3.mask_then_crop_margin64.generated.json --output-root backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous --roi-mode mask_then_crop --crop-margin-px 64 --overwrite
```

## 训练命令

当前已完成的 `640 / batch=4` 基线命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe --device cpu --workers 0 --batch 4 --imgsz 640 --epochs 180 --patience 60 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

已完成的 `768 / batch=2` 对照训练命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768 --device cpu --workers 0 --batch 2 --imgsz 768 --epochs 180 --patience 60 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

## 评估命令

当前已完成的 `640 / batch=4` 基线评估命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe --device cpu --workers 0
```

对应 `768 / batch=2` 对照 run 的评估命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768 --device cpu --workers 0
```

## 严格断点续训命令

如果 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768` 训练中途被打断，严格断点续训不要再走 `run_person_flow.py train`，而是直接对这个 run 的 `last.pt` 调用底层训练脚本：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --project-config person-train-model\person_project_config.json --resume backend-train-model\person-train-model\train-result\artifacts\runs\person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768\weights\last.pt
```

## 备注

- 这一版的目标是先修掉 v2 中一批 keep-positive 但又被 crop bbox 裁残的样本，同时继续压制 ROI 外可见区域。
- 当前这轮 `imgsz=768`、`batch=2` 对照训练已完成；它保持数据集、keep rule、`mask_then_crop + margin64` 和初始化来源不变，专门验证更高输入分辨率是否能继续抬 `Recall`、`mAP50`、`mAP50-95`。
- 现有结果表明：这条 `img768` 对照 run 虽然 Precision 更高，但 native test 的 Recall、mAP50、mAP75、mAP50-95 都低于当前 `640 / batch=4` 主线，也没有优于 `person_roi_aware_v2_from_fullframe`，因此它应保留为**已完成对照实验**，不应升级为默认主线。
- `--resume` 会严格沿用 checkpoint 内保存的训练状态，因此不要再混传新的 `--imgsz`、`--batch`、`--dataset-yaml`、`--base-model`、`--run-name` 等训练参数；如果你想改这些参数，那已经不属于严格断点续训，而是新开一轮训练。
- 如果后续需要与 v2 做单因子对比，优先只改 `crop_margin_px` 与数据集版本，其余训练参数先尽量保持一致。
- 训练评估完成后，应把本版本与 `person_roi_aware_v2`、`person_roi_aware`、`person_fullframe` 的指标对比继续追加到 `backend-train-model/person-train-model/train-docs/roi_compare.md`。

# person_roi_aware_v3_crop_only_margin64

## 当前定位

- 当前已落地的 v3 对照实验分支。
- keep rule 同样沿用 v2：`bottom_center_inside == true OR box_ioa_with_roi >= 0.25`。
- 图像处理流程为：`crop_only + crop_margin_px=64`。
- 当前推荐 run 名：`person_roi_aware_v3_crop_only_margin64_from_fullframe`。

## 数据集与产物

- ROI 配置：
  - `backend-train-model/person-train-model/train-result/working/roi/roi_config.v3.crop_only_margin64.generated.json`
- 数据集 YAML：
  - `backend-train-model/person-train-model/train-result/prepared/person_roi_aware_v3_crop_only_margin64/sequence_contiguous/dataset.yaml`
- 对应 prepare 报告：
  - `backend-train-model/person-train-model/train-result/prepared/person_roi_aware_v3_crop_only_margin64/sequence_contiguous/prepare_report.json`
- 首次执行本节 `prepare-roi-aware` 前，上述数据集目录与统计文件可以还不存在；执行后才会生成。

## 如需重生成数据集

先生成带版本元数据的 ROI 配置：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py extract-roi-config --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v3.crop_only_margin64.generated.json --roi-mode crop_only --crop-margin-px 64 --overwrite
```

再生成独立的 v3 `crop_only + margin64` 数据集：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py prepare-roi-aware --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v3.crop_only_margin64.generated.json --output-root backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_crop_only_margin64\sequence_contiguous --roi-mode crop_only --crop-margin-px 64 --overwrite
```

## 训练命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_crop_only_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_crop_only_margin64_from_fullframe --device cpu --workers 0 --batch 4 --imgsz 640 --epochs 180 --patience 60 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

## 评估命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_crop_only_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_crop_only_margin64_from_fullframe --device cpu --workers 0
```

## 备注

- 这一版的主要价值是作为对照，验证“边界正样本更自然”到底来自 `crop_only`，还是仅仅来自 `margin64`。
- 这一版更容易把 ROI 外可见但未保留为标签的 person 带回 crop 图中，所以必须配合可视化抽查，不建议直接跳过 `mask_then_crop + margin64` 就把它当默认主线。
- 训练评估完成后，同样需要把本版本的指标和结论继续追加到 `backend-train-model/person-train-model/train-docs/roi_compare.md`。

# person_roi_aware_v2

## 当前定位

- 当前历史上已完成训练验证、且表现最好的 ROI-aware v2 分支。
- 当前 keep rule 为：`bottom_center_inside == true OR box_ioa_with_roi >= 0.25`。
- 当前图像处理流程为：`mask_then_crop + crop_margin_px=0`。
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
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py extract-roi-config --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v2.generated.json --roi-mode mask_then_crop --crop-margin-px 0 --overwrite
```

再重生成独立的 v2 ROI-aware 数据集：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py prepare-roi-aware --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v2.generated.json --output-root backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v2\sequence_contiguous --roi-mode mask_then_crop --crop-margin-px 0 --overwrite
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

- 当前版本主要用于和 `person_roi_aware`、`person_fullframe` 以及后续 v3 版本做对照。
- 如果 `imgsz=640` 版本仍然 recall 偏低，再尝试 `imgsz=768, batch=2`，其余条件尽量先保持不变。
- 这一版是当前已完成训练验证的 ROI-aware 历史最佳基线。

# person_roi_aware

## 当前定位

- 历史 ROI-aware v1 分支。
- 当前 keep rule 为：`center_inside == true`。
- 当前图像处理流程可视为：`mask_then_crop + crop_margin_px=0`。
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

如果只是做当前 v1 / v2 / v3 的公平对照，优先使用 `from_fullframe` 初始化：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v1_from_fullframe --device cpu --workers 0 --batch 4 --imgsz 640 --epochs 180 --patience 60 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

## 评估命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v1_from_fullframe --device cpu --workers 0
```

## 备注

- 如果要复现最早的历史 baseline，可继续使用历史 run 名 `person_roi_aware_baseline` 与 `backend-train-model\weights\yolov8n.pt` 作为初始化。
- 当前阶段更有价值的用法是：把这一版当成旧规则对照组，与 `person_roi_aware_v2` 以及两条 v3 路线比较 recall、mAP50、mAP50-95。

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

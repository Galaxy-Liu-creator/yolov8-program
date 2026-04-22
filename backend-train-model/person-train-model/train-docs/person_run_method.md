# Person 检测训练运行方法

本文档记录当前 `person` 单类检测模型的 CPU 训练入口。当前电脑没有独立显卡，仅使用 CPU 训练；集成显卡不作为 PyTorch / Ultralytics 的 CUDA 训练设备使用。

## 1. 当前数据集

- 任务类型：YOLO 目标检测
- 类别定义：`0: person`
- 数据集配置：
  - `backend-train-model/person-train-model/train-result/prepared/person_fullframe/sequence_contiguous/dataset.yaml`
- person 项目配置：
  - `backend-train-model/person-train-model/person_project_config.json`
- 数据集统计：
  - train：`350` 张图片，`1258` 个 person 框
  - val：`77` 张图片，`219` 个 person 框
  - test：`75` 张图片，`181` 个 person 框
  - 合计：`502` 张图片，`1658` 个 person 框
- 空标注负样本：
  - 新建空标注：`7` 个
  - 源标签本身为空：`1` 个
  - 最终空标注：`8` 个

## 2. 运行前确认

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

如果返回 `True`，即可离线训练；当前配置默认不允许远程下载模型。

建议正式训练命令显式传入 `--base-model backend-train-model\weights\yolov8n.pt`。不传时脚本也会尝试使用本地默认 `yolov8n.pt`，但显式传入更便于日志追溯和后续复现。

## 3. 推荐 CPU 训练命令

CPU 训练会比较慢，但最稳妥。建议先用默认 `imgsz=640` 保证检测精度，`batch=4` 如果内存压力大再降到 `batch=2`。

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --device cpu --workers 0 --batch 4 --imgsz 640 --epochs 180 --patience 40 --base-model backend-train-model\weights\yolov8n.pt
```

说明：

- `--device cpu`：明确使用 CPU，不尝试 CUDA。
- `--workers 0`：Windows + CPU 下更稳定，避免多进程 DataLoader 额外问题。
- `--batch 4`：当前默认值；如果训练报内存不足，改成 `--batch 2`。
- `--imgsz 640`：优先保证 person 检测精度。
- `--epochs 180`：给小数据集足够收敛轮数。
- `--patience 40`：连续 40 轮无明显提升后自动早停。
- `--base-model backend-train-model\weights\yolov8n.pt`：显式使用本地 YOLOv8n 预训练权重进行 person 微调，避免误用 clothes 权重或触发远程下载。

## 4. 慢速但更稳的 CPU 命令

如果电脑训练过程中明显卡顿、内存压力大或温度过高，使用下面的保守命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --device cpu --workers 0 --batch 2 --imgsz 640 --epochs 180 --patience 40 --base-model backend-train-model\weights\yolov8n.pt
```

如果仍然太慢，可以临时降低输入尺寸做快速可用性训练，但最终正式权重仍建议回到 `imgsz=640`：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --device cpu --workers 0 --batch 2 --imgsz 512 --epochs 120 --patience 30 --run-name person_fullframe_cpu_fastcheck --base-model backend-train-model\weights\yolov8n.pt
```

## 5. 从头执行完整流程

如果需要重新汇总标签、重新生成 `dataset.yaml`、训练、评估并导出 person 权重 alias，使用：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py all --overwrite --device cpu --workers 0 --batch 4 --imgsz 640 --epochs 180 --patience 40 --base-model backend-train-model\weights\yolov8n.pt
```

注意：`all` 会覆盖 person prepared 数据集和 person 导出 alias，但不会执行 `--deploy`，不会覆盖 `inspection-flask/weights/workwear_detect_yolov8.pt`。

## 6. 单独重新生成数据集

如果只想重新整理 person 数据集，不训练：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py prepare --overwrite
```

输出位置：

```text
backend-train-model/person-train-model/train-result/prepared/person_fullframe/sequence_contiguous/dataset.yaml
```

## 7. 训练中断后续训

当前 person wrapper 没有额外封装 `resume` 参数。若训练中断，需要直接调用现有训练入口做**严格断点续训**，并使用 person 项目配置。

注意：当前 `train_workwear.py` 的 `--resume` 会严格沿用 checkpoint 内保存的训练配置，因此不要再同时传入 `--dataset-yaml`、`--base-model`、`--imgsz`、`--epochs`、`--batch`、`--patience`、`--workers`、`--device` 等训练参数。

先确认 `last.pt` 是否存在：

```powershell
Test-Path backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\last.pt
```

续训命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --project-config D:\University-Competition\Innovation_Entrepreneurship\MyProgram\yolov8-program\backend-train-model\person-train-model\person_project_config.json --resume D:\University-Competition\Innovation_Entrepreneurship\MyProgram\yolov8-program\backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\last.pt
```

如果只想让脚本自动选择当前项目最近一个仍可续训的 `last.pt`，也可以后续再单独补一条 bare `--resume` 版本；但对当前 person baseline，优先推荐显式指定这次训练的 `last.pt`，更稳妥。

## 8. 单独评估

训练完成后，默认 best 权重位置：

```text
backend-train-model/person-train-model/train-result/artifacts/runs/person_fullframe_baseline/weights/best.pt
```

评估命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --device cpu --workers 0
```

如果使用了自定义 run 名称，需要显式传入：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --run-name person_fullframe_cpu_fastcheck --device cpu --workers 0
```

## 9. 导出 person 权重

导出命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py export --overwrite
```

导出后 person alias 位置：

```text
backend-train-model/person-train-model/train-result/export/person_detect_yolov8.pt
```

该 alias 只保存在 person 训练结果目录，不会写入线上 `workwear` 权重路径。

## 10. 结果检查重点

训练结束后优先查看：

- `backend-train-model/person-train-model/train-result/artifacts/runs/person_fullframe_baseline/results.csv`
- `backend-train-model/person-train-model/train-result/artifacts/runs/person_fullframe_baseline/weights/best.pt`
- `backend-train-model/person-train-model/train-result/artifacts/reports/person_fullframe_baseline_eval.json`

重点关注指标：

- `metrics/mAP50(B)`：person 检测基础可用性
- `metrics/mAP50-95(B)`：定位质量
- `metrics/precision(B)`：误报倾向
- `metrics/recall(B)`：漏报倾向

如果 recall 明显偏低，后续应优先检查 person 漏标、遮挡样本、小目标和边缘目标；如果 precision 明显偏低，后续应优先检查空标注负样本、背景误检和阈值设置。

## 11. ROI-aware person 数据集生成

当已经使用 Labelme 为每条序列标好 `roi` polygon 后，可以新增一条 ROI-aware person 平行分支。该分支不会覆盖当前 fullframe person baseline。

### 11.1 创建 ROI 标注工作区

如果已经像当前数据这样为每张图片都导出了 Labelme ROI JSON，可以跳过本步骤，直接进入 `11.2`，用现有 `roi-json` 目录作为 `--roi-json-root`。

如果还没有整理 Labelme ROI JSON，才需要先自动创建清晰的 ROI 工作区，并为每条序列抽取代表帧：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py setup-roi-workdir
```

默认输出结构：

```text
backend-train-model/person-train-model/roi-work/
├─ <sequence_name>/
│  ├─ frames/
│  ├─ roi-json/
│  └─ README.md
├─ README.md
└─ roi_work_manifest.json
```

默认每条序列抽取 `3` 张代表帧。如果想覆盖已经抽过的同名代表帧，可以使用：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py setup-roi-workdir --overwrite-roi-frames
```

如果想每条序列抽更多代表帧，例如 `5` 张：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py setup-roi-workdir --roi-frames-per-sequence 5
```

生成后，进入每个序列的 `README.md` 查看对应 Labelme 启动命令。Labelme 保存的 `.json` 应放到对应序列的 `roi-json/` 目录。

### 11.2 提取 ROI 配置

当前已有逐图 ROI JSON，可直接从 ROI 公共根递归读取；当前 `person_project_config.json` 默认已指向该目录：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py extract-roi-config --overwrite
```

这会读取以下现有目录中的 `.json`：

```text
D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\roi-json\group3_1\D04_20260123074846\roi-json
D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\roi-json\group3_1\D05_20260123074841\roi-json
D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\roi-json\group3_1\D15_20260123074848\roi-json
D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\roi-json\group3_2\1\roi-json
D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\roi-json\group3_2\D15_20260119203927\roi-json
D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\roi-json\group3_3\D02_20260123070624\roi-json
D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\roi-json\group3_3\D02_20260123074836\roi-json
```

如果需要改用自动创建的工作区，则显式传工作区根目录：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py extract-roi-config --roi-json-root backend-train-model/person-train-model/roi-work --overwrite
```

推荐目录结构仍为：

```text
backend-train-model/person-train-model/roi-work/<sequence_name>/roi-json/*.json
```

如果某条序列的图片根目录末级名与 `sequence_name` 不同，例如 `group3_2\1`，脚本也会尝试把图片根目录末级名作为路径别名识别；但更推荐目录名仍使用 `person_project_config.json` 里的 `sequence_name`，便于后续追溯。

对应提取命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py extract-roi-config --overwrite
```

输出位置来自 `person_project_config.json`：

```text
backend-train-model/person-train-model/train-result/working/roi/roi_config.generated.json
```

规则：

- 只读取 `label == "roi"` 且 `shape_type == "polygon"` 的 shape；
- 支持每张图片一个 ROI polygon，并写入 `per_image`；
- 如果同一序列所有图片 ROI 完全一致，也会额外写入可回退的 `per_sequence`；
- 同一张图片出现多个不一致 JSON 时会直接报错；
- 缺少 ROI、存在多个 ROI、未知序列名或点越界时会直接报错。

### 11.3 生成 ROI-aware 数据集

生成命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py prepare-roi-aware --overwrite
```

建议在修正过原图片根目录或 person 标签后使用 `--overwrite`，这样会同步刷新汇总 person 标签目录与 ROI-aware 输出目录；不带 `--overwrite` 时会尽量复用既有汇总标签。

默认输出：

```text
backend-train-model/person-train-model/train-result/prepared/person_roi_aware/sequence_contiguous/dataset.yaml
```

处理规则：

- 读取原图、原 person 标签和每张图片对应的 ROI polygon；
- 对 ROI 外区域置黑；
- 裁剪到 ROI polygon 的最小外接矩形；
- 只保留中心点落在 ROI polygon 内的 person 框；
- 对保留框做裁剪和坐标重映射；
- ROI 内无人时保留为空标注负样本。

### 11.4 训练 ROI-aware person baseline

训练命令示例：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware\sequence_contiguous\dataset.yaml --run-name person_roi_aware_baseline --device cpu --workers 0 --batch 4 --imgsz 640 --epochs 180 --patience 40 --base-model backend-train-model\weights\yolov8n.pt
```

评估命令示例：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware\sequence_contiguous\dataset.yaml --run-name person_roi_aware_baseline --device cpu --workers 0
```

对照重点：

- 与 `person_fullframe_baseline` 保持同样训练参数；
- 重点比较 `recall`、`mAP50`、`mAP50-95`；
- 不要在 ROI-aware 结果未验证前替换当前 fullframe baseline。

## 12. 当前不做的事情

- 不使用 GPU / CUDA 训练。
- 不把 person 标签混入 clothes 标签目录。
- 不修改 `train_workwear.py`、`dataset_tools.py`、`config.py` 的已有主逻辑。
- 不直接覆盖 `inspection-flask/weights/workwear_detect_yolov8.pt`。
- 不在未完成 person 模型评估前，将其认定为最终线上权重。

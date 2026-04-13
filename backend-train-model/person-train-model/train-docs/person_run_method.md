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

## 3. 推荐 CPU 训练命令

CPU 训练会比较慢，但最稳妥。建议先用默认 `imgsz=640` 保证检测精度，`batch=4` 如果内存压力大再降到 `batch=2`。

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --device cpu --workers 0 --batch 4 --imgsz 640 --epochs 180 --patience 40
```

说明：

- `--device cpu`：明确使用 CPU，不尝试 CUDA。
- `--workers 0`：Windows + CPU 下更稳定，避免多进程 DataLoader 额外问题。
- `--batch 4`：当前默认值；如果训练报内存不足，改成 `--batch 2`。
- `--imgsz 640`：优先保证 person 检测精度。
- `--epochs 180`：给小数据集足够收敛轮数。
- `--patience 40`：连续 40 轮无明显提升后自动早停。

## 4. 慢速但更稳的 CPU 命令

如果电脑训练过程中明显卡顿、内存压力大或温度过高，使用下面的保守命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --device cpu --workers 0 --batch 2 --imgsz 640 --epochs 180 --patience 40
```

如果仍然太慢，可以临时降低输入尺寸做快速可用性训练，但最终正式权重仍建议回到 `imgsz=640`：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --device cpu --workers 0 --batch 2 --imgsz 512 --epochs 120 --patience 30 --run-name person_fullframe_cpu_fastcheck
```

## 5. 从头执行完整流程

如果需要重新汇总标签、重新生成 `dataset.yaml`、训练、评估并导出 person 权重 alias，使用：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py all --overwrite --device cpu --workers 0 --batch 4 --imgsz 640 --epochs 180 --patience 40
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

当前 person wrapper 没有额外封装 `resume` 参数。若训练中断，需要直接调用现有训练入口续训，并使用 person 项目配置。

先确认 `last.pt` 是否存在：

```powershell
Test-Path backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\last.pt
```

续训命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --project-config D:\University-Competition\Innovation_Entrepreneurship\MyProgram\yolov8-program\backend-train-model\person-train-model\person_project_config.json --dataset-yaml D:\University-Competition\Innovation_Entrepreneurship\MyProgram\yolov8-program\backend-train-model\person-train-model\train-result\prepared\person_fullframe\sequence_contiguous\dataset.yaml --resume D:\University-Competition\Innovation_Entrepreneurship\MyProgram\yolov8-program\backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\last.pt --device cpu --workers 0
```

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

## 11. 当前不做的事情

- 不使用 GPU / CUDA 训练。
- 不把 person 标签混入 clothes 标签目录。
- 不修改 `train_workwear.py`、`dataset_tools.py`、`config.py` 的已有主逻辑。
- 不直接覆盖 `inspection-flask/weights/workwear_detect_yolov8.pt`。
- 不在未完成 person 模型评估前，将其认定为最终线上权重。

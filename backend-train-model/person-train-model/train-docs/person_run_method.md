# 运行前置条件

本文档用于统一记录 `person` 七条训练分支的运行方式：`person_roi_aware_with_new_labels_v1_mask_then_crop_margin64`、`person_fullframe_with_new_labels`、`person_roi_aware_v3_mask_then_crop_margin64`、`person_roi_aware_v3_crop_only_margin64`、`person_roi_aware_v2`、`person_roi_aware`、`person_fullframe`。当前训练默认在另一台带 GPU 的电脑上执行；除非用户明确要求回退到本机 CPU，否则本文件中的训练 / 评估命令默认按 GPU 训练编写。

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

- 当前默认优先使用 GPU（`--device 0`）训练；只有当训练机出现 DataLoader 稳定性问题时，才把 `--workers` 回退到 `0`。
- 所有版本的训练与评估命令都建议显式传入 `--project-config`、`--dataset-yaml` 与 `--run-name`，避免误用默认数据集、默认配置或默认 run 名；当前 wrapper 已会从 `project-config -> training.default_train_args` 读取默认训练参数，但关键实验尤其是非默认输入尺寸评估，仍建议显式传 `--imgsz / --batch / --workers / --device`。
- 所有 ROI-aware 派生版本都必须使用独立输出目录，不要把不同版本的 prepared 数据集写到同一路径。
- 如果只是刷新某一版 ROI-aware 数据集，只覆盖该版本自己的 `output-root`，不要顺手覆盖其他版本产物。
- 所有训练、评估、导出和全流程 JSON 报告都必须按 run 名分目录保存，目录结构固定为：`backend-train-model/person-train-model/train-result/artifacts/reports/<run_name>/<report_file>.json`。例如 `person_fullframe_baseline` 的训练和评估报告分别放在 `.../reports/person_fullframe_baseline/person_fullframe_baseline_train.json` 与 `.../reports/person_fullframe_baseline/person_fullframe_baseline_eval.json`。
- `reports/` 根目录只允许放 run 子目录或少量全局审计日志；不要再把 `*_train.json`、`*_eval.json`、`*_export.json`、`*_all.json` 直接平铺到 `reports/` 根目录。新增脚本、手工整理历史报告或编写复盘命令时，都必须使用上面的分层路径，以便和 `artifacts/runs/<run_name>/` 一一对应、方便维护和回溯。
- 当前所有 ROI-aware `from_fullframe` 分支都默认把 `person_fullframe_baseline/weights/best.pt` 作为初始化来源。
- 现在 `extract-roi-config` 与 `prepare-roi-aware` 都支持显式传 `--roi-mode` 与 `--crop-margin-px`；如果要做版本化 ROI-aware 数据集，两个阶段都建议显式传这两个参数，保证 ROI 配置元数据与 prepare 行为一致。
- 当前正式建议使用的版本化 ROI-aware 配置入口：
  - `backend-train-model/person-train-model/person_project_config.roi_with_new_labels.v1.mask_then_crop_margin64.json`
  - `backend-train-model/person-train-model/person_project_config.roi_v3.mask_then_crop_margin64.json`
  - `backend-train-model/person-train-model/person_project_config.roi_v3.crop_only_margin64.json`
  - `backend-train-model/person-train-model/person_project_config.roi_v2.mask_then_crop_ioa25.json`
  - `backend-train-model/person-train-model/person_project_config.roi_v1.center_inside.json`

# ROI-aware随机性训练

## seed=7

### 当前定位

- 用于对 `person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_from_fullframe` 做随机性复核，只变更 `seed=7`，其余训练口径保持一致。
- 保持相同的 ROI-aware prepared 数据集、上游初始化权重、输入尺寸与 batch 设置，重点观察随机种子对指标波动的影响。

### 训练命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.roi_with_new_labels.v1.mask_then_crop_margin64.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_with_new_labels_v1_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_seed7_from_fullframe --device 0 --workers 4 --batch 4 --imgsz 640 --epochs 180 --patience 60 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_with_new_labels_baseline\weights\best.pt --seed 7
```

### 评估命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.roi_with_new_labels.v1.mask_then_crop_margin64.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_with_new_labels_v1_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --weights backend-train-model\person-train-model\train-result\artifacts\runs\person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_seed7_from_fullframe\weights\best.pt --run-name person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_seed7_from_fullframe --imgsz 640 --batch 4 --workers 4 --device 0 --report-name person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_seed7_from_fullframe_eval
```

## seed=13

### 当前定位

- 用于对 `person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_from_fullframe` 做随机性复核，只变更 `seed=13`，其余训练口径保持一致。
- 与 `seed=7` 保持相同的数据集、初始化权重和训练超参，便于对比随机性波动。

### 训练命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.roi_with_new_labels.v1.mask_then_crop_margin64.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_with_new_labels_v1_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_seed13_from_fullframe --device 0 --workers 4 --batch 4 --imgsz 640 --epochs 180 --patience 60 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_with_new_labels_baseline\weights\best.pt --seed 13
```

### 评估命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.roi_with_new_labels.v1.mask_then_crop_margin64.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_with_new_labels_v1_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --weights backend-train-model\person-train-model\train-result\artifacts\runs\person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_seed13_from_fullframe\weights\best.pt --run-name person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_seed13_from_fullframe --imgsz 640 --batch 4 --workers 4 --device 0 --report-name person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_seed13_from_fullframe_eval
```

## 文档迭代约束

- 以后每新增一个训练版本，直接在本文档中新增一个新的 H1 版本段。
- 版本段顺序固定为：**最新在前，历史在后**。
- 不要把旧版本段直接改写成新版本；新版本应单独新增，旧版本保留为历史对照。
- 每个版本段尽量保持同一结构：`当前定位`、`数据集与产物`、`如需重生成数据集`、`训练命令`、`评估命令`、`备注`。
- 如果当前需求不是“如何跑这条命令”，而是“下一轮该优先做什么改进”，优先看 `backend-train-model/person-train-model/train-docs/roi_next_iteration_plan.md`。

# person_roi_aware_with_new_labels_v1_mask_then_crop_margin64

## 当前定位

- 当前 `new_person_labels` 完成 `group_0001 ~ group_0006` 组级 ROI 核验后的第一版 ROI-aware 训练入口。
- 适用于：6 个新组都已确认 `A` 类稳定组、且同组 ROI 模板可以稳定复用于组内其他图片的情况。
- 当前推荐 run 名：`person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_from_fullframe`。
- 当前更推荐沿用已验证更稳的 ROI 图像处理口径：`mask_then_crop + crop_margin_px=64`。
- 当前已新增独立配置入口：`backend-train-model/person-train-model/person_project_config.roi_with_new_labels.v1.mask_then_crop_margin64.json`。
- 后续这条 ROI-aware new labels v1 线，优先直接使用上述独立配置文件，不再继续借用 `person_project_config.fullframe_with_new_labels.json` 作为临时入口。

## 数据集与产物

- person 项目配置：
  - `backend-train-model/person-train-model/person_project_config.roi_with_new_labels.v1.mask_then_crop_margin64.json`
- 当前 ROI JSON 根目录：
  - `D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\roi-json`
- 当前已完成 ROI 核验的新增组：
  - `group_0001`
  - `group_0002`
  - `group_0003`
  - `group_0004`
  - `group_0005`
  - `group_0006`
- 当前建议使用的版本化 ROI 配置输出：
  - `backend-train-model/person-train-model/train-result/working/roi/roi_config.fullframe_with_new_labels.v1.mask_then_crop_margin64.generated.json`
- 当前建议使用的 ROI-aware prepared 输出目录：
  - `backend-train-model/person-train-model/train-result/prepared/person_roi_aware_with_new_labels_v1_mask_then_crop_margin64/sequence_contiguous`
- 对应数据集 YAML：
  - `backend-train-model/person-train-model/train-result/prepared/person_roi_aware_with_new_labels_v1_mask_then_crop_margin64/sequence_contiguous/dataset.yaml`
- 对应 prepare 报告：
  - `backend-train-model/person-train-model/train-result/prepared/person_roi_aware_with_new_labels_v1_mask_then_crop_margin64/sequence_contiguous/prepare_report.json`

## 如需重生成数据集

先提取当前 new labels ROI-aware v1 的 ROI 配置：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py extract-roi-config --project-config backend-train-model\person-train-model\person_project_config.roi_with_new_labels.v1.mask_then_crop_margin64.json --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.fullframe_with_new_labels.v1.mask_then_crop_margin64.generated.json --roi-mode mask_then_crop --crop-margin-px 64 --overwrite
```

再生成独立的 ROI-aware prepared 数据集：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py prepare-roi-aware --project-config backend-train-model\person-train-model\person_project_config.roi_with_new_labels.v1.mask_then_crop_margin64.json --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.fullframe_with_new_labels.v1.mask_then_crop_margin64.generated.json --output-root backend-train-model\person-train-model\train-result\prepared\person_roi_aware_with_new_labels_v1_mask_then_crop_margin64\sequence_contiguous --roi-mode mask_then_crop --crop-margin-px 64 --overwrite
```

## 训练命令

当前推荐先直接以稳健 fullframe 扩样权重作为初始化来源，启动第一版 ROI-aware new labels 训练：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.roi_with_new_labels.v1.mask_then_crop_margin64.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_with_new_labels_v1_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_from_fullframe --device 0 --workers 4 --batch 4 --imgsz 640 --epochs 180 --patience 60 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_with_new_labels_baseline\weights\best.pt
```

如果训练机显存或 DataLoader 稳定性有压力，可先用更保守的 batch：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.roi_with_new_labels.v1.mask_then_crop_margin64.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_with_new_labels_v1_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_from_fullframe_batch2 --device 0 --workers 4 --batch 2 --imgsz 640 --epochs 180 --patience 60 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_with_new_labels_baseline\weights\best.pt
```

## 评估命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.roi_with_new_labels.v1.mask_then_crop_margin64.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_with_new_labels_v1_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --weights backend-train-model\person-train-model\train-result\artifacts\runs\person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_from_fullframe\weights\best.pt --run-name person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_from_fullframe --imgsz 640 --batch 4 --workers 4 --device 0 --report-name person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_from_fullframe_eval
```

## 备注

- 严格说，当前不是“ROI 核验完成后直接跳过数据准备只跑 train”，而是：**先 `extract-roi-config`，再 `prepare-roi-aware`，最后再 `train / evaluate`。**
- 当前正式建议优先使用独立配置文件 `person_project_config.roi_with_new_labels.v1.mask_then_crop_margin64.json`；不要再把这条新线继续写成“借用 fullframe 配置的临时方案”。
- 如果 `extract-roi-config` 之后发现某个 `group_000X` 没有进入 `per_sequence`，优先检查的不是训练参数，而是该组 `roi-json/` 下是否保留了多份顶点略有差异的 JSON。
- 当前这一版的上游初始化更推荐锁到 `person_fullframe_with_new_labels_baseline/weights/best.pt`，不要回退到旧 `person_fullframe_baseline`，否则新组 fullframe 扩样收益不会完整传递到 ROI-aware v1。
- 当前这条分支更适合先作为“new labels ROI-aware 第一版正式对照实验”使用；在看到 test 指标与逐图抽检结果前，不建议直接把它写成已经替代 fullframe 主线的默认唯一版本。

# person_fullframe_with_new_labels

## 当前定位

- 当前最新的 `person` fullframe 扩样分支。
- 用于把原有 `502` 张旧 `person` 图与 `new_person_labels` 的 `2507` 张图合并后重新训练 fullframe `person`。
- 当前推荐 run 名：`person_fullframe_with_new_labels_baseline`。
- 当前显式设置 `roi.enabled=false`，因此它只是 fullframe 分支，不应直接当成已补齐 ROI 的 ROI-aware 上游版本。

## 数据集与产物

- person 项目配置：
  - `backend-train-model/person-train-model/person_project_config.fullframe_with_new_labels.json`
- 聚合标签目录：
  - `backend-train-model/person-train-model/train-result/working/aggregated_labels_fullframe_with_new_labels`
- 数据源汇总：
  - `backend-train-model/person-train-model/train-result/person_source_dataset_summary_fullframe_with_new_labels.json`
- 数据集 YAML：
  - `backend-train-model/person-train-model/train-result/prepared/person_fullframe_with_new_labels/sequence_contiguous/dataset.yaml`
- 对应 prepare 报告：
  - `backend-train-model/person-train-model/train-result/prepared/person_fullframe_with_new_labels/sequence_contiguous/prepare_report.json`
- 当前 prepare 统计：
  - train：`2105` 张图片，`5984` 个 person 框
  - val：`453` 张图片，`1586` 个 person 框
  - test：`451` 张图片，`1291` 个 person 框
  - 合计：`3009` 张图片，`8861` 个 person 框
- 空标注负样本：
  - 新建空标注：`7`
  - 源标签本身为空：`6`
  - 最终空标注：`13`
- 新增样本中已确认保留为空白 txt 的文件：
  - `00179.txt`
  - `00516.txt`
  - `00559.txt`
  - `01332.txt`

## 如需重生成数据集

先重新聚合标签，并确保缺失标签已补为空白 txt：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py prepare-labels --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --overwrite
```

再重生成 fullframe prepared 数据集：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py prepare --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --overwrite
```

## 训练命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe_with_new_labels\sequence_contiguous\dataset.yaml --run-name person_fullframe_with_new_labels_baseline --device 0 --workers 4 --batch 4 --imgsz 640 --epochs 180 --patience 40 --base-model backend-train-model\weights\yolov8n.pt
```

如果训练机显存或稳定性有压力，可先用更保守的 batch：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe_with_new_labels\sequence_contiguous\dataset.yaml --run-name person_fullframe_with_new_labels_baseline_batch2 --device 0 --workers 4 --batch 2 --imgsz 640 --epochs 180 --patience 40 --base-model backend-train-model\weights\yolov8n.pt
```

## 评估命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe_with_new_labels\sequence_contiguous\dataset.yaml --run-name person_fullframe_with_new_labels_baseline --imgsz 640 --batch 4 --workers 4 --device 0
```

## 下一步第一优先级：`imgsz=768` 单因子对照

当前这条 `person_fullframe_with_new_labels` 线的下一步第一优先级，是先做 **输入分辨率单因子对照**，验证小目标和高 IoU 框质量能否改善。

实验约束：

- 保持数据集不变；
- 保持 `epochs / patience / base-model` 不变；
- 当前优先先做更严格的单因子对照，因此保持 `batch=4` 不变，只改 `imgsz=768`；
- 重点观察 `mAP50-95`、`mAP75` 和小目标场景的漏检 / 框偏移。

### 训练命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe_with_new_labels\sequence_contiguous\dataset.yaml --run-name person_fullframe_with_new_labels_img768 --device 0 --workers 4 --batch 4 --imgsz 768 --epochs 180 --patience 40 --base-model backend-train-model\weights\yolov8n.pt
```

如果 `imgsz=768, batch=4` 在训练机上遇到显存或稳定性问题，再退回下面这个保守备选：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe_with_new_labels\sequence_contiguous\dataset.yaml --run-name person_fullframe_with_new_labels_img768_batch2 --device 0 --workers 4 --batch 2 --imgsz 768 --epochs 180 --patience 40 --base-model backend-train-model\weights\yolov8n.pt
```

### 评估命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe_with_new_labels\sequence_contiguous\dataset.yaml --weights backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_with_new_labels_img768\weights\best.pt --run-name person_fullframe_with_new_labels_img768 --imgsz 768 --batch 4 --workers 4 --device 0 --report-name person_fullframe_with_new_labels_img768_eval
```

说明：这条命令同时显式锁定了 `project-config`、`dataset-yaml`、`weights`、`run-name` 和 `imgsz=768`，因此评估指标与报告元数据会一起对齐；其中 `report_name` 仍沿用 `person_fullframe_with_new_labels_img768_eval`，会直接覆盖旧报告。此前如果只补 `--imgsz 768` 但没有把评估入口全部对齐，仍可能出现报告中的 `project_config_path` / `image_roots` 与当前扩样 fullframe 数据集不完全自洽的情况。

## 备注

- 这条分支当前已经完成 `prepare-labels` 与 `prepare`，空标签补齐逻辑已经落盘，不需要手工再去新建空白 txt。
- 当前这版 fullframe 扩样是“旧 `person` + 新 `person`”的合并训练入口，不包含新增 ROI 信息；如果后续要接 ROI-aware，需要先为新样本补齐 ROI，再单独准备新的 ROI-aware 数据集。
- `prepare` 期间如果再次出现“标注框极小越界，已自动裁剪到 [0,1]”提示，当前可视为非致命数据清洗告警；只要 `prepare_report.json` 正常生成，就不影响后续训练启动。

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
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py extract-roi-config --project-config backend-train-model\person-train-model\person_project_config.roi_v3.mask_then_crop_margin64.json --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v3.mask_then_crop_margin64.generated.json --roi-mode mask_then_crop --crop-margin-px 64 --overwrite
```

再生成独立的 v3 `mask_then_crop + margin64` 数据集：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py prepare-roi-aware --project-config backend-train-model\person-train-model\person_project_config.roi_v3.mask_then_crop_margin64.json --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v3.mask_then_crop_margin64.generated.json --output-root backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous --roi-mode mask_then_crop --crop-margin-px 64 --overwrite
```

## 训练命令

当前已完成的 `640 / batch=4` 基线命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.roi_v3.mask_then_crop_margin64.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe --device 0 --workers 4 --batch 4 --imgsz 640 --epochs 180 --patience 60 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

已完成的 `768 / batch=2` 对照训练命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.roi_v3.mask_then_crop_margin64.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768 --device 0 --workers 4 --batch 2 --imgsz 768 --epochs 180 --patience 60 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

## 评估命令

当前已完成的 `640 / batch=4` 基线评估命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.roi_v3.mask_then_crop_margin64.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe --imgsz 640 --batch 4 --workers 4 --device 0
```

对应 `768 / batch=2` 对照 run 的评估命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.roi_v3.mask_then_crop_margin64.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768 --imgsz 768 --batch 2 --workers 4 --device 0
```

## Seed 稳定性对照命令

如果接下来要验证当前 v3 主线相对 `v2` 的领先是否稳定，优先补下面两组 seed 对照；除了 `--seed` 与 `--run-name` 外，其余训练条件都保持与当前 `640 / batch=4` 主线一致。

Seed 7 训练命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.roi_v3.mask_then_crop_margin64.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed7 --device 0 --workers 4 --batch 4 --imgsz 640 --epochs 180 --patience 60 --seed 7 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

Seed 7 评估命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.roi_v3.mask_then_crop_margin64.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed7 --imgsz 640 --batch 4 --workers 4 --device 0 --report-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed7_eval
```

Seed 13 训练命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.roi_v3.mask_then_crop_margin64.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed13 --device 0 --workers 4 --batch 4 --imgsz 640 --epochs 180 --patience 60 --seed 13 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

Seed 13 评估命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.roi_v3.mask_then_crop_margin64.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed13 --imgsz 640 --batch 4 --workers 4 --device 0 --report-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed13_eval
```

## 单帧 FP/FN 复盘命令

当前已经新增逐图 `FP/FN` 复盘脚本 `backend-train-model/person-train-model/train-code/analyze_person_fpfn.py`。若要复盘当前主线 run 在 test split 上的单帧误检 / 漏检，直接运行：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\analyze_person_fpfn.py --eval-report backend-train-model\person-train-model\train-result\artifacts\reports\person_roi_aware_v3_mask_then_crop_margin64_from_fullframe\person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_eval.json --split test --conf-threshold 0.25 --nms-iou 0.7 --match-iou 0.5 --device 0 --output-root backend-train-model\person-train-model\train-result\review\person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_fpfn_test_conf025 --overwrite
```

重点看输出：

- `backend-train-model/person-train-model/train-result/review/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_fpfn_test_conf025/fpfn_summary.md`
- `backend-train-model/person-train-model/train-result/review/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_fpfn_test_conf025/fpfn_per_image.json`

## 严格断点续训命令

如果 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768` 训练中途被打断，严格断点续训不要再走 `run_person_flow.py train`，而是直接对这个 run 的 `last.pt` 调用底层训练脚本：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --project-config person-train-model\person_project_config.roi_v3.mask_then_crop_margin64.json --resume backend-train-model\person-train-model\train-result\artifacts\runs\person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768\weights\last.pt
```

## 备注

- 这一版的目标是先修掉 v2 中一批 keep-positive 但又被 crop bbox 裁残的样本，同时继续压制 ROI 外可见区域。
- 当前这轮 `imgsz=768`、`batch=2` 对照训练已完成；它保持数据集、keep rule、`mask_then_crop + margin64` 和初始化来源不变，专门验证更高输入分辨率是否能继续抬 `Recall`、`mAP50`、`mAP50-95`。
- 现有结果表明：这条 `img768` 对照 run 虽然 Precision 更高，但 native test 的 Recall、mAP50、mAP75、mAP50-95 都低于当前 `640 / batch=4` 主线，也没有优于 `person_roi_aware_v2_from_fullframe`，因此它应保留为**已完成对照实验**，不应升级为默认主线。
- 当前 `roi_cropped_keep_positive_v3_margin64` 复盘已经确认：无 margin 时原本会被裁边的 `54` 个 keep-positive 框里，`margin64` 已经完整救回 `31` 个；剩余 `23` 个全部只是贴原图边界的 `0.001 px` 级残留裁边，说明 ROI crop 已不再是当前主瓶颈。
- 当前更该优先补的是 `seed=7 / seed=13` 稳定性确认和 `FP/FN` 逐图复盘；只有在 `FP/FN` 逐图复盘提示边界场景异常集中，且原图 ROI filter 复盘进一步确认存在一批 `bottom_center_inside=false`、`box_ioa` 接近 `0.25` 的边界人被过滤时，才继续做 `min_box_ioa 0.25 -> 0.20` 的单因子实验。
- `--resume` 会严格沿用 checkpoint 内保存的训练状态，因此不要再混传新的 `--imgsz`、`--batch`、`--dataset-yaml`、`--base-model`、`--run-name` 等训练参数；如果你想改这些参数，那已经不属于严格断点续训，而是新开一轮训练。
- 如果后续还要做和 `v2` 的单因子对比，优先只改一个主变量，并保持 `imgsz / batch / base-model / epochs / patience` 不变。
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
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.roi_v3.crop_only_margin64.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_crop_only_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_crop_only_margin64_from_fullframe --device 0 --workers 4 --batch 4 --imgsz 640 --epochs 180 --patience 60 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

## 评估命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.roi_v3.crop_only_margin64.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_crop_only_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_crop_only_margin64_from_fullframe --imgsz 640 --batch 4 --workers 4 --device 0
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
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py extract-roi-config --project-config backend-train-model\person-train-model\person_project_config.roi_v2.mask_then_crop_ioa25.json --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v2.generated.json --roi-mode mask_then_crop --crop-margin-px 0 --overwrite
```

再重生成独立的 v2 ROI-aware 数据集：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py prepare-roi-aware --project-config backend-train-model\person-train-model\person_project_config.roi_v2.mask_then_crop_ioa25.json --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v2.generated.json --output-root backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v2\sequence_contiguous --roi-mode mask_then_crop --crop-margin-px 0 --overwrite
```

## 训练命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.roi_v2.mask_then_crop_ioa25.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v2\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v2_from_fullframe --device 0 --workers 4 --batch 4 --imgsz 640 --epochs 180 --patience 60 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

## 评估命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.roi_v2.mask_then_crop_ioa25.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v2\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v2_from_fullframe --imgsz 640 --batch 4 --workers 4 --device 0
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

- 当前不建议直接在现有 `person_project_config.json` 默认配置上原地重生成 v1；如需严格复现，请改用 `backend-train-model/person-train-model/person_project_config.roi_v1.center_inside.json`。
- 原因是当前项目默认 keep rule 已经切到 v2；如果要严格重建 v1，应单独准备 v1 配置入口或保留专门的 v1 ROI 配置文件，再输出到独立目录。
- 因此，当前更推荐把仓库里现有 `person_roi_aware` 目录作为冻结的历史对照数据集使用。

## 训练命令

如果只是做当前 v1 / v2 / v3 的公平对照，优先使用 `from_fullframe` 初始化：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.roi_v1.center_inside.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v1_from_fullframe --device 0 --workers 4 --batch 4 --imgsz 640 --epochs 180 --patience 60 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

## 评估命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.roi_v1.center_inside.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v1_from_fullframe --imgsz 640 --batch 4 --workers 4 --device 0
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
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py prepare --project-config backend-train-model\person-train-model\person_project_config.json --overwrite
```

## 训练命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe\sequence_contiguous\dataset.yaml --run-name person_fullframe_baseline --device 0 --workers 4 --batch 4 --imgsz 640 --epochs 180 --patience 40 --base-model backend-train-model\weights\yolov8n.pt
```

如果训练机显存或稳定性有压力，可先用更保守的 batch：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe\sequence_contiguous\dataset.yaml --run-name person_fullframe_baseline_batch2 --device 0 --workers 4 --batch 2 --imgsz 640 --epochs 180 --patience 40 --base-model backend-train-model\weights\yolov8n.pt
```

## 评估命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_fullframe\sequence_contiguous\dataset.yaml --run-name person_fullframe_baseline --imgsz 640 --batch 4 --workers 4 --device 0
```

## 备注

- 如果训练中断，续训仍建议直接调用 `backend-train-model\train_workwear.py` 的 `--resume`，不要在 wrapper 里混传新的训练参数。
- 如需导出 alias，可执行：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py export --overwrite
```

- 导出后 alias 位置：
  - `backend-train-model/person-train-model/train-result/export/person_detect_yolov8.pt`

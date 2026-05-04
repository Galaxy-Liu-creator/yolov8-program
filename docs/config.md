# 训练配置总览

本文档只汇总当前仓库中 `backend-train-model/` 训练主线的正式配置入口、当前主线分支与关键训练参数。

目标不是复述所有历史实验细节，而是回答下面 4 个问题：

1. 现在该信哪个配置入口；
2. 哪些入口是当前正式主线，哪些只是历史/兼容保留；
3. 每条训练分支默认使用什么参数；
4. 哪些组合最容易配错。

---

## 1. 权威来源层级

### 1.1 clothes

当前 clothes 线不要只看 `backend-train-model/project_config.json`。

推荐按下面顺序理解：

1. 当前 baseline 选择结果：
   - `backend-train-model/All-train-model/00_CURRENT_BASELINE/current_clothes_fullframe_baseline.json`
   - `backend-train-model/All-train-model/00_CURRENT_BASELINE/README.md`
2. merged 公共训练配置：
   - `backend-train-model/All-train-model/merged_train_project_config.json`
3. merged 数据集 build / split 入口：
   - `backend-train-model/All-train-model/merged_clothes_v2_balanced.build.json`
   - `backend-train-model/All-train-model/first_train_holdout_v1.build.json`
   - `backend-train-model/All-train-model/unified_holdout_v1.build.json`
4. 默认单源 clothes 兼容入口：
   - `backend-train-model/project_config.json`

### 1.2 person

当前 person 线已经拆成“兼容入口 + 版本化正式入口”：

- 兼容 / 历史入口：
  - `backend-train-model/person-train-model/person_project_config.json`
- 正式 fullframe 扩样入口：
  - `backend-train-model/person-train-model/person_project_config.fullframe_with_new_labels.json`
- 正式 ROI-aware 版本化入口：
  - `backend-train-model/person-train-model/person_project_config.roi_v1.center_inside.json`
  - `backend-train-model/person-train-model/person_project_config.roi_v2.mask_then_crop_ioa25.json`
  - `backend-train-model/person-train-model/person_project_config.roi_v3.mask_then_crop_margin64.json`
  - `backend-train-model/person-train-model/person_project_config.roi_v3.crop_only_margin64.json`

另外，ROI-aware 线的“产物事实”以这些文件为准：

- `backend-train-model/person-train-model/train-result/working/roi/*.generated.json`
- `backend-train-model/person-train-model/train-result/prepared/*/prepare_report.json`
- `backend-train-model/person-train-model/train-result/prepared/*/dataset.yaml`

---

## 2. 当前正式主线

| 方向 | 当前正式主线 | 主要入口 |
| --- | --- | --- |
| clothes | `clothes_merged_v2_balanced_from_first_holdout_v1` | `00_CURRENT_BASELINE/current_clothes_fullframe_baseline.json` |
| person fullframe | `person_fullframe_with_new_labels_baseline` | `person_project_config.fullframe_with_new_labels.json` |
| person ROI-aware | `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` | `person_project_config.roi_v3.mask_then_crop_margin64.json` |

当前只作为对照 / 历史保留，不建议默认切换为主线的分支：

- `person_roi_aware_v3_crop_only_margin64_from_fullframe`
- `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768`
- `person_roi_aware_v2_from_fullframe`
- `person_roi_aware_v1_from_fullframe`
- `backend-train-model/project_config.json` 对应的单源 clothes 默认入口
- `backend-train-model/All-train-model/merged_clothes_v1.build.json`
- `backend-train-model/All-train-model/merged_clothes_v2.build.json`

---

## 3. clothes 配置入口矩阵

| 文件 | 定位 | 是否当前主线 | 关键内容 |
| --- | --- | --- | --- |
| `backend-train-model/project_config.json` | 单源 clothes 兼容入口 | 否 | `sequence_contiguous`，`imgsz=640`，`batch=4`，`epochs=180`，`patience=40`，`workers=4`，`device=0` |
| `backend-train-model/All-train-model/merged_train_project_config.json` | merged clothes 公共训练参数 | 是 | `imgsz=640`，`batch=4`，`epochs=180`，`patience=40`，`workers=4`，`device=0` |
| `backend-train-model/All-train-model/merged_clothes_v2_balanced.build.json` | 当前 train/val build 入口 | 是 | `split_manifest_csv=splits/trainval_balanced_v1.split.csv` |
| `backend-train-model/All-train-model/first_train_holdout_v1.build.json` | first-train / holdout 历史上游入口 | 部分相关 | 当前 baseline 路线中的上游参考 |
| `backend-train-model/All-train-model/unified_holdout_v1.build.json` | 当前统一 test holdout 入口 | 是 | `split_manifest_csv=splits/unified_holdout_v1.split.csv` |
| `backend-train-model/All-train-model/00_CURRENT_BASELINE/current_clothes_fullframe_baseline.json` | 当前 baseline 选择结果 | 是 | 记录 selected run、weight、eval report、rollback candidate |

### 3.1 clothes 当前 baseline 关键信息

- selected run：`clothes_merged_v2_balanced_from_first_holdout_v1`
- baseline weight：`backend-train-model/All-train-model/artifacts/runs/clothes_merged_v2_balanced_from_first_holdout_v1/weights/best.pt`
- comparison dataset：`backend-train-model/All-train-model/datasets/unified_holdout_v1/dataset.yaml`
- merged 训练默认参数：
  - `imgsz=640`
  - `epochs=180`
  - `batch=4`
  - `patience=40`
  - `workers=4`
  - `device=0`
  - `seed=42`

说明：当前 clothes 基线是“baseline 选择结果 + build 配置链路”的组合，不再建议把单个 `project_config.json` 误读成完整主线入口。

---

## 4. person 配置入口矩阵

| 配置文件 | 定位 | `default_dataset_variant` | ROI 模式 | keep rule | prepared 输出 | 默认 run |
| --- | --- | --- | --- | --- | --- | --- |
| `person_project_config.json` | 兼容 / 历史入口，现仅保留 fullframe 默认入口语义 | `fullframe` | `roi.enabled=false` | 不适用 | `person_fullframe` | `person_fullframe_baseline` |
| `person_project_config.fullframe_with_new_labels.json` | 正式 fullframe 扩样入口 | `fullframe` | `roi.enabled=false` | 不适用 | `person_fullframe_with_new_labels` | `person_fullframe_with_new_labels_baseline` |
| `person_project_config.roi_v1.center_inside.json` | 历史 ROI-aware v1 对照 | `roi_aware` | `mask_then_crop` | `center_inside` | `person_roi_aware_v1` | `person_roi_aware_v1_from_fullframe` |
| `person_project_config.roi_v2.mask_then_crop_ioa25.json` | 正式 ROI-aware v2 对照入口 | `roi_aware` | `mask_then_crop` | `bottom_center_inside OR ioa>=0.25` | `person_roi_aware_v2` | `person_roi_aware_v2_from_fullframe` |
| `person_project_config.roi_v3.mask_then_crop_margin64.json` | 当前正式 ROI-aware 主线 | `roi_aware` | `mask_then_crop` | `bottom_center_inside OR ioa>=0.25` | `person_roi_aware_v3_mask_then_crop_margin64` | `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` |
| `person_project_config.roi_v3.crop_only_margin64.json` | 当前已完成对照实验入口 | `roi_aware` | `crop_only` | `bottom_center_inside OR ioa>=0.25` | `person_roi_aware_v3_crop_only_margin64` | `person_roi_aware_v3_crop_only_margin64_from_fullframe` |

补充说明：

- 对 ROI-aware 配置，`recommended_run_name` 仍保留 `person_fullframe_baseline`，用于同一份 source data 的 fullframe fallback 语义。
- wrapper 在 `default_dataset_variant=roi_aware` 时，实际优先使用 `roi_aware_recommended_run_name`，因此正常 ROI-aware 训练 / 评估不会误落到 fullframe run 名。

---

## 5. person 各分支关键训练参数

下表只保留当前最常用、最有复现价值的 canonical 参数。

| 分支 | `project-config` | `dataset-yaml` | `run-name` | `base-model / init` | `imgsz` | `batch` | `epochs` | `patience` | `workers` | `device` | `seed` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| person fullframe baseline | `person_project_config.json` | `train-result/prepared/person_fullframe/sequence_contiguous/dataset.yaml` | `person_fullframe_baseline` | `backend-train-model/weights/yolov8n.pt` | 640 | 4 | 180 | 40 | 4 | 0 | 42 |
| person fullframe with new labels | `person_project_config.fullframe_with_new_labels.json` | `train-result/prepared/person_fullframe_with_new_labels/sequence_contiguous/dataset.yaml` | `person_fullframe_with_new_labels_baseline` | `backend-train-model/weights/yolov8n.pt` | 640 | 4 | 180 | 40 | 4 | 0 | 42 |
| person fullframe with new labels img768 对照 | `person_project_config.fullframe_with_new_labels.json` | 同上 | `person_fullframe_with_new_labels_img768` | `backend-train-model/weights/yolov8n.pt` | 768 | 4 | 180 | 40 | 4 | 0 | 42 |
| ROI-aware v1 对照 | `person_project_config.roi_v1.center_inside.json` | `train-result/prepared/person_roi_aware_v1/sequence_contiguous/dataset.yaml` | `person_roi_aware_v1_from_fullframe` | `person_fullframe_baseline/weights/best.pt` | 640 | 4 | 180 | 60 | 4 | 0 | 42 |
| ROI-aware v2 | `person_project_config.roi_v2.mask_then_crop_ioa25.json` | `train-result/prepared/person_roi_aware_v2/sequence_contiguous/dataset.yaml` | `person_roi_aware_v2_from_fullframe` | `person_fullframe_baseline/weights/best.pt` | 640 | 4 | 180 | 60 | 4 | 0 | 42 |
| ROI-aware v3 mask 主线 | `person_project_config.roi_v3.mask_then_crop_margin64.json` | `train-result/prepared/person_roi_aware_v3_mask_then_crop_margin64/sequence_contiguous/dataset.yaml` | `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` | `person_fullframe_baseline/weights/best.pt` | 640 | 4 | 180 | 60 | 4 | 0 | 42 |
| ROI-aware v3 mask img768 对照 | `person_project_config.roi_v3.mask_then_crop_margin64.json` | 同上 | `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768` | `person_fullframe_baseline/weights/best.pt` | 768 | 2 | 180 | 60 | 4 | 0 | 42 |
| ROI-aware v3 crop-only 对照 | `person_project_config.roi_v3.crop_only_margin64.json` | `train-result/prepared/person_roi_aware_v3_crop_only_margin64/sequence_contiguous/dataset.yaml` | `person_roi_aware_v3_crop_only_margin64_from_fullframe` | `person_fullframe_baseline/weights/best.pt` | 640 | 4 | 180 | 60 | 4 | 0 | 42 |

补充说明：

- `person_project_config.json` 现在明确只保留 fullframe 兼容入口；如果直接拿它去跑 `prepare-roi-aware`，会因为 `roi.enabled=false` 早停报错，这正是为了避免再把兼容 config 误当成 ROI-aware 正式入口。
- `run_person_flow.py` 现在会根据 `project-config` 中的 `default_dataset_variant` 与 `training.default_train_args` 自动选择默认 `dataset.yaml`、`run-name`、训练参数，以及默认 `base_model / init_weights`；但正式实验仍建议显式传参。
- `prepare-roi-aware` 现在也支持显式传 `--split-strategy`，因此 ROI-aware 数据集的切分策略不必再通过改 JSON 临时覆盖。
- `analyze_person_fpfn.py`、overlay、review 等分析脚本可以继续按 CPU 口径运行；训练/评估命令默认按 GPU 口径记录。

---

## 6. 常见错配风险

### 6.1 旧兼容 config + 新版本化 ROI dataset

不推荐：

- `person_project_config.json`
- 配 `person_roi_aware_v3_mask_then_crop_margin64/.../dataset.yaml`

虽然现在 guard 已经更严格，但仍建议直接改用对应版本化 config。

### 6.2 训练 / 评估时省略 `--project-config`

如果省略，wrapper 会默认回到兼容入口：

- `backend-train-model/person-train-model/person_project_config.json`

这对 fullframe 兼容还可用，但对 ROI-aware 路径现在会更早失败，目的是强制切回对应版本化 config，避免继续产生元数据混乱。

### 6.3 把 CPU 分析命令误当成默认训练口径

当前默认训练口径是：

- `--device 0`
- `--workers 4`

CPU / `workers=0` 只保留给：

- 本机分析
- 调试
- DataLoader 稳定性回退

### 6.4 把 `backend-train-model/project_config.json` 误当成 clothes 当前主线

它只是单源 clothes 兼容入口。

当前 clothes 正式主线仍应从下面这组文件理解：

- `All-train-model/00_CURRENT_BASELINE/current_clothes_fullframe_baseline.json`
- `All-train-model/00_CURRENT_BASELINE/README.md`
- `All-train-model/merged_train_project_config.json`
- `All-train-model/*.build.json`

---

## 7. 建议使用方式

### 7.1 复现当前 person ROI-aware 主线

最稳组合：

- `project-config`: `backend-train-model/person-train-model/person_project_config.roi_v3.mask_then_crop_margin64.json`
- `dataset-yaml`: `backend-train-model/person-train-model/train-result/prepared/person_roi_aware_v3_mask_then_crop_margin64/sequence_contiguous/dataset.yaml`
- `run-name`: `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe`

### 7.2 复现当前 fullframe 扩样主线

- `project-config`: `backend-train-model/person-train-model/person_project_config.fullframe_with_new_labels.json`
- `dataset-yaml`: `backend-train-model/person-train-model/train-result/prepared/person_fullframe_with_new_labels/sequence_contiguous/dataset.yaml`
- `run-name`: `person_fullframe_with_new_labels_baseline`

### 7.3 追踪当前 clothes baseline

- 先看：`backend-train-model/All-train-model/00_CURRENT_BASELINE/current_clothes_fullframe_baseline.json`
- 再看：`backend-train-model/All-train-model/00_CURRENT_BASELINE/README.md`
- 训练默认参数看：`backend-train-model/All-train-model/merged_train_project_config.json`

---

## 8. 本文不覆盖的内容

本文不展开这些内容：

- 每一轮历史 report 的逐项指标解释；
- 线上 `inspection-flask/` 阈值与时序规则；
- `otherMonitor/` 里的历史实验参数；
- 所有 resume / 临时 smoke test 命令。

这些内容请分别查阅对应目录下文档。

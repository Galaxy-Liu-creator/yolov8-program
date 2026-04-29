# ROI-aware person 下一轮迭代执行计划

本文档承接 `2026-04-28` 这轮 ROI-aware person 训练后的后续动作。这里记录的不是“凭感觉继续堆训练”，而是**基于已经完成的 ROI 裁边复盘和首轮 FP/FN 复盘**，把下一步优先级重新排清楚。

## 1. 当前判断

- 当前默认主线仍是 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe`。
- 该 run 的 native test 指标为：
  - Precision `0.9208`
  - Recall `0.7075`
  - mAP50 `0.7779`
  - mAP75 `0.4578`
  - mAP50-95 `0.4607`
- 它相对 `person_fullframe_baseline` 确实有提升，但相对 `person_roi_aware_v2_from_fullframe` 只体现为**很小的 native test 优势**。
- `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768` 已完成对照；虽然 Precision 提到 `0.9663`，但 Recall 降到 `0.6435`，mAP50-95 降到 `0.4399`，说明继续放大 `imgsz` 不是当前最优先的方向。

因此这轮更准确的结论是：

1. `ROI-aware v3 mask_then_crop + margin64` 方向没有走偏，但当前主瓶颈已经不再像是“再加一点 crop margin”或“继续放大输入尺寸”。
2. 下一步更该先确认两件事：
   - 当前 `v3` 相对 `v2` 的小幅领先到底稳不稳定。
   - 当前漏检到底集中在哪些具体场景和序列。
3. 只有当人工复盘明确指向 ROI 边界仍在漏人时，才应该把 `min_box_ioa 0.25 -> 0.20` 提升为下一条正式实验。

## 2. 已完成复盘结论

### 2.1 ROI 裁边复盘已经基本排除“crop 仍是主问题”

已执行命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\review_roi_cropped_keep_boxes.py --project-config backend-train-model\person-train-model\person_project_config.json --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v3.mask_then_crop_margin64.generated.json --output-root backend-train-model\person-train-model\train-result\review\roi_cropped_keep_positive_v3_margin64 --margin-px 64 --overwrite
```

当前结论：

- 共扫描 `502` 张图。
- 如果没有 margin，原本会有 `54` 个 keep-positive 框被 crop。
- `margin64` 已完整救回其中 `31` 个。
- 剩余 `23` 个“仍然裁边”的样本并不是新的主要 ROI 瓶颈：
  - `20` 个是贴原图下边界；
  - `3` 个是贴原图右边界；
  - 全部都只是 `0.001 px` 级别的浮点残留裁边；
  - margin crop 已经顶到原图边界，继续加 margin 也不会再有实质收益。

重点输出目录：

- `backend-train-model/person-train-model/train-result/review/roi_cropped_keep_positive_v3_margin64/`
- `backend-train-model/person-train-model/train-result/review/roi_cropped_keep_positive_v3_margin64/cropped_keep_positive_summary.md`
- `backend-train-model/person-train-model/train-result/review/roi_cropped_keep_positive_v3_margin64/cropped_keep_positive_summary.json`

这一步的实际意义是：**ROI crop 问题已经基本处理到头了，当前不应再把“继续加 margin”放在首位。**

### 2.2 当前主线 test split 的逐图 FP/FN 复盘已经落地

已新增脚本：

- `backend-train-model/person-train-model/train-code/analyze_person_fpfn.py`

已执行命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\analyze_person_fpfn.py --eval-report backend-train-model\person-train-model\train-result\artifacts\reports\person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_eval.json --split test --conf-threshold 0.25 --nms-iou 0.7 --match-iou 0.5 --device cpu --output-root backend-train-model\person-train-model\train-result\review\person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_fpfn_test_conf025 --overwrite
```

当前汇总结果：

- images: `75`
- gt_boxes: `115`
- pred_boxes: `87`
- tp: `80`
- fp: `7`
- fn: `35`
- precision: `0.919540`
- recall: `0.695652`

当前误差最集中的序列：

- `D15_20260119061405`：`tp 21 / fp 6 / fn 13`
- `D15_20260119203927`：`tp 7 / fp 0 / fn 11`
- `D02_20260123074836`：`tp 8 / fp 0 / fn 5`
- `D02_20260123070624`：`tp 15 / fp 0 / fn 4`

当前最值得优先人工回看的 FN 帧：

- `images/test/D02_20260123074836_frame_0023.jpg`
- `images/test/D02_20260123074836_frame_0024.jpg`
- `images/test/D15_20260119061405_frame_0346.jpg`
- `images/test/D15_20260119203927_frame_0162.jpg` 到 `images/test/D15_20260119203927_frame_0173.jpg`

重点输出目录：

- `backend-train-model/person-train-model/train-result/review/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_fpfn_test_conf025/`
- `backend-train-model/person-train-model/train-result/review/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_fpfn_test_conf025/fpfn_summary.md`
- `backend-train-model/person-train-model/train-result/review/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_fpfn_test_conf025/fpfn_per_image.json`

这一步带来的判断变化是：**当前瓶颈更像是“难序列 / 难样本 / 训练稳定性”，而不是 ROI crop margin 本身。**

## 3. 下一步执行顺序

当前更稳妥的顺序应写成：

1. 先补 `seed=7`、`seed=13`，确认当前 `v3` 相对 `v2` 的提升不是偶然波动。
2. 结合 `fpfn_summary.md` 与 `fpfn_per_image.json`，把 hardest sequences 做人工 FN 分桶复盘。
3. 只有当逐图 `FN` 复盘提示边界场景异常集中，且原图 ROI filter 复盘进一步确认存在一批 `bottom_center_inside=false`、`box_ioa` 接近 `0.25` 的边界人被过滤时，才启动 `min_box_ioa 0.25 -> 0.20` 的单因子实验。
4. 如果 FN 主要集中在远处小人、遮挡、半身、背光，而不是 ROI 边界问题，就优先补难样本，而不是继续调 keep rule。

## 4. 可直接执行的命令

### 4.1 Seed 7

训练：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed7 --device cpu --workers 0 --batch 4 --imgsz 640 --epochs 180 --patience 60 --seed 7 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

评估：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed7 --report-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed7_eval --device cpu --workers 0
```

### 4.2 Seed 13

训练：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed13 --device cpu --workers 0 --batch 4 --imgsz 640 --epochs 180 --patience 60 --seed 13 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

评估：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed13 --report-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed13_eval --device cpu --workers 0
```

### 4.3 如需重跑当前主线 test 的逐图 FP/FN 复盘

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\analyze_person_fpfn.py --eval-report backend-train-model\person-train-model\train-result\artifacts\reports\person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_eval.json --split test --conf-threshold 0.25 --nms-iou 0.7 --match-iou 0.5 --device cpu --output-root backend-train-model\person-train-model\train-result\review\person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_fpfn_test_conf025 --overwrite
```

### 4.4 如需针对问题帧做 ROI overlay 抽查

这里不再泛看，而是优先盯住上面几条 hardest sequences。

命令模板：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\visualize_roi_filter_samples.py --project-config backend-train-model\person-train-model\person_project_config.json --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v3.mask_then_crop_margin64.generated.json --output-root backend-train-model\person-train-model\train-result\review\roi_filter_overlays_v3_margin64 --stem D15_20260119203927_frame_0162 --stem D15_20260119203927_frame_0164 --stem D15_20260119061405_frame_0346
```

## 5. 仅在满足条件时才做的 `ioa20` 单因子实验

### 5.1 触发条件

只有下面两点同时成立，才建议启动 `min_box_ioa 0.25 -> 0.20`：

1. 原图 ROI filter 复盘明确看到一批“肉眼看起来已经接近入区，但按代码判定 `bottom_center_inside` 仍然是 `false`，同时 `box_ioa` 又略低于 `0.25`，结果没进训练集”的边界人。
2. 这些样本在原始标注中的数量和占比足够高，并且与当前 hard sequences 的漏检场景高度重合，而不是极少数零散例外。

如果 FN 主体不是这一类，那就不要优先动 `keep_rule`。

### 5.2 实验约束

一旦开这条实验，只允许改一个主变量：

- `mask_then_crop` 不变
- `crop_margin_px=64` 不变
- `imgsz=640` 不变
- `batch=4` 不变
- `epochs=180` 不变
- `patience=60` 不变
- `base-model=person_fullframe_baseline/weights/best.pt` 不变
- 只把 `roi.keep_rule.min_box_ioa` 从 `0.25` 改到 `0.20`

### 5.3 条件实验命令

先复制一份版本化配置：

```powershell
Copy-Item backend-train-model\person-train-model\person_project_config.json backend-train-model\person-train-model\person_project_config.roi_v4_mask_then_crop_margin64_ioa20.json
```

然后只改下面这些字段：

```json
{
  "roi": {
    "mode": "mask_then_crop",
    "crop_margin_px": 64,
    "keep_rule": {
      "center_inside": false,
      "bottom_center_inside": true,
      "min_box_ioa": 0.20
    },
    "config_path": "train-result/working/roi/roi_config.v4.mask_then_crop_margin64_ioa20.generated.json"
  },
  "person_dataset": {
    "roi_aware_prepared_output_root": "train-result/prepared/person_roi_aware_v4_mask_then_crop_margin64_ioa20/sequence_contiguous",
    "roi_aware_recommended_run_name": "person_roi_aware_v4_mask_then_crop_margin64_ioa20_from_fullframe"
  }
}
```

提取 ROI 配置：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py extract-roi-config --project-config backend-train-model\person-train-model\person_project_config.roi_v4_mask_then_crop_margin64_ioa20.json --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v4.mask_then_crop_margin64_ioa20.generated.json --overwrite
```

生成 prepared 数据集：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py prepare-roi-aware --project-config backend-train-model\person-train-model\person_project_config.roi_v4_mask_then_crop_margin64_ioa20.json --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v4.mask_then_crop_margin64_ioa20.generated.json --output-root backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v4_mask_then_crop_margin64_ioa20\sequence_contiguous --overwrite
```

训练：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.roi_v4_mask_then_crop_margin64_ioa20.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v4_mask_then_crop_margin64_ioa20\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v4_mask_then_crop_margin64_ioa20_from_fullframe --device cpu --workers 0 --batch 4 --imgsz 640 --epochs 180 --patience 60 --seed 42 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

评估：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.roi_v4_mask_then_crop_margin64_ioa20.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v4_mask_then_crop_margin64_ioa20\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v4_mask_then_crop_margin64_ioa20_from_fullframe --report-name person_roi_aware_v4_mask_then_crop_margin64_ioa20_from_fullframe_eval --device cpu --workers 0
```

判定标准：

1. Recall 要有实际改善，而不是只换来 Precision 变化。
2. mAP50-95 至少不能低于当前 `v3 mask_then_crop + margin64` 主线。
3. 新引入的 ROI 外干扰人不能明显变多。

## 6. 当前暂不建议做的事

- 不继续默认把 `imgsz` 从 `640` 往上堆。
- 不把“剩余 `23` 个裁边框”继续当成主要矛盾。
- 不在没做 seed 验证前就直接宣称 `v3` 稳定领先 `v2`。
- 不把 `crop_only`、`yolov8s` 当成当前第一优先级。
- 不同时改 `keep_rule`、`imgsz`、`batch`、`base-model` 去跑混合变量实验。

当前最稳妥的重心就是两件事：

1. `seed=7 / seed=13` 稳定性验证。
2. 围绕 `D15_20260119061405`、`D15_20260119203927`、`D02_20260123074836`、`D02_20260123070624` 的人工 FN 复盘。

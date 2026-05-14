# ROI-aware person 当前阶段行动计划

本文档用于记录 **ROI-aware person 当前阶段真正优先要做什么**。

这里记录的不是早期规则设计背景，也不是把所有命令直接堆成 runbook，而是要回答下面几个问题：

1. 当前默认主线是哪一条；
2. 当前最可信的已知结论是什么；
3. 下一步到底先做什么、不先做什么；
4. 什么条件满足后，才值得启动 `ioa20` 这类条件实验。

如果你想看：

- **为什么 ROI 规则会从 `center_inside` 演进到 `bottom_center_inside OR box_ioa >= 0.25`**，优先看：
  - `backend-train-model/person-train-model/train-docs/roi_problem_solution.md`
- **hardest FN 当前人工复核双主线与 crowded / overlap 机制收口要求**，优先看：
  - `backend-train-model/person-train-model/train-docs/人工复核.md`

## 1. 当前阶段一句话结论

- 当前默认主线仍是 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe`。
- 该 run 的 native test 指标为：
  - Precision `0.9208`
  - Recall `0.7075`
  - mAP50 `0.7779`
  - mAP75 `0.4578`
  - mAP50-95 `0.4607`
- 它相对 `person_fullframe_baseline` 确实有提升，但相对 `person_roi_aware_v2_from_fullframe` 只体现为**很小的 native test 优势**。
- `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768` 已完成对照；虽然 Precision 提到 `0.9663`，但 Recall 降到 `0.6435`，mAP50-95 降到 `0.4399`，说明继续放大 `imgsz` 不是当前最优先的方向。

因此当前更准确的结论是：

1. `ROI-aware v3 mask_then_crop + margin64` 方向没有走偏，但当前主瓶颈已经不再像是“再加一点 crop margin”或“继续放大输入尺寸”。
2. 下一步更该先确认两件事：
   - 当前 `v3` 相对 `v2` 的小幅领先到底稳不稳定。
   - 当前漏检到底集中在哪些具体场景和序列。
3. 只有当人工复盘明确指向 ROI 边界仍在漏人时，才应该把 `min_box_ioa 0.25 -> 0.20` 提升为下一条正式实验。

也就是说，当前更稳妥的执行顺序是：

```text
先做 seed 稳定性确认
-> 再做 hardest FN 人工复盘深化
-> 再判断是否存在边界证据闭环
-> 只有这时才开 ioa20 单因子实验
```

## 2. 已完成复盘结论

### 2.1 ROI 裁边复盘已经基本排除“crop 仍是主问题”

已执行命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\review_roi_cropped_keep_boxes.py --project-config backend-train-model\person-train-model\person_project_config.roi_v3.mask_then_crop_margin64.json --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v3.mask_then_crop_margin64.generated.json --output-root backend-train-model\person-train-model\train-result\review\roi_cropped_keep_positive_v3_margin64 --margin-px 64 --overwrite
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

### 2.3 当前 hardest FN 的人工复核已经把主问题重新分流

结合 `人工复核.md` 当前 `5.7` 阶段口径，当前更稳的判断是：

- hardest FN 已经至少拆成两条主线：
  1. `D15_20260119061405` 代表的“可见性弱型”；
  2. `D15_20260119203927 + D05_20260123074841` 代表的“crowded / overlap 型”。
- `D02_20260123070624` 与 `D02_20260123074836` 继续保留为远景 / 贴边对照序列；
- 当前证据仍不足以支持把 `small_boundary_person` 升级为整体主矛盾。

这意味着：

> 当前不能因为 ROI-aware 线存在边界规则，就默认把 `keep_rule` 当成 hardest FN 的第一解释；仍应先尊重人工复核给出的真实主线结构。

## 3. 下一步执行顺序

当前更稳妥的顺序应写成：

1. 先补 `seed=7`、`seed=13`，确认当前 `v3` 相对 `v2` 的提升不是偶然波动。
2. 结合 `fpfn_summary.md` 与 `fpfn_per_image.json`，把 hardest sequences 做人工 FN 分桶复盘。
3. 只有当逐图 `FN` 复盘提示边界场景异常集中，且原图 ROI filter 复盘进一步确认存在一批 `bottom_center_inside=false`、`box_ioa` 接近 `0.25` 的边界人被过滤时，才启动 `min_box_ioa 0.25 -> 0.20` 的单因子实验。
4. 如果 FN 主体最后仍然更偏可见性弱型或 crowded / overlap 型，而不是 ROI 边界问题，就优先补难样本与继续做机制复盘，而不是继续调 keep rule。

## 4. 当前明确不优先做什么

### 4.1 不优先继续加 crop margin

原因不是“margin 没有用”，而是：

- `margin64` 的有效收益已经拿到；
- 剩余裁边几乎都是贴原图边界的残留；
- 继续加 margin 很难再带来实质改观。

### 4.2 不优先继续放大 `imgsz`

当前 `img768` 对照已经完成，而且结果不支持把它升级为主线。

### 4.3 不优先直接切 `yolov8s`

当前优先策略不是直接换更大模型，而是先搞清楚：

- 当前主误差结构到底是什么；
- 当前主线的小幅领先到底稳不稳。

### 4.4 不优先把 `keep_rule` 当成头号调参对象

当前这套 `keep_rule`：

- `center_inside = false`
- `bottom_center_inside = true`
- `min_box_ioa = 0.25`

仍然应视为**当前有效基线**。

但“它是当前有效基线”并不等于“当前应继续优先围绕它调参”。

在没有边界证据闭环前，不建议默认把 hardest FN 归因到它身上。

## 5. 附录：可直接执行的命令

本节只保留**当前仍有直接执行价值**的命令模板。

这些命令不是在说“全部都要立刻跑”，而是当你已经完成上面的优先级判断后，可以直接使用的附录入口。

### 5.1 Seed 7

训练：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.roi_v3.mask_then_crop_margin64.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed7 --device 0 --workers 4 --batch 4 --imgsz 640 --epochs 180 --patience 60 --seed 7 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

评估：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.roi_v3.mask_then_crop_margin64.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed7 --report-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed7_eval --imgsz 640 --batch 4 --workers 4 --device 0
```

### 5.2 Seed 13

训练：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.roi_v3.mask_then_crop_margin64.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed13 --device 0 --workers 4 --batch 4 --imgsz 640 --epochs 180 --patience 60 --seed 13 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

评估：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.roi_v3.mask_then_crop_margin64.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v3_mask_then_crop_margin64\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed13 --report-name person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed13_eval --imgsz 640 --batch 4 --workers 4 --device 0
```

### 5.3 如需重跑当前主线 test 的逐图 FP/FN 复盘

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\analyze_person_fpfn.py --eval-report backend-train-model\person-train-model\train-result\artifacts\reports\person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_eval.json --split test --conf-threshold 0.25 --nms-iou 0.7 --match-iou 0.5 --device cpu --output-root backend-train-model\person-train-model\train-result\review\person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_fpfn_test_conf025 --overwrite
```

### 5.4 如需针对问题帧做 ROI overlay 抽查

这里不再泛看，而是优先盯住上面几条 hardest sequences。

命令模板：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\visualize_roi_filter_samples.py --project-config backend-train-model\person-train-model\person_project_config.roi_v3.mask_then_crop_margin64.json --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v3.mask_then_crop_margin64.generated.json --output-root backend-train-model\person-train-model\train-result\review\roi_filter_overlays_v3_margin64 --stem D15_20260119203927_frame_0162 --stem D15_20260119203927_frame_0164 --stem D15_20260119061405_frame_0346
```

## 6. 仅在满足条件时才做的 `ioa20` 单因子实验

### 6.1 触发条件

只有下面两层证据都成立，才建议启动 `min_box_ioa 0.25 -> 0.20`：

1. **逐图 FN 人工复盘**明确提示：边界场景异常集中，而且这些边界人不是零散个例。
2. **原图 ROI filter 复盘**进一步确认：
   - 这批人肉眼看起来已经接近入区；
   - `bottom_center_inside = false`；
   - `box_ioa` 只是略低于 `0.25`；
   - 结果被当前规则挡在训练集外。

如果 FN 主体不是这一类，那就不要优先动 `keep_rule`。

### 6.2 实验约束

一旦开这条实验，只允许改一个主变量：

- `mask_then_crop` 不变
- `crop_margin_px=64` 不变
- `imgsz=640` 不变
- `batch=4` 不变
- `epochs=180` 不变
- `patience=60` 不变
- `base-model=person_fullframe_baseline/weights/best.pt` 不变
- 只把 `roi.keep_rule.min_box_ioa` 从 `0.25` 改到 `0.20`

### 6.3 条件实验命令

只有当第 `6.1` 节的触发条件已经满足时，再执行下面这些步骤。

先复制一份版本化配置：

```powershell
Copy-Item backend-train-model\person-train-model\person_project_config.roi_v3.mask_then_crop_margin64.json backend-train-model\person-train-model\person_project_config.roi_v4_mask_then_crop_margin64_ioa20.json
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
    "default_dataset_variant": "roi_aware",
    "roi_aware_prepared_output_root": "train-result/prepared/person_roi_aware_v4_mask_then_crop_margin64_ioa20/sequence_contiguous",
    "roi_aware_recommended_run_name": "person_roi_aware_v4_mask_then_crop_margin64_ioa20_from_fullframe",
    "export_alias_path": "train-result/export/person_detect_yolov8_roi_v4_mask_then_crop_margin64_ioa20.pt",
    "export_alias_metadata_path": "train-result/export/person_detect_yolov8_roi_v4_mask_then_crop_margin64_ioa20.metadata.json"
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
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.roi_v4_mask_then_crop_margin64_ioa20.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v4_mask_then_crop_margin64_ioa20\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v4_mask_then_crop_margin64_ioa20_from_fullframe --device 0 --workers 4 --batch 4 --imgsz 640 --epochs 180 --patience 60 --seed 42 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

评估：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.roi_v4_mask_then_crop_margin64_ioa20.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v4_mask_then_crop_margin64_ioa20\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v4_mask_then_crop_margin64_ioa20_from_fullframe --report-name person_roi_aware_v4_mask_then_crop_margin64_ioa20_from_fullframe_eval --imgsz 640 --batch 4 --workers 4 --device 0
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

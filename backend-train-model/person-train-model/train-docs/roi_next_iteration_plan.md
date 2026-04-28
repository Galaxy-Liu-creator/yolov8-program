# ROI-aware person 下一轮迭代执行计划

本文档用于承接 `2026-04-28` 这轮 ROI-aware person 训练完成后的下一步动作，目标不是继续“盲加训练”，而是先把**当前瓶颈到底在数据、ROI keep rule，还是训练波动**这三件事拆开。

## 1. 当前判断

- 当前默认主线仍是 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe`。
- 该 run 的 native test 指标为：
  - Precision `0.9208`
  - Recall `0.7075`
  - mAP50 `0.7779`
  - mAP75 `0.4578`
  - mAP50-95 `0.4607`
- 它相比 `person_fullframe_baseline` 是有提升的，但相比 `person_roi_aware_v2_from_fullframe` 只体现为**很小的 test 优势**。
- `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768` 已完成对照，Precision 提到 `0.9663`，但 Recall 降到 `0.6435`，mAP50-95 降到 `0.4399`。

因此当前更准确的结论是：

1. ROI-aware v3 方向没有走错，但这轮提升还不够理想。
2. 当前瓶颈已经不再像是“把 `imgsz` 继续放大”就能解决的问题。
3. 下一步优先级应该从“再堆训练参数”切回“先找漏检来源 + 做单因子受控实验”。

## 2. 下一轮执行原则

下一轮统一按下面的约束执行：

1. **先复盘，再开新训练。**
2. 每次新训练只改一个主因素，不要同时改 `keep_rule`、`imgsz`、`batch`、`base_model`。
3. 在专门做种子稳定性验证之前，默认固定：
   - `mask_then_crop`
   - `crop_margin_px=64`
   - `imgsz=640`
   - `batch=4`
   - `epochs=180`
   - `patience=60`
   - `base-model=person_fullframe_baseline/weights/best.pt`
4. 在确认当前主线是否真的稳定优于 `v2` 之前，**不要**把 `0.005 ~ 0.02` 量级的小差距直接写成“明显领先”。

## 3. 第一阶段：先做复盘，不启动新训练

### 3.1 复查 ROI 边界 keep-positive 但仍被 crop 过的样本

目的：

- 先确认当前 `mask_then_crop + margin64` 虽然把 `cropped_boxes` 从 `54` 压到 `23`，但剩下这批样本到底长什么样。
- 如果剩余问题集中在 ROI 边缘、半身入区、远处小人，那么下一步应优先动 `keep_rule` 或补难样本，而不是继续加大输入尺寸。

命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\review_roi_cropped_keep_boxes.py --project-config backend-train-model\person-train-model\person_project_config.json --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v3.mask_then_crop_margin64.generated.json --output-root backend-train-model\person-train-model\train-result\review\roi_cropped_keep_positive_v3_margin64 --margin-px 64 --overwrite
```

重点看这些输出：

- `backend-train-model/person-train-model/train-result/review/roi_cropped_keep_positive_v3_margin64/cropped_keep_positive_summary.md`
- `backend-train-model/person-train-model/train-result/review/roi_cropped_keep_positive_v3_margin64/cropped_keep_positive_summary.json`
- `backend-train-model/person-train-model/train-result/review/roi_cropped_keep_positive_v3_margin64/overlays/`
- `backend-train-model/person-train-model/train-result/review/roi_cropped_keep_positive_v3_margin64/current_mask_crops/`
- `backend-train-model/person-train-model/train-result/review/roi_cropped_keep_positive_v3_margin64/margin64_mask_crops/`

本阶段要回答的问题：

- 剩余 `23` 个裁边框里，是否大部分都属于**边界进入人**而不是随机噪声。
- `margin64` 没救回来的样本，是因为 ROI polygon 本身太紧，还是 keep rule 仍然保守。
- 是否出现“明明脚点已入区，但由于 `box_ioa >= 0.25` 仍然不够而被丢掉”的情况。

### 3.2 对问题帧做 ROI filter overlay 可视化

目的：

- 把 ROI polygon、原始 person 框、keep/drop 原因直接叠图看掉。
- 这一轮优先盯 `cropped_keep_positive_summary.md` 里最靠前的样本，不要泛看。

命令模板：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\visualize_roi_filter_samples.py --project-config backend-train-model\person-train-model\person_project_config.json --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v3.mask_then_crop_margin64.generated.json --output-root backend-train-model\person-train-model\train-result\review\roi_filter_overlays_v3_margin64 --stem D15_20260119203927_frame_0181 --stem D15_20260119203927_frame_0182
```

补充说明：

- `--stem` 建议替换成上一步 summary 里真正排在前面的样本 stem。
- 输出清单在：
  - `backend-train-model/person-train-model/train-result/review/roi_filter_overlays_v3_margin64/roi_filter_overlay_manifest.json`
  - `backend-train-model/person-train-model/train-result/review/roi_filter_overlays_v3_margin64/*.jpg`

### 3.3 做一轮人工 FN 桶化，不急着先开新实验

这一轮至少把当前主线 run 的明显漏检按下面几类手工分桶：

- `small_far`：远处小人、框面积明显偏小。
- `roi_boundary`：人已部分进入 ROI，但边界样本不稳定。
- `occlusion`：人被车辆、设备、立柱遮挡。
- `truncation`：人只露上半身 / 下半身。
- `dense_overlap`：多人重叠或站位过近。
- `blur_backlight`：运动模糊、背光、低照度。
- `label_issue`：原标注本身就有歧义或漏标。

这一阶段不要求先写新脚本，先把最主要的漏检类型统计出来。否则下一轮训练还是在撞运气。

## 4. 第二阶段：先验证当前主线是否稳定，不急着宣称领先 v2

当前 `v3` 相比 `v2` 的 test 提升太小，先补两组 seed 对照更稳妥。

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

### 4.3 这一阶段的判断标准

- 如果三组 seed 的波动幅度已经和 `v2 -> v3` 的提升同量级，那当前就不应写成“v3 稳定领先 v2”。
- 如果三组 seed 都能稳定保持：
  - Recall 不低于当前主线太多；
  - mAP50-95 平均值仍高于 `v2`；
  - test 表现排序基本一致；
  那才说明当前 `v3` 不是偶然跑出来的。

## 5. 第三阶段：只做一个 keep rule 单因子实验

### 5.1 当前最值得先试的受控变量

下一轮最推荐先试：

- `mask_then_crop + crop_margin_px=64` 不变；
- `base-model` 不变；
- `imgsz=640 / batch=4 / epochs=180 / patience=60` 不变；
- 只把 `roi.keep_rule.min_box_ioa` 从 `0.25` 小幅放松到 `0.20`。

原因：

- 当前 `margin64` 已经证明对缓解裁边有效，所以不应先把它撤掉。
- `img768` 已经说明继续放大输入尺寸不解决核心问题。
- 如果复盘后确认仍有一部分“脚点已入区但 box_ioa 略低于 0.25”的边界人被挡在训练集外，那么 `0.20` 是比 `any overlap` 更克制的松绑方式。

### 5.2 先复制一份版本化 project config

先复制当前配置：

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

只做这一个单因子改动，不要顺手再改 `imgsz`、`batch`、`patience` 或初始化来源。

### 5.3 生成版本化 ROI 配置与 prepared 数据集

提取 ROI 配置：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py extract-roi-config --project-config backend-train-model\person-train-model\person_project_config.roi_v4_mask_then_crop_margin64_ioa20.json --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v4.mask_then_crop_margin64_ioa20.generated.json --overwrite
```

生成版本化 prepared 数据集：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py prepare-roi-aware --project-config backend-train-model\person-train-model\person_project_config.roi_v4_mask_then_crop_margin64_ioa20.json --roi-config backend-train-model\person-train-model\train-result\working\roi\roi_config.v4.mask_then_crop_margin64_ioa20.generated.json --output-root backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v4_mask_then_crop_margin64_ioa20\sequence_contiguous --overwrite
```

### 5.4 训练与评估命令

训练：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py train --project-config backend-train-model\person-train-model\person_project_config.roi_v4_mask_then_crop_margin64_ioa20.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v4_mask_then_crop_margin64_ioa20\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v4_mask_then_crop_margin64_ioa20_from_fullframe --device cpu --workers 0 --batch 4 --imgsz 640 --epochs 180 --patience 60 --seed 42 --base-model backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_baseline\weights\best.pt
```

评估：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py evaluate --project-config backend-train-model\person-train-model\person_project_config.roi_v4_mask_then_crop_margin64_ioa20.json --dataset-yaml backend-train-model\person-train-model\train-result\prepared\person_roi_aware_v4_mask_then_crop_margin64_ioa20\sequence_contiguous\dataset.yaml --run-name person_roi_aware_v4_mask_then_crop_margin64_ioa20_from_fullframe --report-name person_roi_aware_v4_mask_then_crop_margin64_ioa20_from_fullframe_eval --device cpu --workers 0
```

### 5.5 这轮 keep rule 实验的判定标准

如果下面三点同时满足，才说明 `ioa=0.20` 值得继续：

1. Recall 有实际提升，不只是 Precision 变化。
2. mAP50-95 至少不低于当前 `v3 mask_then_crop + margin64` 主线。
3. 复盘后发现新引入的 ROI 外干扰人没有明显变多。

如果只是 Recall 涨一点，但 mAP50-95 掉回去，或者引入了更多 ROI 外人，那就不应继续把规则放松。

## 6. 第四阶段：如果 FN 主要集中在小人 / 遮挡，再优先补数据

如果人工 FN 桶化之后发现漏检主要来自：

- 远处小人；
- 只露半身的人；
- 车辆或设备遮挡下的人；
- ROI 边缘的入区人；

那下一步更该做的是**补难样本**，而不是继续堆训练参数。

建议做法：

1. 从已有序列里优先补 `30 ~ 60` 张这类困难帧。
2. 保持类别定义不变，只补 `person`。
3. 补完后优先重跑：
   - `person_fullframe_baseline`
   - 当前最佳 ROI-aware 主线，或上面这个 `ioa20` 版本

训练命令直接复用：

- `backend-train-model/person-train-model/train-docs/person_run_method.md` 中 `person_fullframe`
- `backend-train-model/person-train-model/train-docs/person_run_method.md` 中 `person_roi_aware_v3_mask_then_crop_margin64`

## 7. 当前暂不建议做的事

- 不继续默认把 `imgsz` 从 `640` 往上堆。
- 不在没做 seed 验证前就直接宣称 `v3` 稳定领先 `v2`。
- 不把 `yolov8s` 当成当前第一优先级。
- 不同时改 `keep_rule`、`imgsz`、`batch`、`base-model` 去跑“混合变量实验”。

当前更稳妥的顺序应写成：

1. 先做 ROI 边界 / FN 复盘。
2. 再做当前主线的 seed 稳定性确认。
3. 然后只做一个 `min_box_ioa=0.20` 的单因子实验。
4. 如果 FN 主要是难样本问题，再补数据重跑。

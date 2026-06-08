# backend-train-model 目录说明

本文件作用域覆盖 `backend-train-model/` 目录下的全部代码、配置、训练产物说明与文档。

## 1. 当前目录定位

- 本目录负责后端训练链路，不负责在线页面和数据库业务。
- 当前训练方向包括 `clothes` fullframe、`person` fullframe、ROI-aware person，以及后续可能的 `personcrop -> clothes` 对照。
- `inspection-flask/` 只作为在线链路参考；除非用户明确要求，不要在后端训练任务中顺手修改在线系统。
- 仓库根 `docs/` 可作为业务背景参考，但训练事实以本目录配置、报告和当前用户说明为准。
- 当前后端训练默认在另一台带 GPU 的电脑上执行；如无特殊说明，后续训练命令默认按 GPU（`--device 0`）口径编写，`--workers 0` 只作为稳定性回退方案。
- 当用户对训练语义、ROI 裁剪影响、标签保留逻辑、指标解读或生产贴合度的表述可能不准确时，AI Agent 不应默认附和；应基于代码、配置、产物和当前链路明确指出可能不对的部分，给出更合理解释或替代建议后再继续执行。

## 2. 必读文件

- 任何数据集、标注、训练配置、转换、可视化任务，先读仓库根 `docs/dataset.md`。
- 修改本目录前先读根 `AGENTS.md`，再读本文件。
- 涉及 `clothes` merged baseline 时读：`backend-train-model/All-train-model/00_CURRENT_BASELINE/README.md`。
- 涉及 `person` 或 ROI-aware person 时读：`backend-train-model/person-train-model/train-docs/person_run_method.md`、`backend-train-model/person-train-model/train-docs/roi_problem_solution.md`、`backend-train-model/person-train-model/train-docs/roi_next_iteration_plan.md`。
- 涉及 `clothes / person` 新增样本接入、以及“新工服款式是否拆类”时读：`backend-train-model/person-train-model/train-docs/new_train.md`。

## 3. 更新日志强制要求

当你修改 `backend-train-model/` 下任意代码、配置、训练文档、汇报材料或本文件时，必须在同一轮修改中同步更新：

- `backend-train-model/docs/update_log.md`

更新时至少写清：

1. 变更来源；
2. 变更总览；
3. 涉及文件；
4. 新增 / 变更配置项；
5. 兼容性注意；
6. 本轮明确不改动的部分。

## 4. 配置修改规则

- 优先修改配置入口，不要把新路径、新默认值硬编码进流程。
- `clothes` 默认入口：`backend-train-model/project_config.json`。
- merged 工服入口：`backend-train-model/All-train-model/*.build.json` 与 `merged_train_project_config.json`。
- person / ROI 入口：`backend-train-model/person-train-model/person_project_config*.json`。
- 其中 `backend-train-model/person-train-model/person_project_config.json` 当前只保留为兼容 / 历史入口；正式 ROI-aware 版本应优先使用独立版本化配置文件。
- person 扩样但尚未补齐 ROI 时，优先使用独立 fullframe 配置：`backend-train-model/person-train-model/person_project_config.fullframe_with_new_labels.json`，不要直接覆盖当前 ROI-aware 主配置。
- 新增配置项后，同步检查 CLI 默认值、训练 / 评估 / 导出报告、文档和 update log 是否一致。
- 当前仓库外原始数据默认采用 sibling layout：父目录下同时存在 `yolov8-program/` 与 `frame_label/`；配置文件内优先使用各自目录可解析的相对路径，默认数据根可统一理解为相对于仓库根的 `../frame_label`，如需兼容特殊机器可通过环境变量 `YOLO_FRAME_LABEL_ROOT` 覆盖。
- 历史 `build_report.json` 只记录当时构建状态，可能包含旧绝对路径；当前路径以配置文件为准。

## 5. 工服训练现状

- 当前 `clothes` 类别：`0 -> clothes`。
- 当前主 baseline：`clothes_merged_v2_balanced_from_first_holdout_v1`。
- baseline 权重：`All-train-model/artifacts/runs/clothes_merged_v2_balanced_from_first_holdout_v1/weights/best.pt`。
- 统一 holdout：`All-train-model/datasets/unified_holdout_v1/dataset.yaml`，`75` 张图、`150` 个 GT 框。
- test 指标：Precision `0.9797`，Recall `0.9653`，mAP50 `0.9875`，mAP75 `0.8773`，mAP50-95 `0.8042`。
- FP/FN 复盘：`TP=144 / FP=3 / FN=6`，复盘入口在 `All-train-model/00_CURRENT_BASELINE/baseline_fpfn_summary.md`。

## 6. person 与 ROI-aware 现状

- 当前 `person` 类别：`0 -> person`。
- person 源数据：`502` 张图、`1658` 个 person 框，最终空标注 `8` 个。
- `person_fullframe` 切分：`train=350 / val=77 / test=75`。
- `person_fullframe_baseline` test：Precision `0.9228`，Recall `0.6740`，mAP50 `0.7606`，mAP50-95 `0.4102`。
- 历史 ROI-aware v1 数据集输出：`502` 张图，保留框 `1343`，丢弃框 `315`，裁剪框 `49`，ROI 空负样本 `12`。
- `person_roi_aware_baseline` test：Precision `0.9390`，Recall `0.5950`，mAP50 `0.6738`，mAP50-95 `0.3867`，当前作为历史对照保留。
- 已新增 fullframe 扩样配置：`person_project_config.fullframe_with_new_labels.json`；它把原有 `502` 张图与 `new_person_labels` 的 `2507` 张图合并用于 fullframe person，但当前显式设置 `roi.enabled=false`，避免在新样本尚未补齐 ROI 前误接入 ROI-aware 流程。
- 已新增方案 C fullframe 配置：`person_project_config.fullframe_with_new_labels_and_hard_examples.v1.json`；它把 `person_fullframe_with_new_labels` 与 `../frame_label/new_hard_examples` 一并并回 fullframe person 主训练集，当前默认初始化权重为 `person_fullframe_with_new_labels_baseline/weights/best.pt`；当前 prepare 汇总为总图 `4517`、最终空白负样本标签 `13`。
- 当前正式 ROI-aware 配置入口已版本化：
  - `person_project_config.roi_with_new_labels.v1.mask_then_crop_margin64.json`
  - `person_project_config.roi_v1.center_inside.json`
  - `person_project_config.roi_v2.mask_then_crop_ioa25.json`
  - `person_project_config.roi_v3.mask_then_crop_margin64.json`
  - `person_project_config.roi_v3.crop_only_margin64.json`
- 已新增 hard-only 严格 holdout 配置：`person_project_config.new_hard_examples.v1.sequence_holdout.json`；对应 prepared 输出目录为 `train-result/prepared/person_new_hard_examples_v1/sequence_holdout/`。
- `train-code/prepare_new_hard_examples_dataset.py` 当前支持 `sequence_contiguous` 与 `sequence_holdout` 独立输出，并额外写出 `split_manifest.jsonl`；如需对源数据做 fail-fast 配对校验，可显式传 `--strict-pairing`。
- 该 fullframe 扩样数据已完成 prepare：总图 `3009`、总框 `8861`，split 为 `train=2105 / val=453 / test=451`；输出目录为 `train-result/prepared/person_fullframe_with_new_labels/sequence_contiguous/`，对应 summary 为 `train-result/person_source_dataset_summary_fullframe_with_new_labels.json`。
- 当前 new labels 工服可用基线 run：`clothes_merged_with_new_labels_v1_baseline`；权重为 `backend-train-model/new_clothes_train/train-result/artifacts/runs/clothes_merged_with_new_labels_v1_baseline/weights/best.pt`；split 为 `train=2106 / val=450 / test=453`。Val 指标：Precision `0.9769`，Recall `0.9594`，mAP50 `0.9817`，mAP75 `0.8645`，mAP50-95 `0.7106`；Test 指标：Precision `0.9835`，Recall `0.9683`，mAP50 `0.9924`，mAP75 `0.8491`，mAP50-95 `0.7075`。
- 当前 new labels person fullframe 可用权重：
  - 稳健基线：`person_fullframe_with_new_labels_baseline`，权重为 `backend-train-model/person-train-model/train-result/artifacts/runs/person_fullframe_with_new_labels_baseline/weights/best.pt`；Val 指标：Precision `0.9554`，Recall `0.9067`，mAP50 `0.9517`，mAP75 `0.4910`，mAP50-95 `0.5095`；Test 指标：Precision `0.9304`，Recall `0.8552`，mAP50 `0.9054`，mAP75 `0.4527`，mAP50-95 `0.4802`。
  - 最新候选：`person_fullframe_with_new_labels_img768`，权重为 `backend-train-model/person-train-model/train-result/artifacts/runs/person_fullframe_with_new_labels_img768/weights/best.pt`；Val 指标：Precision `0.9356`，Recall `0.8960`，mAP50 `0.9457`，mAP75 `0.5135`，mAP50-95 `0.5147`；Test 指标：Precision `0.8798`，Recall `0.8446`，mAP50 `0.8948`，mAP75 `0.4968`，mAP50-95 `0.4970`。
- 当前两条原始 fullframe person 候选权重（`person_fullframe_with_new_labels_baseline`、`person_fullframe_with_new_labels_and_hard_examples_v1_from_baseline`）通过 Ultralytics 读取时的类别名仍是 `{0: 'item'}`；为避免污染 `personcrop` 口径，当前已额外生成两份 `person` 命名 alias 权重：
  - `backend-train-model/person-train-model/train-result/export/person_detect_yolov8_with_new_labels.pt`
  - `backend-train-model/person-train-model/train-result/export/person_detect_yolov8_with_new_labels_and_hard_examples_v1.pt`
- 后续凡是走 `backend-train-model/train_workwear.py prepare --mode personcrop` 的上游 person，默认优先使用这两份 alias 权重；只有在明确需要复用原始 `best.pt` 时，才额外显式传 `--monitored-person-labels item`。
- 当前 `personcrop` 正式下游 source dataset 应对齐 `backend-train-model/new_clothes_train/train-result/datasets/clothes_merged_with_new_labels_v1/dataset.yaml`，即当前 `3009` 图 clothes 扩样主线；旧的 `backend-train-model/project_config.json` 单源 `95` 图 clothes 入口只保留为历史轻量验证口径，不再作为正式 `personcrop` A/B 的默认 source dataset。
- 当前 `personcrop` 训练 / 评估 / 导出应显式使用 `backend-train-model/personcrop-train/personcrop_project_config.json`；该配置把 artifacts 根目录固定到 `backend-train-model/personcrop-train/train-result/artifacts`，使 run、reports、export 与 `personcrop-train/` 分支一一对应。
- `personcrop` 命名口径：`pred_pc_person_*` 表示由上游 `person` 模型生成的裁剪数据集，`pred_pc_clo_*` 表示在对应裁剪数据集上训练得到的下游 `clothes` 模型 run。
- 当前 `person` 额外 hard examples（`4517` 图线）只用于提升上游 person A/B，不应在未补齐 clothes 标注前直接并入 `personcrop` 下游或 `clothes` 主训练集；是否需要补入 `clothes` 端，应以后续 `personcrop` 复盘是否显示“下游 clothes 本身确有稳定收益缺口”为准。
- 当前 person 训练 / 评估 JSON 报告目录已按 run 名分层：`person-train-model/train-result/artifacts/reports/<run_name>/<report_file>.json`，与 `artifacts/runs/<run_name>/` 一一对应；后续不要再把 `*_train.json`、`*_eval.json`、`*_export.json`、`*_all.json` 平铺到 `reports/` 根目录。
- 当前 person new labels 取舍：`img768` 的 Test mAP50-95 高于 `640` 稳健基线（`0.4970` vs `0.4802`），但 Precision、Recall、mAP50 低于 `640`；因此阶段汇报中可写作“最新候选”，不宜直接表述为已替代稳健基线。
- 当前 ROI-aware v2 配置：`train-result/working/roi/roi_config.v2.generated.json`，keep rule 为 `bottom_center_inside OR box_ioa >= 0.25`。
- 当前 ROI-aware v2 数据集输出：`502` 张图，保留框 `1342`，丢弃框 `316`，裁剪框 `54`，ROI 空负样本 `14`。
- 当前 ROI-aware v3 `mask_then_crop + crop_margin_px=64` 配置：`train-result/working/roi/roi_config.v3.mask_then_crop_margin64.generated.json`。
- 当前 ROI-aware v3 `mask_then_crop + crop_margin_px=64` 数据集输出：`502` 张图，保留框 `1335`，丢弃框 `316`，裁剪框 `23`，ROI 空负样本 `15`。
- 当前 ROI-aware v3 `crop_only + crop_margin_px=64` 配置：`train-result/working/roi/roi_config.v3.crop_only_margin64.generated.json`。
- 当前 ROI-aware v3 `crop_only + crop_margin_px=64` 数据集输出：`502` 张图，保留框 `1335`，丢弃框 `316`，裁剪框 `23`，ROI 空负样本 `15`。
- 已完成 `roi_cropped_keep_positive_v3_margin64` 复盘：无 margin 时原本会裁边的 `54` 个 keep-positive 框里，`margin64` 已完整救回 `31` 个；剩余 `23` 个全部只是贴原图下/右边界的 `0.001 px` 级残留裁边，说明 ROI crop 已不再是当前主瓶颈。输出目录：`train-result/review/roi_cropped_keep_positive_v3_margin64/`。
- 当前 native test 领先的 ROI-aware run（优势很小）：`person_roi_aware_v3_mask_then_crop_margin64_from_fullframe`。
- `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` test：Precision `0.9208`，Recall `0.7075`，mAP50 `0.7779`，mAP50-95 `0.4607`。
- `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768` test：Precision `0.9663`，Recall `0.6435`，mAP50 `0.7535`，mAP50-95 `0.4399`。
- `person_roi_aware_v3_crop_only_margin64_from_fullframe` test：Precision `0.7955`，Recall `0.6766`，mAP50 `0.7432`，mAP50-95 `0.4521`。
- 已新增逐图 FP/FN 复盘脚本：`backend-train-model/person-train-model/train-code/analyze_person_fpfn.py`。当前主线 test split 在 `conf=0.25 / nms_iou=0.7 / match_iou=0.5` 下的首轮复盘结果为 `TP=80 / FP=7 / FN=35`，误差主要集中在 `D15_20260119061405`、`D15_20260119203927`、`D02_20260123074836`、`D02_20260123070624`。输出目录：`train-result/review/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_fpfn_test_conf025/`。
- 当前结论：`ROI-aware v3 mask_then_crop + margin64 + from_fullframe 初始化` 相比历史 `person_roi_aware_baseline` 仍是明显提升；相比 `person_roi_aware_v2_from_fullframe` 只体现为很小的 native test 优势，同时明显减少了裁剪框（`54 -> 23`）。`crop_only + margin64` 与 `imgsz=768, batch=2` 这两条已完成的对照实验都没有优于当前 `640 / batch=4` 主线；其中 `img768` 虽然 Precision 更高，但 Recall、mAP50、mAP50-95 都回落，因此不应升级为默认主线。
- 当前优先方案：保留 `person_fullframe_baseline` 作为上游初始化来源，默认主线仍是 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe`，`person_roi_aware_v2_from_fullframe` 继续保留为稳定备选。
- 当前下一轮优先动作：先做 `seed=7 / seed=13` 稳定性确认，并围绕上述 hard sequences 做人工 FN 复盘；只有当逐图 `FN` 复盘与原图 ROI filter 复盘共同表明：存在一批接近 ROI 边界、且可能因 `min_box_ioa=0.25` 被过滤的样本时，才尝试只放松 `min_box_ioa` 的单因子实验；在此之前不默认继续放大 `imgsz`，也不把 `yolov8s` 作为第一优先级。
- 已完成但不建议作为默认主线的对照实验：
  - `person_roi_aware_v3_crop_only_margin64_from_fullframe`
  - `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768`
- 对比文档入口：`backend-train-model/person-train-model/train-docs/roi_compare.md`。
- 下一轮改进执行文档入口：`backend-train-model/person-train-model/train-docs/roi_next_iteration_plan.md`。

## 7. 代码边界

- 不要把当前工服模型写成“完整未穿工服告警模型”；它只是 `clothes` 检测子模型。
- 不要把当前 person + ROI 规则写成“已完成工人身份识别”。
- 如果扩展到多类或新任务，必须明确兼容性影响，并写入 `docs/update_log.md`。
- 不要修复无关历史产物或旧目录，除非用户明确要求。

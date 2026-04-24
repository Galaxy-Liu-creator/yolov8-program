# backend-train-model 目录说明

本文件作用域覆盖 `backend-train-model/` 目录下的全部代码、配置、训练产物说明与文档。

## 1. 当前目录定位

- 本目录负责后端训练链路，不负责在线页面和数据库业务。
- 当前训练方向包括 `clothes` fullframe、`person` fullframe、ROI-aware person，以及后续可能的 `personcrop -> clothes` 对照。
- `inspection-flask/` 只作为在线链路参考；除非用户明确要求，不要在后端训练任务中顺手修改在线系统。
- 仓库根 `docs/` 可作为业务背景参考，但训练事实以本目录配置、报告和当前用户说明为准。

## 2. 必读文件

- 任何数据集、标注、训练配置、转换、可视化任务，先读仓库根 `docs/dataset.md`。
- 修改本目录前先读根 `AGENTS.md`，再读本文件。
- 涉及 `clothes` merged baseline 时读：`backend-train-model/All-train-model/00_CURRENT_BASELINE/README.md`。
- 涉及 `person` 或 ROI-aware person 时读：`backend-train-model/person-train-model/train-docs/person_run_method.md` 与 `backend-train-model/person-train-model/train-docs/roi_problem_solution.md`。

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
- person / ROI 入口：`backend-train-model/person-train-model/person_project_config.json`。
- 新增配置项后，同步检查 CLI 默认值、训练 / 评估 / 导出报告、文档和 update log 是否一致。
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
- 当前 ROI-aware v2 配置：`train-result/working/roi/roi_config.v2.generated.json`，keep rule 为 `bottom_center_inside OR box_ioa >= 0.25`。
- 当前 ROI-aware v2 数据集输出：`502` 张图，保留框 `1342`，丢弃框 `316`，裁剪框 `54`，ROI 空负样本 `14`。
- 当前最佳 ROI-aware run：`person_roi_aware_v2_from_fullframe`。
- `person_roi_aware_v2_from_fullframe` test：Precision `0.9364`，Recall `0.6957`，mAP50 `0.7774`，mAP50-95 `0.4555`。
- 当前结论：`ROI-aware v2 + from_fullframe 初始化` 明显优于历史 `person_roi_aware_baseline`，并且当前 native 结果也高于 `person_fullframe_baseline`；但由于分支间 `dataset.yaml` 不同，和 fullframe 的比较应表述为“当前分支级结果领先”，不是严格同数据集公平对照。
- 当前优先方案：保留 `person_fullframe_baseline` 作为上游初始化来源，把 `person_roi_aware_v2_from_fullframe` 作为当前最佳 ROI-aware person 分支；若后续仍要继续冲 recall，再试 `imgsz=768`、`batch=2`，暂不优先切换 `yolov8s`。
- 对比文档入口：`backend-train-model/person-train-model/train-docs/roi_compare.md`。

## 7. 代码边界

- 不要把当前工服模型写成“完整未穿工服告警模型”；它只是 `clothes` 检测子模型。
- 不要把当前 person + ROI 规则写成“已完成工人身份识别”。
- 如果扩展到多类或新任务，必须明确兼容性影响，并写入 `docs/update_log.md`。
- 不要修复无关历史产物或旧目录，除非用户明确要求。

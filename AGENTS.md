# AI Agent 项目总入口

本文件是仓库级 AI 上下文的**唯一主说明入口**。新开 Codex、Claude Code 或其他 AI Agent 窗口时，应先读取本文件；进入子目录工作时，再读取该目录下更近的 `AGENTS.md`。

`CLAUDE.md` 仅作为 Claude Code 的自动读取跳转文件，内容不再重复维护。`.claude/` 不作为项目说明入口使用。

## 1. 入口与维护规则

- **先读顺序**：`AGENTS.md` → 相关子目录 `AGENTS.md` → 任务相关文档 / 配置 / 结果文件。
- **数据集任务必读**：凡涉及数据理解、标注格式、训练配置、数据转换、校验、可视化，先读 `docs/dataset.md`。
- **示例文件**：理解clothes标注格式时同时查看 `docs/dataset_examples/sample_001.jpg` 与 `docs/dataset_examples/sample_001.txt`；若缺失，先提示用户补充，不要凭文件名猜测。
- **上下文迭代**：每次修改长期有效的信息，例如数据路径、类别定义、训练策略、当前 baseline、业务链路、文档写作口径时，必须同步检查并更新本文件或对应子目录 `AGENTS.md`。
- **不要重复维护**：长期事实尽量写在一个最贴近作用域的 `AGENTS.md`；其他入口只引用它，避免 `AGENTS.md`、`CLAUDE.md`、`.claude/` 三套内容互相打架。
- **编码要求**：Markdown / JSON / YAML 默认按 UTF-8 读写；PowerShell 控制台可能显示中文乱码，读取中文文件时优先用 Python `encoding="utf-8"`。
- **允许纠错与反驳**：当用户对技术判断、代码语义、训练逻辑、指标原因或生产贴合度的表述可能不准确时，AI Agent 不应默认附和；应明确指出可能不对的部分，说明依据，并给出更合理的修正解释或替代建议。
- **交流风格要求**：AI Agent 应以严谨务实的学术风格回应用户，具备辩证思维和独立思考能力；用户的判断不一定正确，需要基于实验证据进行评估；当用户判断缺乏证据支持或存在逻辑漏洞时，应明确纠正并给出正确的方法和建议；避免使用过于轻松或营销化的语气，保持专业性和学术严谨性。

## 2. Python 与运行环境

- 默认 Conda 环境：`yolo_code`
- Python 解释器：`D:\Miniconda3_python\envs\yolo_code\python.exe`
- Python 版本：`3.9.25`
- 训练 / 数据脚本默认不联网下载模型；优先使用仓库或本地显式指定的权重。
- 当前后端训练默认在另一台带 GPU 的电脑上执行；如无特殊说明，优先使用 GPU（`--device 0`）训练。
- `--workers 0` 仅作为 Windows / DataLoader 稳定性回退方案，不再作为默认训练口径。

## 3. 仓库模块分工

- `backend-train-model/`：后端训练主目录，负责 `clothes`、`person`、ROI-aware person 的数据准备、训练、评估、导出和报告。
- `backend-train-model/All-train-model/`：多源 `clothes` 合并训练、统一 holdout、当前工服 baseline 固化。
- `backend-train-model/person-train-model/`：`person_fullframe` 与 `person_roi_aware` 训练分支。
- `inspection-flask/`：在线检测与告警链路，包含 `person -> ROI -> workwear -> track-level temporal rule` 的当前实现。
- `otherMonitor/`：另外三类检测路线，包含隔离栏缺失、打电话、吸烟检测的历史代码、训练产物或 demo。
- `docs/`：数据说明、业务方案、代码分析、汇报材料、论文材料等文档。
- `inspection-flask_old/`：旧版系统与历史参考代码，除非用户明确要求，不作为当前实现入口。

## 4. 数据集与标注核心事实

- 当前正式训练数据以目标检测为主，标注格式为 YOLO 检测格式：`class_id x_center y_center width height`，坐标归一化到 `[0, 1]`。
- `clothes` 类别：`0 -> clothes`。
- `person` 类别：`0 -> person`。
- 代码默认切分比例：`train=0.70 / val=0.15 / test=0.15`；但当前主实验可能用显式 split manifest 覆盖默认比例。
- 代码默认切分策略：`sequence_contiguous`，用于默认单源 `clothes` prepare 与当前 `person_fullframe / person_roi_aware` 数据集。
- 当前 `clothes` merged baseline 不是简单默认切分，而是以 `All-train-model/splits/*.split.csv` 为准：`trainval_balanced_v1.split.csv` 构建训练/验证集，`unified_holdout_v1.split.csv` 构建统一 test holdout。
- 当前仓库外原始数据默认采用 sibling layout：父目录下同时存在 `yolov8-program/` 与 `frame_label/`；文档默认写法统一为相对于仓库根的 `../frame_label`，如需兼容特殊机器可通过环境变量 `YOLO_FRAME_LABEL_ROOT` 覆盖。
- 当前真实路径以配置文件为准：`backend-train-model/project_config.json`、`backend-train-model/All-train-model/*.build.json`、`backend-train-model/person-train-model/person_project_config*.json`。
- 部分历史 `build_report.json` 可能保留旧绝对路径记录；更新路径或重新构建时不要反向以旧报告覆盖当前配置。
- `person` prepared 数据集的 `dataset.yaml` 默认不写机器绝对 `path:`，让 `train/val/test` 按 `dataset.yaml` 所在目录解析；不要重新生成带旧盘符或本机绝对路径的 YAML。

## 5. `clothes` / 工服训练现状

- 当前 `clothes` fullframe baseline 已固定在 `backend-train-model/All-train-model/00_CURRENT_BASELINE/`。
- 当前选中 run：`clothes_merged_v2_balanced_from_first_holdout_v1`。
- 当前权重：`backend-train-model/All-train-model/artifacts/runs/clothes_merged_v2_balanced_from_first_holdout_v1/weights/best.pt`。
- 统一 holdout：`backend-train-model/All-train-model/datasets/unified_holdout_v1/dataset.yaml`，共 `75` 张图、`150` 个 GT 框。
- 当前 test 指标：Precision `0.9797`，Recall `0.9653`，mAP50 `0.9875`，mAP75 `0.8773`，mAP50-95 `0.8042`。
- 单帧 FP/FN 复盘口径：`conf=0.45`，NMS IoU `0.7`，GT 匹配 IoU `0.5`；`TP=144 / FP=3 / FN=6`。
- 工服模型本身只检测 `clothes`，不能直接等同于“未穿工服告警器”；上线告警仍需结合 `person`、ROI、track 和时序规则。

## 6. `person` 与 ROI-aware person 现状

- `person` 源数据共 `502` 张图、`1658` 个 person 框；最终训练标签文件 `502` 个，其中空标注 `8` 个。
- `person` 训练 / 评估 JSON 报告按 run 名分层保存：`backend-train-model/person-train-model/train-result/artifacts/reports/<run_name>/<report_file>.json`，与 `artifacts/runs/<run_name>/` 一一对应；后续不要再把 `*_train.json`、`*_eval.json`、`*_export.json`、`*_all.json` 平铺到 `reports/` 根目录。
- `person_fullframe` 数据集切分：`train=350 / val=77 / test=75`；框数：`train=1258 / val=219 / test=181`。
- `person_fullframe_baseline` test 指标：Precision `0.9228`，Recall `0.6740`，mAP50 `0.7606`，mAP50-95 `0.4102`。
- ROI JSON 根目录默认写法：`../frame_label/roi-json`。
- 当前已生成 ROI 配置：`backend-train-model/person-train-model/train-result/working/roi/roi_config.generated.json`，共 `502` 个 JSON，`scope=per_image`，`mode=mask_then_crop`。
- 历史 ROI-aware v1 数据集输出 `502` 张图，保留 person 框 `1343` 个，丢弃 `315` 个，裁剪边界框 `49` 个，ROI 空负样本 `12` 张。
- `person_roi_aware_baseline` test 指标：Precision `0.9390`，Recall `0.5950`，mAP50 `0.6738`，mAP50-95 `0.3867`，当前作为历史对照保留。
- 当前 ROI-aware v2 配置文件：`backend-train-model/person-train-model/train-result/working/roi/roi_config.v2.generated.json`。
- 当前 ROI-aware v2 数据集输出 `502` 张图，保留 person 框 `1342` 个，丢弃 `316` 个，裁剪边界框 `54` 个，ROI 空负样本 `14` 张。
- 当前 ROI-aware v3 `mask_then_crop + crop_margin_px=64` 配置文件：`backend-train-model/person-train-model/train-result/working/roi/roi_config.v3.mask_then_crop_margin64.generated.json`。
- 当前 ROI-aware v3 `mask_then_crop + crop_margin_px=64` 数据集输出 `502` 张图，保留 person 框 `1335` 个，丢弃 `316` 个，裁剪边界框 `23` 个，ROI 空负样本 `15` 张。
- 当前 ROI-aware v3 `crop_only + crop_margin_px=64` 配置文件：`backend-train-model/person-train-model/train-result/working/roi/roi_config.v3.crop_only_margin64.generated.json`。
- 当前 ROI-aware v3 `crop_only + crop_margin_px=64` 数据集输出 `502` 张图，保留 person 框 `1335` 个，丢弃 `316` 个，裁剪边界框 `23` 个，ROI 空负样本 `15` 张。
- 当前 person 正式配置入口已版本化：
  - fullframe 扩样：`backend-train-model/person-train-model/person_project_config.fullframe_with_new_labels.json`
  - fullframe 扩样 + hard examples 方案 C：`backend-train-model/person-train-model/person_project_config.fullframe_with_new_labels_and_hard_examples.v1.json`
  - hard-only holdout：`backend-train-model/person-train-model/person_project_config.new_hard_examples.v1.sequence_holdout.json`
  - new labels ROI-aware v1：`backend-train-model/person-train-model/person_project_config.roi_with_new_labels.v1.mask_then_crop_margin64.json`
  - ROI-aware v1：`backend-train-model/person-train-model/person_project_config.roi_v1.center_inside.json`
  - ROI-aware v2：`backend-train-model/person-train-model/person_project_config.roi_v2.mask_then_crop_ioa25.json`
  - ROI-aware v3 mask：`backend-train-model/person-train-model/person_project_config.roi_v3.mask_then_crop_margin64.json`
  - ROI-aware v3 crop：`backend-train-model/person-train-model/person_project_config.roi_v3.crop_only_margin64.json`
- 当前 `backend-train-model/person-train-model/train-code/prepare_new_hard_examples_dataset.py` 已支持 `sequence_contiguous` 与 `sequence_holdout` 独立输出，并额外写出 `split_manifest.jsonl`；如需对源数据做 fail-fast 配对校验，可显式传 `--strict-pairing`。
- `backend-train-model/person-train-model/person_project_config.json` 当前保留为兼容 / 历史入口，不再作为 ROI-aware v2/v3 的正式唯一配置来源。
- 已完成 `roi_cropped_keep_positive_v3_margin64` 复盘：无 margin 时原本会裁边的 `54` 个 keep-positive 框里，`margin64` 已完整救回 `31` 个；剩余 `23` 个全部只是贴原图下/右边界的 `0.001 px` 级残留裁边，说明 ROI crop 已不再是当前主瓶颈。复盘输出目录：`backend-train-model/person-train-model/train-result/review/roi_cropped_keep_positive_v3_margin64/`。
- 当前 native test 领先的 ROI-aware run（优势很小）：`person_roi_aware_v3_mask_then_crop_margin64_from_fullframe`。
- `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` test 指标：Precision `0.9208`，Recall `0.7075`，mAP50 `0.7779`，mAP50-95 `0.4607`。
- `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768` test 指标：Precision `0.9663`，Recall `0.6435`，mAP50 `0.7535`，mAP50-95 `0.4399`。
- `person_roi_aware_v3_crop_only_margin64_from_fullframe` test 指标：Precision `0.7955`，Recall `0.6766`，mAP50 `0.7432`，mAP50-95 `0.4521`。
- 已新增 person 单帧复盘脚本：`backend-train-model/person-train-model/train-code/analyze_person_fpfn.py`。当前主线 test split 在 `conf=0.25 / nms_iou=0.7 / match_iou=0.5` 下的首轮复盘结果为 `TP=80 / FP=7 / FN=35`，误差主要集中在 `D15_20260119061405`、`D15_20260119203927`、`D02_20260123074836`、`D02_20260123070624`。输出目录：`backend-train-model/person-train-model/train-result/review/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_fpfn_test_conf025/`。
- 当前结论：`ROI-aware v3 mask_then_crop + margin64 + from_fullframe 初始化` 相比历史 `person_roi_aware_baseline` 仍是明显提升；相比 `person_roi_aware_v2_from_fullframe` 则只体现为**很小的 native test 优势**，同时显著减少了边界裁剪框（`54 -> 23`）。`crop_only + margin64` 与 `imgsz=768, batch=2` 这两条已完成的对照实验都没有优于当前 `640 / batch=4` 主线；其中 `img768` 虽然 Precision 更高，但 Recall、mAP50、mAP50-95 都回落，因此不应升级为默认主线。
- 当前优先策略不是直接换 `yolov8s`，也不再默认继续放大输入尺寸；保留 `person_fullframe_baseline` 作为初始化来源，默认主线仍是 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe`，`person_roi_aware_v2_from_fullframe` 继续保留为稳定备选。
- 当前下一轮优先动作：先做 `seed=7 / seed=13` 稳定性确认，并围绕上述 hard sequences 做人工 FN 复盘；只有当逐图 `FN` 复盘与原图 ROI filter 复盘共同表明：存在一批接近 ROI 边界、且可能因 `min_box_ioa=0.25` 被过滤的样本时，才尝试只放松 `min_box_ioa` 的单因子实验；在此之前不默认继续放大 `imgsz`，也不把 `yolov8s` 作为第一优先级。
- 已完成但不建议作为默认主线的对照实验：
  - `person_roi_aware_v3_crop_only_margin64_from_fullframe`
  - `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768`
- 系统性对比文档入口：`backend-train-model/person-train-model/train-docs/roi_compare.md`。
- ROI 边界改进建议记录在 `backend-train-model/person-train-model/train-docs/roi_problem_solution.md`：优先考虑 `bottom_center_inside OR box_ioa >= 0.25`，并配合 `crop_margin_px=64`。
- 下一轮改进执行文档入口：`backend-train-model/person-train-model/train-docs/roi_next_iteration_plan.md`。

## 7. `inspection-flask` 在线链路现状

- 当前在线链路不是“已完成真实工人身份识别”，而是基于 `person + ROI + workwear + track + temporal` 的候选作业人员工服合规判断。
- 权重默认位置：`inspection-flask/weights/person_detect_yolov8.pt` 与 `inspection-flask/weights/workwear_detect_yolov8.pt`。
- 关键阈值位于 `inspection-flask/settings.py`：`PERSON_CONF=0.55`、`WORKWEAR_CONF=0.45`、`ROI_MIN_OVERLAP_RATIO=0.5`。
- 时序规则：`TEMPORAL_WINDOW_SIZE=5`、`TEMPORAL_TRIGGER_RATIO=0.6`、`MIN_TRACK_APPEAR_FRAMES=2`。
- 跟踪器：`SimpleIoUTracker`，默认 IoU 阈值 `0.3`，`TRACKER_MAX_AGE=2`。
- 文档或代码中要区分 `ROI 内人员 / 作业区人员`、`候选作业人员`、`真实身份已确认工人`，不要把代理规则写成最终身份识别能力。

## 8. `otherMonitor` 三类检测现状

四类检测在项目定位上应视为同一项目的四个方向：工服检测、隔离栏缺失检测、打电话检测、吸烟检测。写汇报或论文时不要表述为“工服是主线，其他三类是后加拓展”；可以通过篇幅和细节自然体现工服检测资料更完整。

### 8.1 隔离栏缺失检测

- 入口：`otherMonitor/BarrierMonitor/BarrierMonitor.py`。
- 类别：`0 barrier_post`、`1 compliant_barrier`、`2 idle_barrier`、`3 car`。
- 逻辑：YOLO 整帧检测 → 按 ROI 判断车辆和隔离栏 → 状态机处理车辆进入、停稳、等待、检查、报警、恢复。
- 当前脚本推理设备固定为 CPU，ROI 与输出路径仍有硬编码，适合作为时序状态机和告警去抖参考，不宜直接复制为生产实现。

### 8.2 打电话检测

- 入口：`otherMonitor/call_runs/calling/`。
- 真实状态：训练实验归档，不是完整上线链路。
- 已有多模型对比：`yolo11m`、`yolo11s`、`yolo11n`、`yolov8s`。
- `summary-gpu.json` 当前只汇总 `yolo11m-gpu`：Precision `0.8871`，Recall `0.9155`，mAP50 `0.9438`，mAP50-95 `0.6594`。
- 数据 YAML 在仓库外，最终 leaderboard 不完整；可借鉴多模型 benchmark 与 artifacts 留存方式。

### 8.3 吸烟检测

- 入口：`otherMonitor/smoke/42_demo/1_train.py`、`2_val.py`、`3_webcam.py`。
- 当前训练脚本激活版本：`YOLO("yolov8s.yaml").load("yolov8s.pt")`，`epochs=100`、`imgsz=960`、`batch=4`、`workers=0`、`amp=True`。
- 数据配置：`A_my_data.yaml`，类别为 `smoking`；外部数据约 `16551` train、`4952` val/test。
- 仓库内本地样本子集：`otherMonitor/smoke/picture/data/` 与 `labels/`，各 `448` 个。
- 历史记录显示混合训练 `train5` 的 mAP50-95 约 `0.705`，高于只用公共数据的约 `0.683~0.698`；可借鉴“公共数据 + 现场数据混训”思路。
- 当前 train / val / demo 三个脚本权重入口不完全一致，只适合作为阶段参考。

## 9. 文档与汇报写作口径

- 论文、汇报、方案文档默认按“四类检测共同组成项目”来写，不要写成“先做单一工服，后来加入三类检测”。
- 可以适当让工服检测内容更细，因为仓库中工服、person、ROI 的数据治理和结果更完整，但文字上不要明确贬低其他三类方向的地位。
- 学生汇报风格优先：表述清楚、通俗，保留必要术语，例如 `fullframe person`、`ROI-aware person`、`sequence_contiguous`、`unified holdout`。
- 开发环境不需要写进论文正文；除非用户要求，不要在正文里说明“本文档使用 LaTeX 编写”。

## 10. 业务 / 方案文档约束

- 仓库中的业务说明、方案设计、检测链路、生产路线类文档用于理解当前阶段目标、代码现状和演进方向，不是不可质疑的固定真理。
- 当真实生产目标、现场约束、当前代码实现、误报 / 漏报与文档冲突时，优先尊重真实情况和用户最新说明。
- 发现冲突时应明确指出，并提出修订建议；经用户批准后再更新对应文档。
- 更新业务 / 方案类文档时，优先区分：真实生产目标、当前阶段实现、当前能力边界、升级触发条件、后续演进路线。
- 不要把“当前代理实现”直接写成“最终业务终局”。

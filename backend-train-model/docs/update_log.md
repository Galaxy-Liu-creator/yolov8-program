# Update Log

## 2026-06-03 统一 sibling layout 路径体系

1. 变更来源：用户把本机原始图片与标注目录统一调整为 `frame_label`，并要求将项目中的路径体系改造为开发机 / 训练机共用的 sibling layout，避免继续依赖旧的 `all_labels` 与机器绝对路径。
2. 变更总览：
   - 将 `backend-train-model/config.py`、`project_config.json`、`All-train-model/*.build.json`、`new_clothes_train/clothes_merged_with_new_labels_v1.build.json`、`person_project_config*.json` 中的原始数据路径统一改为相对 `frame_label` 的写法。
   - 在 `config.py`、`prepare_new_hard_examples_dataset.py`、`prepare_new_clothes_dataset.py`、`validate_new_clothes_source.py` 中新增 `YOLO_FRAME_LABEL_ROOT` 覆盖能力；默认按父目录下同时存在 `yolov8-program/` 与 `frame_label/` 的 sibling layout 解析外部数据根。
   - 同步更新根 `AGENTS.md`、`backend-train-model/AGENTS.md`、`docs/dataset.md`、`docs/目录结构说明.md` 以及多份训练运行文档，统一文档默认口径为 `../frame_label`，并把仓库位置相关命令改成相对进入方式。
3. 涉及文件：
   - `backend-train-model/config.py`
   - `backend-train-model/project_config.json`
   - `backend-train-model/All-train-model/*.build.json`
   - `backend-train-model/new_clothes_train/clothes_merged_with_new_labels_v1.build.json`
   - `backend-train-model/new_clothes_train/train-code/prepare_new_clothes_dataset.py`
   - `backend-train-model/new_clothes_train/train-code/validate_new_clothes_source.py`
   - `backend-train-model/person-train-model/person_project_config*.json`
   - `backend-train-model/person-train-model/train-code/prepare_new_hard_examples_dataset.py`
   - `AGENTS.md`
   - `backend-train-model/AGENTS.md`
   - `docs/dataset.md`
   - `docs/目录结构说明.md`
   - `backend-train-model/docs/README.md`
   - `backend-train-model/docs/total-run-method.md`
   - `backend-train-model/new_clothes_train/train-docs/new_clothes_run_method.md`
   - `backend-train-model/person-train-model/train-docs/*.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 新增环境变量约定：`YOLO_FRAME_LABEL_ROOT`
   - 默认仓库外数据根目录：相对于仓库根的 `../frame_label`
   - 配置文件中的原始数据目录统一改为相对路径；其解析锚点仍保持“相对于各自配置文件所在目录”。
5. 兼容性注意：
   - 历史 `args.yaml`、历史训练 / 评估报告、旧 `build_report.json` 中保留的绝对路径属于历史快照，本轮不回写篡改，避免破坏可追溯性；当前实际执行口径以配置文件和更新后的文档为准。
   - 若特殊机器无法满足 sibling layout，可显式设置 `YOLO_FRAME_LABEL_ROOT` 覆盖默认外部数据根。
   - 本轮没有统一改写 `python_candidates` 中的解释器绝对路径；如训练机解释器位置不同，应优先通过实际激活环境运行，或后续再单独版本化该部分环境配置。
6. 本轮明确不改动：
   - 不重跑任何训练、评估、导出或 ROI-aware 数据集生成流程。
   - 不修改历史训练产物、在线检测链路实现或 ROI JSON 标注内容。
   - 不把历史日志条目中的旧机器绝对路径批量改写为新口径。

## 2026-06-01 新增 hard examples fullframe 并回方案与 holdout 变体

1. 变更来源：用户确认执行方案 C，并要求同时补充 `new_hard_examples` 的 `sequence_holdout` 变体，以及审改 `backend-train-model/person-train-model/train-code/prepare_new_hard_examples_dataset.py` 的配对、冲突和审计能力。
2. 变更总览：
   - 新增 `backend-train-model/person-train-model/person_project_config.fullframe_with_new_labels_and_hard_examples.v1.json`，把 `person_fullframe_with_new_labels` 与 `all_labels/new_hard_examples` 一并纳入新的 fullframe 主训练集配置，并默认从 `person_fullframe_with_new_labels_baseline` 权重继续训练。
   - 新增 `backend-train-model/person-train-model/person_project_config.new_hard_examples.v1.sequence_holdout.json`，把 hard-only 数据集的严格 `sequence_holdout` 版本独立配置化，避免和现有 `sequence_contiguous` 产物混用。
   - 更新 `backend-train-model/config.py` 的 `resolve_sequence_name_from_image_root(...)`，对 `all_labels/new_hard_examples/*/*/frames` 解析出 `hard_<group>_<sequence>` 风格序列名，解决方案 C fullframe prepare 时与历史 `group3_2/1` 这类目录名冲突的问题。
   - 审改 `backend-train-model/person-train-model/train-code/prepare_new_hard_examples_dataset.py`：输出根目录改为按 `split-strategy` 自动落到 `.../person_new_hard_examples_v1/<split-strategy>`；新增 `--strict-pairing`；把跨序列冲突校验从 filename 扩到 stem；新增 `split_manifest.jsonl`；并把这些元数据写回 `prepare_report.json`。
   - 重新生成 `person_new_hard_examples_v1/sequence_contiguous` 与 `person_new_hard_examples_v1/sequence_holdout` 两套 prepared 数据；同时执行 `person_fullframe_with_new_labels_and_hard_examples.v1` 的 fullframe prepare，产出新的汇总标签与 prepared 输出目录。
   - 更新 `backend-train-model/person-train-model/train-docs/person_run_method.md`，新增 `person_fullframe_with_new_labels_and_hard_examples_v1` 与 `person_new_hard_examples_v1_sequence_holdout` 两个版本段，并同步刷新 `person_new_hard_examples_v1` 的 regenerate 命令与 manifest 说明。
3. 涉及文件：
   - `backend-train-model/config.py`
   - `backend-train-model/person-train-model/train-code/prepare_new_hard_examples_dataset.py`
   - `backend-train-model/person-train-model/person_project_config.fullframe_with_new_labels_and_hard_examples.v1.json`
   - `backend-train-model/person-train-model/person_project_config.new_hard_examples.v1.sequence_holdout.json`
   - `backend-train-model/person-train-model/train-docs/person_run_method.md`
   - `backend-train-model/person-train-model/train-result/prepared/person_new_hard_examples_v1/sequence_contiguous/*`
   - `backend-train-model/person-train-model/train-result/prepared/person_new_hard_examples_v1/sequence_holdout/*`
   - `backend-train-model/person-train-model/train-result/working/aggregated_labels_fullframe_with_new_labels_and_hard_examples_v1/*`
   - `backend-train-model/person-train-model/train-result/person_source_dataset_summary_fullframe_with_new_labels_and_hard_examples_v1.json`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 新增 fullframe 配置入口：`backend-train-model/person-train-model/person_project_config.fullframe_with_new_labels_and_hard_examples.v1.json`
   - 新增 hard holdout 配置入口：`backend-train-model/person-train-model/person_project_config.new_hard_examples.v1.sequence_holdout.json`
   - `backend-train-model/config.py` 的 `resolve_sequence_name_from_image_root(...)` 现在会把 `new_hard_examples/*/*/frames` 解析成 `hard_<group>_<sequence>`，避免和已有非 `frames` 目录的短名称冲突。
   - `prepare_new_hard_examples_dataset.py` 新增 CLI：`--strict-pairing`
   - `prepare_new_hard_examples_dataset.py` 新增产物：`split_manifest.jsonl`
   - `prepare_new_hard_examples_dataset.py` 的默认输出目录从固定 `sequence_contiguous` 改为根据 `--split-strategy` 自动映射到对应子目录
5. 兼容性注意：
   - `person_new_hard_examples_v1` 的 `sequence_contiguous` 与 `sequence_holdout` 现在拥有各自独立的 `dataset.yaml`、`prepare_report.json`、`split_manifest.jsonl` 与 project-config；后续训练和评估不要混用。
   - `run_person_flow.py` 会校验显式传入的 `dataset.yaml` 是否落在当前 project-config 预期的 prepared 根目录内，因此 holdout 版必须配套使用新的 `person_project_config.new_hard_examples.v1.sequence_holdout.json`。
   - 方案 C 当前只覆盖 fullframe 主线；由于 `new_hard_examples` 仍无 ROI JSON，本轮没有新增 ROI-aware hard examples 版本。
   - `prepare_new_hard_examples_dataset.py` 目前仍默认允许非严格配对，只是在 `prepare_report.json` 中记录并提供 `--strict-pairing` 供后续 fail-fast；这样可以避免在源数据临时波动时直接打断现有 hard-only 流程。
6. 本轮明确不改动：
   - 不启动新的训练、评估或导出；本轮只完成配置、prepared 数据和运行文档更新。
   - 不修改任何 ROI JSON、人工作业台账、在线检测链路或 `inspection-flask/` 下的实现。
   - 不修改当前已确定的 ROI-aware v2/v3 主线配置、权重选择或业务阈值。

# 2026-05-25 写入 new_person_labels 复盘总结

1. 变更来源：用户要求把本次 `person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_from_fullframe` 的 FP/FN 复盘结果、改进做法和重点关注项整理到 `backend-train-model/person-train-model/train-docs/new_person_labels复盘.md`。
2. 变更总览：
   - 新增 `backend-train-model/person-train-model/train-docs/new_person_labels复盘.md`，集中记录本次 ROI-aware new labels v1 的复盘口径、总体指标、重点问题序列、典型样本、改进做法与后续重点关注项。
   - 复盘内容明确了当前最集中问题：`group_0004 / group_0005 / group_0006` 的 FP/FN 聚集，以及 `D15_20260119061405 / D15_20260119203927` 的连续漏检簇。
   - 复盘建议明确下一步优先做单因子实验：先人工复核重点序列，再考虑只放松 `min_box_ioa=0.25`，不要同时改模型、尺寸和 ROI 规则。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/new_person_labels复盘.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练配置或 JSON 参数。
   - 仅新增复盘文档与对应的长期记录说明。
5. 兼容性注意：
   - 复盘文档只记录当前阶段的分析结论，不改变现有 `person_run_method.md` 的训练主线。
   - 本轮复盘明确强调：当前 prepared 数据集没有缺失 `.txt` 的图片，空白负样本均为显式保存。
6. 本轮明确不改动：
   - 不修改模型权重、prepared 数据集、ROI 标注内容或训练脚本实现。
   - 不启动新的训练、评估或导出。

## 2026-05-25 补充 ROI-aware 随机性复核命令与复盘结论

1. 变更来源：用户要求在 `person_run_method.md` 中补充 `person_roi_aware_with_new_labels_v1_mask_then_crop_margin64` 的 `seed=7` / `seed=13` 随机性训练与评估命令，并同步完成该 run 的 FP/FN 复盘与 prepared 口径核对。
2. 变更总览：
   - 在 `backend-train-model/person-train-model/train-docs/person_run_method.md` 新增 `ROI-aware随机性训练` 版本段，分别补充 `seed=7` 与 `seed=13` 的训练 / 评估命令，保持与当前 ROI-aware new labels v1 主线一致的 `dataset.yaml`、`base-model`、`imgsz=640`、`batch=4`、`workers=4`、`device=0` 口径。
   - 通过 `analyze_person_fpfn.py` 对 `person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_from_fullframe` 做了单帧 FP/FN 复盘，并沉淀了 `fpfn_summary.md` 与 `fpfn_per_image.json`。
   - 复盘过程中补充核对了 fullframe 与 ROI-aware prepared 口径：图片数与 split 计数一致，但 ROI-aware 因 `keep_rule` 与 `crop_margin_px=64` 导致 box 数减少，并新增了空负样本。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/person_run_method.md`
   - `backend-train-model/person-train-model/train-result/review/person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_from_fullframe_fpfn_test_conf0250/fpfn_summary.md`
   - `backend-train-model/person-train-model/train-result/review/person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_from_fullframe_fpfn_test_conf0250/fpfn_per_image.json`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增 JSON 配置项。
   - 仅新增两个随机性复核训练 / 评估命令入口，未调整数据集 prepare 逻辑或训练超参策略本身。
5. 兼容性注意：
   - `seed=7` / `seed=13` 仅用于随机性稳定性确认，不应替代当前 `seed=42` 主线结论。
   - 单帧 FP/FN 复盘使用的是 `conf=0.25 / nms_iou=0.7 / match_iou=0.5` 的业务复盘口径，不应与标准 eval 报告中的 COCO mAP 直接混为一谈。
   - ROI-aware prepared 数据集中所有图片均有对应 `.txt`，其中一部分为空白负样本；不存在“图片有但缺少 label 文件”的当前问题。
6. 本轮明确不改动：
   - 不重新训练、也不重跑 `seed=7` / `seed=13`。
   - 不修改 ROI JSON、prepared 数据集内容、`analyze_person_fpfn.py` 代码逻辑或在线链路。
   - 不调整 `person_fullframe_with_new_labels` 的 fullframe 主线配置与 baseline 权重选择。

## 2026-05-25 规范 person 训练评估报告目录结构

1. 变更来源：用户要求把 `backend-train-model/person-train-model/train-result/artifacts/reports` 下的评估报告按 `artifacts/runs` 的 run 目录格式区分，并在 `person_run_method.md` 中增加后续训练 / 评估产物必须遵循该目录结构的约束。
2. 变更总览：
   - 将 person 历史训练 / 评估 JSON 报告从 `reports/` 根目录平铺迁移为 `reports/<run_name>/<report_file>.json`。
   - 更新历史 JSON 顶层 `report_path` 字段，使其指向迁移后的真实文件位置。
   - 更新 `train_workwear.py`，后续 `train / evaluate / export / all` 生成的 JSON 报告都会按 run 名写入 `reports/<run_name>/`；查找最近训练报告时改用递归扫描，兼容新分层与旧平铺历史报告。
   - 更新 `analyze_person_fpfn.py` 的默认 eval report 路径，并把 `person-train-model/train-docs/` 中旧的平铺报告引用批量改为分层路径。
   - 在 `person_run_method.md`、仓库根 `AGENTS.md` 与 `backend-train-model/AGENTS.md` 中固化新约束。
3. 涉及文件：
   - `backend-train-model/train_workwear.py`
   - `backend-train-model/person-train-model/train-code/analyze_person_fpfn.py`
   - `backend-train-model/person-train-model/train-docs/person_run_method.md`
   - `backend-train-model/person-train-model/train-docs/*.md`
   - `backend-train-model/person-train-model/train-result/artifacts/reports/<run_name>/*.json`
   - `AGENTS.md`
   - `backend-train-model/AGENTS.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增 JSON 配置项。
   - 新增产物目录约定：`backend-train-model/person-train-model/train-result/artifacts/reports/<run_name>/<report_file>.json`。
   - 新增脚本行为：`train_workwear.py` 的训练、评估、导出和 all 总报告按 run 名分目录写入。
5. 兼容性注意：
   - 新目录与 `artifacts/runs/<run_name>/` 一一对应，便于同时回看权重、曲线图和 JSON 指标。
   - 旧的 `reports/<run_name>_eval.json`、`reports/<run_name>_train.json` 这类平铺路径不再作为 person 文档和后续命令的推荐入口。
   - `train_workwear.py` 查找最近训练报告时仍会递归扫描 `*_train.json`，因此对已有分层报告和可能遗留的旧平铺报告均保持兼容。
6. 本轮明确不改动：
   - 不重跑任何训练、评估、导出或 FP/FN 复盘。
   - 不修改 `artifacts/runs/<run_name>/` 下的权重、曲线图、`results.csv` 等训练产物。
   - 不修改 prepared 数据集、ROI JSON 标注、在线检测链路或其他模块的报告目录策略。

## 2026-05-21 新增 `new_person_labels` ROI-aware v1 独立配置文件并改写运行命令

1. 变更来源：用户认为 `person_project_config.fullframe_with_new_labels.json` 中 `roi.enabled=false` 不应再继续充当 ROI-aware new labels v1 的临时入口，因此要求新增一份独立配置文件，并同步把 `person_run_method.md` 中对应训练命令改为使用新配置。
2. 变更总览：
   - 新增 `backend-train-model/person-train-model/person_project_config.roi_with_new_labels.v1.mask_then_crop_margin64.json`。
   - 该配置基于 `fullframe_with_new_labels` 的数据源与 sequence 定义构建，但显式开启 `roi.enabled=true`，并版本化固定：`mask_then_crop + crop_margin_px=64`、`work_root`、`config_path`、`roi_aware_prepared_output_root`、`roi_aware_recommended_run_name` 与导出别名路径。
   - 更新 `backend-train-model/person-train-model/train-docs/person_run_method.md`，把 `person_roi_aware_with_new_labels_v1_mask_then_crop_margin64` 这一节中的 `project-config` 全部切换到新配置文件，不再继续写成“借用 fullframe 配置的临时方案”。
   - 同步更新仓库级 `AGENTS.md` 与 `backend-train-model/AGENTS.md`，把 `new labels ROI-aware v1` 配置入口补入当前正式版本化配置列表，并明确：`person_project_config.fullframe_with_new_labels.json` 继续保留 `roi.enabled=false`，只服务 fullframe 主线。
3. 涉及文件：
   - `backend-train-model/person-train-model/person_project_config.roi_with_new_labels.v1.mask_then_crop_margin64.json`
   - `backend-train-model/person-train-model/train-docs/person_run_method.md`
   - `AGENTS.md`
   - `backend-train-model/AGENTS.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 新增独立配置入口：`backend-train-model/person-train-model/person_project_config.roi_with_new_labels.v1.mask_then_crop_margin64.json`
   - 该配置显式设置：
     - `roi.enabled = true`
     - `roi.mode = mask_then_crop`
     - `roi.crop_margin_px = 64`
     - `roi.work_root = roi-work-with-new-labels-v1-mask-then-crop-margin64`
     - `roi.config_path = train-result/working/roi/roi_config.fullframe_with_new_labels.v1.mask_then_crop_margin64.generated.json`
     - `person_dataset.default_dataset_variant = roi_aware`
     - `person_dataset.roi_aware_prepared_output_root = train-result/prepared/person_roi_aware_with_new_labels_v1_mask_then_crop_margin64/sequence_contiguous`
     - `person_dataset.roi_aware_recommended_run_name = person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_from_fullframe`
5. 兼容性注意：
   - 这次新增的是 `new_person_labels` ROI-aware v1 的独立配置入口，不应再把 `person_project_config.fullframe_with_new_labels.json` 直接改成 `roi.enabled=true`；后者仍保留为 fullframe 主线正式入口。
   - 当前新配置虽然继承了 `fullframe_with_new_labels` 的数据源与 label 聚合入口，但其 `default_dataset_variant`、ROI 路径与推荐 run 名都已独立版本化，后续运行时不要把两者的 prepared 输出与 run 名混用。
   - 当前这条配置更适合作为 `new labels ROI-aware 第一版正式对照实验` 入口，不代表它已经自动升级为默认唯一主线；是否成为后续推荐版本，仍需以评估结果和逐图抽检结果为准。
6. 本轮明确不改动：
   - 不修改任何现有 ROI JSON 标注内容、`roi_plan_summary.json`、`new_person_labels_ROI分组标记.md` 或人工台账文件。
   - 不修改训练脚本实现、fullframe prepared 数据集或历史 ROI-aware v2/v3 配置文件内容。
   - 不启动新的训练、评估、导出，也不修改在线检测链路与历史人工复核正文。

## 2026-05-21 新增 `new_person_labels` ROI-aware v1 训练运行方法

1. 变更来源：用户说明 `new_person_labels` 的 `group_0001 ~ group_0006` 已完成组级 ROI 核验，并要求把这条 ROI-aware 第一版的训练 / 评估命令正式写入 `backend-train-model/person-train-model/train-docs/person_run_method.md`，且格式需与现有运行文档保持一致。
2. 变更总览：
   - 更新 `backend-train-model/person-train-model/train-docs/person_run_method.md`。
   - 在文档最前面新增一节：`person_roi_aware_with_new_labels_v1_mask_then_crop_margin64`，作为当前 `new_person_labels` 完成 ROI 核验后的第一版 ROI-aware 训练入口。
   - 明确补入该版本的 `当前定位`、`数据集与产物`、`如需重生成数据集`、`训练命令`、`评估命令` 和 `备注`。
   - 当前这条运行方法采用：`mask_then_crop + crop_margin_px=64`，并推荐以 `person_fullframe_with_new_labels_baseline/weights/best.pt` 作为初始化来源，run 名为 `person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_from_fullframe`。
   - 文档中同时明确：ROI 核验完成后并不是直接跳过数据准备就训练，而是仍需按顺序执行 `extract-roi-config -> prepare-roi-aware -> train -> evaluate`。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/person_run_method.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练脚本参数。
   - 无新增 `person_project_config*.json`。
   - 本轮新增的是 `new_person_labels` ROI-aware v1 的运行口径与命令，不修改现有训练逻辑。
5. 兼容性注意：
   - 当前新增的 ROI-aware v1 仍继续借用 `person_project_config.fullframe_with_new_labels.json` 作为数据源登记入口，但实际 ROI-aware 数据集、ROI 配置和 run 名都通过显式参数独立版本化，不应与 fullframe prepared 输出或历史 pending_roi 输出混用。
   - 只有在 `extract-roi-config` 结果里确认 `group_0001 ~ group_0006` 都稳定进入 `per_sequence` 时，这条训练线才算真正满足“组级 ROI 已核验通过”的前提；如果某个组意外落到 `per_image`，应优先回查 `roi-json/` 内容，而不是直接继续训练。
   - 当前这条命令更适合作为第一版正式对照实验，不代表它已经自动成为默认唯一主线；是否升级为主推荐版本仍要以后续评估指标和逐图抽检结果为准。
6. 本轮明确不改动：
   - 不修改 `new_person_labels_ROI分组标记.md`、`new_person_labels_frames逻辑分组.md` 或人工台账文档。
   - 不修改任何现有 prepared 数据集内容、ROI JSON 标注内容或训练脚本实现。
   - 不启动新的训练、评估、导出，也不修改在线检测链路与历史人工复核正文。

## 2026-05-21 补充各稳定组的 ROI 验证代表帧

1. 变更来源：用户要求直接更新 `backend-train-model/person-train-model/train-docs/new_person_labels_ROI分组标记.md`，在当前 `7.1A` 已有的组级 ROI 起画代表帧基础上，为 `group_0001 ~ group_0006` 每组再补几张对应代表帧，减少只看中心帧而遗漏边界变化的风险。
2. 变更总览：
   - 更新 `backend-train-model/person-train-model/train-docs/new_person_labels_ROI分组标记.md`。
   - 将 `7.1A 当前 new_person_labels 六个组的直接可用代表帧` 从单一“5 张代表帧清单”改成两层结构：`第一轮直接起画帧` + `建议补充验证帧`。
   - 当前 6 个稳定组都新增了 `4` 张补充验证帧，用于在完成第一版粗略组级 ROI 后，再做边界复核；这样每组总计 `9` 张帧，仍控制在“通常不超过 10 张”的范围内。
   - 同步更新 `7.2A` 的标注落地步骤，把原来“其余 4 张代表帧做校验”改成“先用其余 4 张起画帧快速校验，再用 4 张补充验证帧做边界复核”，使文档与新的代表帧策略一致。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/new_person_labels_ROI分组标记.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练脚本参数。
   - 无新增 `project_config`、ROI keep rule、prepared 数据集或训练配置。
   - 本轮只补充代表帧抽样与组级 ROI 校验口径，不修改训练逻辑。
5. 兼容性注意：
   - 新增的 `4` 张补充验证帧不是要求全部重新手画不同 ROI，而是用于验证“同一版组级 ROI 模板是否仍成立”；最终落盘时仍应只保留单一组级 ROI 模板，避免被工具链识别成 `per_image ROI`。
   - 当前这批补充帧是为了提高粗略 ROI 第一版的边界覆盖，不代表 `group_0001 ~ group_0006` 需要重新回到细拆阶段；只有当补充验证帧显示同一版 ROI 明显不成立时，才考虑把该组降级为 `B 类` 再继续细拆。
6. 本轮明确不改动：
   - 不修改 `new_person_labels_人工分组记录表模板.xlsx`、`roi_plan_summary.json` 或 `new_person_labels_frames_grouping_t006/` 下的当前目录结构。
   - 不修改任何 `person_project_config*.json`、ROI-aware 版本化配置、prepared 数据集或训练脚本。
   - 不启动新的训练、评估、导出，也不修改在线检测链路与历史人工复核正文。

## 2026-05-20 根据已完成的人工台账回填 ROI 标注计划

1. 变更来源：用户说明 `backend-train-model/person-train-model/train-docs/new_person_labels_人工分组记录表模板.xlsx` 的 `组级台账` 已完成填写，且本轮只需要推进粗略 ROI 第一版，因此要求根据现有台账直接补全 `ROI标注计划` 工作表，并在 `new_person_labels_frames_grouping_t006` 工作目录下补齐必要信息。
2. 变更总览：
   - 回填 `new_person_labels_人工分组记录表模板.xlsx` 中 `ROI标注计划` 工作表，按当前 `组级台账` 的收口结果为 `group_0001 ~ group_0006` 生成 6 行 ROI 计划。
   - 当前 6 个组统一按 `A` 类稳定组、`组级ROI`、`是否可共用一版ROI=是`、`不继续细拆` 的口径进入粗略组级 ROI 第一版。
   - 在 `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/` 下新增 `roi_plan_summary.json`，把每组的图片数、分辨率、负责人、ROI 工作目录、ROI JSON 输出目录、建议代表帧数量和抽检数量做成机器可读汇总。
   - 更新 `new_person_labels_frames_grouping_t006/README.md`，明确当前人工台账收口结果、粗略 ROI 第一版执行口径，以及每组后续使用的 `roi-work/` 与 `roi-json/` 目录。
   - 在 `grouped/group_0001 ~ group_0006/` 下补齐后续 ROI 标注使用的 `roi-work/` 与 `roi-json/` 目录。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/new_person_labels_人工分组记录表模板.xlsx`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/README.md`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/roi_plan_summary.json`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0001/roi-work/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0001/roi-json/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0002/roi-work/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0002/roi-json/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0003/roi-work/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0003/roi-json/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0004/roi-work/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0004/roi-json/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0005/roi-work/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0005/roi-json/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0006/roi-work/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0006/roi-json/`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练脚本参数。
   - 无新增 `project_config`、ROI keep rule 或 prepared 数据集。
   - 本轮新增的是粗略 ROI 第一版的协作计划、工作目录与计划汇总，不修改训练逻辑。
5. 兼容性注意：
   - `ROI标注计划` 当前基于已完成的 `组级台账` 直接回填，因此其中 `人工组名称` 暂不额外发明新的场景中文名，默认沿用当前 `group_0001 ~ group_0006` 作为稳定组标识。
   - `计划完成日期` 当前统一保留为 `待定`，因为台账中没有给出明确排期；后续实际开工后可再补具体日期。
   - 当前 `roi-work/` 与 `roi-json/` 目录只表示粗略 ROI 第一版的工作入口，不代表这些组已经完成 Labelme 标注或已经生成正式 `roi_config`。
6. 本轮明确不改动：
   - 不修改 `person_project_config.fullframe_with_new_labels.json`、任何 ROI-aware 版本化配置、任何现有 prepared 数据集或训练脚本。
   - 不修改 `new_person_labels_frames逻辑分组.md`、`new_person_labels_ROI分组标记.md` 的长期分组原则。
   - 不启动新的训练、评估、导出，也不修改在线检测链路与历史人工复核正文。

## 2026-05-19 补充“工作区宽覆盖”场景的视角填写口径

1. 变更来源：用户进一步追问当加油站工作区基本覆盖整张图时，`new_person_labels` 人工分组表里的“视角编号 / 左偏右偏居中”到底应该怎么填，并要求把这条判断规则补到 `new_person_labels_人工分组记录表操作指南.md` 的对应位置。
2. 变更总览：
   - 更新 `backend-train-model/person-train-model/train-docs/new_person_labels_人工分组记录表操作指南.md`。
   - 将 `组级台账` 中 `视角编号` 的解释从较抽象的“视角或机位方向”改为更贴近当前任务的“主作业区 / 计划 ROI / 主要目标簇在画面中的横向位置”，并把示例改成 `居中`。
   - 在 `组级台账` 表后新增“`视角编号` / 方位怎么判断”的补充说明，明确这不是摄影学机位编号，而是看主作业区在画面横向上偏左、偏中还是偏右，并补入“三等分法”与加油站监控常见场景的填写口径。
   - 新增“工作区宽覆盖 / 全幅作业区”这一类场景的推荐写法：当作业区基本覆盖整张图、左右都有有效工作区域时，默认优先写 `居中`，并在 `备注` 中补 `工作区宽覆盖` 或 `全幅作业区`。
   - 同步细化 `图片明细` 表中 `左偏/右偏/居中` 一列的解释，明确如果工作区基本铺满整张图，优先写 `居中`。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/new_person_labels_人工分组记录表操作指南.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练脚本参数。
   - 无新增 `project_config`、ROI 配置或 prepared 数据集。
   - 本轮只补充分组填写口径，不修改训练流程、数据准备逻辑或 Excel 模版结构。
5. 兼容性注意：
   - 本轮补入的是人工填写口径，不代表必须把 Excel 模版新增一个正式的“全幅/宽覆盖”枚举列值；当前更推荐的落地方式仍是：`视角编号` 写 `居中`，并在 `备注` 中补 `工作区宽覆盖`。
   - “左侧 / 居中 / 右侧” 仍然是主口径；只有当主作业区明显偏左或偏右，并且这种差异会影响 ROI 共用时，才建议把它作为正式拆分依据。
6. 本轮明确不改动：
   - 不修改 `new_person_labels_人工分组记录表模板.xlsx` 的工作表结构与列名。
   - 不修改任何 `person_project_config*.json`、ROI 配置、prepared 数据集或训练脚本。
   - 不启动新的训练、评估、导出，也不修改在线检测链路与历史人工复核正文。

## 2026-05-19 细化人工分组记录表中的“继续细拆”填写规则

1. 变更来源：用户进一步追问 `new_person_labels` 人工分组流程中“什么时候需要继续细拆、是不是只看代表帧、细拆后表格怎么写、目录结构应该怎么建”等具体执行问题，并要求把这些口径补进 `new_person_labels_人工分组记录表操作指南.md`，尤其写进 Step 5 部分。
2. 变更总览：
   - 更新 `backend-train-model/person-train-model/train-docs/new_person_labels_人工分组记录表操作指南.md`。
   - 在 `组级台账` 说明部分新增“继续细拆”的判断口径，明确：代表帧只是第一轮入口，真正的细拆依据应是“代表帧发现差异 + 组内补充样本验证 + 差异确实影响是否能共用一版 ROI”。
   - 补充了哪些情况通常应正式细拆、哪些情况更适合只在 `图片明细` 中记录而不拆整个组，例如：白天/夜晚稳定分批、近中远景稳定分批、左右/居中机位差异、不同作业区混杂、稳定异类小簇等。
   - 把“细拆时表格怎么写”写得更具体：保留母组行，在其下新增子组行；子组 `当前自动组ID` 仍保留原自动组，`人工细分后的最终组ID` 则写成 `group_0001_a_day`、`group_0001_b_night` 这类形式，并给出完整示例表。
   - 在操作步骤的 Step 5 中补入“细拆后的目录结构”建议，明确推荐保留母组目录作为来源工作区，再在母组目录下建立 `manual_split/<子组ID>/images|labels/`，同时可保留 `undecided/` 放边界样本。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/new_person_labels_人工分组记录表操作指南.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练脚本参数。
   - 无新增 `project_config`、ROI 配置或 prepared 数据集。
   - 本轮只细化人工协作口径与目录组织建议，不修改训练流程与数据准备逻辑。
5. 兼容性注意：
   - 本轮更新的是操作指南，不代表现有 `new_person_labels_frames_grouping_t006/grouped/` 目录已经自动生成了所有 `manual_split/` 子目录；后续仍需按实际细拆结果手动创建。
   - 当前 Excel 模版结构本身不必重做；新增的细拆写法基于现有 `组级台账` 列即可落地，核心是“保留母组行 + 新增子组行 + 表格与目录一一对应”。
   - `group_0001_a_day` 这类命名是推荐口径，不是唯一固定字符串；但建议继续保持英文/数字命名，以减少后续目录、脚本和 ROI 配置引用时的歧义。
6. 本轮明确不改动：
   - 不修改 `new_person_labels_人工分组记录表模板.xlsx` 的工作表结构。
   - 不修改 `person_project_config.fullframe_with_new_labels.json`、任何 ROI 配置、prepared 数据集或训练脚本。
   - 不启动新的训练、评估、导出，也不修改在线检测链路与历史人工复核正文。

## 2026-05-18 新增人工分组记录表操作指南

1. 变更来源：用户要求新增一份 Markdown 操作指南，详细解释 `new_person_labels_人工分组记录表模板.xlsx` 中每一个标题的意义，并说明组员实际开展人工分组时应该如何填写信息、按什么顺序推进。
2. 变更总览：
   - 新增 `backend-train-model/person-train-model/train-docs/new_person_labels_人工分组记录表操作指南.md`。
   - 文档系统说明了 Excel 模版 4 个工作表的用途，以及 `填写说明`、`组级台账`、`图片明细`、`ROI标注计划` 中每一个可见标题的意义、推荐填写方式、固定口径和示例。
   - 文档还补充了组员的实际操作步骤，包括：认领自动组、查看 `group_summary.json` 代表帧、先做组级判断、再补图片明细、最后只对稳定组填写 ROI 标注计划，以及常见错误提醒。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/new_person_labels_人工分组记录表操作指南.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练脚本参数。
   - 无新增 `project_config`、ROI 配置或 prepared 数据集。
   - 本轮只新增人工协作说明文档，不修改训练流程与数据准备逻辑。
5. 兼容性注意：
   - 该指南是对 Excel 模版的文字解释与填写规范，不替代 `group_summary.json`、`group_manifest.csv` 以及前面两份分组策略文档。
   - 文档默认仍以 `t006` 自动粗分组结果作为当前主参考版本；若后续主参考版本切换，应同步检查这份指南中的路径与组编号说明。
6. 本轮明确不改动：
   - 不修改 `person_project_config.fullframe_with_new_labels.json`、旧 `person_project_config.roi_*.json`、`roi_config*.generated.json` 或任何现有 prepared 数据集。
   - 不修改训练脚本主链、评估脚本、模型权重、在线检测链路或人工复核历史台账正文。

## 2026-05-18 新增人工分组 Excel 模版

1. 变更来源：用户要求先生成一份可直接发给队友使用的 `new_person_labels` 人工分组记录表 Excel 模版，用于后续人工逻辑分组、ROI 策略确认和协作分工。
2. 变更总览：
   - 新增 Excel 文件 `backend-train-model/person-train-model/train-docs/new_person_labels_人工分组记录表模板.xlsx`。
   - 模版包含 4 个工作表：
     - `填写说明`：说明分组目标、填写顺序、A/B/C 类稳定性定义、ROI 策略口径以及当前自动粗分组主参考版本；
     - `组级台账`：用于记录自动组到人工最终组的映射、组稳定性等级、是否继续细拆、能否共用 ROI、代表帧、负责人、状态等；
     - `图片明细`：用于记录需要继续细拆或需要逐图 ROI 的图片级补充信息；
     - `ROI标注计划`：用于安排每个最终组的 ROI scope、工作目录、代表帧数量、抽检数量、标注状态和负责人。
   - `组级台账` 中已预填当前 `t006` 自动粗分组的 6 个自动组及图片数，便于队友直接从当前主参考版本开始分工。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/new_person_labels_人工分组记录表模板.xlsx`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练脚本参数。
   - 无新增 `project_config` 或 ROI 配置。
   - 本轮只新增协作使用的 Excel 模版，不修改训练流程与数据准备逻辑。
5. 兼容性注意：
   - 该 Excel 仅作为人工协作记录模板，不应替代 `group_summary.json` 与 `group_manifest.csv` 作为自动粗分组原始结果来源。
   - `组级台账` 里预填的 6 个自动组来源于 `feature_threshold=0.06` 的主参考版本；后续如果主参考版本变化，应同步更新模版或另存新版本。
6. 本轮明确不改动：
   - 不修改 `person_project_config.fullframe_with_new_labels.json`、旧 `person_project_config.roi_*.json`、`roi_config*.generated.json` 或任何现有 prepared 数据集。
   - 不修改训练脚本主链、评估脚本、模型权重、在线检测链路或人工复核历史台账正文。

## 2026-05-18 新增 frames 逻辑分组说明并生成 t006 工作目录结构

1. 变更来源：用户要求在完成自动粗分组后，继续把 `new_person_labels` 的分组依据、人工继续细分的方法、以及已经生成的工作目录结构正式整理成文档，并明确给出最终产物路径。
2. 变更总览：
   - 更新 `backend-train-model/person-train-model/train-docs/new_person_labels_frames逻辑分组.md`，系统写入自动粗分组依据、`0.08 / 0.06 / 0.04` 三档阈值的比较理由、为什么当前以 `0.06` 作为主参考、以及人工继续细分时应如何看代表帧、如何判断能否共用 ROI、如何把组划分成 `A / B / C` 三类。
   - 在文档中显式写入自动粗分组主结果路径：`new_person_labels_roi_grouping_t006/group_summary.json` 与 `group_manifest.csv`，并同步写入已创建的物理分组目录模板路径：`new_person_labels_frames_grouping_t006/grouped/`。
   - 已创建 `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/` 下的 6 组物理目录模板：`group_0001` 到 `group_0006`，每组均包含 `images/` 与 `labels/` 两级目录，用作后续人工继续细拆、放图与放标签的工作区。
   - 更新 `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/README.md`，说明该目录与自动粗分组结果目录的关系、当前结构和后续使用方式。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/new_person_labels_frames逻辑分组.md`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/README.md`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0001/images/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0001/labels/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0002/images/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0002/labels/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0003/images/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0003/labels/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0004/images/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0004/labels/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0005/images/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0005/labels/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0006/images/`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_frames_grouping_t006/grouped/group_0006/labels/`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练脚本参数。
   - 无新增 `project_config`。
   - 本轮新增的是基于 `t006` 自动粗分组结果的说明文档和物理目录模板，不直接修改现有训练配置、ROI 配置或 prepared 数据集。
5. 兼容性注意：
   - `new_person_labels_frames_grouping_t006/grouped/` 当前只是**工作目录模板**，目录已创建，但并不意味着所有图片与标签都已经人工确认并放入到最终组中。
   - `new_person_labels_roi_grouping_t006/` 与 `new_person_labels_frames_grouping_t006/` 的角色不同：前者保存自动粗分组结果，后者保存后续人工物理分组工作区；不要把两者混用。
   - 当前以 `0.06` 为主参考，不代表 `0.04` 与 `0.08` 结果无效；它们仍可作为“偏细参考”和“偏粗参考”辅助人工判断。
6. 本轮明确不改动：
   - 不修改 `person_project_config.fullframe_with_new_labels.json`、旧 `person_project_config.roi_*.json`、`roi_config*.generated.json` 或任何现有 prepared 数据集。
   - 不修改训练脚本主链、评估脚本、模型权重、在线检测链路或人工复核历史台账正文。

## 2026-05-18 新增 ROI 自动粗分组脚本并落地首轮 new_person_labels 结果

1. 变更来源：用户询问能否先对 `new_person_labels` 做自动化分组，以降低 `3000+` 图片 ROI-aware 标注前的纯手工分组成本，并希望把自动分组思路与结果纳入当前 ROI 分组方案。
2. 变更总览：
   - 新增 `backend-train-model/person-train-model/train-code/auto_group_new_person_labels_roi.py`，用于对 `new_person_labels_flat_20260503` 先按图片分辨率与粗视觉特征生成第一轮自动粗分组结果。脚本支持输出 `group_manifest.csv`、`group_summary.json`、`README.md`，并可选生成 `grouped/` 物理分组目录；当前默认阈值已调整为 `0.08`，同时新增 `--clean-output` 选项，避免旧分组残留污染新结果。
   - 已在 `backend-train-model/person-train-model/train-result/working/` 下落地一版首轮自动粗分组结果（当前用于结果解读的是 `new_person_labels_roi_grouping_t008/` 这版 `feature_threshold=0.08` 输出），并在 `new_person_labels_ROI分组标记.md` 中补充脚本入口、推荐命令和当前结果解读。
   - 当前 `feature_threshold=0.08` 下的首轮自动粗分组结果为：`2507` 张图被拆成 `5` 组，其中 `1280x720` 一组 `272` 张，`1920x1080` 四组共 `2235` 张；这说明该批数据并非一个统一稳定 ROI 场景，但这些自动组仍然只是第一轮候选组，后续仍需按代表帧继续人工复核和细拆。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-code/auto_group_new_person_labels_roi.py`
   - `backend-train-model/person-train-model/train-docs/new_person_labels_ROI分组标记.md`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_roi_grouping_t008/group_manifest.csv`
   - `backend-train-model/person-train-model/train-result/working/new_person_labels_roi_grouping_t008/group_summary.json`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 新增自动粗分组脚本参数：
     - `--feature-threshold`
     - `--representatives-per-group`
     - `--materialize-mode`
     - `--create-empty-missing-labels`
     - `--clean-output`
   - 默认自动分组阈值设置为 `0.08`，用于生成更有区分度的第一轮候选组。
5. 兼容性注意：
   - 自动分组结果当前只应被视为“ROI-aware 前的第一轮候选物理 / 逻辑分组建议”，**不等于最终人工确认后的 ROI 逻辑组**。
   - `new_person_labels_roi_grouping/` 下当前落地的 `grouped/` 目录是为后续 ROI-aware 分组标注服务的中间产物，不应直接替代当前 `new_person_labels/images` 与 `person_labels` 作为 fullframe 训练主线的原始入口。
   - 当前 5 组里仍然存在大组（如 `group_0002`、`group_0005`），后续应优先回看 `group_summary.json` 中的代表帧，再决定是否需要继续人工细拆；不要把自动粗分组结果直接当作最终组级 ROI 单位。
6. 本轮明确不改动：
   - 不修改 `person_project_config.fullframe_with_new_labels.json`、旧 `person_project_config.roi_*.json`、`roi_config*.generated.json` 或任何现有 prepared 数据集。
   - 不修改训练脚本主链、评估脚本、模型权重、在线检测链路或人工复核历史台账正文。

## 2026-05-18 新增 new_person_labels ROI 分组与标记方案文档

1. 变更来源：用户要求把“针对当前 `3000+` 张 `new_person_labels` 图片，ROI-aware 标注到底该怎么做、是否应该全量逐图、如果不逐图应该如何分组和实施”的完整方案，正式写入 `backend-train-model/person-train-model/train-docs/new_person_labels_ROI分组标记.md`。
2. 变更总览：
   - 新增 `backend-train-model/person-train-model/train-docs/new_person_labels_ROI分组标记.md`，系统整理 `new_person_labels` 当前更适合采用的 ROI 标注方案。
   - 文档明确区分了：物理分组、逻辑分组、组级 ROI、逐图 ROI 各自的含义，并给出针对 `3000+` 图片的推荐策略：优先采用“组级 ROI 为主、逐图 ROI 为辅”的分层混合方案，而不是默认整包 flat source 共用一个 ROI，也不是默认全量逐图 ROI。
   - 文档进一步细化了 `A 类稳定组 / B 类半稳定组 / C 类不稳定组` 的判断口径、代表帧抽取建议、组级 ROI 的抽检标准、什么时候应继续细分、什么时候才建议逐图 ROI，以及为什么 ROI-aware 第一版不必强求覆盖 `3000+` 全量图片。
   - 同步写清了后续如何把这套分组与标注结果衔接到 `ROI_Labelme.md`、`extract-roi-config`、`prepare-roi-aware` 和后续 new labels ROI-aware 版本化配置中。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/new_person_labels_ROI分组标记.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练脚本参数。
   - 无新增已落盘的 `person_project_config*.json`。
   - 本轮只新增 ROI 分组与标记方案文档，用于指导后续物理分组、逻辑分组和 ROI-aware 标注实施，不直接修改现有训练配置、ROI 配置或 prepared 数据集。
5. 兼容性注意：
   - 文档中提到的“物理分组”建议优先在新目录下完成，不应直接破坏当前 `new_person_labels/images` 与 `person_labels` 作为 fullframe 主线原始入口的结构。
   - 文档中提出的 `70%~85% 组级 ROI / 10%~20% 细分后组级 ROI / 5%~15% 逐图 ROI 或暂缓` 是工程推荐比例，不是强制阈值；实际仍应以 ROI 稳定性和人工可维护性为准。
   - 本轮并没有直接创建 grouped 数据目录、ROI JSON、ROI config 或新的 ROI-aware 版本化配置；后续只有在实际分组和标注开始后，才建议继续新增正式配置文件和 prepared 数据产物。
6. 本轮明确不改动：
   - 不修改 `person_project_config.fullframe_with_new_labels.json`、旧 `person_project_config.roi_*.json`、`roi_config*.generated.json` 或任何现有 prepared 数据集。
   - 不修改训练脚本、评估脚本、模型权重、在线检测链路或人工复核历史台账正文。

## 2026-05-18 新增 fullframe 修正方案并补充 new labels ROI-aware 标注说明

1. 变更来源：用户要求把 `person_with_new_labels` 当前 fullframe 上游修正方式单独整理成正式文档，并把 `new_person_labels` 做 ROI-aware 时与旧固定 sequence 不同的标注要点写入 `ROI_Labelme.md`，同时明确回答“mixed 场景 flat source 是否必须切成多个场景序列”这一问题的工程口径。
2. 变更总览：
   - 新增 `backend-train-model/person-train-model/train-docs/person_with_new_labels_fullframe_fix_plan.md`，把 `人工复核.md` 当前 `5.13` 阶段已收口的 hardest FN 结论，转成可执行的 fullframe 修正方案。文档明确区分了：当前优先应先做的数据治理动作、何时适合从 `seed7` best 继续 fine-tune、何时应按 `640` 稳健配方重训，以及进入 new labels ROI-aware 正式训练前需要满足的条件。
   - 更新 `backend-train-model/person-train-model/train-docs/ROI_Labelme.md`，新增 `new_person_labels ROI-aware` 专项说明，明确把它与旧 `group3_1 / group3_2 / group3_3` 固定 sequence 的 ROI 标注方式区分开：旧固定 sequence 通常可按“一条 sequence 抽代表帧 -> 一版 ROI”推进，而 `new_person_labels_flat_20260503` 若内部混有多个摄像头 / 场景 / 视角，则不应默认整包只画一个 ROI，而应优先先拆成 ROI 稳定的小组，再做 Labelme 标注与后续 ROI-aware 数据准备。
   - 在 ROI 文档中补充了 `new_person_labels` 的推荐分组方法、何时才需要逐图 ROI、以及独立 `ROI work / ROI config / ROI-aware prepared output / project_config` 的版本化建议，避免后续直接覆盖当前 `fullframe_with_new_labels` 产物。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/person_with_new_labels_fullframe_fix_plan.md`
   - `backend-train-model/person-train-model/train-docs/ROI_Labelme.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练脚本参数。
   - 无新增已落盘的 `person_project_config*.json`。
   - 本轮新增的是 fullframe 修正方案文档，并在 ROI 标注文档中补充 `new_person_labels ROI-aware` 的工程约束与目录组织建议；这些内容用于指导后续数据治理与配置版本化，不直接修改现有训练配置、ROI 配置或 prepared 数据集。
5. 兼容性注意：
   - `person_with_new_labels_fullframe_fix_plan.md` 当前提供的是工程执行方案，不等于仓库已经自动完成 `must_relabel_list / hard_positive_expand_list / defer_list` 三张动作清单；后续仍需由人工复核结果回填到源标签修正与补样动作中。
   - `ROI_Labelme.md` 新增的 `new_person_labels` 专项说明，并不是说 mixed 场景 flat source 在 fullframe 训练中绝对不能作为一个入口存在；它强调的是：**当目标变成 ROI-aware 时，不应默认给整包 flat source 共用一个 ROI**，否则 ROI 语义、场景边界与后续 prepared 数据质量都可能失真。
   - 本轮没有直接创建 new labels ROI-aware 的正式版本化 `project_config`，也没有落盘新的 `roi_config*.generated.json`；后续只有在 ROI 分组与标注实际完成后，才建议继续新增正式配置文件。
6. 本轮明确不改动：
   - 不修改 `person_project_config.fullframe_with_new_labels.json`、旧 `person_project_config.roi_*.json`、`roi_config*.generated.json` 或任何现有 prepared 数据集。
   - 不修改训练脚本、评估脚本、模型权重、在线检测链路或人工复核历史台账正文。

## 2026-05-14 新增 person_with_new_labels 决策与运行文档

1. 变更来源：用户要求把“新增 `new_person_labels` 之后，当前应先继续 fullframe 训练还是先等 ROI 补齐”的判断整理成正式文档，并把对应训练 / 评估命令单独沉淀为 runbook，统一放到 `backend-train-model/person-train-model/train-docs/` 下。
2. 变更总览：
   - 新增 `backend-train-model/person-train-model/train-docs/person_with_new_labels_decision.md`，系统说明当前 new labels person 主线与旧 502 张 ROI-aware 主线的关系，并明确当前更合理的方案是：先继续 `person_fullframe_with_new_labels` 训练，把 ROI 补齐作为并行准备工作推进，ROI 补齐后再新开 new labels 的 ROI-aware 正式版本。
   - 新增 `backend-train-model/person-train-model/train-docs/person_with_new_labels_run.md`，给出与上述决策相匹配的当前可执行命令，重点覆盖 `person_fullframe_with_new_labels_baseline_seed7 / seed13` 的训练与评估命令，以及 `img768` 候选在“640 稳定后再补 seed”的条件式入口。
   - 在 runbook 中明确写出：当前不把旧 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_seed7 / seed13` 命令当作 new labels 主线的第一优先动作；同时保留 ROI 补齐后的后续接入约束，但不伪造尚未落盘的 new labels ROI-aware 正式配置命令。
   - 后续按用户反馈，已进一步规范 `person_with_new_labels_run.md` 的 Markdown 格式，去掉会影响预览显示的多余缩进，确保“运行前检查”“seed7 / seed13 训练与评估”等代码块在文档中可直接看到完整命令，而不是显示为空白代码框。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/person_with_new_labels_decision.md`
   - `backend-train-model/person-train-model/train-docs/person_with_new_labels_run.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练配置文件。
   - 无新增脚本参数。
   - 本轮只新增决策文档与运行文档，不修改现有 `person_project_config*.json`、ROI 配置、prepared 数据集、模型权重或评估逻辑。
5. 兼容性注意：
   - `person_with_new_labels_decision.md` 与 `person_with_new_labels_run.md` 的核心约束是：当前可直接执行的主线仍是 `person_fullframe_with_new_labels`，不是旧 502 张 ROI-aware 主线的 seed 稳定性确认；因此不要把这两份新文档中的“下一步先跑 fullframe seed7 / seed13”误读成对旧 ROI-aware 主线的结论修订。
   - runbook 当前故意不提供“可直接执行”的 new labels ROI-aware 训练命令，因为这条线的正式版本化配置与 ROI 数据入口尚未作为仓库当前事实完全落盘；后续一旦补齐 ROI 并新增正式配置，应优先更新这两份文档，而不是继续复用旧 502 张 ROI-aware 命令。
   - `person_with_new_labels_run.md` 当前应以普通 Markdown 段落 + 标准 fenced code block 方式渲染；如果后续再次批量生成类似 runbook，需避免给整份文档每一行额外添加前导空格，以免编辑器预览把代码块显示成空白或异常折叠。
6. 本轮明确不改动：
   - 不修改现有 `person_run_method.md`、`roi_next_iteration_plan.md`、`人工复核.md`、`person_project_config*.json` 或 `roi_config*.generated.json`。
   - 不修改任何训练代码、数据准备流程、模型权重、评估报告和在线检测链路。

## 2026-05-14 补齐 5.13 阶段 sequence notes 模版

1. 变更来源：用户要求把 `stage_2026-05-13_crowded_overlap_formal_closeout/` 下需要的 `5-13notes.md` 模版补齐，并明确参考 `backend-train-model/person-train-model/train-docs/人工复核.md` 中 `5.13` 阶段“今天至少要回答什么、哪些问题不阻塞推进、下一步更建议先做什么”的收口口径。
2. 变更总览：
   - 统一把 `5.13` 阶段三条必需 sequence notes 重构为更贴近 `5.10` 阶段 `5-10notes.md` 的表格化模板结构，而不只是保留“5.13 阶段结论摘要版”。
   - 对 crowded 主线两条核心序列 `D15_20260119203927`、`D05_20260123074841`，按 `5-10notes.md` 的写法补齐为：`本轮定位 -> 今天优先看的帧 -> 今天要回答的问题 -> 记录提醒 -> 字段总览表 -> 推荐填写顺序 -> 逐帧正式收口记录表 -> sequence 级正式结论 -> 当前明确不建议优先做什么`。
   - 对对照序列 `D15_20260119061405`，同步补成与 `5-10notes.md` 对照模板一致的结构：`本轮定位 -> 今天建议只抽看 -> 今天要回答的问题 -> 记录提醒 -> 字段总览表 -> 推荐填写顺序 -> 对照帧正式收口记录表 -> 对照序列正式结论 -> 当前明确不建议优先做什么`。
   - 在不回写 `5.10` 历史阶段正文的前提下，把 `5.13` 阶段需要的“当前正式收口口径”直接嵌入表格中，保证后续组员既能按模板继续补 overlay 级短句，也能直接复用当前 sequence 级收口结论。
   - 本轮保持 `semantic_bucket_summary.md`、`semantic_bucket_manifest.json`、`active_stage.json` 与 `review_stage_index.md` 不变；只补齐 `5-13notes.md` 的模板结构与当前正式收口话术。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-13_crowded_overlap_formal_closeout/sequence_notes/sequence_D15_20260119203927/5-13notes.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-13_crowded_overlap_formal_closeout/sequence_notes/sequence_D05_20260123074841/5-13notes.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-13_crowded_overlap_formal_closeout/sequence_notes/sequence_D15_20260119061405/5-13notes.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练配置、数据配置、脚本参数或评估参数。
   - 本轮只补充人工复核 notes 模版结构，不改动训练入口、prepared 数据集、模型权重、ROI 配置或在线链路代码。
5. 兼容性注意：
   - 本轮新增的是 `5.13` 阶段 notes 的固定填写结构，目的是让后续继续补 overlay 级短句或 sequence 级收口时可以直接沿用同一模版；不改变 `semantic_bucket_manifest.json` 的字段语义。
   - `5.13` 模版现在在章节组织上已尽量对齐 `5.10` 阶段 `5-10notes.md`，但每一栏表达的仍然是“正式收口”语义，而不是继续回到 `5.10` 当天的“机制探索中”语义。
   - `D15_20260119203927` 仍主要按 sequence 级结论保守收口，`D05_20260123074841` 仍保留“顶部问答偏一框合两人、逐帧结论偏第二人无响应”的内部口径差异；这些差异被明确记录为“不阻塞推进”的问题，而不是本轮必须返工完成的硬阻塞项。
   - `D15_20260119061405` 仍只作为对照序列，不应被误读为当前下一轮训练的主入口。
6. 本轮明确不改动：
   - 不修改 `5.10` 阶段 `5-10notes.md`、`semantic_bucket_summary.md`、`semantic_bucket_manifest.json`。
   - 不修改 `5.13` 阶段的 `semantic_bucket_summary.md`、`semantic_bucket_manifest.json`、`active_stage.json` 或 `review_stage_index.md`。
   - 不修改训练代码、数据准备流程、评估脚本、模型权重和在线检测链路。

## 2026-05-13 更新阶段汇报 PPT 后端模型训练进展页

1. 变更来源：用户要求在不覆盖原始 PPT 的前提下，继续修改 `backend-train-model/docs/PPT/` 下阶段汇报材料，把“后端模型训练进展”页更新为当前 `clothes` 与 `person` 的最新 new labels 可用基线 / 候选权重，并写出对应指标；用户补充说明卡片可以适当拉大，但必须保证文字完整放入且布局合理。
2. 变更总览：
   - 新增 / 更新输出副本 `backend-train-model/docs/PPT/大创PPT汇报_人工复核阶段版_训练进展更新_20260513.pptx`，继续保留原始 `大创PPT汇报.pptx` 与上一版 `大创PPT汇报_人工复核阶段版_20260513.pptx`，未覆盖源文件。
   - 将第 4 页“后端模型训练进展”改为两张加宽大卡片：左侧汇总 `clothes new labels baseline`，右侧汇总 `person new labels baseline / candidate`，保留原 PPT 的深蓝页眉、橙色标题、白色圆角卡片和正文风格。
   - `clothes` 更新为 `clothes_merged_with_new_labels_v1_baseline`，写入权重路径、split `2106 / 450 / 453`、Val 指标 `P 0.9769 / R 0.9594 / mAP50 0.9817 / mAP75 0.8645 / mAP50-95 0.7106`，以及 Test 指标 `P 0.9835 / R 0.9683 / mAP50 0.9924 / mAP75 0.8491 / mAP50-95 0.7075`。
   - `person` 写入 `person_fullframe_with_new_labels_img768` 作为最新候选，`person_fullframe_with_new_labels_baseline` 作为稳健基线；写入 split `2105 / 453 / 451`，并补齐 `img768` Val / Test 指标与 `640` 稳健基线 Test 指标。
   - PPT 页内明确取舍：`img768` 的 `mAP50-95` 更高，但 `640` 稳健基线的 Precision / Recall / mAP50 更稳，因此 `img768` 先作为最新候选，不直接写成已替代稳健基线。
   - 同步更新 `backend-train-model/AGENTS.md`，沉淀当前 new labels 工服与 person 可用基线 / 候选权重及指标，避免后续汇报或训练文档回退到旧口径。
3. 涉及文件：
   - `backend-train-model/docs/PPT/大创PPT汇报_人工复核阶段版_训练进展更新_20260513.pptx`
   - `backend-train-model/docs/PPT/大创PPT汇报_人工复核阶段版_20260513.pptx`（只读作为上一版来源，未覆盖）
   - `backend-train-model/docs/PPT/大创PPT汇报.pptx`（未覆盖）
   - `backend-train-model/AGENTS.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练配置项。
   - 无新增 CLI 参数。
   - 无新增或替换模型权重；本轮只引用已有训练产物和评估报告，生成新的 PPT 汇报副本。
5. 兼容性注意：
   - 第 4 页为适配完整指标文本，采用两张更大的内容卡片承载 `clothes` 与 `person` 两条线，删去了上一版右侧小卡片式阶段收口内容；这是汇报版式调整，不改变训练结论本身。
   - `person_fullframe_with_new_labels_img768` 只写为“最新候选”，不是默认上线权重或已替换稳健基线；后续若要升级默认基线，仍需结合稳定性、召回和实际误检 / 漏检复盘。
6. 本轮明确不改动：
   - 不覆盖原始 PPT 或上一版人工复核阶段 PPT。
   - 不修改训练代码、prepare 流程、数据集 split、评估脚本、模型权重或在线检测链路。
   - 不修改人工复核原始记录、review 图片素材或历史阶段台账。

## 2026-05-13 生成阶段汇报 PPT 人工复核版

1. 变更来源：用户要求参考 `backend-train-model/person-train-model/train-docs/人工复核.md` 中的四次人工复核任务，以及 `person_fullframe_with_new_labels_hard_sample_review/` 下前三次复核记录，修改 `backend-train-model/docs/PPT/` 下现有 `.pptx` 阶段汇报；要求保留源文件，不覆盖原 PPT，并在新稿中加入对应图片例证。
2. 变更总览：
   - 新增 `backend-train-model/docs/PPT/大创PPT汇报_人工复核阶段版_20260513.pptx`，源 `大创PPT汇报.pptx` 保持不覆盖。
   - 新稿沿用原 PPT 的标题栏、卡片、双图对照页等版式与字体样式，仅在副本中更新阶段内容。
   - 更新代表帧页口径：把 `D15_20260119061405_frame_0346` 写作“可见性弱型”例证，把 `D15_20260119203927_frame_0180` 写作 `crowded / overlap` 例证，并明确对应 5.6 / 5.7 / 5.10 复核结论。
   - 将原“对应的解决方案”页调整为“人工复核阶段成果”，概括 `5.6` 第一轮语义复核、`5.7` 双主线确认、`5.10` 机制复盘启动三步。
   - 新增“人工复核例证”页，加入 `D05_20260123074841_frame_0029` 的 crowded / overlap 对照图，以及 `D02_20260123074836_frame_0023` 的远景 / 贴边对照图。
   - 新增“下阶段任务安排（5.13）”页；按用户当前汇报口径，将 `5.13` 写作下一阶段任务，而不是本阶段已完成成果。
3. 涉及文件：
   - `backend-train-model/docs/PPT/大创PPT汇报_人工复核阶段版_20260513.pptx`
   - `backend-train-model/docs/PPT/大创PPT汇报.pptx`（只读参考，未覆盖）
   - `backend-train-model/docs/update_log.md`
   - 参考素材目录：`backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/`
4. 新增 / 变更配置项：
   - 无新增训练配置项。
   - 无新增 CLI 参数。
   - 本轮仅生成汇报材料，不改动数据准备、训练、评估或在线检测逻辑。
5. 兼容性注意：
   - 新 PPT 中的 `5.13` 页服从用户当前汇报要求，作为“下阶段任务安排”呈现；这与目录中已有 `active_stage.json` 的历史状态记录不冲突，因为本轮没有修改人工复核台账本身。
   - 新稿中的人工复核成果只把 `5.6`、`5.7`、`5.10` 作为本阶段已完成内容；`5.13` 不写成已完成成果。
6. 本轮明确不改动：
   - 不覆盖原始 PPT。
   - 不修改 `人工复核.md`、各阶段 `semantic_bucket_summary.md`、`semantic_bucket_manifest.json` 或 `sequence_notes`。
   - 不修改任何训练代码、配置文件、权重或 review 原始图片素材。

## 2026-05-13 新增 5.13 阶段承接 crowded 主线正式收口

1. 变更来源：用户要求不要把当前新结论继续写入 `5.10` 段，而是新开 `5.13` 阶段，独立沉淀 crowded / overlap 主线的正式结论、已发现问题和下一阶段任务。
2. 变更总览：
   - 新增 `stage_reviews/stage_2026-05-13_crowded_overlap_formal_closeout/` 阶段目录，并补齐 `stage_meta.json`、`semantic_bucket_manifest.json`、`semantic_bucket_summary.md` 与三条 `sequence_notes/**/5-13notes.md`。
   - 更新 `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/active_stage.json`，把当前 active stage 从 `5.10` 切换到 `5.13`。
   - 更新 `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/review_stage_index.md`，把 `5.13` 调整为当前激活阶段，并把 `5.10` 降为历史阶段。
   - 更新 `backend-train-model/person-train-model/train-docs/人工复核.md`，新增 `## 5.13 crowded/overlap正式收口与下一阶段任务确认`，并把 `5.10` 明确改成历史阶段口径；同时把 `5.13` 段改写为与 `5.10 / 5.7` 一致的阶段结构，补齐“今天应该先做什么”“建议的压缩节奏”“当前阶段收口标准”“当前阶段人工复核具体怎么做”“今天的最低交付”等固定小节。
   - 保持 `5.10` 阶段 `semantic_bucket_manifest.json` 与 `semantic_bucket_summary.md` 继续只表达 `2026-05-10` 当天的阶段目标和机制收口要求，不把 `5.13` 的正式结论继续回写进去。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/active_stage.json`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/review_stage_index.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-13_crowded_overlap_formal_closeout/stage_meta.json`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-13_crowded_overlap_formal_closeout/semantic_bucket_manifest.json`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-13_crowded_overlap_formal_closeout/semantic_bucket_summary.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-13_crowded_overlap_formal_closeout/sequence_notes/sequence_D15_20260119203927/5-13notes.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-13_crowded_overlap_formal_closeout/sequence_notes/sequence_D05_20260123074841/5-13notes.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-13_crowded_overlap_formal_closeout/sequence_notes/sequence_D15_20260119061405/5-13notes.md`
   - `backend-train-model/person-train-model/train-docs/人工复核.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练配置、数据配置或脚本参数。
   - 本轮只新增人工复核阶段台账与阶段入口切换，不修改训练代码、prepare 流程、评估命令、数据集切分、模型权重或在线链路代码。
5. 兼容性注意：
   - `5.13` 阶段的正式收口结论，仍然主要依据 `5.10` 现有 notes，因此 `D15_20260119203927_frame_0143 / 0180` 继续属于“按 sequence 级结论保守收口”的写法，不等于它们已经补齐和 `D05` 一样细的逐帧证据表。
   - 当前正式收口更偏 `second_person_no_response`，但并不代表 `merge_two_people` 已被永久排除；它仍保留为后续需要继续核验的伴随分支。
   - `D15_20260119061405` 继续只作为“可见性弱型”对照序列使用；本轮没有为修正对照 notes 的局部措辞而回改 `5-10notes.md`。
6. 本轮明确不改动的部分：
   - 不修改 `stage_2026-05-10_crowded_overlap_mechanism_closeout/sequence_notes/**/5-10notes.md` 正文。
   - 不修改 `5.7` 与 `5.6` 历史阶段的 summary / manifest / notes 正文内容。
   - 不修改 `by_source/` 共享素材、训练脚本、prepared 数据集、评估报告、模型权重和在线链路代码。

## 2026-05-10 细化 5.10 阶段 sequence notes 模版并补齐字段中文注释

1. 变更来源：用户指出 `stage_2026-05-10_crowded_overlap_mechanism_closeout/sequence_notes` 下的 `5-10notes.md` 模版还不够易填，要求把几个 notes 模版都改好，并为每个字段补上清晰的中文注释和代表含义，便于组员直接按模版填写。
2. 变更总览：
   - 更新 `sequence_D15_20260119203927/5-10notes.md`，新增字段填写说明、逐帧模版和 sequence 级结论模版，并对 `semantic_*`、`mechanism_*`、`need_relabel`、`relabel_status` 等字段补上中文含义说明。
   - 更新 `sequence_D05_20260123074841/5-10notes.md`，补齐与 crowded / overlap 主线一致的逐帧记录模版、sequence 级结论模版和字段中文说明。
   - 更新 `sequence_D15_20260119061405/5-10notes.md`，为“可见性弱型”对照序列新增对照帧记录模版、对 crowded 主线的区分作用字段，以及 `need_relabel / relabel_status` 等中文说明。
   - 继续把三份 notes 模版从“条目式说明”升级为“表格化填写说明 + 表格化逐帧模版 + 表格化 sequence 结论模版 + 示例填写”，让组员能够直接照表填，不必再自行理解字段结构。
   - 对照三份 `5-10notes1.md` 中已经完成的问答结果，把**已确认的 sequence / 对照序列级结论**直接并入正式 `5-10notes.md` 的原模版结构中：包括 D15 crowded 主线更偏“第二人无响应”、D05 crowded 辅助对照更偏“一框合两人且存在遮挡叠加匹配失败”、D15_20260119061405 仍稳定属于“可见性弱型”对照，并明确哪些内容仍待后续逐帧细分。
   - 本轮只改 `5.10` 阶段 notes 模版与填写口径，不直接替用户填写逐帧结论，也不提前回填 `semantic_bucket_manifest.json` 与 `semantic_bucket_summary.md`。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-10_crowded_overlap_mechanism_closeout/sequence_notes/sequence_D15_20260119203927/5-10notes.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-10_crowded_overlap_mechanism_closeout/sequence_notes/sequence_D05_20260123074841/5-10notes.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-10_crowded_overlap_mechanism_closeout/sequence_notes/sequence_D15_20260119061405/5-10notes.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练配置、数据配置或脚本参数。
   - 本轮只细化人工复核 notes 模版的字段解释与填写结构，不改动训练逻辑、评估命令、数据集切分、模型权重或在线链路代码。
5. 兼容性注意：
   - 本轮新增的是“便于人工填写”的中文字段说明，不改变 `semantic_bucket_manifest.json` 既有字段名和预期取值。
   - 正式 `5-10notes.md` 不再额外写明“从 `5-10notes1.md` 同步”，而是直接保留原模版结构并写入当前已确认结论；`5-10notes1.md` 继续保留为中间工作记录即可。
   - 只有当组员按新模版真正补齐逐帧判断后，才适合把结论同步回写到 `semantic_bucket_manifest.json` 与 `semantic_bucket_summary.md`；当前 notes 结构更新本身不代表结论已完成。
6. 本轮明确不改动的部分：
   - 不修改 `5.7` 与 `5.6` 历史阶段正文内容。
   - 不修改 `semantic_bucket_manifest.json`、`semantic_bucket_summary.md`、`by_source/` 共享素材、训练脚本、prepared 数据集、评估报告、模型权重和在线链路代码。

## 2026-05-10 直接重导 `by_source` overlay 并将中文图例并入生成流程

1. 变更来源：用户要求不要只在现有 overlay 上做二次后处理，而是直接重新生成一份并覆盖 `person_fullframe_with_new_labels_hard_sample_review/by_source/` 下原有 overlay 图片。
2. 变更总览：
   - 修改 `backend-train-model/person-train-model/train-code/export_hard_review_assets.py`，将左上角中文图例直接并入 `create_overlay()` 生成流程。
   - 图例随 overlay 原生导出，明确区分：蓝色匹配预测框、绿色匹配 GT 框、红色 FN GT 框，以及可能出现的橙色 FP 预测框。
   - 重新执行 `export_hard_review_assets.py`，覆盖 `by_source/**/overlays/*.jpg` 下原有复核 overlay 图，使后续重新导出时默认就带中文说明。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-code/export_hard_review_assets.py`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/by_source/**/overlays/*.jpg`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练配置、数据配置或脚本参数。
   - 本轮只改 overlay 生成样式，不改动训练逻辑、prepare 流程、评估命令、数据集切分和模型权重。
5. 兼容性注意：
   - 从本轮之后，只要重新运行 `export_hard_review_assets.py`，导出的 by_source overlay 就会自带中文图例，不再依赖额外的二次标注步骤。
   - 重新导出 by_source 时，`images/`、`labels/`、`README.md`、`review_asset_manifest.json` 和发送 zip 也会按脚本现有逻辑一并刷新；当前没有改动这些结构的字段语义。
6. 本轮明确不改动的部分：
   - 不修改人工标注文件、`stage_reviews/` 台账、训练脚本主流程、prepared 数据集、评估报告、模型权重和在线链路代码。

## 2026-05-10 为 `by_source` overlay 批量补中文框颜色图例

1. 变更来源：用户要求对 `person_fullframe_with_new_labels_hard_sample_review/by_source/` 下的复核图补充清晰的中文图例，明确区分蓝色框、绿色框、红色框各自含义，并应用到整批 `by_source` 复核 overlay 图片上。
2. 变更总览：
   - 新增脚本 `backend-train-model/person-train-model/train-code/annotate_by_source_overlay_legend_zh.py`，递归处理 `by_source/**/overlays/*.jpg`。
   - 在每张 overlay 左上角增加中文图例，明确说明：`GT=人工标注`、`Pred=模型检测`，并区分蓝色匹配预测框、绿色匹配 GT 框、红色漏检 GT 框，以及可能出现的橙色 FP 预测框。
   - 本轮只处理复核 overlay 图，不修改 `images/` 下原图、`labels/` 下标注文件及 review 台账结构。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-code/annotate_by_source_overlay_legend_zh.py`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/by_source/**/overlays/*.jpg`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练配置、数据配置或脚本参数。
   - 本轮新增的是 overlay 可视化后处理脚本，不改动训练逻辑、prepare 流程、评估命令、数据集切分和模型权重。
5. 兼容性注意：
   - 图例脚本默认直接覆盖 `overlays/` 里的 jpg 文件，因此后续如果重新执行 `export_hard_review_assets.py` 或重新导出 by_source 复核图，可能需要再次运行本脚本补回中文图例。
   - 图例语义基于当前 by_source overlay 生成口径：绿色表示已匹配 GT，蓝色表示与该 GT 成功匹配的预测框，红色表示 FN GT，橙色表示 FP 预测框。
6. 本轮明确不改动的部分：
   - 不修改 `images/` 原图、`labels/` 标注文件、`review_asset_manifest.json`、`stage_reviews/` 台账、训练脚本主流程、prepared 数据集、评估报告、模型权重和在线链路代码。

## 2026-05-10 加快 `5.10` 阶段推进节奏并压缩训练前置等待

1. 变更来源：用户指出当前项目进度较赶，`backend-train-model/person-train-model/train-docs/人工复核.md` 中 `5.10` 阶段推进节奏偏慢；要求只修改 `5.10` 部分，给同一阶段配置更多当轮任务，不再把训练前置动作拉成过长链路。
2. 变更总览：
   - 仅重写 `人工复核.md` 的 `5.10 crowded/overlap机制收口与下一阶段启动准备` 部分，保留 `5.7` 与 `5.6` 历史阶段正文不动。
   - 将 `5.10` 的执行口径从“先做机制收口，再择机判断下一步”改成“机制收口 + relabel 判断 + 下一轮训练入口判断”同一轮并行推进。
   - 新增压缩节奏、当天最低交付、当日分流结论等内容，要求 crowded 重点帧、manifest 回写、sequence notes、summary 结论和训练入口判断尽量在同一天内形成闭环。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/人工复核.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练配置、数据配置或脚本参数。
   - 本轮只调整 `5.10` 阶段的人工复核执行节奏、任务密度与输出要求，不修改训练代码、prepare 流程、评估命令、数据集切分、模型权重或在线链路代码。
5. 兼容性注意：
   - 本轮只是把 `5.10` 阶段的推进方式改得更紧凑，不改变当前 hardest FN 的两条主线判断，也不把多变量训练升级为默认动作。
   - 即使强调加快节奏，`5.10` 仍然要求先完成 crowded / overlap 主机制收口，再决定是否走 hard sample 治理、ROI 证据链补充或修框 / 补标分支。
6. 本轮明确不改动的部分：
   - 不修改 `5.7` 与 `5.6` 历史阶段正文内容。
   - 不修改 `stage_reviews/` 下现有复核记录、`by_source/` 共享素材、训练脚本、prepared 数据集、评估报告、模型权重和在线链路代码。

## 2026-05-10 按日期口径新增 `5.10` 人工复核阶段并切换 active stage

1. 变更来源：用户指出 `5.7` 是按日期编号的历史阶段，不应继续把它当成今天的默认阶段；要求直接修改当前人工复核入口，使文档与阶段索引改成“`2026-05-10` 这一天应该做什么”。
2. 变更总览：
   - 更新 `backend-train-model/person-train-model/train-docs/人工复核.md`，新增 `## 5.10 crowded/overlap机制收口与下一阶段启动准备`，明确今天的阶段目标、优先帧、机制级收口要求、退出条件与不建议优先做的事项。
   - 将 `5.7` 在手册中的定位改成“`2026-05-07` 历史阶段”，不再把它写成今天默认执行入口；同时保留 `5.6` 作为更早历史阶段。
   - 更新 `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/active_stage.json`，把当前 active stage 从 `5.7` 切换到 `5.10`。
   - 更新 `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/review_stage_index.md`，把当前激活阶段、历史阶段顺序和使用建议同步改成按日期推进的口径。
   - 新增 `stage_reviews/stage_2026-05-10_crowded_overlap_mechanism_closeout/` 阶段目录及初始台账文件：
     - `stage_meta.json`
     - `semantic_bucket_summary.md`
     - `semantic_bucket_manifest.json`
     - `sequence_notes/**/5-10notes.md`
   - `5.10` 阶段的 manifest 改成承接 `5.7` 已有语义结论、继续补 `mechanism_primary / mechanism_secondary / mechanism_confidence` 的结构，避免今天再把 `5.7` 已完成的语义桶重做一遍。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/人工复核.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/active_stage.json`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/review_stage_index.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-10_crowded_overlap_mechanism_closeout/stage_meta.json`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-10_crowded_overlap_mechanism_closeout/semantic_bucket_summary.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-10_crowded_overlap_mechanism_closeout/semantic_bucket_manifest.json`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-10_crowded_overlap_mechanism_closeout/sequence_notes/**/5-10notes.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练配置、数据配置或脚本参数。
   - 本轮新增的是人工复核阶段目录与台账字段，不修改训练代码、prepare 流程、评估命令、数据集切分、模型权重或在线链路代码。
5. 兼容性注意：
   - 从本轮之后，`5.7` 明确视为 `2026-05-07` 当天的历史阶段；今天默认应以 `5.10` active stage 为准。
   - `5.10` 阶段的 manifest 重点补的是机制字段，不建议再把 `5.7` 已完成的语义字段整轮重抄一遍。
   - 如果后续进入 `5.11` 或更高日期阶段，应继续沿用这种“按日期开新阶段 + active stage 切换 + 历史阶段保留”的写法。
6. 本轮明确不改动的部分：
   - 不修改 `5.7` 与 `5.6` 阶段已经归档的 summary / manifest / notes 正文内容。
   - 不修改 `by_source/` 共享素材、`review_asset_manifest.json`、训练脚本、prepared 数据集、评估报告、模型权重和在线链路代码。

## 2026-05-10 重排 person 人工复核 / ROI-aware / fullframe 后续文档的当前口径

1. 变更来源：用户要求把当前更合理的下一步方案按优先级写回 `backend-train-model/person-train-model/train-docs/人工复核.md`，并同时审核、清理和改写多份已经过时的 person / ROI 训练文档，删除对现阶段参考价值不高的旧方案，换成真正更有价值的当前行动口径。
2. 变更总览：
   - 继续更新 `backend-train-model/person-train-model/train-docs/人工复核.md`，把文档入口明确切到 `active_stage.json`，补充 `5.7 crowded/overlap` 当前还差什么、收口标准、默认执行入口、双主线与机制级复盘要求，并把后半部分的通用流程改成以 current active stage 驱动的写法。
   - 重写 `backend-train-model/person-train-model/train-docs/roi_next_iteration_plan.md` 的正文定位，明确它是“当前阶段行动计划”而不是历史 runbook；保留当前主线、已完成复盘结论和 `ioa20` 触发条件，同时把命令块下沉为附录，不再让命令本身盖过优先级判断。
   - 重写 `backend-train-model/person-train-model/train-docs/roi_problem_solution.md` 的文档定位，使其从“下一版建议方案”切换为“规则设计背景与现行口径说明”；保留 `center_inside` 太硬、`bottom_center_inside`、IoA 语义、`0.25` 起点等长期有效解释，同时删除/降级已经被 v2/v3 与后续实验证据覆盖的“推荐落地顺序 / 推荐训练对照 / 下一版最推荐方案”等过时未来时态内容。
   - 重写 `backend-train-model/person-train-model/train-docs/person_train_solution.md` 的主叙事，从“fullframe 扩样后的小目标改进方案”切到“hardest FN 双主线分析与后续方案”，新增基于 `5.7` 人工复核的最新记录，明确：当前主问题已拆成“可见性弱型”和“crowded / overlap 型”，远景 / 贴边更多是对照子类，不再继续把 `small_boundary_person` 或单纯 `img768` 收益当成整条线的主推进框架。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/人工复核.md`
   - `backend-train-model/person-train-model/train-docs/roi_next_iteration_plan.md`
   - `backend-train-model/person-train-model/train-docs/roi_problem_solution.md`
   - `backend-train-model/person-train-model/train-docs/person_train_solution.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练配置、数据配置或脚本参数。
   - 本轮仅更新 person / ROI 训练文档、人工复核手册和文档优先级口径，不修改训练代码、prepare 流程、评估命令逻辑、数据集切分、模型权重或在线链路代码。
5. 兼容性注意：
   - `roi_problem_solution.md` 现在主要承担“规则设计背景”职责，不应再被误用成当前行动计划；当前行动优先级应以 `roi_next_iteration_plan.md` 为准。
   - `person_train_solution.md` 现在不再把整条 fullframe 线主要写成“小目标改进方案”；如果后续文档或汇报仍沿用旧标题口径，应同步调整为更贴近 hardest FN 双主线的表述。
   - `人工复核.md` 虽然继续保留 `5.6` 历史阶段，但当前默认执行入口必须以 `active_stage.json` 为准；后续新增 `5.8` 或更高阶段时，应继续沿用这种“历史保留 + active stage 驱动”的写法。
6. 本轮明确不改动的部分：
   - 不修改 `stage_reviews/` 下已有人工复核记录正文内容。
   - 不修改 `by_source/` 共享素材、`review_asset_manifest.json`、训练脚本、prepared 数据集、评估报告、模型权重和在线链路代码。

## 2026-05-08 全仓库复查顶层 sequence notes 依赖并删除冗余索引目录

1. 变更来源：用户要求先全仓库检查是否还存在对 `person_fullframe_with_new_labels_hard_sample_review/sequence_*/notes.md` 的引用，再检查 README / 手册 / 组员说明文本是否都已经切换到 `stage_reviews/` 结构；若确认没有实际依赖，则删除顶层 `sequence_*` 目录，并同步更新相关说明文档。
2. 变更总览：
   - 复查后确认：当前仍提到顶层 `sequence_*/notes.md` 的主要是历史 `update_log.md` 记录；用于实际协作和当前操作的文档已切到 `stage_reviews/` 结构。
   - 继续更新 `backend-train-model/person-train-model/train-docs/人工复核.md`，把阶段操作步骤进一步收敛到“当前激活阶段目录 + 5-xnotes.md + 当前阶段 summary/manifest”的真实写法，并删除仍然提示先打开顶层 sequence 索引页的现行指导。
   - 更新 `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/README.md`，将顶层 `sequence_*` 目录从“兼容保留层”进一步升级为“已不再需要的旧层”，明确后续只看 `stage_reviews/`。
   - 更新 `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/bucket_summary_links.md`，将跳转目标全部切换为 `review_stage_index.md`、`active_stage.json` 与 `stage_reviews/stage_*/sequence_notes/`。
   - 更新 `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/review_stage_index.md`，去掉“顶层 `sequence_*/notes.md` 仍作为兼容层”的表述，改为明确写出其历史过渡任务已完成。
   - 在确认当前操作文档已切换后，删除 review 根目录下 5 个顶层 `sequence_*` 索引目录：
     - `sequence_D15_20260119061405/`
     - `sequence_D15_20260119203927/`
     - `sequence_D02_20260123070624/`
     - `sequence_D02_20260123074836/`
     - `sequence_D05_20260123074841/`
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/人工复核.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/README.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/bucket_summary_links.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/review_stage_index.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/sequence_D15_20260119061405/`（删除）
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/sequence_D15_20260119203927/`（删除）
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/sequence_D02_20260123070624/`（删除）
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/sequence_D02_20260123074836/`（删除）
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/sequence_D05_20260123074841/`（删除）
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练配置、数据配置或脚本参数。
   - 本轮仅清理 review 目录中的冗余索引层并更新文档入口，不修改训练代码、prepare 流程、评估命令、数据集切分或模型权重。
5. 兼容性注意：
   - 当前全仓库历史 `update_log.md` 仍保留旧路径文本，作为历史记录的一部分；这些文本不再代表当前实际使用路径，也不应继续作为操作入口。
   - 从本轮之后，若有人再按旧路径寻找 `sequence_*/notes.md`，应统一改为：先看 `review_stage_index.md` / `active_stage.json`，再进入对应 `stage_reviews/stage_*/sequence_notes/`。
   - 根级 `semantic_bucket_summary.md` 与 `semantic_bucket_manifest.json` 仍保留为兼容入口，因此删除顶层 `sequence_*` 后，不影响当前阶段 summary / manifest 的定位方式。
6. 本轮明确不改动的部分：
   - 不修改 `stage_reviews/` 下两轮已归档 notes / summary / manifest 的正文内容。
   - 不修改 `by_source/` 共享素材、`review_asset_manifest.json`、训练脚本、prepared 数据集、评估报告、模型权重和在线链路代码。

## 2026-05-08 细化分阶段人工复核操作说明并明确顶层 sequence 索引目录处置策略

1. 变更来源：用户要求继续修改 `backend-train-model/person-train-model/train-docs/人工复核.md`，让每个阶段下“当前阶段人工复核具体怎么做”写得更具体，必须包含目录结构、实际操作顺序与工具使用方式；同时询问在 `stage_reviews/` 已具备两轮完整 notes / summary / manifest 后，顶层 `sequence_*` 目录是否仍有保留必要。
2. 变更总览：
   - 进一步细化 `人工复核.md` 中 `5.7 crowded/overlap机械复盘及双主线推进` 的执行步骤，新增当前激活阶段目录结构示意、逐张复核顺序、三层记录方法、修框触发条件和双主线落地要求。
   - 同步细化 `人工复核.md` 中 `5.6 第一轮代表帧语义复核与结构化回填` 的执行步骤，新增历史阶段目录结构、第一批代表帧的实际回填流程、多人协作分工和“不要把新阶段发现回写到 5.6”的限制说明。
   - 把手册中残留的旧单例写法继续替换为新的阶段写法，例如明确要求把观察写到当前阶段 `5-xnotes.md`，把结构化记录写到当前阶段目录下的 `semantic_bucket_manifest.json`，把总结写到当前阶段目录下的 `semantic_bucket_summary.md`。
   - 更新 review 根目录 `README.md`，明确判断：顶层 `sequence_*` 目录从结构纯度上看已经成为“冗余兼容层”；当前暂时保留只是为了避免文档链接、组员习惯路径或外部脚本失效，后续确认无依赖后可以整体删除。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/人工复核.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/README.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练配置、数据配置或脚本参数。
   - 本轮仅细化人工复核手册与 review 总入口说明，不修改训练代码、prepare 流程、评估命令、数据集切分或模型权重。
5. 兼容性注意：
   - 当前顶层 `sequence_*` 目录虽然已被判断为结构性冗余，但本轮**没有直接删除**，仍保留为兼容层；这样可以避免已有相对路径、外部脚本或协作者本地使用习惯立刻失效。
   - 如果后续要真正删除顶层 `sequence_*` 目录，建议先统一检查：`人工复核.md`、`README.md`、其他 review 文档、组员说明文本以及可能引用这些路径的脚本是否都已经完全切到 `stage_reviews/` 结构。
6. 本轮明确不改动的部分：
   - 不删除当前顶层 `sequence_*` 索引目录。
   - 不修改 `stage_reviews/` 下两轮已归档 notes / summary / manifest 的正文结论内容。

## 2026-05-08 将人工复核产物改造成按阶段归档结构并补齐兼容入口

1. 变更来源：用户指出当前多轮人工复核反复覆盖同一个 `notes.md`、`semantic_bucket_summary.md`、`semantic_bucket_manifest.json`，不利于回溯，并要求我按阶段重新设计 review 工作台，直接落地目录结构、阶段索引、兼容入口和手册说明。
2. 变更总览：
   - 在 `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/` 下正式引入 `stage_reviews/` 分阶段归档结构，每一轮人工复核单独一个 `stage_*/` 子目录。
   - 新增阶段总索引 `review_stage_index.md` 与机器可读入口 `active_stage.json`，明确当前激活阶段、历史阶段顺序（最新在前）以及每轮的 summary / manifest / notes 位置。
   - 新增两轮阶段元信息文件：
     - `stage_reviews/stage_2026-05-07_crowded_overlap_dual_lines/stage_meta.json`
     - `stage_reviews/stage_2026-05-06_first_semantic_review/stage_meta.json`
   - 将原先根目录里持续覆盖的 summary / manifest 内容拆分为两轮阶段产物：
     - `stage_reviews/stage_2026-05-07_crowded_overlap_dual_lines/semantic_bucket_summary.md`
     - `stage_reviews/stage_2026-05-07_crowded_overlap_dual_lines/semantic_bucket_manifest.json`
     - `stage_reviews/stage_2026-05-06_first_semantic_review/semantic_bucket_summary.md`
     - `stage_reviews/stage_2026-05-06_first_semantic_review/semantic_bucket_manifest.json`
   - 将 5 条重点序列的人工复核正文改成按阶段单独存放，新增：
     - 5.7 阶段：`sequence_notes/sequence_*/5-7notes.md`
     - 5.6 阶段：`sequence_notes/sequence_*/5-6notes.md`
   - 把顶层 5 个 `sequence_*/notes.md` 全部改造成“阶段 notes 索引页”，不再继续承载新阶段正文。
   - 把根级 `semantic_bucket_summary.md` 改成兼容入口 Markdown，把根级 `semantic_bucket_manifest.json` 改成兼容入口 JSON，不再继续保存某一轮的真实 records。
   - 更新根目录 `README.md`，明确区分：共享素材目录、分阶段真实产物目录、以及顶层兼容 / 索引入口。
   - 同步更新 `backend-train-model/person-train-model/train-docs/人工复核.md`，把“当前阶段怎么写记录、写到哪里、多人怎么协作”的说明改成基于 `stage_reviews/` 的新结构，并把旧的单例写法改成阶段写法。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/README.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/review_stage_index.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/active_stage.json`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/semantic_bucket_summary.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/semantic_bucket_manifest.json`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/sequence_D15_20260119061405/notes.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/sequence_D15_20260119203927/notes.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/sequence_D02_20260123070624/notes.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/sequence_D02_20260123074836/notes.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/sequence_D05_20260123074841/notes.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-07_crowded_overlap_dual_lines/stage_meta.json`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-07_crowded_overlap_dual_lines/semantic_bucket_summary.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-07_crowded_overlap_dual_lines/semantic_bucket_manifest.json`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-07_crowded_overlap_dual_lines/sequence_notes/**/5-7notes.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-06_first_semantic_review/stage_meta.json`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-06_first_semantic_review/semantic_bucket_summary.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-06_first_semantic_review/semantic_bucket_manifest.json`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/stage_reviews/stage_2026-05-06_first_semantic_review/sequence_notes/**/5-6notes.md`
   - `backend-train-model/person-train-model/train-docs/人工复核.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练配置、数据配置或脚本参数。
   - 本轮新增的是 review 归档结构与文档入口，不修改训练脚本、prepare 流程、评估命令、数据集切分或模型权重。
5. 兼容性注意：
   - 根级 `semantic_bucket_summary.md` 与 `semantic_bucket_manifest.json` 现在都只作为兼容入口，不再代表某一轮人工复核的真实正文与真实 records；真实内容必须进入 `stage_reviews/stage_*/` 查看。
   - 顶层 `sequence_*/notes.md` 现在也只作为阶段 notes 索引页，不能再继续把新一轮观察直接写回这些单例文件。
   - `5.6` 阶段目录中的内容属于基于当前已知旧 notes / 旧 summary / 旧 manifest 重建后的历史阶段归档，其中 `stage_meta.json` 已明确写入 `reconstructed_from_root_snapshot=true`；后续如果拿到更原始的 5.6 快照，可以再替换。
   - 当前 `active_stage.json` 指向的是 `5.7 crowded/overlap机械复盘及双主线推进`；后续进入 `5.8` 或更高阶段时，应先更新 `人工复核.md` 中的最新阶段 H2，再同步新增 stage 目录并切换 active stage 指针。
6. 本轮明确不改动的部分：
   - 不修改 `by_source/` 下的共享复核素材和 `review_asset_manifest.json` 内容。
   - 不修改训练脚本、prepared 数据集、评估报告、模型权重、在线链路代码和既有实验指标口径。

## 2026-05-07 修订当前阶段汇报 PPT 中的问题与缺陷 / 解决方案页

1. 变更来源：用户要求继续修改 `backend-train-model/docs/PPT/workwear-stage-report-20260507/output.pptx`，将“问题与缺陷”“关键 FN 样例展示”“解决方案”三页改为基于 `person_fullframe_with_new_labels_baseline` 与 `person_fullframe_with_new_labels_img768` 的最新分桶与人工复核结论，不再沿用旧版 ROI-aware hard FN 口径。
2. 变更总览：
   - 将问题页改写为 `baseline 640` 与 `img768` 的 test FN 分桶对比，明确写出：当前主矛盾不是“贴边小人”，真正占大头的是 `medium_large_pose_or_appearance` 与 `small_interior_person`。
   - 将样例页改为 fullframe hard sample review 目录中的代表帧对照，使用 `D15_20260119061405_frame_0346` 与 `D15_20260119203927_frame_0180` 的 `baseline 640 / img768` overlay 图，直接展示“可见性弱型”和“crowded / overlap 型”两条主线。
   - 将解决方案页改写为最新执行顺序：先做 crowded / overlap 机理复盘，再按“可见性弱型 / crowded 型”两条主线推进，最后在需要时补正式复盘台账；同时明确“不优先把贴边小人当主因，不优先继续单纯放大 imgsz，也不在机制未明前直接跳到 NMS 调参”。
   - 同步更新本次 PPT 的 `narrative_plan.md`，让其素材来源与问题定义和最新版本保持一致。
3. 涉及文件：
   - `backend-train-model/docs/PPT/workwear-stage-report-20260507/output.pptx`
   - `backend-train-model/docs/PPT/workwear-stage-report-20260507/narrative_plan.md`
   - `tmp/slides/workwear-stage-report-20260507/build/build_deck.mjs`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新的训练配置项、数据配置项或评估脚本参数。
   - 本轮仅修订 PPT 叙事、示例图片与结论表达，不改动训练代码、模型权重、复盘脚本或数据集内容。
5. 兼容性注意：
   - 本轮汇报口径明确以 `person分桶.md` 与 `人工复核.md` 为准，避免继续沿用“ROI 边界过硬是唯一主矛盾”这一过时表述。
   - 新版问题页与解决方案页强调的是 fullframe baseline/img768 分桶后的真实结论，并不等于否定 ROI-aware 主线训练本身的阶段成果；二者在汇报中分别承担“当前效果展示”和“问题归因 / 下一步动作”两个不同角色。
6. 本轮明确不改动的部分：
   - 不修改任何训练脚本、prepared 数据集、评估报告、模型权重或在线链路代码。
   - 不覆盖旧版 `大创PPT汇报.pptx`，继续只维护 `workwear-stage-report-20260507/output.pptx` 这一当前阶段汇报版本。

## 2026-05-07 基于上一阶段模板生成当前阶段汇报 PPT

1. 变更来源：用户要求基于 `backend-train-model/docs/PPT/大创PPT汇报.pptx` 的背景和大体内容，按当前阶段已完成工作重新归纳汇报主线，并生成新的 `.pptx` 文件，且需要包含训练结果图展示。
2. 变更总览：
   - 新增当前阶段汇报输出目录 `backend-train-model/docs/PPT/workwear-stage-report-20260507/`，产出新的阶段汇报文件 `output.pptx`。
   - 新增 `narrative_plan.md`，明确这次 PPT 的受众、叙事主线、页码结构、素材来源和版式复用策略。
   - 新 PPT 继续沿用上一阶段的封面 / 目录 / 三段式章节结构和整体配色，但正文内容已改为“承接 ROI-aware 初版后的增量进展”，重点覆盖 `v2 -> v3` 迭代、对照实验、FP/FN 复盘、hard sample 语义归因和下一阶段推进顺序。
   - 在新 PPT 中加入当前主线 run 的训练结果图与 PR 曲线图，并加入两张关键 FN 复盘样例图，避免只保留文字总结。
3. 涉及文件：
   - `backend-train-model/docs/PPT/workwear-stage-report-20260507/narrative_plan.md`
   - `backend-train-model/docs/PPT/workwear-stage-report-20260507/output.pptx`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新的训练配置项、数据配置项或评估脚本参数。
   - 本轮仅新增阶段汇报材料及其叙事规划文件，不改动训练代码、数据集、模型权重或实验结论口径。
5. 兼容性注意：
   - 新 PPT 的叙事边界继续遵守 `backend-train-model/docs/阶段PPT汇报.md` 已收紧后的口径：上阶段已覆盖 ROI-aware 初版，本阶段默认从 `person_roi_aware_v2_from_fullframe` 之后继续汇报。
   - 文中关于当前主线、问题定义和下一步顺序的表述，统一以根 `AGENTS.md`、`backend-train-model/AGENTS.md` 以及 `person_train_compare.md / roi_next_iteration_plan.md / 人工复核.md` 的最新口径为准，避免回退到旧版“ROI 边界过硬是唯一主矛盾”的表述。
6. 本轮明确不改动的部分：
   - 不修改任何训练脚本、prepared 数据集、评估报告、模型权重或在线链路代码。
   - 不覆盖旧版 `大创PPT汇报.pptx`，仅在新目录中新增当前阶段汇报版本。

## 2026-05-07 调整人工复核手册中的 5.7 更新标题层级

1. 变更来源：用户要求修改 `backend-train-model/person-train-model/train-docs/人工复核.md`，不要在每个 H3 标题里重复写日期，而是把时间提升为单独的 H2 标题，作为阶段更新分隔。
2. 变更总览：
   - 调整 `backend-train-model/person-train-model/train-docs/人工复核.md` 的 5.7 更新结构。
   - 将原先写在两个 H3 标题中的 `5.7 更新` 提升为单独的 H2 标题：`## 5.7 更新`。
   - 保留原有两块内容，但将其改成该 H2 下的普通 H3 小节，分别用于记录“阶段性结论”和“当前下一步应该做什么”。
   - 补充一句层级说明，明确后续新增阶段更新时，继续按“日期 H2 -> 具体内容 H3”的方式追加。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/人工复核.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练配置、数据配置或脚本参数。
   - 本轮仅调整文档标题层级与写法，不修改训练代码、prepare 流程、评估命令、数据集切分或模型权重。
5. 兼容性注意：
   - 本轮只调整文档结构，不改变 5.7 更新段落本身承载的结论和执行优先级。
   - 后续如果继续追加新的阶段更新，建议沿用相同层级：先新增日期 H2，再在其下使用 H3 写具体结论与下一步动作，避免同一日期在多个小标题里重复出现。
6. 本轮明确不改动的部分：
   - 不修改 `semantic_bucket_summary.md`、`semantic_bucket_manifest.json` 的当前结论内容。
   - 不修改 `sequence_*/notes.md`、`by_source/` 素材、训练脚本、prepared 数据集与当前主线配置。

## 2026-05-07 根据 D15_20260119203927 新版 notes 同步更新语义汇总与人工复核下一步

1. 变更来源：用户补充并修订了 `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/sequence_D15_20260119203927/notes.md`，明确这条序列的 3 张代表帧分别属于“围栏遮挡”与“两人重叠”类型，并要求我重新同步 `semantic_bucket_summary.md`、`semantic_bucket_manifest.json`，再把新的下一步动作写入 `backend-train-model/person-train-model/train-docs/人工复核.md`，并明确标注为 5.7 更新。
2. 变更总览：
   - 更新 `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/semantic_bucket_manifest.json`，把 `D15_20260119203927_frame_0142 / 0143 / 0180` 的 `semantic_primary`、`need_relabel`、`relabel_status` 与备注从 pending 状态正式回填为人工结论。
   - 更新 `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/semantic_bucket_summary.md`，把本轮已完成记录从 `12 -> 15`，并同步修正语义桶分布：`occluded=5`、`crowded_or_overlap=5`、`partial_body=3`、`pose_or_shape_unusual=2`。
   - 在 summary 中明确写清：`D15_20260119203927` 与 `D15_20260119061405` 不是同质序列，当前 hardest FN 至少包含两条稳定主类型，即“可见性弱型”和“crowded / overlap 型”。
   - 同步修订 `backend-train-model/person-train-model/train-docs/人工复核.md`，新增 `2.1 / 2.2` 两个小节，显式标注为“5.7 更新”，把当前阶段结论与下一步工作顺序写清。
   - 在 `人工复核.md` 中把下一步明确收敛到 crowded / overlap 机制复盘、两条 D15 主线拆分推进，以及后续如需正式台账时再补 `split / gt_index / reviewed_by / reviewed_at` 等元数据。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/semantic_bucket_manifest.json`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/semantic_bucket_summary.md`
   - `backend-train-model/person-train-model/train-docs/人工复核.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练配置、数据配置或脚本参数。
   - 本轮仅同步人工复核结论与后续执行顺序，不修改训练代码、prepare 流程、评估命令、数据集切分或模型权重。
5. 兼容性注意：
   - 当前 `semantic_bucket_manifest.json` 与 `semantic_bucket_summary.md` 仍然严格依据五个 `sequence_*/notes.md` 已写内容回填，不额外读取图片或 overlay 去推断未写明字段；因此 `split`、`gt_index`、`reviewed_by`、`reviewed_at` 依旧保持空字符串或 `null`，这不代表这些字段不存在，只是当前 notes 尚未统一沉淀。
   - 本轮把 crowded / overlap 从“可能只是次要子问题”上调为“稳定主子类型之一”，但这仍然是基于当前 15 张代表帧人工复核得到的阶段结论，不等于已经完成更细粒度的机制归因；是否属于“合框 / 漏响应 / 匹配不过线”，仍需下一步继续复盘。
   - `人工复核.md` 中新增的 5.7 更新段落，属于当前阶段的执行优先级说明；如果后续 crowded / overlap 机制复盘得出新结论，应继续回写这份手册和 summary，避免文档口径落后于实际进展。
6. 本轮明确不改动的部分：
   - 不修改五个 `sequence_*/notes.md` 的原始人工文字记录。
   - 不修改 `by_source/` 下的复核素材、`review_asset_manifest.json`、训练脚本、prepared 数据集、现有实验结论和当前主线配置。

## 2026-05-07 按五个 sequence notes 回填 hardest FN 语义汇总与 manifest

1. 变更来源：用户说明已经完成 `person_fullframe_with_new_labels_hard_sample_review` 下五个重点序列的人工复核，要求我根据五个 `sequence_*/notes.md` 回填 `semantic_bucket_summary.md` 和 `semantic_bucket_manifest.json`，并给出本轮结论与下一步建议。
2. 变更总览：
   - 正式填写 `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/semantic_bucket_summary.md`，把五个重点序列的人工复核结果整理成可读结论。
   - 在 summary 中明确写入本轮覆盖范围：`5` 个序列、`15` 张代表帧、`15` 条 FN GT 记录，其中 `12` 条已补齐主/次语义，`3` 条仍待补齐。
   - 在 summary 中按 `semantic_primary` 汇总当前主桶分布，并补充对 `semantic_secondary` 的解释，强调当前 hardest FN 的主因更偏“可见性不足驱动的复合难例”，而不是纯边界小人或纯极小目标。
   - 在 summary 中补齐五个序列各自的“主问题 / 代表帧 / 下一步建议”，并把 `D15_20260119203927` 明确标记为当前仍待补齐人工主结论的对照序列。
   - 正式填写 `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/semantic_bucket_manifest.json`，按五个 `notes.md` 中已经写出的代表帧逐条回填 `records`。
   - 对 notes 中未统一给出的 `split`、`gt_index`、`reviewed_by`、`reviewed_at` 不做猜测补填，统一保留为空字符串或 `null`；对 `D15_20260119203927` 的 3 条记录以 `relabel_status=pending` 标识其仍待补齐人工语义结论。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/semantic_bucket_summary.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/semantic_bucket_manifest.json`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练配置、数据配置或脚本参数。
   - 本轮仅回填人工复核产物，不修改训练代码、prepare 流程、评估命令、数据集切分或模型权重。
5. 兼容性注意：
   - 当前 manifest 和 summary 严格依据五个 `sequence_*/notes.md` 已写内容生成，不额外读取图片或 overlay 去推断未写明字段，因此它们反映的是“本轮 notes 已明确沉淀出的人工结论”，不是全量 15 条记录都已完全闭环。
   - `D15_20260119203927` 的 3 条代表帧目前仍缺少 `semantic_primary`、`semantic_secondary`、`need_relabel` 等人工回填字段，所以当前桶分布只统计了其余 `12` 条已完成记录；后续若补齐这 3 条，需要同步更新 summary 和 manifest。
   - notes 中未统一给出 `split`、`gt_index`、`reviewed_by`、`reviewed_at`，因此本轮继续保持空值占位；如果后续需要把这些结果用于更正式的复盘台账，应先回到原始 FN 明细或由复核人补写后再更新。
6. 本轮明确不改动的部分：
   - 不修改五个 `sequence_*/notes.md` 的原始人工文字记录。
   - 不修改 `by_source/` 下的复核素材、`review_asset_manifest.json`、训练脚本、prepared 数据集、现有实验结论和当前主线配置。

## 2026-05-06 新增 person hardest val/test 分桶复盘文档并沉淀结论

1. 变更来源：用户要求说明 `person_fullframe_with_new_labels` 这条线中“对 hardest val/test 样本做分桶复盘”应该怎么做，并让我实际完成这轮分桶、给出最终结论；随后又要求把这次分桶结果写入 `backend-train-model/person-train-model/train-docs/person分桶.md`，再继续给出更贴近业务语义的二层归纳。
2. 变更总览：
   - 新增并填充 `backend-train-model/person-train-model/train-docs/person分桶.md`。
   - 文档明确写入本轮复盘口径：对 `baseline / img768` 的 `val / test` 四组结果，在 `conf=0.25 / nms_iou=0.7 / match_iou=0.5` 下做逐图 FP/FN 复盘，并对每个 FN GT 框计算 `best_iou / rel_height / min_edge_px` 后分桶。
   - 文档沉淀四类算法桶：`small_boundary_person`、`small_interior_person`、`medium_large_pose_or_appearance`、`crowded_or_localization`，并分别给出 baseline val、baseline test、img768 val、img768 test 的 FN 数量、占比、主要序列和 hardest 图片。
   - 文档补充 baseline 与 img768 的合并视角对比，明确记录：两者 hardest FN 的主体都不是单纯边界小人，而是 `medium_large_pose_or_appearance + small_interior_person`；`img768` 没有改变失败结构，反而让 `medium_large_pose_or_appearance` 占比更高。
   - 文档继续给出更贴近业务语义的二层归纳和下一步优先级：先围绕 `D15_20260119061405 / D15_20260119203927` 做中等/较大难例人工复核，再围绕 `D02_20260123070624 / D02_20260123074836` 看小型内部 / 边界人问题，最后才考虑是否把 `person-guided clothes` 提升为后续验证分支。
   - 按用户后续要求，不再单独拆新的 `person语义细分桶.md`，而是把“语义细分桶怎么做”直接并入 `person分桶.md`：新增最该优先人工复核的序列 / 图片、建议语义标签集合、逐 GT 标注字段、从算法分桶到人工语义复核的执行步骤，以及建议的 review 目录结构。
   - 文档明确写清：当前不需要把全部 FN 全量人工看完，更推荐“自动分桶预筛 + 关键代表帧人工复核”的两层流程；第一批优先帧聚焦 `D15_20260119061405_frame_0345/0346/0348/0355`、`D02_20260123070624_frame_0060/0061`、`D02_20260123074836_frame_0022`、`D05_20260123074841_frame_0026`。
   - 为了先把“算法预筛能做的全部做完”，本轮新增自动统计产物 `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_prescreen_summary.json`，在 4 个既有 FN 主桶之外，又额外计算了 `size_bin / pred_mode / crowd_bin / edge / combined repeated frames` 等辅助预筛结果。
   - `person分桶.md` 继续补入上述辅助预筛规则的显式定义，并把 4 个 run 的扩展统计表、4 run 合并后的 hardest sequences / repeated frames，以及自动评分后建议优先人工复核的代表帧名单写入文档。
   - 文档同时明确区分：FN 四桶是当前主结论的正式分桶口径；`size_bin / pred_mode / crowd_bin / edge` 是本轮新增的 heuristic 预筛规则，只用于先缩小人工复核范围，不应误写成长期固定 canonical 标准。
   - 按用户最新要求，文档又进一步明确写入当前推荐推进顺序：现阶段先固定“按实际 FN 样本分桶”为主线，暂不切换到“按 8 个来源桶分桶”的补充分桶；只有当第一轮人工语义复核结束后，仍需要做来源归因时，再回头补做 8 来源桶视角的统计。
   - 按用户后续要求，基于 `person分桶.md` 中推荐的目录结构，补齐了 `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/` 下的 review 目录骨架，新增 `README.md`、`bucket_summary_links.md`、`semantic_bucket_summary.md`、`semantic_bucket_manifest.json` 以及 5 个重点序列的 `notes.md` 模板，并在各个 Markdown 文件中用中文写清用途和使用方式。
   - 新增 `backend-train-model/person-train-model/train-docs/人工复核.md`，把人工复核所需软件、环境、安装方式、两种复核模式、LabelImg 具体使用步骤、语义标签解释、修框记录口径和第一轮建议执行顺序写成完整操作手册。
   - 新增 `backend-train-model/person-train-model/train-code/export_hard_review_assets.py`，用于把当前优先人工复核帧按 `prepare_report.json` 的 8 个来源自动整理到 review 工作台，并为每张图生成按 run 区分的 overlay 图。
   - 实际导出了 `20` 张当前优先人工复核图片，并在 `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/by_source/` 下按 8 个来源建立 `source_*` 目录；每个来源目录内再按 `sequence_*` 拆分，并分别放入 `images/`、`labels/`、`overlays/`。
   - 同步新增 `by_source/README.md` 与 `by_source/review_asset_manifest.json`，用于让组员按来源领取素材，并明确知道每张图对应哪些 run 的 overlay 文件。
   - 针对“直接发送原始目录 / jpg / txt 给组员时可能出现解析失败”的问题，导出脚本进一步新增 `by_source/send_packages/`，并按用户最新要求改为只生成 **1 个总压缩包** `all_sources__review_bundle.zip`，统一包含全部 `source_*` 顶层目录；不再按每条序列单独生成 zip。
   - 进一步细化 `sequence_D15_20260119203927/notes.md`，补齐当前实际已经导出的 3 张代表帧：`0142 / 0143 / 0180`。
   - 按用户最新要求，进一步把顶层 `sequence_*` 目录调整为“只保留 `notes.md` 记录文件”，不再在这些目录里重复维护图片、标签或 overlay；实际复核素材统一只放在 `by_source/` 下，同时同步修订 `person分桶.md`、`README.md`、相关 `notes.md` 和 `人工复核.md` 的说明口径。
   - 按用户后续要求，在 `人工复核.md` 中新增一版明确的“组员统一填写规范”：补充多人协作时谁改 `notes.md`、谁汇总 `semantic_bucket_manifest.json`、谁最终更新 `semantic_bucket_summary.md` 的推荐流程，并明确 `by_source/review_asset_manifest.json` 只是素材索引文件，人工复核过程中不需要修改。
   - 为避免组员误改全局文件，`人工复核.md` 进一步补充了可直接转发给组员的“最简规则”：默认只需要在 `by_source/` 看素材，并在对应 `sequence_*/notes.md` 记录观察；`semantic_bucket_manifest.json`、`semantic_bucket_summary.md` 与 `by_source/review_asset_manifest.json` 由指定汇总人或素材维护人统一处理。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/person分桶.md`
   - `backend-train-model/person-train-model/train-docs/人工复核.md`
   - `backend-train-model/person-train-model/train-code/export_hard_review_assets.py`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_prescreen_summary.json`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/README.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/bucket_summary_links.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/semantic_bucket_summary.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/semantic_bucket_manifest.json`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/by_source/README.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/by_source/review_asset_manifest.json`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/sequence_D15_20260119061405/notes.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/sequence_D15_20260119203927/notes.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/sequence_D02_20260123070624/notes.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/sequence_D02_20260123074836/notes.md`
   - `backend-train-model/person-train-model/train-result/review/person_fullframe_with_new_labels_hard_sample_review/sequence_D05_20260123074841/notes.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增 JSON 配置字段。
   - 本轮仅新增分析文档与结论，不修改训练脚本、project config、prepared 数据集、权重文件或评估命令。
5. 兼容性注意：
   - 文档中的分桶是基于现有 `fpfn_per_image.json` 复盘结果和统一几何规则得到的“算法分桶”，不是逐帧人工逐框标注的新真值；当前新增的语义细分桶部分主要是执行指南和目录设计，不等于已经完成全量人工语义标注。
   - 当前新增的 `size_bin / pred_mode / crowd_bin / edge` 统计，是为了本轮“先自动做完预筛”而显式定义的辅助 heuristic；后续若继续复用这些统计，必须沿用本文档写清的阈值，不要把它们误当成仓库历史上早已固定的官方桶定义。
   - `person_fullframe_with_new_labels_hard_sample_review/` 下新增的目录骨架和 Markdown 文件，当前主要承担“人工复核工作台”和“模板”作用，其中大部分文件仍属于待填写状态；它们不是已经完成的人工结论本身。
   - `by_source/` 下当前导出的图片集合，是基于这轮自动预筛后的优先人工复核名单整理出来的，不等于“全量 560 个 FN GT 全部拷出”；如果后续人工复核范围扩大，需要重新运行 `export_hard_review_assets.py` 或扩展选择逻辑。
   - `by_source/send_packages/` 里的 `all_sources__review_bundle.zip` 只是“更稳的传输形态”，不替代 `by_source/source_*/sequence_*/` 下的原始导出目录；人工复核仍以解压后查看素材、并把结论回写到 `notes.md / semantic_bucket_manifest.json / semantic_bucket_summary.md` 为准。
   - 当前推荐的目录职责已经调整为：`by_source/` 专门放实际复核素材，顶层 `sequence_*` 专门写记录；后续不要再把同一批图片 / 标签 / overlay 复制第二份到顶层 `sequence_*`，否则容易造成双份素材不一致。
   - 当前推荐的协作方式是：组员优先修改自己负责序列的 `notes.md`，再由汇总人批量更新 `semantic_bucket_manifest.json`，最后由组长或统一汇总人更新 `semantic_bucket_summary.md`；不要让多人同时直接改同一个 JSON 或 summary 文件。
   - 除非用户或组长明确指定，否则普通组员不应直接修改 `semantic_bucket_manifest.json`、`semantic_bucket_summary.md` 或 `by_source/review_asset_manifest.json`，以减少多人并发编辑带来的冲突风险。
   - `人工复核.md` 中当前默认推荐 LabelImg 作为 bbox 复核工具，Labelme 只作为可选补充；如果后续团队改用其他标注软件，应同步更新这份手册，避免文档和实际流程脱节。
   - 本轮把 `person分桶.md` 作为独立分析入口使用，不替代 `person_train_solution.md` 中更宏观的结论记录；两者应保持“一个讲全局方案，一个讲分桶细节”的分工。
6. 本轮明确不改动的部分：
   - 不修改 `person_train_solution.md`、`experence_from_yolov5.md` 的既有结论。
   - 不修改现有 clothes / person 训练脚本、prepared 数据集、权重、评估报告与当前主线配置。

## 2026-05-05 按 gnew 多视频拼接事实改造 new_clothes_train 切分策略并同步文档

1. 变更来源：用户明确说明 `gnew` 不是单一连续序列，而是由 `3~4` 个不同视频 / 场景拼接形成，要求按 `new_clothes_train/train-docs/check_log.md` 的建议修正切分逻辑，优先保证训练评估分布更稳，并同步更新运行文档与审查日志。
2. 变更总览：
   - 更新 `new_clothes_train/train-code/prepare_new_clothes_dataset.py`：将 gnew 的切分策略从 `sequence_contiguous_by_sorted_stem` 改为 `stratified_random_by_positive_empty`，按 `positive / empty` 两层独立随机分配 `train / val / test`，固定 `seed=42`。
   - 重新生成 `new_clothes_train/train-result/splits/clothes_merged_with_new_labels_v1.split.csv` 与 `clothes_merged_with_new_labels_v1_summary.json`。
   - 重新 build `new_clothes_train/train-result/datasets/clothes_merged_with_new_labels_v1/`，让新的 split 真正进入 merged 数据集。
   - 更新 `new_clothes_train/train-code/validate_new_clothes_source.py`：校验逻辑对齐 `build_merged_clothes_dataset.py` 的坐标容差与边界处理，避免把可被 builder 正常接受的轻微边界框误报为非法标注。
   - 更新 `new_clothes_train/train-docs/new_clothes_run_method.md`，把 gnew 新切分策略、修复后的分布统计、build 后关键计数和校验结果写成最新正式口径。
   - 更新 `new_clothes_train/train-docs/check_log.md`，把“旧版 contiguous 问题”与“本轮已执行修复结果”区分清楚，并把“gnew 由 3~4 个视频 / 场景拼接形成”升级为已确认事实。
3. 涉及文件：
   - `backend-train-model/new_clothes_train/train-code/prepare_new_clothes_dataset.py`
   - `backend-train-model/new_clothes_train/train-code/validate_new_clothes_source.py`
   - `backend-train-model/new_clothes_train/train-result/splits/clothes_merged_with_new_labels_v1.split.csv`
   - `backend-train-model/new_clothes_train/train-result/splits/clothes_merged_with_new_labels_v1_summary.json`
   - `backend-train-model/new_clothes_train/train-docs/new_clothes_run_method.md`
   - `backend-train-model/new_clothes_train/train-docs/check_log.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - gnew 切分策略：`sequence_contiguous_by_sorted_stem -> stratified_random_by_positive_empty`
   - gnew 切分随机种子：`seed=42`
   - gnew `holdout_group`：`new_source_sequence_contiguous_v1 -> new_source_stratified_random_v2`
   - 校验脚本新增容差常量：`COORD_TOLERANCE=1e-6`、`BOX_EDGE_TOLERANCE=1e-6`
5. 兼容性注意：
   - 这次修改不会影响 legacy `g31/g32/g33` 的 split 口径，它们仍沿用既有 `trainval_balanced_v1` 与 `unified_holdout_v1`。
   - 当前“分层随机切分”是为先修复 gnew `val/test` 分布失衡问题而采用的稳妥版本；它比旧 contiguous 方案更适合当前训练，但仍不是最终的“按真实视频场景整段切分”终态。
   - 如果后续能补齐每段视频对应的 stem 范围，建议继续升级为“按场景整段切分 + 场景级 split 分配”。
   - `validate_new_clothes_source.py` 的“非法标注”口径现在与 builder 对齐，因此更新后 `invalid_label_file_count=0` 不表示原始标注完全无边界贴边现象，而是表示不存在超出 builder 可接受容差的非法 YOLO 行。
6. 本轮明确不改动的部分：
   - 不修改 `All-train-model/` 下现有 baseline、历史 runs、旧 split manifest 和既有基线结论。
   - 不修改 `inspection-flask/` 在线链路、person 主线或其他监控方向代码。

## 2026-05-05 统一 person 主线分桶与 person-guided clothes 路线验证的优先级

1. 变更来源：用户指出 `person_train_solution.md` 中“先做 hard sample 分桶”和 `experence_from_yolov5.md` 中“person-guided clothes 路线验证”看起来像两套并列建议，要求统一两者的推进顺序并写回 person 训练分析文档。
2. 变更总览：
   - 在 `backend-train-model/person-train-model/train-docs/person_train_solution.md` 顶部新增一条 `2026-05-05` 记录段。
   - 明确区分：`person hard sample 分桶` 解决的是上游 `person` 主线诊断问题；`oracle / pred person-guided clothes` 解决的是下游 clothes 路线验证问题。
   - 统一写清当前优先级：先继续做 `person` 主线的 hard sample 分桶；再对 current clothes fullframe hardest cases 做轻量复盘；只有当 clothes 难例也明显集中在 person 附着小目标场景时，才启动小规模 `oracle person-guided clothes` 验证；只有 oracle 版明确胜出，才继续推进真实 `pred-personcrop clothes`。
   - 把 `experence_from_yolov5.md` 中的路线建议正式降为“person 主线之后的次级验证分支”，避免误解为当前要立即依赖尚不稳定的 person 预测框切换主线。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/person_train_solution.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增 JSON 配置字段。
   - 本轮仅统一分析文档中的优先级与术语边界，不改训练脚本、配置文件、评估命令或现有实验产物。
5. 兼容性注意：
   - 本轮没有否定 `person-guided clothes` 路线本身，而是把它的位置明确调整为：在 `person` 主线分桶之后、并且有 clothes hard case 证据支持时再启动的小规模验证分支。
   - 文档中的 `oracle person-guided clothes` 仍然只是路线验证概念，不等同于最终部署链路；后续若要落地到真实链路，仍需单独评估 `pred-personcrop clothes` 受到当前 person 上游误差影响的幅度。
6. 本轮明确不改动的部分：
   - 不修改 `backend-train-model/docs/experence_from_yolov5.md` 中已有结论，只在 `person_train_solution.md` 中补充统一后的主线优先级说明。
   - 不修改现有 clothes / person 训练脚本、prepared 数据集、权重、评估报告和既有基线指标。

## 2026-05-05 新增 new_clothes_train 的工服扩样整理配置与运行文档

1. 变更来源：用户提供新的 `clothes` 标注数据源，要求将其与 `All-train-model/` 中现有 legacy clothes 数据整合，在 `backend-train-model/new_clothes_train/` 下补齐整理脚本、build 配置、训练配置和运行文档，并确保缺失标注图片自动补空白 txt。
2. 变更总览：
   - 新增 `new_clothes_train/train-code/prepare_new_clothes_dataset.py`，用于扫描 `new_clothes_labels` 图片与标注、自动补齐空白 txt、继承旧 split manifest，并生成新的 merged split 清单与统计摘要。
   - 新增 `new_clothes_train/new_clothes_train_project_config.json`，默认训练参数对齐当前 clothes 主线：`imgsz=640`、`epochs=180`、`batch=4`、`patience=40`、`workers=4`、`device=0`、`seed=42`。
   - 新增 `new_clothes_train/clothes_merged_with_new_labels_v1.build.json`，沿用现有 `All-train-model/*.build.json` 的 JSON 风格，接入旧 7 个 legacy source 与新的 `gnew` source。
   - 新增 `new_clothes_train/new_clothes_run_method.md`，记录数据来源、缺标补空规则、切分方式、整理结果，以及 build / train / evaluate / export 命令。
   - 已生成 `new_clothes_train/train-result/working/new_source_prepare_summary.json`、`new_clothes_train/train-result/splits/clothes_merged_with_new_labels_v1.split.csv`、`new_clothes_train/train-result/splits/clothes_merged_with_new_labels_v1_summary.json` 等整理产物。
3. 涉及文件：
   - `backend-train-model/new_clothes_train/train-code/prepare_new_clothes_dataset.py`
   - `backend-train-model/new_clothes_train/new_clothes_train_project_config.json`
   - `backend-train-model/new_clothes_train/clothes_merged_with_new_labels_v1.build.json`
   - `backend-train-model/new_clothes_train/new_clothes_run_method.md`
   - `backend-train-model/new_clothes_train/train-result/working/new_source_prepare_summary.json`
   - `backend-train-model/new_clothes_train/train-result/splits/clothes_merged_with_new_labels_v1.split.csv`
   - `backend-train-model/new_clothes_train/train-result/splits/clothes_merged_with_new_labels_v1_summary.json`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 新增 `source_id=gnew`、`sequence_name=new_clothes_flat_2507` 的新数据源接入配置。
   - 新增 `split_manifest_csv=new_clothes_train/train-result/splits/clothes_merged_with_new_labels_v1.split.csv`。
   - 新增新源补齐标注目录：`new_clothes_train/train-result/working/new_source_completed_labels`。
   - 新增独立训练配置文件：`new_clothes_train/new_clothes_train_project_config.json`。
5. 兼容性注意：
   - 旧 7 个 legacy clothes source 不重新洗牌，继续继承 `trainval_balanced_v1` 与 `unified_holdout_v1` 的既有切分，避免破坏当前基线对照口径。
   - 新增 `gnew` 源当前按平铺文件名排序后做 `70/15/15` 连续切分；如果后续确认存在更细粒度时序边界，应再拆分 sequence 后重建 manifest。
   - `classes.txt` 被识别为说明性孤立文件，不参与样本配对或训练。
   - 构建 merged 数据集时应先进入 `backend-train-model/` 目录执行 `build_merged_clothes_dataset.py`，否则会因工作目录错误找不到脚本。
6. 本轮明确不改动的部分：
   - 不修改 `All-train-model/` 下现有 baseline、历史 runs、旧 split manifest 和已固化评估结论。
   - 不修改 `inspection-flask/` 在线链路、person 训练主线或其他监控方向代码。

## 2026-05-05 继续细化 YOLOv5 经验文档中的 person-guided clothes 执行顺序

1. 变更来源：用户进一步指出当前 person 指标并不乐观，要求把 `experence_from_yolov5.md` 中关于 `personcrop clothes` 的建议改得更严谨，避免误写成“现在就应直接依赖当前 person 预测框做主线”。
2. 变更总览：
   - 更新 `backend-train-model/docs/experence_from_yolov5.md` 中关于 `person-guided clothes` 的描述。
   - 明确区分三条路线：`fullframe clothes`、`oracle personcrop clothes`、`pred-personcrop clothes`。
   - 明确写入：当前更合理的优先级应是先做 **oracle 路线验证**，先判断“路线值不值”，而不是直接把 `pred-personcrop clothes` 升级为下一条默认主线。
   - 补充更详细的建议执行顺序：先复盘 fullframe hard cases，再做 oracle person-guided 对照，只有当 oracle 版明显优于 fullframe 时，才继续推进依赖当前 person 上游的真实 `pred-personcrop clothes`，之后再考虑更大模型、细粒度标签和更接近旧系统的端到端规则链实验。
3. 涉及文件：
   - `backend-train-model/docs/experence_from_yolov5.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增 JSON 配置字段。
   - 本轮仅细化分析文档中的实验顺序与术语边界，不修改训练脚本、配置文件或评估命令。
5. 兼容性注意：
   - 文档中的 `oracle personcrop clothes` 是“路线验证”概念，不等同于最终部署链路；后续若要落地为真实线上方案，仍需单独评估 `pred-personcrop clothes` 受到当前 person 上游误差影响的幅度。
   - 本轮没有否定 `person-guided clothes` 路线本身，而是把其研究顺序从“直接上依赖 person 预测框的主线”调整为“先做不依赖当前 person 质量的 oracle 验证”。
6. 本轮明确不改动的部分：
   - 不修改 `inspection-flask_old/` 下任何旧代码、旧权重或旧文档。
   - 不修改 `backend-train-model/` 下现有 clothes / person 训练脚本、prepared 数据集、基线指标和 person 训练主线结论。

## 2026-05-05 新增基于 inspection-flask_old 的 YOLOv5 工服经验审查文档

1. 变更来源：用户要求审查 `inspection-flask_old/` 中旧版 YOLOv5 工服检测代码，梳理其训练线索、数据切分线索与可借鉴经验，并将分析结论沉淀为新文档 `experence_from_yolov5.md`。
2. 变更总览：
   - 新增 `backend-train-model/docs/experence_from_yolov5.md`。
   - 文档系统性梳理了旧代码中能确认的 YOLOv5 工服线证据：权重入口、推理参数、person-guided 白底输入流程、`coat / cloth / shirt` 标签语义、以及旧线上规则判断方式。
   - 明确记录：`inspection-flask_old/` 内未保留可直接复现的 `train.py`、`val.py`、工服 `data.yaml`、split manifest 或正式评估报告，因此无法从当前旧仓库唯一还原其 train/val/test 切分方法。
   - 基于现有证据总结对当前 YOLOv8 clothes 训练最值得借鉴的方向：优先做 `person-guided clothes` 对照、优先解决小目标有效像素与背景干扰问题，再考虑更大模型、细粒度标签或更大输入尺寸。
3. 涉及文件：
   - `backend-train-model/docs/experence_from_yolov5.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增 JSON 配置字段。
   - 本轮仅新增分析文档，不修改训练脚本、数据集配置、评估口径或在线链路配置。
5. 兼容性注意：
   - 文档中的“旧 YOLOv5 训练与切分方法”只写入了当前仓库能核实的部分；未找到的训练脚本、dataset yaml 和 split 文件已明确标注为缺失，不应把推断写成既定事实。
   - 文档中的建议重点是路线借鉴，不代表当前应直接回退到 YOLOv5 或直接推翻现有 YOLOv8 fullframe baseline。
6. 本轮明确不改动的部分：
   - 不修改 `inspection-flask_old/` 下任何旧代码、旧权重或旧文档。
   - 不修改 `backend-train-model/` 下现有 clothes / person 训练脚本、prepared 数据集和基线指标。

## 2026-05-05 修订 person fullframe 扩样分析文档中的 img768 结论与后续顺序

1. 变更来源：用户要求基于已经完成的 `person_fullframe_with_new_labels_img768` 正式评估结果，修订 `person_train_solution.md` 中关于 `mAP50-95` 提升不上去的原因分析、两次训练早停结论以及后续推荐执行顺序。
2. 变更总览：
   - 在 `person_train_solution.md` 顶部新增 `2026-05-05` 记录段，保留 `2026-05-04` 旧记录作为历史对照。
   - 用当前正式 `train 768 + eval 768` 报告修正 `img768` 的外部 eval 数值：val `0.51466`、test `0.49699`。
   - 将“当前正式 `img768` 是按 640 误评估”的表述降级为历史命令风险说明，明确当前保留的正式 eval 报告已经按 `768` 运行。
   - 细化早停结论：明确 `img768` 可视为平台期 patience 早停；baseline 因为是 resume run，只表述为后段平台化，不再写成同等强度的标准早停证据。
   - 同步把推荐执行顺序改为：先锁定现有正式结论，再做 hard sample 分桶复盘，之后按小目标 / 暗光主因分流，最后再考虑更大模型或额外稳定性对照。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/person_train_solution.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增 JSON 配置字段。
   - 本轮仅更新分析文档口径与推荐执行顺序，不改训练 / 评估命令、不改脚本默认参数。
5. 兼容性注意：
   - 本轮不会重跑训练、评估或复盘脚本；文档中的最新结论以当前仓库已保留的 `results.csv`、`*_train.json`、`*_eval.json` 为依据。
   - `2026-05-04` 旧记录仍保留，后续阅读时应以前置的 `2026-05-05` 新记录为最新结论。
6. 本轮明确不改动的部分：
   - 不修改任何训练脚本、prepared 数据集、权重文件或评估报告内容。
   - 不改写 `person_run_method.md`、ROI-aware 相关配置和在线链路代码。

## 2026-05-05 修正 person fullframe img768 的评估命令口径

1. 变更来源：用户准备重新评估 `person_fullframe_with_new_labels_img768`，要求把运行文档中的对应评估命令替换成能够同时保证评估指标与报告元数据自洽的版本，并明确继续覆盖旧报告。
2. 变更总览：
   - 更新 `person_run_method.md` 中 `person_fullframe_with_new_labels` 的 `imgsz=768` 对照实验评估命令。
   - 在原有显式 `--project-config`、`--dataset-yaml`、`--run-name`、`--imgsz 768` 基础上，补充显式 `--weights backend-train-model\person-train-model\train-result\artifacts\runs\person_fullframe_with_new_labels_img768\weights\best.pt`。
   - 保持 `--report-name person_fullframe_with_new_labels_img768_eval` 不变，继续覆盖旧报告。
   - 同步把说明文字改成“评估入口整体对齐”的口径，明确本次不仅是修正 `imgsz=768`，也是为了让 `project_config_path`、`image_roots` 等报告元数据与当前 fullframe 扩样数据集保持一致。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/person_run_method.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增 JSON 配置字段。
   - 文档中的 `img768` 评估命令新增显式 `--weights` 参数。
   - 文档中的 `img768` 评估命令继续使用 `--report-name person_fullframe_with_new_labels_img768_eval` 覆盖旧报告。
5. 兼容性注意：
   - 本轮只更新运行文档，不重跑训练或评估；旧报告是否被覆盖取决于后续是否按新命令实际执行。
   - 只要继续使用同一个 `report_name`，重新评估后会覆盖同名旧报告；若未来需要并存多版结果，应改用新的 `report_name`。
6. 本轮明确不改动的部分：
   - 不修改训练脚本逻辑、prepare 逻辑或任何 ROI-aware 配置。
   - 不改写既有训练权重、prepared 数据集或历史指标结论。

## 2026-05-04 继续收口 person 兼容入口语义、ROI v1 路径冲突与 split-strategy 覆盖能力

1. 变更来源：用户继续做完整人工审查，进一步指出 `person_project_config.json` 的 `fullframe + roi.enabled=true` 语义混杂、`roi_v1` 与兼容入口共用 ROI 配置 / prepared 输出路径、以及 ROI-aware prepare 无法像 fullframe 一样临时覆盖 `split_strategy`。
2. 变更总览：
   - 更新 `person_project_config.json`：将兼容入口明确收口为 fullframe-only，`roi.enabled` 改为 `false`，避免再把该文件误当成 ROI-aware 正式入口。
   - 更新 `person_project_config.roi_v1.center_inside.json`：把 `roi.config_path` 版本化为 `roi_config.v1.center_inside.generated.json`，并把 `roi_aware_prepared_output_root` 独立为 `person_roi_aware_v1/sequence_contiguous`，避免与兼容入口或其他历史路径相互覆盖。
   - 更新 `run_person_flow.py` 与 `prepare_roi_aware_person_dataset.py`：为 ROI-aware prepare 补齐 `--split-strategy` 覆盖能力，并让 fullframe / ROI-aware 两条 prepare 路径都能从 CLI 临时覆盖切分策略。
   - 同步更新 `docs/config.md`，把 person 兼容入口、ROI-aware v1 prepared 路径，以及 `prepare-roi-aware --split-strategy` 的现状写清楚。
   - 额外核实 `roi_v1 keep_rule.min_box_ioa=0.0`：当前代码判断是 `roi_settings.min_box_ioa > 0.0 and box_ioa >= ...`，因此 `0.0` 不会导致 IoA 条件永远为真；本轮仅记录结论，不修改该逻辑。
3. 涉及文件：
   - `backend-train-model/person-train-model/person_project_config.json`
   - `backend-train-model/person-train-model/person_project_config.roi_v1.center_inside.json`
   - `backend-train-model/person-train-model/train-code/run_person_flow.py`
   - `backend-train-model/person-train-model/train-code/prepare_roi_aware_person_dataset.py`
   - `docs/config.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - `person_project_config.json -> roi.enabled: true -> false`
   - `person_project_config.roi_v1.center_inside.json -> roi.config_path: train-result/working/roi/roi_config.v1.center_inside.generated.json`
   - `person_project_config.roi_v1.center_inside.json -> person_dataset.roi_aware_prepared_output_root: train-result/prepared/person_roi_aware_v1/sequence_contiguous`
   - `run_person_flow.py -> --split-strategy`
   - `prepare_roi_aware_person_dataset.py -> --split-strategy`
   - `prepare_roi_aware_dataset(..., split_strategy=...)`：新增 ROI-aware 切分策略覆盖参数，并把实际生效值写入 `prepare_report.json`
5. 兼容性注意：
   - 现在省略 `--project-config` 时，wrapper 默认仍会回到 `person_project_config.json`，但该入口只保留 fullframe 兼容语义；若继续用它跑 ROI-aware prepare，会被更早拦截。这是刻意收紧，不再鼓励兼容入口承担 ROI-aware 正式职责。
   - `roi_v1` 的新路径不会自动迁移旧 prepared 目录或旧 ROI config 文件；历史产物仍保留原状，但后续若重跑 v1，应以新的版本化路径为准。
   - 本轮没有修改 `recommended_run_name` 在 ROI-aware 配置中的保留语义；正常 ROI-aware 默认 run 名仍由 `roi_aware_recommended_run_name` 提供。
6. 本轮明确不改动的部分：
   - 不修改任何已生成 prepared 数据集内容、训练权重或评估结果。
   - 不改写 `roi_v1 keep_rule.min_box_ioa=0.0` 的行为，因为当前实现已确认安全。
   - 不修改在线链路与其他监控方向代码。

## 2026-05-04 继续修复 person 配置消费中的 fullframe prepare、冗余字段与 ROI disabled 校验问题

1. 变更来源：用户继续人工复核 person 线，进一步指出 `all` 命令在 fullframe 路径下会因重复创建汇总标签目录而失败、`data.label_root` 是未被消费的死字段，以及 `roi.enabled=false` 时仍会执行 keep rule 校验存在潜在误伤风险。
2. 变更总览：
   - 修复 `run_person_flow.py`：`run_prepare_for_variant()` 的 fullframe 分支改为复用 `ensure_person_labels_available()`，避免 `all` 命令在 `overwrite=false` 时第二次创建 `aggregated_label_root` 直接报错。
   - 修复 `prepare_person_dataset.py`：当 `roi.enabled=false` 时，不再强制要求 `roi.keep_rule` 至少启用一条保留条件；只有启用 ROI-aware 时才执行该校验。
   - 清理 person 全部正式配置中的冗余 `data.label_root` 字段，避免误导读者以为 loader 会消费该字段；当前聚合标签真实入口仍是 `person_dataset.aggregated_label_root`。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-code/prepare_person_dataset.py`
   - `backend-train-model/person-train-model/train-code/run_person_flow.py`
   - `backend-train-model/person-train-model/person_project_config.json`
   - `backend-train-model/person-train-model/person_project_config.fullframe_with_new_labels.json`
   - `backend-train-model/person-train-model/person_project_config.roi_v1.center_inside.json`
   - `backend-train-model/person-train-model/person_project_config.roi_v2.mask_then_crop_ioa25.json`
   - `backend-train-model/person-train-model/person_project_config.roi_v3.mask_then_crop_margin64.json`
   - `backend-train-model/person-train-model/person_project_config.roi_v3.crop_only_margin64.json`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增 JSON 业务字段。
   - 删除冗余字段：`data.label_root`
   - `run_person_flow.py`：fullframe prepare 改为复用 `ensure_person_labels_available()`
   - `prepare_person_dataset.py`：`roi.keep_rule` 的强制校验仅在 `roi.enabled=true` 时触发
5. 兼容性注意：
   - 删除 `data.label_root` 不影响现有配置加载，因为 loader 从未读取该字段；真实汇总标签入口仍由 `person_dataset.aggregated_label_root` 提供。
   - `person_project_config.fullframe_with_new_labels.json` 现在即使把 keep rule 全部置空，只要 `roi.enabled=false` 也不会因为 ROI disabled 分支触发无意义报错。
   - 本轮未改变 `fullframe + roi.enabled=true` 的兼容入口能力，也未修改任何已生成 prepared 数据集。
6. 本轮明确不改动的部分：
   - 不修改任何训练指标结论与 run 选择结果。
   - 不重跑训练、评估、prepare 或 review。
   - 不修改在线链路与其他监控方向代码。

## 2026-05-04 跟进修复 person 包装脚本与版本化配置的 4 个遗漏问题

1. 变更来源：用户在统一训练配置后继续人工复核，指出 person 线仍存在 4 个问题：`prepare` 阶段对 ROI-aware 变体仍硬编码走 fullframe、wrapper 不能从配置读取默认初始化权重、ROI 配置中的 fullframe fallback 命名语义容易误读、以及 `default_dataset_variant` 与 `roi.enabled` 缺少必要的交叉校验。
2. 变更总览：
   - 修复 `run_person_flow.py`：现在会根据 `dataset.yaml` 目标路径或 `default_dataset_variant` 自动选择 fullframe prepare / ROI-aware prepare，不再把 ROI-aware 变体错误导向 `prepare --mode fullframe`。
   - 扩展 `prepare_person_dataset.py` 的 `TrainDefaults`，支持从 `training.default_train_args` 读取 `base_model` 与 `init_weights`，并让 `run_person_flow.py` 在 CLI 未显式传参时自动继承这些默认初始化来源。
   - 在 `prepare_person_dataset.py` 中增加必要校验：当 `person_dataset.default_dataset_variant=roi_aware` 时，`roi.enabled` 必须为 `true`。
   - 为 fullframe / ROI-aware 正式配置补齐 `training.default_train_args.base_model`，并同步更新 `docs/config.md` 对 `recommended_run_name` 语义与默认初始化来源的说明。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-code/prepare_person_dataset.py`
   - `backend-train-model/person-train-model/train-code/run_person_flow.py`
   - `backend-train-model/person-train-model/person_project_config.json`
   - `backend-train-model/person-train-model/person_project_config.fullframe_with_new_labels.json`
   - `backend-train-model/person-train-model/person_project_config.roi_v1.center_inside.json`
   - `backend-train-model/person-train-model/person_project_config.roi_v2.mask_then_crop_ioa25.json`
   - `backend-train-model/person-train-model/person_project_config.roi_v3.mask_then_crop_margin64.json`
   - `backend-train-model/person-train-model/person_project_config.roi_v3.crop_only_margin64.json`
   - `docs/config.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - `training.default_train_args.base_model`：新增到 fullframe / ROI-aware 正式配置，用于 wrapper 默认继承初始化来源
   - `TrainDefaults.base_model` / `TrainDefaults.init_weights`：新增代码级配置消费字段
   - `run_person_flow.py`：新增按目标 `dataset.yaml` 识别 fullframe / roi_aware prepare 路径的逻辑
   - `prepare_person_dataset.py`：新增 `default_dataset_variant=roi_aware -> roi.enabled=true` 校验
5. 兼容性注意：
   - `recommended_run_name=person_fullframe_baseline` 在 ROI-aware 配置中仍保留，用于 fullframe fallback 语义；正常 ROI-aware 默认 run 名仍由 `roi_aware_recommended_run_name` 提供，不构成功能性错误。
   - 本轮没有把 `fullframe + roi.enabled=true` 判定为非法组合，因为兼容入口 `person_project_config.json` 仍需要保留这种“默认 fullframe、可显式切到 ROI-aware”的双用途能力。
   - 若后续继续新增版本化 ROI-aware 配置，建议同步补齐 `training.default_train_args.base_model`，否则 wrapper 会重新依赖 CLI 手动传参。
6. 本轮明确不改动的部分：
   - 不修改任何历史指标结论与已生成 prepared 数据集统计。
   - 不重跑训练、评估、export 或 review。
   - 不修改 `inspection-flask/` 在线链路和其他监控方向代码。

## 2026-05-04 统一训练配置入口、版本化 person ROI-aware config，并新增总览文档

1. 变更来源：用户要求系统性审查 `backend-train-model/` 训练主线的全部配置文件、代码消费逻辑与训练文档，把不一致项统一到“最新、最贴近当前进度”的口径，并在仓库根 `docs/` 下补一份训练配置总览。
2. 变更总览：
   - 为 person 新增正式版本化 ROI-aware 配置入口：
     - `backend-train-model/person-train-model/person_project_config.roi_v1.center_inside.json`
     - `backend-train-model/person-train-model/person_project_config.roi_v2.mask_then_crop_ioa25.json`
     - `backend-train-model/person-train-model/person_project_config.roi_v3.mask_then_crop_margin64.json`
     - `backend-train-model/person-train-model/person_project_config.roi_v3.crop_only_margin64.json`
   - 在 `person_project_config.json` 与 `person_project_config.fullframe_with_new_labels.json` 中显式加入 `person_dataset.default_dataset_variant`，并把兼容 / 正式入口边界固定下来。
   - 扩展 `prepare_person_dataset.py` / `run_person_flow.py`，让 wrapper 可以从 `project-config -> training.default_train_args` 和 `person_dataset.default_dataset_variant` 读取默认训练参数、默认 dataset root 与默认 run 名，减少“兼容 config + 版本化 dataset”错配。
   - 将 clothes 的 `project_config.json` 与 `All-train-model/merged_train_project_config.json` 默认训练口径统一为 GPU（`device=0`、`workers=4`）。
   - 统一 `person_run_method.md`、`roi_problem_solution.md`、`roi_next_iteration_plan.md`、`docs/dataset.md`、`backend-train-model/AGENTS.md`、仓库根 `AGENTS.md` 的配置口径，并新增 `docs/config.md` 作为训练配置总览入口。
3. 涉及文件：
   - `backend-train-model/project_config.json`
   - `backend-train-model/All-train-model/merged_train_project_config.json`
   - `backend-train-model/All-train-model/00_CURRENT_BASELINE/README.md`
   - `backend-train-model/person-train-model/person_project_config.json`
   - `backend-train-model/person-train-model/person_project_config.fullframe_with_new_labels.json`
   - `backend-train-model/person-train-model/person_project_config.roi_v1.center_inside.json`
   - `backend-train-model/person-train-model/person_project_config.roi_v2.mask_then_crop_ioa25.json`
   - `backend-train-model/person-train-model/person_project_config.roi_v3.mask_then_crop_margin64.json`
   - `backend-train-model/person-train-model/person_project_config.roi_v3.crop_only_margin64.json`
   - `backend-train-model/person-train-model/train-code/prepare_person_dataset.py`
   - `backend-train-model/person-train-model/train-code/run_person_flow.py`
   - `backend-train-model/person-train-model/train-docs/person_run_method.md`
   - `backend-train-model/person-train-model/train-docs/roi_problem_solution.md`
   - `backend-train-model/person-train-model/train-docs/roi_next_iteration_plan.md`
   - `backend-train-model/AGENTS.md`
   - `AGENTS.md`
   - `docs/dataset.md`
   - `docs/config.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - `person_dataset.default_dataset_variant`：新增，支持 `fullframe` / `roi_aware`
   - `prepare_person_dataset.PersonProjectContext.training_defaults`：新增代码级配置消费字段
   - `prepare_person_dataset.PersonProjectContext.default_dataset_variant`：新增代码级配置消费字段
   - `backend-train-model/project_config.json -> training.default_train_args.workers: 0 -> 4`
   - `backend-train-model/project_config.json -> training.default_train_args.device: cpu -> 0`
   - `backend-train-model/All-train-model/merged_train_project_config.json -> training.default_train_args.workers: 0 -> 4`
   - `backend-train-model/All-train-model/merged_train_project_config.json -> training.default_train_args.device: cpu -> 0`
   - `run_person_flow.py`：CLI 的 `imgsz / epochs / batch / patience / workers / device / seed` 由硬编码默认值改为优先读取当前 `project-config`
5. 兼容性注意：
   - `backend-train-model/person-train-model/person_project_config.json` 仍保留为兼容 / 历史入口，但不再建议作为 ROI-aware v2/v3 的正式唯一配置来源。
   - 现在如果依赖 wrapper 的隐式默认值，实际取值会随 `project-config` 中的 `training.default_train_args` 与 `person_dataset.default_dataset_variant` 变化；正式实验仍建议显式传入 `--project-config`、`--dataset-yaml`、`--run-name` 和关键训练参数。
   - 本轮没有重生成任何 prepared 数据集，也没有改写历史 report；历史产物中的旧 metadata 会继续保留原状。
6. 本轮明确不改动的部分：
   - 不重跑任何训练、评估、导出或 review 任务。
   - 不修改 `inspection-flask/` 在线链路配置。
   - 不改变当前指标结论、ROI keep rule 的实验结论或既有 baseline 选择结果。

## 2026-05-04 继续统一 person 运行文档中的 GPU / project-config 口径

1. 变更来源：用户继续要求清理 `person_run_method.md` 中残留的 CPU 命令与未显式传入 `--project-config` 的历史段落，避免同一份运行文档再次出现 GPU / CPU 混用和配置口径不统一。
2. 变更总览：继续把 `person_roi_aware_v2`、`person_roi_aware`、`person_fullframe` 以及剩余 ROI-aware v3 段落的训练 / 评估命令统一为 GPU 默认口径；同时补齐显式 `--project-config`、`--imgsz`、`--batch`、`--workers` 传参，并把文案中的“CPU 压力”改成训练机显存 / 稳定性表述。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/person_run_method.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：未新增项目配置文件字段；本轮仅统一运行文档中的命令口径，默认训练 / 评估示例统一为 `--device 0 --workers 4`，并要求历史分支命令显式传入 `--project-config`。
5. 兼容性注意：若后续某台 GPU 训练机 DataLoader 稳定性不足，仍可按文档总则把 `--workers` 回退到 `0`；若显存不足，可保留 `batch=2` 作为备选，但不应再把 GPU 主线命令写回 CPU 口径。
6. 本轮明确不改动的部分：未改动训练脚本逻辑、ROI keep rule、已有训练产物、历史指标结论与 `roi_compare.md` 内容。

## 2026-05-04 统一 fullframe 扩样线的 project-config 口径并增加 dataset/config 一致性校验

变更来源：
- 用户指出 `person_fullframe_with_new_labels` 相关 train / eval report 中，存在 `dataset.yaml` 明明来自 fullframe 扩样线，但 `project_config_path` 却仍指向旧 `person_project_config.json` 的混乱情况，要求把配置口径统一，避免后续继续出现这种元数据错配。

变更总览：
1. 更新 `backend-train-model/person-train-model/train-docs/person_run_method.md`：
   - 在 `person_fullframe_with_new_labels` 段内，所有 train / evaluate 命令统一显式传入 `--project-config backend-train-model/person-train-model/person_project_config.fullframe_with_new_labels.json`；
   - 通用运行约束补充：train / evaluate 命令建议同时显式传 `--project-config`、`--dataset-yaml`、`--run-name`，避免再混入默认旧配置。
2. 更新配置文件默认训练口径：
   - `backend-train-model/person-train-model/person_project_config.json`
   - `backend-train-model/person-train-model/person_project_config.fullframe_with_new_labels.json`
   的 `training.default_train_args` 从 CPU 口径统一改为 GPU 口径（`device=0`、`workers=4`）。
3. 更新 `backend-train-model/person-train-model/train-code/run_person_flow.py`：
   - 新增 `validate_explicit_dataset_yaml_matches_context()`；
   - 当用户显式传入 `--dataset-yaml` 时，若其路径不属于当前 `--project-config` 对应的 prepared 输出根目录，将直接报错，阻止继续生成“dataset 来自 A，但 config 来自 B”的混乱 report。

涉及文件：
- `backend-train-model/person-train-model/train-docs/person_run_method.md`
- `backend-train-model/person-train-model/person_project_config.json`
- `backend-train-model/person-train-model/person_project_config.fullframe_with_new_labels.json`
- `backend-train-model/person-train-model/train-code/run_person_flow.py`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- `person_project_config.json -> training.default_train_args.workers: 0 -> 4`
- `person_project_config.json -> training.default_train_args.device: cpu -> 0`
- `person_project_config.fullframe_with_new_labels.json -> training.default_train_args.workers: 0 -> 4`
- `person_project_config.fullframe_with_new_labels.json -> training.default_train_args.device: cpu -> 0`

兼容性注意：
- 以后如果显式传 `--dataset-yaml`，它必须和当前 `--project-config` 的 prepared 根目录一致，否则 `run_person_flow.py` 会直接报错，这是本轮为了防止 report 元数据混乱而新增的保护机制。
- 本轮不会修改已有历史 report 文件；历史 report 中已经写入的旧 `project_config_path` 仍会保留原状。

本轮明确不改动：
- 不重生成任何 prepared 数据集。
- 不自动重跑历史训练或评估。
- 不顺手改动 ROI-aware 其他历史实验 report 的内容。

## 2026-05-03 删除 `person_fullframe_with_new_labels_baseline` 的本轮训练产物

变更来源：
- 用户确认刚才启动的 `person` 训练过慢，希望删除这次新产生的训练 run 产物，避免保留一轮未打算继续使用的 CPU 训练输出。

变更总览：
1. 定位并删除本轮刚生成的训练 run 目录：
   - `backend-train-model/person-train-model/train-result/artifacts/runs/person_fullframe_with_new_labels_baseline`
2. 核对这次没有新的评估 report，也没有新的 export alias，因此本轮只删除训练 run 目录本身。
3. 明确保留本次数据整理相关产物：
   - `person_project_config.fullframe_with_new_labels.json`
   - `aggregated_labels_fullframe_with_new_labels`
   - `person_source_dataset_summary_fullframe_with_new_labels.json`
   - `prepared/person_fullframe_with_new_labels/sequence_contiguous/`

涉及文件：
- `backend-train-model/person-train-model/train-result/artifacts/runs/person_fullframe_with_new_labels_baseline/`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无新的配置项或训练参数变更。
- 本轮只删除本次训练输出目录，不修改训练入口、数据集或文档中的推荐命令。

兼容性注意：
- 删除的是本轮 run 产物，不影响后续继续使用同一份 `dataset.yaml` 重新开跑。
- 现有的 prepared 数据集和空标签补齐结果仍然保留，因此后续若要重训，不需要重新整理这批 `person` 数据。

本轮明确不改动：
- 不删除 `person_fullframe_with_new_labels` 的 prepared 数据集。
- 不删除新建的 fullframe 扩样配置和训练文档。
- 不删除历史 `person_fullframe_baseline` 或任意 ROI-aware run。

## 2026-05-03 将 `person_fullframe_with_new_labels` 的 `prepare-labels` / `train` 命令写入运行手册

变更来源：
- 用户要求在确认空标签已经补成空白 `txt` 之后，把对应的训练命令写入 `backend-train-model\person-train-model\train-docs\person_run_method.md`，避免后续手工检索命令时遗漏这条 fullframe 扩样入口。

变更总览：
1. 在 `backend-train-model/person-train-model/train-docs/person_run_method.md` 顶部新增 `person_fullframe_with_new_labels` 版本段，按既有结构补齐：
   - 当前定位；
   - 数据集与产物；
   - `prepare-labels` / `prepare` 重新生成命令；
   - 训练命令；
   - 评估命令；
   - 备注。
2. 明确写入这次扩样的空标签处理结果，确保文档直接说明：
   - 新样本中 `00179`、`00516`、`00559`、`01332` 已作为空白 `txt` 保留；
   - `prepare-labels` 已完成空标签补齐并落盘；
   - 后续训练前不需要再手工补空标签。
3. 将该版本段的训练命令固定为 `person_fullframe_with_new_labels_baseline`，并保留一个更保守的 `batch=2` 备选命令，方便 CPU 环境下先做轻量验证。

涉及文件：
- `backend-train-model/person-train-model/train-docs/person_run_method.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无新的训练配置项或模型参数。
- 本轮只把已有 fullframe 扩样配置对应的运行命令写入运行手册。

兼容性注意：
- 本轮没有改动任何训练逻辑、数据准备逻辑或 ROI-aware 配置。
- 新增的 fullframe 版本段只是文档入口，实际数据仍然以 `person_project_config.fullframe_with_new_labels.json` 和对应 prepared 输出为准。
- 文档中的命令默认使用已生成的 `dataset.yaml`，不额外隐含重新训练或重新导出动作。

本轮明确不改动：
- 不修改 `person_project_config.fullframe_with_new_labels.json` 的内容。
- 不重新生成数据集。
- 不启动任何训练、评估或导出任务。

## 2026-05-03 新增 `person_fullframe_with_new_labels` 扩样配置并完成 `new_person_labels` 合并整理

变更来源：
- 用户已经完成新的 `person` 标注，图片目录为 `D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\new_person_labels\images`，标注目录为 `D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\new_person_labels\person_labels`，希望先把 `person` 整理进现有训练体系，同时确认是否可以和旧 `person` 一起训练。
- 当前新样本只有 `person` 标注，没有同步准备 `clothes`，因此需要先判断是直接并入 fullframe 训练，还是误接入现有 ROI-aware 主线。

变更总览：
1. 新增独立的 fullframe 扩样配置 `backend-train-model/person-train-model/person_project_config.fullframe_with_new_labels.json`，将原有 `502` 张旧 `person` 图与 `new_person_labels` 的 `2507` 张图并入同一套 `person` 训练入口。
2. 在该配置中新增一条 `new_person_labels` 序列：
   - `source_id: g34`
   - `group: new_person_labels`
   - `sequence_name: new_person_labels_flat_20260503`
   - `image_root: D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\new_person_labels\images`
   - `label_root: D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\new_person_labels\person_labels`
3. 明确把这次扩样限定为 `fullframe person`，并显式设置 `roi.enabled=false`，避免在新样本尚未补齐 ROI 时误接入 ROI-aware 训练主线。
4. 已执行 `prepare-labels` 与 `prepare`，生成并落盘：
   - `train-result/working/aggregated_labels_fullframe_with_new_labels`
   - `train-result/person_source_dataset_summary_fullframe_with_new_labels.json`
   - `train-result/prepared/person_fullframe_with_new_labels/sequence_contiguous/`
   - `train-result/prepared/person_fullframe_with_new_labels/sequence_contiguous/dataset.yaml`
5. 同步更新 `backend-train-model/AGENTS.md`，把这次 fullframe 扩样配置及其输出统计写入长期上下文，避免后续再把“新样本已整理完成”与“ROI-aware 主线已准备好”混在一起。

结果摘要：
- 总图片：`3009`
- 总标注框：`8861`
- 空标注文件：`13`
- 切分：`train=2105 / val=453 / test=451`
- 新增样本中的空标注文件：`00179`、`00516`、`00559`、`01332`
- 旧数据中自动补空标注的样本仍按原策略处理，`prepare` 成功完成，没有中断训练链路

涉及文件：
- `backend-train-model/person-train-model/person_project_config.fullframe_with_new_labels.json`
- `backend-train-model/AGENTS.md`
- `backend-train-model/person-train-model/train-result/person_source_dataset_summary_fullframe_with_new_labels.json`
- `backend-train-model/person-train-model/train-result/prepared/person_fullframe_with_new_labels/sequence_contiguous/`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- `person_dataset.recommended_run_name`
- `person_dataset.aggregated_label_root`
- `person_dataset.summary_path`
- `person_dataset.prepared_output_root`
- `person_dataset.roi_aware_prepared_output_root`
- `person_dataset.roi_aware_recommended_run_name`
- `person_dataset.export_alias_path`
- `person_dataset.export_alias_metadata_path`
- 新增序列 `g34 / new_person_labels / new_person_labels_flat_20260503`
- `roi.enabled=false`

兼容性注意：
- 本轮没有改动 `person` 原始 fullframe 训练逻辑，也没有覆盖现有 ROI-aware 主配置。
- `sequence_contiguous` 仍适用于这次扩样，因为新旧样本的 stem 不重名，且新样本以独立 flat 序列接入。
- `prepare` 期间出现的少量“标注框极小越界、已自动裁剪到 [0,1]”提示属于非致命校正，没有阻断数据集生成。

本轮明确不改动：
- 不修改任何训练代码、评估脚本或在线推理代码。
- 不生成新的 `clothes` 数据或 `ROI-aware person` 数据。
- 不启动新的训练、评估或导出任务。

## 2026-05-03 新增 `new_train.md` 统一说明 `clothes / person` 扩样接入策略

变更来源：
- 用户准备继续为 `clothes` 和 `person` 增加训练样本，并明确追问：`person` 是否只需要正常训练，以及 `clothes` 面对“新工服款式”时，到底应该在标注阶段拆类，还是先单类训练、后续再处理。

变更总览：
1. 新增 `backend-train-model/person-train-model/train-docs/new_train.md`，集中回答当前仓库下这类问题，明确区分：
   - `person` 扩样的默认处理方式；
   - `clothes` 在“工服款式不同但业务语义不变”时的推荐做法；
   - 什么时候才值得把 `clothes` 从单类升级为多类。
2. 在文档中明确写清当前仓库前提：
   - `person` 仍是单类 `0 -> person`
   - `clothes` 仍是单类 `0 -> clothes`
   - 在线链路默认通过 `WORKWEAR_LABELS=["clothes"]` 与 `WORKWEAR_COMPLIANCE_MODE="any"` 解释工服检测结果
3. 将当前推荐策略收敛为：
   - `person` 正常加样本、正常训练；
   - `clothes` 若只是新旧工服款式差异，先保持单类 `clothes`，并通过 `style_tag / source_id / sequence_name` 等元数据记录域差异；
   - 至少保留一部分新款工服样本做独立 holdout，不要只看混训后的总体指标。
4. 同步更新 `backend-train-model/AGENTS.md` 的“必读文件”入口，避免后续再次把“新工服款式不同”直接误写成“默认应该拆类”。

涉及文件：
- `backend-train-model/person-train-model/train-docs/new_train.md`
- `backend-train-model/AGENTS.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无新的训练配置项、模型参数、ROI keep rule 或数据准备脚本变更。
- 本轮仅新增文档说明与入口引用。

兼容性注意：
- 本轮没有把 `clothes` 正式升级为多类，也没有改动任何现有 `class_names`、`dataset.yaml`、`build.json`、在线 `WORKWEAR_LABELS` 或训练默认参数。
- 文档中的建议是：当前仓库下，面对“款式不同但都算合规工服”的新增样本，优先把问题视为样本域扩展，而不是立即改写为多类检测任务。
- 如果后续真的要把 `clothes` 拆成多类，仍需同步检查训练配置、评估口径和在线规则，而不是只改标注文件。

本轮明确不改动：
- 不修改任何训练代码、评估脚本、ROI prepare 逻辑或在线推理代码。
- 不重建 `clothes` 或 `person` 数据集。
- 不启动新的训练、评估或导出任务。

## 2026-04-28 根据用户反馈收紧阶段边界，改为“承接上次 ROI-aware 初版，当前从 v2 继续汇报”

变更来源：
- 用户指出：上一阶段汇报时已经完成 `ROI-aware person` 初版，因此本轮 `阶段PPT汇报.md` 不能再把“ROI-aware 跑通”写成本阶段主成果，而应从 `v2` 开始写，作为接着上次汇报继续推进的内容。

变更总览：
1. 重写 `backend-train-model/docs/阶段PPT汇报.md` 的阶段边界定义，明确：
   - 上一阶段已完成 `person_fullframe_baseline` 与 `ROI-aware person` 初版跑通
   - 本阶段默认从 `person_roi_aware_v2_from_fullframe` 起算
2. 将 `Slide 4 / Slide 5` 的“本阶段进展”口径改为：
   - `v2 -> v3 mask_then_crop + margin64`
   - `crop_only + margin64` 对照
   - `imgsz=768` 对照
   - 逐图 FP/FN 与 hard FN 诊断闭环
3. 将 `Slide 7 / Slide 8 / Slide 10` 的问题与解决方案口径改为“承接 v2 后继续优化”的版本，避免继续把：
   - 早期 ROI-aware 初版成果
   - 更早期 `center_inside -> bottom-center` 方案
   写成当前阶段新增内容。

涉及文件：
- `backend-train-model/docs/阶段PPT汇报.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无训练配置、ROI keep rule、模型参数或数据准备逻辑变更。
- 本轮只调整阶段汇报文档的时间边界与叙事口径。

兼容性注意：
- 本轮修改后的 `阶段PPT汇报.md` 更适合直接作为“接着上次汇报”的改稿依据，而不是再作为从零介绍 ROI-aware person 的材料。
- 文档仍保留 `大创PPT汇报.pptx` 的页码结构，但 person 线的阶段起点已收紧到 `v2`。

本轮明确不改动：
- 不修改 `大创PPT汇报.pptx` 文件本身。
- 不启动新的训练、评估或数据集重构。
- 不修改任何训练代码、ROI prepare 逻辑或 review 脚本。

## 2026-04-28 按《大创PPT汇报.pptx》页码结构重写阶段汇报文档

变更来源：
- 用户要求结合 `backend-train-model/docs/大创PPT汇报.pptx` 的现有页码结构，修改 `backend-train-model/docs/阶段PPT汇报.md`，使其不再是一份独立材料，而是可以直接对照现有 PPT 改稿的文档。

变更总览：
1. 读取并提取 `大创PPT汇报.pptx` 的 10 页文字结构，确认当前 deck 采用的是：
   - `本阶段进展`
   - `问题与缺陷`
   - `改进方案`
   的三段式叙事。
2. 将 `阶段PPT汇报.md` 重写为“按 Slide 1-10 对应修改”的格式，直接对齐现有 PPT 页码，而不是继续维持通用型阶段总结结构。
3. 保留原 deck 的主叙事框架，但把其中已经过时的内容替换为当前真实结论，重点修正：
   - `person` 旧指标
   - 把 `ROI 裁边 / ROI 边界过硬` 写成主因的旧口径
   - 把 `center_inside -> bottom-center or box_ioA>=0.25` 写成“下一步方案”的旧表述
4. 在文档中补充每页建议口播、应替换的旧口径，以及与当前页最匹配的图路径，方便直接改 PPT。

涉及文件：
- `backend-train-model/docs/阶段PPT汇报.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无训练配置、评估阈值、ROI keep rule 或模型权重变更。
- 本轮只更新汇报文档结构与文案口径。

兼容性注意：
- `大创PPT汇报.pptx` 中保留了较早阶段的内容，因此本文档明确区分了：
  - 可以保留的页码结构
  - 需要替换的旧指标和旧结论
- 当前文档推荐保留 deck 的三段式结构，但不再继续使用“ROI 边界太严格是当前主瓶颈”这一旧判断。

本轮明确不改动：
- 不修改 `大创PPT汇报.pptx` 文件本身。
- 不启动新的训练、评估或数据重构。
- 不修改任何训练代码、ROI prepare 逻辑、模型配置文件或 review 脚本。

## 2026-04-28 重写阶段 PPT 汇报素材并补充可直接引用的配图建议

变更来源：
- 用户准备做阶段汇报，希望把“这一阶段完成的任务、遇到的问题、解决方案与下一步计划”统一整理到 `backend-train-model/docs/阶段PPT汇报.md`，并顺便挑出几张适合直接放进 PPT 的图。

变更总览：
1. 重写 `backend-train-model/docs/阶段PPT汇报.md`，将内容从早期 baseline 口径更新为当前阶段真实进展：
   - `person_fullframe_baseline`
   - `person_roi_aware_v2_from_fullframe`
   - `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe`
   - `crop_only + margin64`
   - `imgsz=768` 对照
2. 将“本阶段完成的任务、核心指标对比、主要问题、已采取措施、阶段性结论、下一步计划”按 PPT 可直接复用的结构重写，避免继续沿用旧版 `center_inside` / 旧 baseline 的表述。
3. 补充一组已存在于仓库中的推荐配图与统计数据来源，便于后续直接制作：
   - 当前主线训练曲线与 PR 曲线
   - ROI crop 改进示意图
   - 关键 hard FN 复盘图
   - FN 分桶统计摘要

涉及文件：
- `backend-train-model/docs/阶段PPT汇报.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无新的训练配置、模型参数或数据准备参数变更。
- 本轮仅更新汇报文档与配图建议。

兼容性注意：
- 本轮更新不修改任何训练代码、评估口径、prepared 数据集、ROI keep rule 或模型权重。
- 文档中引用的结论基于当前仓库内已经存在的训练结果与复盘产物，尤其是：
  - `roi_cropped_keep_positive_v3_margin64`
  - `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_fpfn_test_conf025`
  - `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_fn_buckets`
  - `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_key_fn_review`

本轮明确不改动：
- 不启动新的长时间训练。
- 不重生成新的 prepared 数据集。
- 不修改 `prepare_roi_aware_person_dataset.py`、`run_person_flow.py`、`analyze_person_fpfn.py` 或任何模型配置文件。

## 2026-04-28 新增 ROI-aware person hard FN 拼图复盘脚本，并补齐 latest img768 的逐图 FP/FN 结果

变更来源：
- 用户提出：当前只看单独的 FN 帧，看不出“到底是 ROI 过滤、crop、还是模型本身没学到”，希望直接看“最近一次训练之后的 ROI 图”和有问题样本，并结合 `roi_next_iteration_plan.md` 判断更有效的提升方向。

变更总览：
1. 新增 `backend-train-model/person-train-model/train-code/review_person_roi_failures.py`：
   - 读取 `analyze_person_fpfn.py` 生成的 `fpfn_per_image.json`；
   - 对同一张问题帧同时输出：
     - 原图视角的 ROI polygon、crop bbox、original person 框 keep/drop 状态；
     - prepared ROI 图上的 GT TP / GT FN / matched pred / FP；
     - 样本级统计标题，便于判断问题更偏 ROI 规则、crop 边界还是模型检测能力。
2. 使用既有 `analyze_person_fpfn.py`，补跑最新一次训练 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768` 的 test split 逐图复盘，输出到：
   - `backend-train-model/person-train-model/train-result/review/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768_fpfn_test_conf025/`
3. 本轮新增 hard FN 拼图工具后，可以直接围绕 `D15_20260119061405`、`D15_20260119203927`、`D02_20260123074836`、`D02_20260123070624` 做同帧联动复盘，而不再需要在“单帧 FN 截图”和“单独 ROI overlay”之间来回切换。

涉及文件：
- `backend-train-model/person-train-model/train-code/review_person_roi_failures.py`
- `backend-train-model/person-train-model/train-result/review/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768_fpfn_test_conf025/fpfn_per_image.json`
- `backend-train-model/person-train-model/train-result/review/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768_fpfn_test_conf025/fpfn_summary.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无训练默认配置项变更。
- 新增复盘脚本参数：
  - `--fpfn-json`
  - `--stem`
  - `--top-fn`
  - `--output-root`
  - `--overwrite`

兼容性注意：
- 本轮新增的是“诊断视角”和新的 review 产物，不修改任何 ROI keep rule、prepared 数据集、训练参数或模型权重。
- `review_person_roi_failures.py` 依赖已有的 `fpfn_per_image.json`；因此在复盘新的 run 前，仍需先执行 `analyze_person_fpfn.py`。
- 最新 `img768` run 的逐图复盘结果表明：在同一 test split、同一 `conf=0.25 / nms_iou=0.7 / match_iou=0.5` 口径下，它从当前主线的 `TP=80 / FP=7 / FN=35` 退到 `TP=74 / FP=8 / FN=41`，因此这轮补充结果支持“`img768` 不是当前优先升级方向”的既有结论。

本轮明确不改动：
- 不修改 `prepare_roi_aware_person_dataset.py`、`run_person_flow.py`、`analyze_person_fpfn.py` 或任何训练 / 评估主流程。
- 不重生成 prepared 数据集。
- 不启动新的长时间训练。

## 2026-04-28 继续统一修正文档中 ROI keep rule 的证据链表述

变更来源：
- 用户继续追问此前文档中“脚点已入区但 `box_ioa < 0.25` 所以没进训练集”的说法为何与代码冲突，并要求继续扫描相关文档，把类似的逻辑混写全部修正。

变更总览：
1. 继续回查 `prepare_roi_aware_person_dataset.py` 的 keep rule 实现，明确文档口径必须区分两类证据：
   - 逐图 `FN/FPFN` 复盘只能说明“prepared 数据集里已经保留下来的 GT，模型有没有检出来”；
   - 原图 ROI filter / overlay 复盘才能说明“某批边界人是否在 prepare 阶段就被 keep rule 过滤掉了”。
2. 统一修正 `AGENTS.md`、`backend-train-model/AGENTS.md`、`person_run_method.md`、`roi_next_iteration_plan.md` 中对下一步 `ioa20` 实验的触发描述，避免再把“模型漏检”和“样本未进训练集”写成同一层证据。
3. 修正文档中的 ROI 规则术语：
   - 将 `阶段PPT汇报.md` 中含糊的 `bottom-center` / `box_ioA` 表述改为“框底边中心点在 ROI 内（bottom_center_inside）或 `box_ioa >= 0.25`”；
   - 将 `roi_problem_solution.md`、`update_log.md` 中容易让人误解为“真实脚点检测”的说法收紧为“框底边中心点在 ROI 内，作为脚点语义近似”。
4. 更新 `review_roi_cropped_keep_boxes.py` 的 Markdown 规则标签，将 `min_box_ioa` 对应说明改为“`box_ioa` 达到 `min_box_ioa` 阈值”，并重新生成两份 `cropped_keep_positive_summary.md`。

涉及文件：
- `AGENTS.md`
- `backend-train-model/AGENTS.md`
- `backend-train-model/person-train-model/train-docs/person_run_method.md`
- `backend-train-model/person-train-model/train-docs/roi_next_iteration_plan.md`
- `backend-train-model/person-train-model/train-docs/roi_problem_solution.md`
- `backend-train-model/person-train-model/train-code/review_roi_cropped_keep_boxes.py`
- `backend-train-model/person-train-model/train-result/review/roi_cropped_keep_positive_v2/cropped_keep_positive_summary.md`
- `backend-train-model/person-train-model/train-result/review/roi_cropped_keep_positive_v3_margin64/cropped_keep_positive_summary.md`
- `backend-train-model/docs/阶段PPT汇报.md`
- `backend-train-model/docs/update_log.md`

兼容性注意：
- 本轮只修正文档口径、复盘摘要文案和术语说明，不修改 ROI keep rule 代码、数据集、训练结果或模型权重。
- 当前更严格的统一口径是：若要考虑 `min_box_ioa 0.25 -> 0.20`，必须由“逐图 `FN` 复盘 + 原图 ROI filter 复盘”共同构成证据闭环。

## 2026-04-28 将 person review 目录下的 Markdown 复盘摘要统一改为中文输出

变更来源：
- 用户查看 `backend-train-model/person-train-model/train-result/review/` 下的复盘摘要时，提出这些 `.md` 文件“除了路径，其他内容都希望换成中文”，避免后续人工复盘时还要先做英文字段对照。

变更总览：
1. 更新 `backend-train-model/person-train-model/train-code/review_roi_cropped_keep_boxes.py` 的 Markdown 生成逻辑：
   - 将标题、统计字段、章节名、样本说明改为中文；
   - 将 `train/val/test`、`top/bottom/left/right` 等可读项改为中文；
   - 将规则说明改为“中文解释 + 原规则名”的形式，便于人工阅读同时保留技术对应关系。
2. 更新 `backend-train-model/person-train-model/train-code/analyze_person_fpfn.py` 的 Markdown 生成逻辑：
   - 将标题、字段名、表头、误检 / 漏检分组标题改为中文；
   - 保留 run 名、序列名、路径等原始标识，避免丢失定位信息。
3. 重新生成当前 review 目录下已有的 3 个 Markdown 摘要文件：
   - `backend-train-model/person-train-model/train-result/review/roi_cropped_keep_positive_v2/cropped_keep_positive_summary.md`
   - `backend-train-model/person-train-model/train-result/review/roi_cropped_keep_positive_v3_margin64/cropped_keep_positive_summary.md`
   - `backend-train-model/person-train-model/train-result/review/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_fpfn_test_conf025/fpfn_summary.md`

涉及文件：
- `backend-train-model/person-train-model/train-code/review_roi_cropped_keep_boxes.py`
- `backend-train-model/person-train-model/train-code/analyze_person_fpfn.py`
- `backend-train-model/person-train-model/train-result/review/roi_cropped_keep_positive_v2/cropped_keep_positive_summary.md`
- `backend-train-model/person-train-model/train-result/review/roi_cropped_keep_positive_v3_margin64/cropped_keep_positive_summary.md`
- `backend-train-model/person-train-model/train-result/review/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_fpfn_test_conf025/fpfn_summary.md`
- `backend-train-model/docs/update_log.md`

兼容性注意：
- 本轮只调整 Markdown 摘要的人类可读文本，不修改对应 JSON 结构与字段名。
- 路径、run 名、序列名、图片 stem 等定位信息继续保留原值，不做翻译。

本轮明确不改动：
- 不改 ROI 规则、训练参数、评估阈值和任何模型结果。
- 不改 review 目录下的图片、JSON 结果内容，只重写 Markdown 摘要文本。

## 2026-04-28 修正 `roi_next_iteration_plan.md` 中关于 `bottom_center_inside` 与 `box_ioa` 的不严谨表述

变更来源：
- 用户指出 `backend-train-model/person-train-model/train-docs/roi_next_iteration_plan.md` 中曾写到“脚点已入区，但 box_ioa 略低于 `0.25`，结果没进训练集”，而当前代码 keep rule 又是 `bottom_center_inside OR box_ioa >= 0.25`，两者在字面上存在冲突。

变更总览：
1. 回查 `prepare_roi_aware_person_dataset.py` 中的实际 keep rule 实现，确认只要 `bottom_center_inside == true`，该框就会被保留，不会再因为 `box_ioa < 0.25` 被丢弃。
2. 将 `roi_next_iteration_plan.md` 中不严谨的表述改为更准确的版本：
   - 从“脚点已入区，但 box_ioa 略低于 `0.25`，结果没进训练集”
   - 改为“肉眼看起来已经接近入区，但按代码判定 `bottom_center_inside` 仍然是 `false`，同时 `box_ioa` 又略低于 `0.25`，结果没进训练集”

涉及文件：
- `backend-train-model/person-train-model/train-docs/roi_next_iteration_plan.md`
- `backend-train-model/docs/update_log.md`

兼容性注意：
- 本轮只修正文档语义，不修改任何 ROI keep rule、数据集、训练结果或代码逻辑。

## 2026-04-28 新增 person 单帧 FP/FN 复盘脚本并重排 ROI-aware v3 下一步优先级

变更来源：
- 用户在完成 `roi_cropped_keep_positive_v3_margin64` 复盘后，继续要求查看复盘结果，并明确希望把后续训练重心收敛到更有效的方向。
- 结合这轮 ROI 裁边复盘结果，确认当前 `margin64` 已经基本解决 keep-positive 裁边问题；继续加 margin 不再是优先事项。
- 为了把“当前问题到底在 ROI 边界，还是在难样本 / 难序列 / 训练波动”拆开，新增了逐图 `FP/FN` 复盘脚本，并实际对当前 v3 主线 test split 跑了一轮复盘。

变更总览：
1. 新增 `backend-train-model/person-train-model/train-code/analyze_person_fpfn.py`。
2. 使用该脚本对 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` 的 test split 做首轮逐图复盘，输出到：
   - `backend-train-model/person-train-model/train-result/review/person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_fpfn_test_conf025/`
3. 记录本轮高信号结论：
   - 当前主线在 `conf=0.25 / nms_iou=0.7 / match_iou=0.5` 下复盘结果为 `TP=80 / FP=7 / FN=35`；
   - 误差主要集中在 `D15_20260119061405`、`D15_20260119203927`、`D02_20260123074836`、`D02_20260123070624`；
   - ROI 裁边复盘已确认剩余 `23` 个裁边框只是原图边界上的 `0.001 px` 级残留，不再应视为当前主瓶颈。
4. 更新 `backend-train-model/person-train-model/train-docs/person_run_method.md`：
   - 补入 `seed=7`、`seed=13` 的训练 / 评估命令；
   - 补入 `analyze_person_fpfn.py` 的复盘命令；
   - 把 v3 主线备注改成“先做 seed 稳定性 + FN 复盘，而不是继续堆 `imgsz` / margin”。
5. 重写 `backend-train-model/person-train-model/train-docs/roi_next_iteration_plan.md`：
   - 把已完成的 ROI 裁边复盘与首轮 FP/FN 复盘结果写入文档；
   - 把下一步顺序改成 `seed 稳定性 -> 人工 FN 复盘 -> 条件触发的 ioa20 单因子实验`；
   - 将 `min_box_ioa=0.20` 明确降级为“只有在逐图 FN 复盘提示边界场景异常集中，且原图 ROI filter 复盘进一步确认存在一批 `bottom_center_inside=false`、`box_ioa` 接近 `0.25` 的边界人被过滤时才启动”的条件实验。
6. 同步更新根 `AGENTS.md` 与 `backend-train-model/AGENTS.md` 的长期口径：
   - 补入 ROI 裁边复盘结论；
   - 补入新 FP/FN 复盘脚本与输出目录；
   - 明确当前重心是 `seed=7 / seed=13` 稳定性确认和 hardest sequences 的人工 FN 复盘。

涉及文件：
- `backend-train-model/person-train-model/train-code/analyze_person_fpfn.py`
- `backend-train-model/person-train-model/train-docs/person_run_method.md`
- `backend-train-model/person-train-model/train-docs/roi_next_iteration_plan.md`
- `backend-train-model/AGENTS.md`
- `AGENTS.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无新的正式训练配置默认值变更。
- 无新的默认 baseline 升级。
- 新增逐图复盘入口脚本：
  - `backend-train-model/person-train-model/train-code/analyze_person_fpfn.py`

兼容性注意：
- 当前 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` 仍是默认主线，`person_roi_aware_v2_from_fullframe` 仍保留为稳定备选。
- 这轮新增的是“诊断能力”和“执行优先级修正”，不是新的正式训练 baseline。
- `min_box_ioa=0.20` 仍然只是条件实验，不应在尚未完成“逐图 FN 复盘 + 原图 ROI filter 复盘”的证据闭环前写成默认下一步。

本轮明确不改动：
- 不修改 `train_workwear.py`、`run_person_flow.py`、ROI prepare 逻辑或任何训练代码主流程。
- 不重跑新的长时间训练。
- 不把 `imgsz=768`、更大 margin 或 `yolov8s` 升级为默认下一步路线。

## 2026-04-28 新增 ROI-aware person 下一轮迭代执行计划文档

变更来源：
- 用户在确认 `img768` 对照训练完成后，继续追问“当前效果是否仍不理想、接下来还能怎么改进”，并接受把“复盘项 + 下一轮受控实验方案 + 对应训练命令”整理成一份具体执行文档。
- 结合当前 `roi_compare.md` 里的结论，判断下一步不应继续默认堆 `imgsz` 或直接切换 `yolov8s`，而应先把 ROI 边界问题、FN 来源和训练波动拆开验证。

变更总览：
1. 新增 `backend-train-model/person-train-model/train-docs/roi_next_iteration_plan.md`。
2. 在新文档中明确写出四段式执行顺序：
   - 先做 ROI 边界 keep-positive 样本复盘与 overlay 可视化；
   - 再做当前 v3 主线的 seed 稳定性确认；
   - 然后只尝试一个 `min_box_ioa: 0.25 -> 0.20` 的单因子 keep rule 实验；
   - 若 FN 主要集中在小人 / 遮挡 / 半身 / 背光，再优先补难样本；若边界场景异常集中，则还需要结合原图 ROI filter 复盘再判断是不是 keep rule 过滤问题。
3. 在文档中补入现有可直接运行的命令：
   - `review_roi_cropped_keep_boxes.py`
   - `visualize_roi_filter_samples.py`
   - `run_person_flow.py train/evaluate` 的 seed 对照命令
   - `ioa20` 单因子实验的版本化配置与训练 / 评估命令
4. 同步更新 `person_run_method.md`，增加“若要看下一轮改进优先级，转看 `roi_next_iteration_plan.md`”的入口说明。
5. 同步更新根 `AGENTS.md` 与 `backend-train-model/AGENTS.md` 的长期口径，明确当前下一轮优先动作是：
   - 先复盘 ROI 边界 / FN
   - 先做 seed 稳定性确认
   - 再做 keep rule 单因子实验
   - 暂不默认继续放大 `imgsz`

涉及文件：
- `backend-train-model/person-train-model/train-docs/roi_next_iteration_plan.md`
- `backend-train-model/person-train-model/train-docs/person_run_method.md`
- `backend-train-model/AGENTS.md`
- `AGENTS.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无训练代码变更。
- 无现成项目配置文件变更。
- 新文档中给出了待执行的版本化配置命名建议：
  - `person_project_config.roi_v4_mask_then_crop_margin64_ioa20.json`
  - `roi_config.v4.mask_then_crop_margin64_ioa20.generated.json`

兼容性注意：
- 这次新增的是“下一轮执行计划文档”，不是已经落地并完成评估的新 baseline。
- 文档里的 `ioa20` 受控实验命令依赖先复制并修改一份版本化 `project_config`；在真实开跑前，不应把该实验当成既成事实写入结果对比结论。
- 当前默认主线仍是 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe`，`person_roi_aware_v2_from_fullframe` 仍是稳定备选。

本轮明确不改动：
- 不修改 `train_workwear.py`、`run_person_flow.py`、ROI prepare 逻辑或任何训练代码。
- 不新建正式实验结果目录，不启动新训练。
- 不把计划性建议误写成已经验证完成的训练结论。

## 2026-04-28 同步 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768` 完整结果到对比文档与长期说明

变更来源：
- 用户确认 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768` 已完成训练与评估，要求把这一轮结果补充迭代到 `backend-train-model/person-train-model/train-docs/roi_compare.md`。
- 读取新生成的 train / eval 报告后确认：这轮 `imgsz=768, batch=2` 对照实验没有打赢当前 `640 / batch=4` 主线，因此需要同步修正文档里的“下一步优先试 `imgsz=768`”口径，避免长期说明继续滞后。

变更总览：
1. 在 `roi_compare.md` 顶部新增 `2026-04-28 person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768 对比` 记录。
2. 补充该 run 与当前 `v3 mask_then_crop + margin64` 主线、`v2`、`crop_only`、`fullframe` 的 `val / test` 指标表、数据集统计差异、增量对比和训练过程说明。
3. 在对比文档中明确写出结论：`img768` 虽然 Precision 更高，但 Recall、mAP50、mAP75、mAP50-95 都低于当前 `640` 主线，也没有优于 `v2`，因此不应升级为默认主线。
4. 同步更新 `backend-train-model/AGENTS.md` 与根 `AGENTS.md` 中 ROI-aware 当前状态的长期口径，补入：
   - `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768` 的 test 指标
   - “`imgsz=768, batch=2` 对照实验已完成，但不优于当前主线”的结论
5. 同步更新 `person_run_method.md` 的 `v3 mask_then_crop` 段，把原来的“下一步优先训练 run 名 / 命令”改成“已完成的 `img768` 对照 run / 命令”，避免运行文档继续停留在实验前状态。

涉及文件：
- `backend-train-model/person-train-model/train-docs/roi_compare.md`
- `backend-train-model/person-train-model/train-docs/person_run_method.md`
- `backend-train-model/AGENTS.md`
- `AGENTS.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无代码配置项变更。
- 无新的 CLI 参数变更。
- 新增长期结论更新：
  - `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768` 已完成评估，但不应升级为默认主线。

兼容性注意：
- `img768` 这轮对比与当前 `v3 mask_then_crop + margin64` 主线使用的是同一 prepared 数据集，因此结论主要反映训练配置变化，而不是样本数量变化。
- `roi_compare.md` 中表格使用统一的 `_eval.json` native eval 口径；`results.csv` 只用于补充训练过程信息，不应和表格指标混为一谈。
- 当前默认主线仍是 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe`，`person_roi_aware_v2_from_fullframe` 继续保留为稳定备选；`crop_only` 与 `img768` 都应视为已完成但不推荐提升为默认主线的对照实验。

本轮明确不改动：
- 不改 `train_workwear.py`、`run_person_flow.py`、prepare 逻辑或任何训练代码。
- 不改 ROI keep rule、`crop_margin_px` 配置、prepared 数据集内容和历史训练产物。
- 不启动新的训练、续训或重新评估，仅整理已完成 run 的结果并更新长期文档。

## 2026-04-28 修正 ROI-aware v3 严格断点续训命令中的 `--project-config` 路径

变更来源：
- 用户按文档中的严格断点续训命令执行 `backend-train-model/train_workwear.py train --resume` 时，收到报错：项目配置文件路径被错误解析成了 `backend-train-model\\backend-train-model\\person-train-model\\person_project_config.json`。
- 排查后确认，`train_workwear.py` 对 `--project-config` 的相对路径会以 `backend-train-model/` 作为基准目录解析，因此文档中的 `backend-train-model\\person-train-model\\person_project_config.json` 多写了一层前缀。

变更总览：
1. 修正 `person_run_method.md` 中 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768` 严格断点续训命令里的 `--project-config` 参数。
2. 将错误写法 `backend-train-model\\person-train-model\\person_project_config.json` 改为脚本可正确解析的相对路径 `person-train-model\\person_project_config.json`。
3. 保持 `--resume ...\\weights\\last.pt` 部分不变，因为该路径按当前仓库根目录运行时仍然有效。

涉及文件：
- `backend-train-model/person-train-model/train-docs/person_run_method.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无代码配置项变更。
- 无新的 CLI 参数变更。
- 本轮只更正文档中的命令路径写法。

兼容性注意：
- 这个修正只影响 `train_workwear.py` 的 `--project-config` 参数写法；`--resume` 仍应指向实际存在的 `weights\\last.pt`。
- 如果从仓库根目录运行 `python backend-train-model\\train_workwear.py`，则 `--project-config` 的相对路径应按 `backend-train-model/` 为基准来写，而不是再手动补一层 `backend-train-model\\`。
- 若后续改用绝对路径传 `--project-config`，则不会再受到这类相对路径基准差异影响。

本轮明确不改动：
- 不改 `train_workwear.py`、`config.py` 或任何训练代码逻辑。
- 不改 ROI keep rule、数据集版本、训练参数和历史训练报告。
- 不启动新的续训或重新训练，仅修正文档中的错误命令。

## 2026-04-27 补充 ROI-aware v3 `img768` 的严格断点续训命令

变更来源：
- 用户在查看下一步 `imgsz=768, batch=2` 训练命令后，进一步追问“训练到中途中断了，怎么严格断点续训”，并要求把对应命令直接补进 `backend-train-model/person-train-model/train-docs/person_run_method.md`。
- 当前仓库中的严格断点续训入口不在 `run_person_flow.py` wrapper，而在底层 `backend-train-model/train_workwear.py train --resume`，因此需要把这条命令显式写进运行文档，避免误用“重新开一轮训练”的方式代替续训。

变更总览：
1. 在 `person_run_method.md` 的 `person_roi_aware_v3_mask_then_crop_margin64` 段中新增“严格断点续训命令”小节。
2. 明确给出 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768` 对应 `last.pt` 的严格续训命令，直接调用 `backend-train-model/train_workwear.py train --resume`。
3. 补充备注说明：`--resume` 模式下不要再混传新的训练参数，否则就不再是严格断点续训。

涉及文件：
- `backend-train-model/person-train-model/train-docs/person_run_method.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无代码配置项变更。
- 无新的 CLI 参数变更。
- 新增文档中的严格断点续训命令入口：
  - `backend-train-model/train_workwear.py train --resume ...\\weights\\last.pt`

兼容性注意：
- 这条续训命令只适用于“同一个 run 中途被打断，且 `last.pt` 仍保留 optimizer / epoch 状态”的情况；如果只是拿 `best.pt` 或已经完成的 run 重新开训，就不属于严格断点续训。
- `run_person_flow.py train --base-model xxx\\last.pt` 不是严格断点续训，它只是在新的训练流程里把 checkpoint 当作初始权重使用。
- 本轮补的是当前 `img768` 实验 run 的明确续训入口，不等于修改 person 训练主线或默认推荐 run。

本轮明确不改动：
- 不改 `train_workwear.py`、`run_person_flow.py` 或任何训练代码逻辑。
- 不改 ROI keep rule、数据集版本、训练参数和历史训练报告。
- 不启动新的续训或重新训练，仅补充运行文档。

## 2026-04-27 更新 `person_run_method.md` 中 ROI-aware v3 的下一步训练命令

变更来源：
- 用户根据 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` 与 `crop_only` / `v2` 的对比结果，要求把下一步继续提升指标所需的训练命令直接补充到 `backend-train-model/person-train-model/train-docs/person_run_method.md`。
- 当前阶段结论已经收敛到：下一步优先在 `mask_then_crop + crop_margin_px=64 + from_fullframe` 这条更优分支上补跑 `imgsz=768, batch=2`，而不是切回 `crop_only` 或直接换 `yolov8s`。

变更总览：
1. 在 `person_run_method.md` 的 `person_roi_aware_v3_mask_then_crop_margin64` 段中保留已完成的 `imgsz=640, batch=4` 基线命令。
2. 新增下一步优先训练的 `imgsz=768, batch=2` run 名、训练命令和对应评估命令，便于后续直接执行。
3. 补充备注说明：这一步是受控实验，只调整输入分辨率和 batch，其他条件保持不变，用于验证小目标 / 边界样本上的进一步收益。

涉及文件：
- `backend-train-model/person-train-model/train-docs/person_run_method.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无代码配置项变更。
- 无新的 CLI 参数变更。
- 新增文档中的下一步推荐 run 名：
  - `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_img768`

兼容性注意：
- 本次新增的是同一数据集版本下的下一步训练命令，不等于替换历史 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` 基线 run。
- `imgsz=768, batch=2` 仅作为当前优先补跑实验；如果后续要写入正式“当前最佳 run”结论，应以新的训练和评估结果为准。
- 本轮未同步修改 `person_project_config.json` 中的默认推荐 run 名；当前更新范围仅限训练运行文档。

本轮明确不改动：
- 不改 `prepare-roi-aware` 逻辑、ROI keep rule、`crop_margin_px` 配置和任何训练代码。
- 不改 `person_project_config.json`、`backend-train-model/AGENTS.md` 或历史训练报告。
- 不启动新的长时间训练，仅更新可直接执行的命令文档。

## 2026-04-24 新增 `roi_compare.md` 并同步 ROI-aware person 当前结论

变更来源：
- 用户已完成 `person_roi_aware_v2_from_fullframe` 的训练与评估，并要求把 `person_roi_aware`、`person_fullframe`、`person_roi_aware_v2` 三次训练的具体数据指标对比写入 `backend-train-model/person-train-model/train-docs/roi_compare.md`。
- 用户进一步要求在对比文档中加入维护约束：以后每次完成新的训练评估，都必须继续新增对比记录。

变更总览：
1. 新增 `backend-train-model/person-train-model/train-docs/roi_compare.md`，集中记录三条 person 分支的训练 / 评估对比结果。
2. 在 `roi_compare.md` 中补充文档维护约束，明确以后每次新增训练评估后都要追加新的对比记录，并保持“最新在前、历史在后”。
3. 同步更新根 `AGENTS.md` 与 `backend-train-model/AGENTS.md` 中的 person / ROI-aware 当前状态，写明：
   - 历史 ROI-aware v1 结果
   - 当前 ROI-aware v2 数据集统计
   - `person_roi_aware_v2_from_fullframe` 的当前 test 指标
   - 当前结论与解读边界

涉及文件：
- `backend-train-model/person-train-model/train-docs/roi_compare.md`
- `backend-train-model/AGENTS.md`
- `AGENTS.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无新增代码配置项。
- 无新的 CLI 参数变更。
- 新增文档维护约束：
  - `roi_compare.md` 后续必须持续追加新的训练 / 评估对比记录。

兼容性注意：
- `roi_compare.md` 中对 `person_fullframe` 与 ROI-aware 分支的比较，明确注明了“不是严格同数据集公平对照”；后续引用该文档时不要把这一点写错。
- 当前“最好”的结论应写成：`ROI-aware v2 数据集 + from_fullframe 初始化` 这套组合最好，而不是把提升简单归因到单一 keep rule。

本轮明确不改动：
- 不新增任何训练代码、prepare 逻辑或配置项。
- 不重跑已有训练与评估，只整理现有报告并写入文档。
- 不修改 `inspection-flask/` 在线链路。

## 2026-04-24 生成 `person_roi_aware_v2` 数据集并重排训练运行文档

变更来源：
- 用户确认保留 `person_roi_aware` 与 `person_roi_aware_v2` 两套产物，并已经手动创建 `backend-train-model/person-train-model/train-result/prepared/person_roi_aware_v2/` 目录。
- 用户要求我直接生成 v2 数据集，并把 `person_run_method.md` 按 `person_fullframe`、`person_roi_aware`、`person_roi_aware_v2` 三个版本拆开，且新增“最新在前、历史在后”的文档迭代约束。

变更总览：
1. 生成独立的 v2 ROI 配置文件 `roi_config.v2.generated.json`，避免覆盖历史 v1 的 ROI 配置元信息。
2. 生成独立的 v2 ROI-aware prepared 数据集 `person_roi_aware_v2/sequence_contiguous`，保留 v1 历史产物不变。
3. 重写 `person_run_method.md` 的组织方式，把通用前置条件单独提到 H1，并把 `person_roi_aware_v2`、`person_roi_aware`、`person_fullframe` 三个版本拆成独立 H1 段。
4. 在运行文档中新增维护约束：以后新增训练版本时，必须新增独立 H1 段，顺序固定为“最新在前、历史在后”，并保持版本段结构一致。

涉及文件：
- `backend-train-model/person-train-model/train-result/working/roi/roi_config.v2.generated.json`
- `backend-train-model/person-train-model/train-result/prepared/person_roi_aware_v2/sequence_contiguous/dataset.yaml`
- `backend-train-model/person-train-model/train-result/prepared/person_roi_aware_v2/sequence_contiguous/prepare_report.json`
- `backend-train-model/person-train-model/train-docs/person_run_method.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无新增代码配置项。
- 新增独立产物路径：
  - `train-result/working/roi/roi_config.v2.generated.json`
  - `train-result/prepared/person_roi_aware_v2/sequence_contiguous/`

兼容性注意：
- 本轮保留旧版 `person_roi_aware/sequence_contiguous` 目录不变；后续训练时请显式传 `--dataset-yaml` 区分 v1 / v2。
- `person_roi_aware_v2` 当前 prepare 统计为：`502` 张图、`1342` 个保留框、`316` 个丢弃框、`14` 张空负样本；与历史 v1 数据集不完全一致，这是本轮规则变化带来的正常结果。
- `person_run_method.md` 现在按版本管理；后续新增版本时不要插入到历史段落中间，应直接加在最前面的版本区。

本轮明确不改动：
- 不启动新的长时间训练，只生成 v2 数据集与整理运行文档。
- 不覆盖历史 `person_roi_aware` v1 prepared 数据集。
- 不修改 `inspection-flask/` 在线检测链路。

## 2026-04-24 落地 ROI-aware person keep rule v2

变更来源：
- 用户针对 `backend-train-model/person-train-model/train-docs/roi_problem_solution.md` 中的 v2 规则继续追问“为什么需要 `bottom_center_inside OR box_ioa >= 0.25`”，并在确认思路后要求把相关代码直接改成 v2。
- 当前更晚的结论文档已经明确：ROI-aware person 的下一步应先修正 ROI keep rule，再继续后续 `from_fullframe` 训练。

变更总览：
1. 扩展 `prepare_person_dataset.py` 的 ROI 配置解析，支持 `roi.keep_rule.bottom_center_inside` 与 `roi.keep_rule.min_box_ioa`，并增加 keep rule 至少启用一个条件的校验。
2. 更新 `prepare_roi_aware_person_dataset.py`，把 ROI-aware 过滤逻辑从单一 `center_inside` 升级为可配置 keep rule；当前默认配置落为 `center_inside=false`、`bottom_center_inside=true`、`min_box_ioa=0.25`。
3. 更新 `visualize_roi_filter_samples.py`，让 overlay 与 prepare 使用同一套 keep rule 判定，并额外绘制框中心点与底边中心点，便于复核边界样本。
4. 更新 `labelme_roi_to_config.py` 与 `person_project_config.json`，让提取出的 ROI 配置元信息与项目默认 keep rule 保持一致。
5. 同步更新 `person_run_method.md` 与 `roi_aware_person_dataset_plan.md`，避免文档继续停留在旧版 `center_inside` 规则。

涉及文件：
- `backend-train-model/person-train-model/train-code/prepare_person_dataset.py`
- `backend-train-model/person-train-model/train-code/prepare_roi_aware_person_dataset.py`
- `backend-train-model/person-train-model/train-code/visualize_roi_filter_samples.py`
- `backend-train-model/person-train-model/train-code/labelme_roi_to_config.py`
- `backend-train-model/person-train-model/person_project_config.json`
- `backend-train-model/person-train-model/train-docs/person_run_method.md`
- `backend-train-model/person-train-model/train-docs/roi_aware_person_dataset_plan.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- `backend-train-model/person-train-model/person_project_config.json`
  - `roi.keep_rule.center_inside`：当前默认调整为 `false`
  - `roi.keep_rule.bottom_center_inside`：新增，当前默认 `true`
  - `roi.keep_rule.min_box_ioa`：新增，当前默认 `0.25`
  - `person_dataset.roi_aware_recommended_run_name`：更新为 `person_roi_aware_v2_from_fullframe`
- 保持 `roi.mode=mask_then_crop` 不变，本轮未引入 `crop_margin_px`。

兼容性注意：
- 旧配置若仍只启用 `center_inside=true`，当前代码仍兼容，不会被强制改成 v2；本轮只是把项目默认配置切到 v2。
- `train-result/working/roi/roi_config.generated.json`、`train-result/prepared/person_roi_aware/.../prepare_report.json` 等历史产物不会自动回写；如需让产物元信息和当前默认规则一致，需要重新执行 `extract-roi-config --overwrite` 与 `prepare-roi-aware --overwrite`。
- `box IoA` 当前采用基于 ROI mask 的像素面积近似计算，阈值按当前文档建议固定为 `0.25`。

本轮明确不改动：
- 不启动新的 `from_fullframe` 长时间训练，也不改动 `person_fullframe_baseline` 既有权重与评估报告。
- 不在本轮加入 `crop_margin_px=64`；该项仍保留为下一阶段可选改进。
- 不修改 `inspection-flask/` 在线检测链路。

## 2026-04-23 统一 AI Agent 上下文入口与项目长期信息

变更来源：
- 用户要求阅读当前仓库文件，将每一类重要信息沉淀到 `.claude`、`AGENTS.md`、`CLAUDE.md` 等 AI 自动读取入口中，并判断保留哪个入口更合适、删除多余文件。

变更总览：
1. 将根目录 `AGENTS.md` 作为唯一主说明入口，集中记录项目模块分工、数据集事实、工服 baseline、person / ROI-aware person 状态、`inspection-flask` 在线链路、`otherMonitor` 三类检测和文档写作口径。
2. 将 `CLAUDE.md` 改为 Claude Code 自动读取跳转文件，只要求 Claude 读取并遵守 `AGENTS.md`，避免重复维护两套事实。
3. 更新 `backend-train-model/AGENTS.md`，补充本目录当前训练范围、工服指标、person 指标、ROI-aware 优先方案和日志维护要求。
4. 更新 `docs/AGENTS.md` 与 `inspection-flask/AGENTS.md`，分别固化文档写作口径与在线检测链路边界。
5. 删除 `.claude/settings.local.json`，因为该文件是 Claude 本地权限设置，不是项目长期说明入口，保留会造成“上下文入口过多”的误解。

涉及文件：
- `AGENTS.md`
- `CLAUDE.md`
- `backend-train-model/AGENTS.md`
- `docs/AGENTS.md`
- `inspection-flask/AGENTS.md`
- `.claude/settings.local.json`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 未新增训练配置项。
- 仅调整 AI Agent 上下文入口与文档维护规则。

兼容性注意：
- Codex 仍以 `AGENTS.md` 为主入口。
- Claude Code 仍会自动读取 `CLAUDE.md`，但长期事实统一跳转到 `AGENTS.md`。
- `.claude/settings.local.json` 删除后，不再保留旧的 Claude 本地命令 allowlist；如后续确实需要 Claude 权限配置，应单独重建，不应混作项目说明文档。

本轮明确不改动：
- 不改训练代码、数据 YAML / JSON 配置、模型权重和训练产物。
- 不修复历史 `update_log.md` 中已有的乱码段落。
- 不重新构建任何数据集或重新评估模型。


## 2026-04-22 ???? PPT ??????? person ??

?????
- ?????? PPT ???????? person ???????? 3 ???????????????????

?????
1. ???? `??PPT??.md` ????????????????????
2. ?? person fullframe baseline ? ROI-aware person baseline ??? 4 ????Precision?Recall?mAP50?mAP50-95?????? best epoch?
3. ?????? person ??????????? mAP50-95 ?? 0.55 ???ROI-aware person ? recall ?? fullframe person?
4. ????????? ROI-aware person ???? fullframe / ROI-aware ? PR ????

?????
- `backend-train-model/docs/??PPT??.md`
- `backend-train-model/docs/update_log.md`

?? / ??????
- ?????????????????

??????
- ?????????????????????????????

??????
- ?????????????ROI JSON ???????
- ????????????????????????

## 2026-04-22 ???? PPT ????? person ? ROI

?????
- ?????? merged fullframe baseline ?????????????? PPT ????? person ??? ROI ?????

?????
1. ?? `??PPT??.md` ???????????? person fullframe baseline?ROI-aware person ? ROI ?????
2. ?????????7 ????502 ? person ???1651 ? person ??502 ? ROI JSON??? person fullframe / ROI-aware ? mAP50 ???
3. ?????? person ?????person ?????ROI ?? overlay ? ROI-aware person ????

?????
- `backend-train-model/docs/??PPT??.md`
- `backend-train-model/docs/update_log.md`

?? / ??????
- ?????????????????

??????
- ?????????????????????????????

??????
- ?????????????ROI JSON ???????
- ????????????????????????

## 2026-04-22 ???? PPT ????

?????
- ????? `backend-train-model/docs` ?????????? PPT ??? Markdown ??????????????????????????????? 2 ????????

?????
1. ?? `??PPT??.md`?? 3 ??????????
2. ???????????7 ????clothes/person ? 502 ????? 980/1651 ??ROI JSON 502 ?????? merged fullframe baseline ? P/R/mAP ???
3. ??????????????????????????ROI ?? overlay?person fullframe / ROI-aware ?????????? PPT?

?????
- `backend-train-model/docs/??PPT??.md`
- `backend-train-model/docs/update_log.md`

?? / ??????
- ???????????????

??????
- ?????????????????????????????
- ??????????? `backend-train-model/docs/` ??????????? Markdown ??? PPT ???

??????
- ??????????????????? ROI ?????
- ?????????????????????????
## 2026-04-21 修正 clothes / person / ROI 默认路径并清理旧 ROI 工作区

变更来源：
- 用户提供了最新的 clothes、person 与 ROI 标注根目录，并要求统一检查项目内相关路径配置，重点修正 YAML / JSON，同时确认 `backend-train-model/person-train-model/roi-work/` 中旧工作区是否仍有价值。

变更总览：
1. 修正 clothes 默认入口与 merged 构建配置：
   - `backend-train-model/config.py`
   - `backend-train-model/project_config.json`
   - `backend-train-model/All-train-model/*.build.json`
   全部改为新的 `all_labels\clothes_labels\...` 根目录；
   同时确认图片现在直接位于各序列目录本身，不再额外拼接 `frames/`。
2. 扩展 person ROI 配置入口：
   - `person_project_config.json` 新增 `roi.json_root`，默认指向 `D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\roi-json`
   - 新增 `roi.work_root`，保留手工抽帧标注工作区的可选路径。
3. 调整 ROI 相关脚本默认值：
   - `run_person_flow.py extract-roi-config` 默认读取 `roi.json_root`
   - `run_person_flow.py setup-roi-workdir` 默认写入 `roi.work_root`
   - `labelme_roi_to_config.py` / `setup_roi_workdir.py` 同步改为配置驱动，不再把 `roi-work` 硬编码为唯一默认源。
4. 同步更新数据说明与 person ROI 操作文档，明确当前公共 ROI 根目录为 `all_labels\roi-json`。
5. 旧的本地 `roi-work/` 仅包含历史代表帧与说明文件，不再被当前默认 ROI 提取流程依赖；本轮将其删除，后续若需要可用 `setup-roi-workdir` 重新生成。

涉及文件：
- `backend-train-model/config.py`
- `backend-train-model/project_config.json`
- `backend-train-model/All-train-model/first_train_holdout_v1.build.json`
- `backend-train-model/All-train-model/merged_clothes_v1.build.json`
- `backend-train-model/All-train-model/merged_clothes_v2.build.json`
- `backend-train-model/All-train-model/merged_clothes_v2_balanced.build.json`
- `backend-train-model/All-train-model/unified_holdout_v1.build.json`
- `backend-train-model/person-train-model/person_project_config.json`
- `backend-train-model/person-train-model/train-code/prepare_person_dataset.py`
- `backend-train-model/person-train-model/train-code/run_person_flow.py`
- `backend-train-model/person-train-model/train-code/labelme_roi_to_config.py`
- `backend-train-model/person-train-model/train-code/setup_roi_workdir.py`
- `backend-train-model/person-train-model/train-docs/person_run_method.md`
- `backend-train-model/person-train-model/train-docs/ROI_Labelme.md`
- `backend-train-model/person-train-model/train-docs/roi_aware_person_dataset_plan.md`
- `backend-train-model/docs/update_log.md`
- `docs/dataset.md`

新增 / 变更配置项：
- `person_project_config.json` 新增：
  - `roi.json_root`
  - `roi.work_root`
- 更新已有路径配置值：
  - `config.py` 中的 `IMAGE_ROOTS` / `LABEL_ROOT`
  - `project_config.json` 中的 `data.image_roots` / `data.label_root`
  - 各 `*.build.json` 中的 `sequences[].image_root` / `sequences[].label_root`
- ROI CLI 默认行为调整：
  - `extract-roi-config` 默认取 `roi.json_root`
  - `setup-roi-workdir` 默认取 `roi.work_root`

兼容性注意：
- 旧配置如果未提供 `roi.json_root`，代码仍会回退到 `roi.work_root`，保持向后兼容。
- 当前删除的是本地旧 `roi-work/` 产物目录，不影响后续再次执行 `setup-roi-workdir` 重新生成。
- 历史日志中保留的旧路径仅用于追溯，不代表当前有效配置。

不改动说明：
- 本轮不修改 person / clothes 的类别定义与标注格式。
- 本轮不重新训练 clothes 或 person 模型。
- 本轮不改动 `inspection-flask/` 或线上权重路径。

## 2026-04-21 新增 ROI 边界保留规则解决方案文档

变更来源：
- 用户确认希望 ROI 外的人被去掉，但认为 `center_inside` 对“部分 person 框在 ROI 内”的边界样本过硬，并要求把讨论中的解决思路写入 `backend-train-model/person-train-model/train-docs/roi_problem_solution.md`。

变更总览：
1. 新增 `roi_problem_solution.md`。
2. 文档明确指出：
   - 不建议使用 `any overlap` 作为保留规则；
   - `center_inside` 对边界人偏硬；
   - ROI 表达的是地面业务区域，因此当前实现更适合使用“框底边中心点在 ROI 内”的判定语义；它只是对脚点位置的近似，不等于真实脚点检测；
   - 使用 `box_ioa = area(person_box ∩ ROI) / area(person_box)`，而不是 IoU。
3. 文档提出下一版推荐规则：
   - `bottom_center_inside == true`
   - 或 `box_ioa_with_roi >= 0.25`
   - 并建议配合 `crop_margin_px = 64`。
4. 文档给出推荐配置字段、落地顺序与后续训练命令建议。

涉及文件：
- `backend-train-model/person-train-model/train-docs/roi_problem_solution.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无代码配置变更。
- 文档中建议后续扩展：
  - `roi.keep_rule.bottom_center_inside`
  - `roi.keep_rule.min_box_ioa`
  - `roi.crop_margin_px`

兼容性注意：
- 本轮只新增方案文档，不修改现有 ROI-aware prepare 逻辑。
- 当前实际生成数据仍使用 `center_inside` 规则，直到后续单独实现 v2。

不改动说明：
- 本轮不重新生成 ROI-aware 数据集；
- 本轮不训练模型；
- 本轮不修改 Labelme ROI JSON 或 person 标签。

## 2026-04-21 复查修改后 4 张 ROI 过滤问题帧

变更来源：
- 用户对 ROI 标注进行了部分修改，并要求以上一轮发现的 4 张 `D15_20260119203927` 问题帧为例重新生成可视化，查看修改效果。

变更总览：
1. 重新从现有 Labelme ROI JSON 根目录提取 ROI 配置：
   - `D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\clothes`
   - 输出仍为 `backend-train-model/person-train-model/train-result/working/roi/roi_config.generated.json`
   - 当前仍为逐图 ROI：`per_image=502`
2. 重新生成 4 张问题帧 overlay：
   - `D15_20260119203927_frame_0181`
   - `D15_20260119203927_frame_0182`
   - `D15_20260119203927_frame_0183`
   - `D15_20260119203927_frame_0184`
3. 复查结果：
   - 4 张图仍均为 `boxes=1, kept=0, dropped=1`；
   - 4 个 person 框中心点仍在 ROI polygon 外；
   - 中心点到 ROI 边界的 signed distance 约为 `-118px` 到 `-133px`。

涉及文件：
- `backend-train-model/person-train-model/train-result/working/roi/roi_config.generated.json`
- `backend-train-model/person-train-model/train-result/review/roi_filter_overlays/`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无新增配置项。

兼容性注意：
- 本轮只刷新 ROI 配置与 overlay review 产物，不重新生成 ROI-aware 训练数据集。
- 若希望这 4 张从空 ROI 负样本变为正样本，需要继续扩大对应图片的 ROI polygon，或后续实现 IoA / margin 保留规则。

不改动说明：
- 本轮不修改 Labelme 源 JSON；
- 本轮不修改 person 标签；
- 本轮不启动训练或评估。

## 2026-04-21 新增 ROI 过滤问题帧可视化

变更来源：
- 用户追问 `D15_20260119203927` 的 ROI-aware test 中为什么存在 9 个空 ROI 负样本，并同意对其中 fullframe 有人但 ROI-aware 为空的 4 张问题帧做可视化检查。

变更总览：
1. 新增 `visualize_roi_filter_samples.py`：
   - 读取原图、聚合 person 标签和逐图 ROI 配置；
   - 在原图上画出 ROI polygon、ROI 最小外接矩形、person 框中心点；
   - 用绿色标记会被 ROI-aware 保留的框；
   - 用红色标记因 `center_inside=false` 被丢弃的框；
   - 生成 overlay 图片和 manifest。
2. 已针对以下 4 张问题帧生成可视化：
   - `D15_20260119203927_frame_0181`
   - `D15_20260119203927_frame_0182`
   - `D15_20260119203927_frame_0183`
   - `D15_20260119203927_frame_0184`

涉及文件：
- `backend-train-model/person-train-model/train-code/visualize_roi_filter_samples.py`
- `backend-train-model/person-train-model/train-result/review/roi_filter_overlays/`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无新增配置项。

兼容性注意：
- 该脚本只生成可视化 review 产物，不修改 ROI JSON、person 标签或训练数据集。
- 当前可视化依据仍是 ROI-aware v1 的 `center_inside` 保留规则。

不改动说明：
- 本轮不调整 ROI polygon；
- 本轮不重新生成 ROI-aware 数据集；
- 本轮不启动训练或评估。

## 2026-04-21 新增 ROI-aware person 首轮训练问题分析文档

变更来源：
- 用户在完成 `person_roi_aware_baseline` 首轮训练与评估后，要求把“训练提前早停、效果一般、下一步如何改进”的分析结论整理为独立文档，放到 `backend-train-model/person-train-model/train-docs/` 下。

变更总览：
1. 新增 `backend-train-model/person-train-model/train-docs/roi_first_problem.md`。
2. 文档系统记录了：
   - ROI-aware 首轮训练 run 与 fullframe 对照 run；
   - early stopping 发生在第 `123` 轮、最佳 `mAP50-95` 出现在第 `83` 轮；
   - ROI-aware 与 fullframe 在 val / test 上的指标对比；
   - 当前问题核心是高 precision、低 recall，test 侧漏检更重；
   - ROI-aware 数据集框数减少、特定序列被过滤过多的现象；
   - 下一步改进优先级，包括：
     - 用 fullframe person best 权重初始化 ROI-aware；
     - 尝试更高 `imgsz`；
     - 为 ROI crop 增加 margin；
     - 放宽边界目标保留规则；
     - 做 ROI 过滤 overlay 质检；
     - 后续再考虑降低训练增强强度。

涉及文件：
- `backend-train-model/person-train-model/train-docs/roi_first_problem.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无新增配置项。
- 无代码逻辑变更。

兼容性注意：
- 本轮仅新增分析文档，不修改现有训练入口、ROI 配置结构或数据准备逻辑。
- 文档中推荐的后续训练命令仍基于当前 `run_person_flow.py` 与已生成的 ROI-aware 数据集路径。

不改动说明：
- 本轮不重训模型；
- 本轮不修改 `labelme_roi_to_config.py`、`prepare_roi_aware_person_dataset.py` 或任何数据集文件；
- 本轮不修改 `inspection-flask/` 或线上权重路径。

## 2026-04-21 支持逐图 ROI JSON 并生成 ROI-aware person 数据集

变更来源：
- 用户澄清已经为每张图片导出了 Labelme ROI JSON，位置在 `D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\clothes\...\roi-json`，不需要使用代表帧重新标注。
- 本轮检查发现当前共有 `502` 个 ROI JSON，和 person 原图 stem 一一对应；同一序列内 ROI polygon 多数不完全一致，因此需要支持 per-image ROI，而不能强制每序列一个 canonical polygon。

变更总览：
1. 扩展 `labelme_roi_to_config.py`：
   - 支持读取逐图 ROI JSON；
   - 输出 `per_image` ROI 配置；
   - 当同一序列 ROI 完全一致时才额外写入 `per_sequence` fallback；
   - 对 Labelme 浮点误差导致的 `-0.0`、`width + 极小误差` 等边界点做容差裁剪。
2. 扩展 `prepare_roi_aware_person_dataset.py`：
   - 优先按 `sequence_name + image_stem` 读取逐图 ROI；
   - 缺少逐图 ROI 时再回退到 `per_sequence`；
   - `prepare_report.json` 记录 `roi_scope`。
3. 更新 `run_person_flow.py` 与 `labelme_roi_to_config.py` 的提取结果打印：
   - 同时显示“序列级 ROI 数”和“逐图 ROI 数”。
4. 已使用现有 clothes ROI JSON 生成统一 ROI 配置：
   - `backend-train-model/person-train-model/train-result/working/roi/roi_config.generated.json`
   - `scope=per_image`
   - `per_image_total=502`
5. 已生成 ROI-aware person 数据集：
   - `backend-train-model/person-train-model/train-result/prepared/person_roi_aware/sequence_contiguous/dataset.yaml`
   - 输入图片 `502`；
   - 输出图片 `502`；
   - 保留 person 框 `1343`；
   - 丢弃 person 框 `315`；
   - 边界裁剪框 `49`；
   - 空 ROI 负样本 `12`。
6. 更新 `person_run_method.md` 与 `ROI_Labelme.md`：
   - 明确代表帧脚手架只服务于“尚未标 ROI”的情况；
   - 当前已逐图标注时，直接传 `--roi-json-root D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\clothes`。

涉及文件：
- `backend-train-model/person-train-model/train-code/labelme_roi_to_config.py`
- `backend-train-model/person-train-model/train-code/prepare_roi_aware_person_dataset.py`
- `backend-train-model/person-train-model/train-code/run_person_flow.py`
- `backend-train-model/person-train-model/train-docs/person_run_method.md`
- `backend-train-model/person-train-model/train-docs/ROI_Labelme.md`
- `backend-train-model/person-train-model/train-docs/roi_aware_person_dataset_plan.md`
- `backend-train-model/docs/update_log.md`
- `backend-train-model/person-train-model/train-result/working/roi/roi_config.generated.json`
- `backend-train-model/person-train-model/train-result/prepared/person_roi_aware/sequence_contiguous/dataset.yaml`
- `backend-train-model/person-train-model/train-result/prepared/person_roi_aware/sequence_contiguous/prepare_report.json`

新增 / 变更配置项：
- 无新增 JSON 配置项。
- ROI 配置文件结构扩展：
  - 新增 `scope=per_image`
  - 新增 `per_image`
  - 新增 `summary.sequence_image_counts`
  - 新增 `summary.sequence_unique_polygon_counts`
- `prepare_report.json` 新增 `roi_scope`。

兼容性注意：
- 旧的每序列单 ROI 配置仍可通过 `per_sequence` 读取。
- 新的逐图 ROI 配置优先级更高，适合当前每张图片都已标 ROI 的数据。
- 当前 `backend-train-model/person-train-model/roi-work/` 仍可保留为后续新序列标注脚手架，但本轮生成 ROI-aware 数据集不依赖它。

不改动说明：
- 本轮不修改已有 Labelme JSON 原文件。
- 本轮不启动训练，不导出或部署权重。
- 本轮不修改 `inspection-flask/` 或线上权重路径。

## 2026-04-21 新增 ROI 标注工作区自动脚手架

变更来源：
- 用户已新建 ROI 相关目录，并要求继续实现“如果没有文件夹可以自行新建，确保正确且层次清晰易于管理”的 ROI 标注工作区准备步骤。

变更总览：
1. 新增 `setup_roi_workdir.py`：
   - 读取 `person_project_config.json` 中的 7 条 person 序列；
   - 自动创建 `roi-work/<sequence_name>/frames/` 与 `roi-work/<sequence_name>/roi-json/`；
   - 每条序列按时间顺序抽取默认 `3` 张代表帧复制到 `frames/`；
   - 为根目录和每条序列生成 `README.md`，写入 Labelme 启动命令与标注规则；
   - 生成 `roi_work_manifest.json`，记录源目录、抽帧结果、输出目录和后续命令；
   - 自动创建 `train-result/working/roi/README.md`，说明 `roi_config.generated.json` 的生成方式。
2. 扩展 `run_person_flow.py`：
   - 新增 `setup-roi-workdir` 命令；
   - 新增 `--roi-frames-per-sequence`；
   - 新增 `--overwrite-roi-frames`；
   - 复用 `--roi-json-root` 作为 ROI 工作区根目录。
3. 已在本地执行默认工作区生成：
   - `backend-train-model/person-train-model/roi-work/`；
   - 7 个序列子目录；
   - 每个序列 `3` 张代表帧；
   - 每个序列独立 `roi-json/` 目录。
4. 更新 `person_run_method.md` 与 `ROI_Labelme.md`，把自动工作区生成作为 ROI-aware 流程的第一步。

涉及文件：
- `backend-train-model/person-train-model/train-code/setup_roi_workdir.py`
- `backend-train-model/person-train-model/train-code/run_person_flow.py`
- `backend-train-model/person-train-model/train-docs/person_run_method.md`
- `backend-train-model/person-train-model/train-docs/ROI_Labelme.md`
- `backend-train-model/docs/update_log.md`
- `backend-train-model/person-train-model/roi-work/README.md`
- `backend-train-model/person-train-model/roi-work/roi_work_manifest.json`
- `backend-train-model/person-train-model/roi-work/<sequence_name>/README.md`
- `backend-train-model/person-train-model/roi-work/<sequence_name>/frames/*.jpg`
- `backend-train-model/person-train-model/roi-work/<sequence_name>/roi-json/`
- `backend-train-model/person-train-model/train-result/working/roi/README.md`

新增 / 变更配置项：
- 无新增 JSON 配置项。
- 新增 CLI：
  - `run_person_flow.py setup-roi-workdir`
  - `--roi-frames-per-sequence`
  - `--overwrite-roi-frames`

兼容性注意：
- `setup-roi-workdir` 只准备 Labelme 标注工作区，不会生成假的 ROI polygon，也不会修改 person 标签。
- 当前 `roi-json/` 目录仍需人工用 Labelme 保存真实 `.json` 后，才能运行 `extract-roi-config --overwrite`。
- 当前已存在的 `roi_config.generated.json` 如为空文件，后续使用 `extract-roi-config --overwrite` 覆盖即可。

不改动说明：
- 本轮不启动 Labelme GUI，不伪造 ROI JSON。
- 本轮不生成 ROI-aware YOLO 数据集，不训练模型。
- 本轮不修改 `inspection-flask/` 或线上权重路径。

## 2026-04-21 落地 ROI-aware person 数据集生成链路

变更来源：
- 用户已完成第一版 ROI polygon 标注，并确认负样本图片中本身没有 person；本轮按既定方案实现 `Labelme ROI json -> ROI 配置 -> ROI-aware person 数据集` 的最小可用链路。

变更总览：
1. 扩展 `person_project_config.json`：
   - 新增 `roi` 配置段；
   - 新增 ROI-aware 数据集输出目录与推荐 run 名。
2. 扩展 person 项目配置加载逻辑：
   - 读取 `roi.enabled`、`roi.mode`、`roi.keep_rule.center_inside`、`roi.config_path`；
   - 读取 `person_dataset.roi_aware_prepared_output_root` 与 `person_dataset.roi_aware_recommended_run_name`；
   - 将 split 配置纳入 person 上下文，供 ROI-aware prepare 复用同一切分口径。
3. 新增 `Labelme ROI json -> ROI config` 脚本：
   - 递归读取 `roi-work` 下的 Labelme JSON；
   - 只接受 `label == "roi"` 且 `shape_type == "polygon"` 的 ROI；
   - 支持通过 `sequence_name` 或唯一的图片根目录末级名识别序列；
   - 同一序列 polygon 不一致、缺少 ROI、多 ROI、未知序列或点越界时直接报错。
4. 新增 ROI-aware person 数据集生成脚本：
   - 对 ROI 外区域置黑；
   - 裁剪到 ROI polygon 最小外接矩形；
   - 只保留中心点落在 ROI 内的 person 框；
   - 对保留框做裁剪与 YOLO 坐标重映射；
   - ROI 内无人时保留为空标注负样本；
   - 输出 `dataset.yaml` 与 `prepare_report.json`；
   - `--overwrite` 时同步刷新汇总 person 标签，避免原图片根目录修正后复用旧标签目录。
5. 扩展 `run_person_flow.py`：
   - 新增 `extract-roi-config`；
   - 新增 `prepare-roi-aware`；
   - 保持原 `prepare/train/evaluate/export/all` 默认行为不变。
6. 更新 person ROI 相关文档，补充 ROI-aware 数据集生成、训练与评估命令，并标记方案已进入第一版代码落地状态。

涉及文件：
- `backend-train-model/person-train-model/person_project_config.json`
- `backend-train-model/person-train-model/train-code/prepare_person_dataset.py`
- `backend-train-model/person-train-model/train-code/labelme_roi_to_config.py`
- `backend-train-model/person-train-model/train-code/prepare_roi_aware_person_dataset.py`
- `backend-train-model/person-train-model/train-code/run_person_flow.py`
- `backend-train-model/person-train-model/train-docs/person_run_method.md`
- `backend-train-model/person-train-model/train-docs/ROI_Labelme.md`
- `backend-train-model/person-train-model/train-docs/roi_aware_person_dataset_plan.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- `roi.enabled`
- `roi.mode`
- `roi.keep_rule.center_inside`
- `roi.config_path`
- `person_dataset.roi_aware_prepared_output_root`
- `person_dataset.roi_aware_recommended_run_name`

兼容性注意：
- 当前 ROI-aware v1 仅支持 `mask_then_crop + center_inside`。
- 现有 `person_fullframe_baseline` 母数据集、默认 `prepare`、训练、评估、导出命令保持不变。
- 本轮没有修改 `backend-train-model/dataset_tools.py` 的 `fullframe/personcrop` 公共 prepare mode，也没有改变 clothes baseline 与 shared personcrop 行为。

不改动说明：
- 本轮不重新生成任何真实数据集产物；
- 本轮不启动训练；
- 本轮不导出或部署 person 权重；
- 本轮不修改 `inspection-flask/`、`All-train-model/` 或线上权重路径。

## 2026-04-21 适配 clothes 图片下沉到 `frames` 子目录

变更来源：
- 用户反馈当前 clothes 原始图片已不再直接放在各序列外层目录，而是统一下沉到对应序列的 `frames/` 子目录。
- 用户要求同步修正 `backend-train-model` 当前默认入口、`All-train-model` 构建配置，以及仓库里仍在直接使用的 `dataset.yaml` / 数据说明文档。

变更总览：
1. 更新 `backend-train-model/config.py` 与 `backend-train-model/project_config.json`，把默认单源 `group3_1` 的 `image_roots` 统一切到 `frames/` 子目录。
2. 更新 `backend-train-model/All-train-model/*.build.json`，把 `group3_1 / group3_2 / group3_3` 的全部 `image_root` 同步切到新的 `frames/` 子目录。
3. 在 `backend-train-model/config.py` 新增 `resolve_sequence_name_from_image_root(...)`，并让 `dataset_tools.py`、`train_workwear.py` 统一使用，避免多个 `frames` 目录被错误识别成同一个序列名。
4. 修正仍在使用的 clothes `dataset.yaml`：
   - `backend-train-model/All-train-model/datasets/merged_clothes_v1_positive_only/dataset.yaml`
   - `backend-train-model/All-train-model/datasets/merged_clothes_v2_full_reviewed/dataset.yaml`
   - `backend-train-model/first-train/artifacts/prepared/fullframe/sequence_contiguous/dataset.yaml`
   使其 `path` 指向当前 `D:\University-Competition\...` 仓库位置；其中 `first-train` 版本同时补回缺失的 `first-train/` 目录层级。
5. 更新 `docs/dataset.md`，明确 clothes 图片现位于各序列目录下的 `frames/` 子目录，而标注根目录保持不变。

涉及文件：
- `backend-train-model/config.py`
- `backend-train-model/dataset_tools.py`
- `backend-train-model/train_workwear.py`
- `backend-train-model/project_config.json`
- `backend-train-model/All-train-model/first_train_holdout_v1.build.json`
- `backend-train-model/All-train-model/merged_clothes_v1.build.json`
- `backend-train-model/All-train-model/merged_clothes_v2.build.json`
- `backend-train-model/All-train-model/merged_clothes_v2_balanced.build.json`
- `backend-train-model/All-train-model/unified_holdout_v1.build.json`
- `backend-train-model/All-train-model/datasets/merged_clothes_v1_positive_only/dataset.yaml`
- `backend-train-model/All-train-model/datasets/merged_clothes_v2_full_reviewed/dataset.yaml`
- `backend-train-model/first-train/artifacts/prepared/fullframe/sequence_contiguous/dataset.yaml`
- `backend-train-model/docs/update_log.md`
- `docs/dataset.md`

新增 / 变更配置项：
- 无新增 JSON 字段或 CLI 参数。
- 更新已有路径配置值：
  - `config.py` 中的 `IMAGE_ROOTS`
  - `project_config.json` 中的 `data.image_roots`
  - 各 `*.build.json` 中 `sequences[].image_root`
- 新增运行时辅助函数：
  - `config.resolve_sequence_name_from_image_root(...)`

兼容性注意：
- 默认单源 `audit / prepare / inspection validate` 现在支持 `image_roots` 直接指向 `frames/` 子目录，不再把多个目录都归并成重复的 `frames` 序列名。
- `All-train-model` 的 merged / holdout 构建逻辑不变，仍以各 `*.build.json` 中显式配置的 `sequence_name + image_root` 为准。
- 本轮只修正当前配置入口与可直接消费的 `dataset.yaml`；历史 build / eval 产物中的旧路径字符串仍代表旧运行现场，不作为当前训练入口。

不改动说明：
- 本轮不修改 `inspection-flask/` 代码。
- 本轮不调整 labels 根目录、类别定义、split manifest、训练超参数或权重加载逻辑。
- 本轮不重建 merged 数据集，也不重跑训练 / 评估任务。

## 2026-04-17 新增 Labelme ROI 标注使用说明

变更来源：
- 用户在确认采用 `Labelme` 进行离线 ROI 标注后，进一步要求单独补一份详细文档，明确说明：`Labelme` 怎么安装、需要什么环境、如何创建环境、当前最稳妥的 Python 版本建议，以及如何实际使用该软件进行 ROI 标注。

变更总览：
1. 新增 `backend-train-model/person-train-model/train-docs/ROI_Labelme.md`。
2. 文档补充了：
   - `Labelme` 的适用场景与当前项目中的定位；
   - 当前最新稳定版与官方 Python 支持范围；
   - 为什么不建议直接安装到仓库默认 `yolo_code` 环境；
   - 推荐的 `Conda` 独立环境创建命令；
   - 官方 `uv` 安装路线；
   - 使用 `Labelme` 进行 polygon ROI 标注的逐步操作说明；
   - 当前项目下 ROI 应如何画、如何组织代表帧与输出 `json`。

涉及文件：
- `backend-train-model/person-train-model/train-docs/ROI_Labelme.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 本轮不修改任何训练代码、推理代码或项目配置文件。
- 仅新增一份面向 ROI 标注阶段的使用文档。

兼容性注意：
- 本轮仅新增文档，不改变当前 `person` 训练、评估、导出和数据准备流程。
- 当前仓库默认训练环境 `yolo_code` 仍保持 `Python 3.9.25` 约定不变；文档只是额外建议为 `Labelme` 单独创建 `Python 3.10` 环境。

不改动说明：
- 本轮不实现 `Labelme json -> ROI 配置` 的自动转换脚本。
- 本轮不新增 ROI 预处理代码，不重训模型，不改现有数据集结构。

## 2026-04-17 新增 ROI-aware person 数据集方案文档

变更来源：
- 用户在复盘 `person` 首轮检测效果后，明确提出希望为“面向业务 ROI 的 person 数据集方案”单独落一份文档，放到 `backend-train-model/person-train-model/train-docs/` 下，指导下一阶段数据准备与训练方向。

变更总览：
1. 新增 `backend-train-model/person-train-model/train-docs/roi_aware_person_dataset_plan.md`。
2. 文档明确区分：
   - 当前 `fullframe + 全图所有人标注` 母数据集；
   - 后续面向业务 ROI 的派生 `person` 数据集。
3. 文档给出 ROI-aware 推荐路线：
   - 不在完整原图里对 ROI 外可见人员故意漏标；
   - 优先采用“ROI 外遮罩 + ROI 最小外接矩形裁剪 + ROI 内人框保留”的生成方式；
   - 保留 fullframe baseline，新增 ROI-aware person 作为平行对照分支。
4. 文档补充了：
   - 标注与样本保留规则；
   - 建议的数据准备流程；
   - 建议的 ROI 配置方式；
   - 训练与评估对照口径；
   - 当前阶段明确不做的事情。

涉及文件：
- `backend-train-model/person-train-model/train-docs/roi_aware_person_dataset_plan.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 本轮不修改任何现有代码配置。
- 仅在方案文档中提出后续实现建议：
  - 可在 `backend-train-model/person-train-model/person_project_config.json` 中新增 `roi` 配置段；
  - 由实现阶段再决定是否正式落地。

兼容性注意：
- 本轮只新增方案文档，不修改 `person` 训练脚本、数据准备脚本、默认训练命令或当前数据集产物。
- 当前 `person_fullframe_baseline` 仍是现有 `person` 训练结果的唯一已落地产物；新增文档不会改变当前链路默认行为。

不改动说明：
- 本轮不修改 `backend-train-model/person-train-model/train-code/` 下的任何脚本。
- 本轮不重新生成 `person` 数据集，不重训模型，不导出新权重。
- 本轮不修改 `inspection-flask/`、`All-train-model/` 或根 `docs/dataset.md` 的现有内容。

## 2026-04-17 修正 person 文档中的严格断点续训命令

变更来源：
- 用户在实际训练 `person` 时发现前一版文档里的续训命令仍然附带了 `--dataset-yaml`、`--device`、`--workers` 等参数，希望改成当前代码真实支持的写法。

变更总览：
1. 更新 `backend-train-model/person-train-model/train-docs/person_run_method.md` 的续训说明。
2. 将续训命令改为仅保留：
   - `train`
   - `--project-config`
   - `--resume path\\to\\last.pt`
3. 补充说明当前 `train_workwear.py --resume` 的行为：
   - 会严格沿用 checkpoint 内保存的训练配置；
   - 不能再同时传入 `--dataset-yaml`、`--base-model`、`--imgsz`、`--epochs`、`--batch`、`--patience`、`--workers`、`--device` 等参数。

涉及文件：
- `backend-train-model/person-train-model/train-docs/person_run_method.md`
- `backend-train-model/docs/update_log.md`

兼容性注意：
- 本轮只修正文档，不修改任何续训代码逻辑。
- 当前 person 推荐续训方式仍然是显式指向本次 run 的 `weights\\last.pt`。

## 2026-04-16 同步 person 训练文档命令，显式固定本地基模

变更来源：
- 用户确认准备进入 `person` 模型训练阶段，希望把 `backend-train-model/person-train-model/train-docs/person_run_method.md` 中的运行命令调整为当前推荐写法。

变更总览：
1. 更新 `backend-train-model/person-train-model/train-docs/person_run_method.md` 中的首次训练命令：
   - 推荐 CPU 训练命令；
   - 慢速保守命令；
   - fastcheck 命令；
   - `all` 全流程命令。
2. 以上命令统一显式增加 `--base-model backend-train-model\weights\yolov8n.pt`。
3. 补充说明：
   - 当前 `person` 首次训练建议从本地 `yolov8n.pt` 微调；
   - 不建议默认省略基模来源，也不建议直接复用 `clothes` 的 best 权重作为 person 起点。

涉及文件：
- `backend-train-model/person-train-model/train-docs/person_run_method.md`
- `backend-train-model/docs/update_log.md`

兼容性注意：
- 本轮只更新文档，不修改 `person` 训练脚本逻辑。
- 中断续训命令仍沿用 `--resume last.pt` 方式，不额外追加 `--base-model`。

## 2026-04-15 新增根 README，并同步文档体系到 unified holdout / merged baseline 当前状态

变更来源：
- 用户要求在 `backend-train-model/` 下新增一份根 `README.md`，集中说明当前训练进度、`docs/` 阅读顺序，以及当前 clothes merged baseline 与其指标。
- 用户同时要求审查 `backend-train-model/docs/` 中哪些文档不再符合当前进度，并做同步修正。

变更总览：
1. 新增 `backend-train-model/README.md`：
   - 汇总当前主线进度；
   - 固化当前 clothes fullframe baseline；
   - 给出 unified holdout 下 `first-train` / `merged strict holdout` / `route verification` 三组关键指标；
   - 明确 `docs/` 当前主线文档与历史文档的阅读顺序。
2. 重写 `backend-train-model/docs/后端训练完成进度.md`：
   - 改为当前真实进度口径；
   - 明确当前 baseline 已固定为 `clothes_merged_v2_balanced_from_first_holdout_v1`；
   - 同步 `person` 数据入口、`person` 权重缺失、`personcrop` 未开始等现状。
3. 重写 `backend-train-model/docs/Problem-Solution.md`：
   - 新增一次 `2026-04-15` 审查记录；
   - 说明历史文档与当前文档混杂导致的阅读歧义；
   - 记录本轮修正动作与当前主线结论。
4. 更新 `backend-train-model/docs/README.md`、`backend-train-model/docs/total-run-method.md`、`backend-train-model/docs/all_vs_first_train_review.md`：
   - 为当前主线入口增加说明；
   - 为统一 holdout 命令文档补充当前状态说明；
   - 将 `all_vs_first_train_review.md` 显式标记为历史报告。
5. 新增子目录说明：
   - `backend-train-model/docs/all_train_docs/README.md`
   - `backend-train-model/docs/first_train_docs/README.md`
   用于显式区分“历史阶段资料”和“当前主线文档”。

涉及文件：
- `backend-train-model/README.md`
- `backend-train-model/docs/README.md`
- `backend-train-model/docs/Problem-Solution.md`
- `backend-train-model/docs/total-run-method.md`
- `backend-train-model/docs/all_vs_first_train_review.md`
- `backend-train-model/docs/后端训练完成进度.md`
- `backend-train-model/docs/all_train_docs/README.md`
- `backend-train-model/docs/first_train_docs/README.md`
- `backend-train-model/docs/update_log.md`

兼容性注意：
- 本轮只更新文档，不修改训练代码、训练参数、模型权重路径或数据集构建逻辑。
- 当前 baseline 仍以 `backend-train-model/All-train-model/00_CURRENT_BASELINE/README.md` 指向的 run 为准。
- 历史文档不会删除，只会补充“历史说明”，避免丢失早期决策上下文。

不改动说明：
- 本轮不重新训练模型；
- 本轮不重跑 unified holdout；
- 本轮不修改 `person-train-model/` 训练逻辑与 `inspection-flask/` 代码。

## 2026-04-15 规整 `docs/all_train_docs` 为历史归档区

变更来源：
- 用户同意继续整理 `backend-train-model/docs/all_train_docs/`，希望把明显过时的旧文档规整成更清晰的归档区。

变更总览：
1. 为以下历史文档统一加上 `[归档]` 标题和“归档说明”头部：
   - `merged_dataset_plan.md`
   - `merged_v2_improvement_plan.md`
   - `run_method.md`
   - `status_and_next_steps.md`
   - `todo_list.md`
   - `unified_holdout_compare_method.md`
2. 更新 `backend-train-model/docs/all_train_docs/README.md`：
   - 增加“文件索引”表；
   - 为每份历史文档标注当前替代入口；
   - 明确本目录用于历史回溯，不直接作为当前主线执行依据。

涉及文件：
- `backend-train-model/docs/all_train_docs/README.md`
- `backend-train-model/docs/all_train_docs/merged_dataset_plan.md`
- `backend-train-model/docs/all_train_docs/merged_v2_improvement_plan.md`
- `backend-train-model/docs/all_train_docs/run_method.md`
- `backend-train-model/docs/all_train_docs/status_and_next_steps.md`
- `backend-train-model/docs/all_train_docs/todo_list.md`
- `backend-train-model/docs/all_train_docs/unified_holdout_compare_method.md`
- `backend-train-model/docs/update_log.md`

兼容性注意：
- 本轮只增加归档提示和索引，不改动这些历史文档的主体论证内容。
- 旧文档仍可用于回溯 merged 路线的历史决策，但不再建议直接照其结论执行当前训练。

不改动说明：
- 本轮不删除历史文档；
- 本轮不修改训练代码、模型权重或数据集。`r`n`r`n## 2026-04-13 补充 person CPU 训练运行文档，并更新 P1 数据资产状态

变更来源：
- 用户确认当前训练设备没有独立显卡，只使用 CPU 训练，要求为 `person` 检测整理专用运行命令。
- 用户要求删除前面微小测试生成且无用的内容，只保留本次 `person` 检测会用到的文件。
- 用户要求在 `backend-train-model/docs/todo_list.md` 中把第二阶段已经完成的部分打勾。

变更总览：
1. 新增 `backend-train-model/person-train-model/train-docs/person_run_method.md`：
   - 明确当前使用 CPU 训练，集成显卡不作为 CUDA 训练设备；
   - 给出推荐 CPU 训练命令、保守 CPU 命令、完整 `all` 流程、单独 prepare、续训、评估与导出命令；
   - 记录当前 `person` 数据集路径、类别定义、split 数量、空标注负样本数量和结果检查重点。
2. 更新 `backend-train-model/docs/todo_list.md`：
   - 将 P1 / 第二阶段中已经完成的 `person` 标签补全、标注规则确认、图片标签同名配对、跨来源命名无冲突、标签隔离、数据目录选定、数据说明 / 运行文档等条目标记为完成；
   - 将近期执行顺序中的“补 person 标签”和“建立独立 person 数据资产”标记为完成；
   - 将里程碑 B 中“有独立 person 标签”“有统一标注规则”标记为完成；
   - 保留“person 示例图片 / 示例标注”未完成状态，避免把尚未落地的独立示例文件误标为完成。
3. 清理检查：
   - 已确认本轮没有残留 `__pycache__`；
   - 未发现 `person-train-model` 下有 smoke / tmp / test 类无用测试产物；
   - 保留 `person` 训练实际会使用的 prepared 数据集、聚合标签、summary 与配置文件。

涉及文件：
- `backend-train-model/docs/todo_list.md`
- `backend-train-model/docs/update_log.md`
- `backend-train-model/person-train-model/train-docs/person_run_method.md`

新增 / 变更配置项：
- 无新增训练代码配置项。
- 新增运行文档中的推荐 CPU 参数：
  - `--device cpu`
  - `--workers 0`
  - `--batch 4`，内存压力大时改为 `--batch 2`
  - `--imgsz 640`
  - `--epochs 180`
  - `--patience 40`

兼容性注意：
- person CPU 训练命令继续使用 `backend-train-model/person-train-model/train-code/run_person_flow.py` 包装现有训练链路，不修改 `train_workwear.py` 主逻辑。
- `person_run_method.md` 中的 `export` 只生成 person 目录内的 `person_detect_yolov8.pt` alias，不会覆盖 `inspection-flask/weights/workwear_detect_yolov8.pt`。
- 集成显卡不按 CUDA 设备处理；如果后续更换独立 NVIDIA 显卡，再把 `--device cpu` 改为 `--device 0`。

不改动说明：
- 本轮不启动正式 `person` 训练。
- 本轮不删除 `person` prepared 数据集、聚合标签和统计摘要，因为它们是当前 `person` 检测训练会直接使用的产物。
- 本轮不补独立 person 示例图片 / 示例标注文件，因此 TODO 中对应条目仍保持未完成。
- 本轮不修改 `inspection-flask/`，不写入线上权重目录。

## 2026-04-15 规整 `docs/all_train_docs` 为历史归档区

变更来源：
- 用户同意继续整理 `backend-train-model/docs/all_train_docs/`，希望把明显过时的旧文档规整成更清晰的归档区。

变更总览：
1. 为以下历史文档统一加上 `[归档]` 标题和“归档说明”头部：
   - `merged_dataset_plan.md`
   - `merged_v2_improvement_plan.md`
   - `run_method.md`
   - `status_and_next_steps.md`
   - `todo_list.md`
   - `unified_holdout_compare_method.md`
2. 更新 `backend-train-model/docs/all_train_docs/README.md`：
   - 增加“文件索引”表；
   - 为每份历史文档标注当前替代入口；
   - 明确本目录用于历史回溯，不直接作为当前主线执行依据。

涉及文件：
- `backend-train-model/docs/all_train_docs/README.md`
- `backend-train-model/docs/all_train_docs/merged_dataset_plan.md`
- `backend-train-model/docs/all_train_docs/merged_v2_improvement_plan.md`
- `backend-train-model/docs/all_train_docs/run_method.md`
- `backend-train-model/docs/all_train_docs/status_and_next_steps.md`
- `backend-train-model/docs/all_train_docs/todo_list.md`
- `backend-train-model/docs/all_train_docs/unified_holdout_compare_method.md`
- `backend-train-model/docs/update_log.md`

兼容性注意：
- 本轮只增加归档提示和索引，不改动这些历史文档的主体论证内容。
- 旧文档仍可用于回溯 merged 路线的历史决策，但不再建议直接照其结论执行当前训练。

不改动说明：
- 本轮不删除历史文档；
- 本轮不修改训练代码、模型权重或数据集。`r`n`r`n## 2026-04-13 生成 baseline 误报漏报清单，并落地 person 独立训练数据入口

变更来源：
- 用户要求完成第一阶段最后一步，整理当前暂定 `clothes fullframe` baseline 的误报 / 漏报清单。
- 用户已完成 `person` 标注并选择方案 B（独立 person 数据集），要求基于 7 个图片根目录与 3 个标签根目录整理出可训练 `dataset.yaml`。
- 用户要求在不修改现有训练主逻辑的前提下，为后续 person 检测训练补齐必要脚本；如新增 Python 文件，统一放在 `backend-train-model/person-train-model/train-code/`。

变更总览：
1. 新增 `analyze_baseline_fpfn.py`，对当前 `00_CURRENT_BASELINE` 指向的权重在 `unified_holdout_v1` test split 上执行单帧 GT 对照，生成逐图 FP/FN 明细和 Markdown 摘要。
2. 将 baseline 清单产物落到 `00_CURRENT_BASELINE/`：
   - `baseline_fpfn_per_image.json`
   - `baseline_fpfn_summary.md`
3. 更新 baseline 入口文档与结构化 JSON，记录清单口径、阈值、TP/FP/FN 与输出路径。
4. 新增 `person_project_config.json`，把 person 任务的图片根目录、汇总标签根目录、类别表、切分比例和隔离产物目录收口到独立配置。
5. 新增 person 训练辅助脚本：
   - `prepare_person_dataset.py`：汇总三组 person 标签，并把 7 张缺失标签图片创建为空白负样本；
   - `run_person_flow.py`：封装现有 `train_workwear.py` 的 `audit / prepare / train / evaluate / export`，避免直接改动主训练逻辑。
6. 实际执行 person `prepare`，生成标准 YOLO 数据集：
   - `backend-train-model/person-train-model/train-result/prepared/person_fullframe/sequence_contiguous/dataset.yaml`
   - 切分结果：train `350` 张 / val `77` 张 / test `75` 张。

涉及文件：
- `backend-train-model/All-train-model/analyze_baseline_fpfn.py`
- `backend-train-model/All-train-model/00_CURRENT_BASELINE/README.md`
- `backend-train-model/All-train-model/00_CURRENT_BASELINE/current_clothes_fullframe_baseline.json`
- `backend-train-model/All-train-model/00_CURRENT_BASELINE/baseline_fpfn_per_image.json`
- `backend-train-model/All-train-model/00_CURRENT_BASELINE/baseline_fpfn_summary.md`
- `backend-train-model/person-train-model/person_project_config.json`
- `backend-train-model/person-train-model/train-code/prepare_person_dataset.py`
- `backend-train-model/person-train-model/train-code/run_person_flow.py`
- `backend-train-model/person-train-model/train-result/person_source_dataset_summary.json`
- `backend-train-model/person-train-model/train-result/prepared/person_fullframe/sequence_contiguous/`
- `backend-train-model/docs/todo_list.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 新增 person 专用项目配置 `backend-train-model/person-train-model/person_project_config.json`：
  - `data.class_names`：`{"0": "person"}`
  - `data.image_roots`：7 个 person 图片根目录；
  - `data.label_root`：`train-result/working/aggregated_labels`；
  - `data.split_ratios`：`0.7 / 0.15 / 0.15`；
  - `artifacts.root`：`train-result/artifacts`，与 `clothes/workwear` 产物隔离；
  - `person_dataset.*`：person 数据汇总、prepare 输出、导出 alias 与推荐 run 名。
- baseline FP/FN 清单脚本默认使用 `conf=0.45`、`IoU=0.5`，该阈值用于人工复盘清单，不改变既有评估报告。

兼容性注意：
- 本轮不修改 `train_workwear.py`、`dataset_tools.py`、`config.py` 的现有训练 / 评估 / 导出逻辑。
- person wrapper 默认不执行 `--deploy`，避免覆盖 `inspection-flask/weights/workwear_detect_yolov8.pt`。
- 现有 `export` 仍会生成 `workwear_detect_yolov8.pt` 原始文件名；person wrapper 只在 person 结果目录中额外复制 alias 为 `person_detect_yolov8.pt`。
- person prepare 过程中发现部分标注存在极小越界，现有 `dataset_tools.py` 已按既有逻辑自动裁剪到 `[0, 1]`，未改动源标签目录。
- 7 张无对应 person `.txt` 的图片已按用户最终口径创建空白标签并纳入训练集/验证集/测试集。
- 额外发现 `D15_20260119061405_frame_0262` 的源 `.txt` 本身为空，因此最终 prepared 数据集中空标注负样本合计为 8 个；`person_source_dataset_summary.json` 已区分 `created_empty_labels` 与 `existing_empty_source_labels`。
- person wrapper 对 `all/export` 阶段做了编排修正：`export` 不再要求先存在 `dataset.yaml`，`all` 不再在正式流水线前重复触发一次 prepare。

不改动说明：
- 本轮不启动完整 person 训练，不生成最终 `person_detect_yolov8.pt`。
- 本轮不修改 `inspection-flask/` 代码，也不写入线上权重目录。
- 本轮不把 person 标签混入现有 clothes 标签目录，不改变当前 clothes baseline 权重。
- 本轮 baseline 清单是单帧 GT 对照，不代表完整 ROI / track / temporal 链路级误报漏报复盘。

## 2026-04-12 固定当前 merged clothes fullframe 暂定 baseline，并新增醒目入口目录

变更来源：
- 用户确认当前可以先把最新 `merged` 结果暂定为 baseline，并进一步要求“明显标注出来”，最好能“拿一个文件夹醒目地放起来”。
- 本轮目标是把当前 baseline 决策固化到仓库里，避免后续继续在多个 run / report 之间来回辨认。

变更总览：
1. 在 `backend-train-model/All-train-model/` 顶层新增醒目的 `00_CURRENT_BASELINE/` 目录，专门作为当前 clothes fullframe baseline 入口。
2. 在新目录中新增：
   - `README.md`：用于面向人快速确认当前暂定 baseline、回滚候选、关键指标和下一步；
   - `current_clothes_fullframe_baseline.json`：用于结构化记录当前 baseline 的 run、权重、评估报告和指标。
3. 同步更新 `backend-train-model/All-train-model/README.md`，把旧的状态表述切换到当前统一 holdout 结论，并显式指向新的 baseline 入口目录。
4. 同步更新 `backend-train-model/docs/todo_list.md`：
   - 标记 `route verification` 已完成；
   - 标记当前 merged fullframe baseline 已暂定固定；
   - 把当前 baseline 与 rollback 候选的真实权重 / 报告路径写入文档。

涉及文件：
- `backend-train-model/All-train-model/00_CURRENT_BASELINE/README.md`
- `backend-train-model/All-train-model/00_CURRENT_BASELINE/current_clothes_fullframe_baseline.json`
- `backend-train-model/All-train-model/README.md`
- `backend-train-model/docs/todo_list.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无新的训练代码配置项。
- 本轮新增的是“baseline 固化入口”：
  - `backend-train-model/All-train-model/00_CURRENT_BASELINE/`

兼容性注意：
- 本轮**不复制** `best.pt` 到新目录中，避免生成第二份物理权重副本而导致后续误用。
- 当前暂定 baseline 仍然使用原始 run 目录中的真实权重：
  - `backend-train-model/All-train-model/artifacts/runs/clothes_merged_v2_balanced_from_first_holdout_v1/weights/best.pt`
- 当前保留的回滚候选仍然是：
  - `backend-train-model/All-train-model/artifacts/runs/clothes_merged_v2_balanced_holdout_v1/weights/best.pt`
- “暂定 baseline” 不等于最终永久结论；如果后续 `personcrop` 对照、离线链路复核或现场样本复核出现反转，应回到该目录更新结论。

不改动说明：
- 本轮不修改 `train_workwear.py`、`build_merged_clothes_dataset.py`、`config.py`、`project_config.json` 或任何训练 / 评估逻辑。
- 本轮不重新训练、不重新评估，也不重建任何数据集。
- 本轮不修改 `inspection-flask/` 在线链路代码。

## 2026-04-11 微调统一 holdout 审查文档，新增总运行手册，并实际构建三套对比数据集

变更来源：
- 用户要求对 `backend-train-model/docs/Problem-Solution.md` 做可信度与表述微调。
- 用户要求把统一 holdout 的完整训练 / 评估命令单独整理成一份 `total-run-method.md`。
- 用户同时要求直接执行构建命令，先生成三套数据集的 `dataset.yaml`，确保后续训练可以正常进行。

变更总览：
1. 微调 `backend-train-model/docs/Problem-Solution.md`：
   - 把模糊的 `datasets/` 改为明确的 `backend-train-model/All-train-model/datasets/`；
   - 把“502 行”改成“502 条样本记录，CSV 含表头为 503 行”；
   - 把“配置正确”收敛为“关键配置项已就绪，待构建验证”；
   - 把 `--report-name` 的描述改成稳定表述；
   - 构建完成后新增一条审查记录，明确 `[P0]` 已解决。
2. 新增 `backend-train-model/docs/total-run-method.md`，集中给出：
   - build 三套数据集命令；
   - cross-eval 命令；
   - strict holdout 重训命令；
   - strict eval 命令；
   - 显式训练参数与结果判断顺序。
3. 实际执行三条 `build_merged_clothes_dataset.py` 命令，成功生成：
   - `All-train-model/datasets/merged_clothes_v2_balanced/`
   - `All-train-model/datasets/unified_holdout_v1/`
   - `All-train-model/datasets/first_train_holdout_v1/`
4. 构建后校验三套目录下的 `dataset.yaml`、`manifest.csv`、`build_report.json` 均存在。

涉及文件：
- `backend-train-model/docs/Problem-Solution.md`
- `backend-train-model/docs/total-run-method.md`
- `backend-train-model/docs/update_log.md`
- `backend-train-model/All-train-model/datasets/merged_clothes_v2_balanced/dataset.yaml`
- `backend-train-model/All-train-model/datasets/merged_clothes_v2_balanced/manifest.csv`
- `backend-train-model/All-train-model/datasets/merged_clothes_v2_balanced/build_report.json`
- `backend-train-model/All-train-model/datasets/unified_holdout_v1/dataset.yaml`
- `backend-train-model/All-train-model/datasets/unified_holdout_v1/manifest.csv`
- `backend-train-model/All-train-model/datasets/unified_holdout_v1/build_report.json`
- `backend-train-model/All-train-model/datasets/first_train_holdout_v1/dataset.yaml`
- `backend-train-model/All-train-model/datasets/first_train_holdout_v1/manifest.csv`
- `backend-train-model/All-train-model/datasets/first_train_holdout_v1/build_report.json`

新增 / 变更配置项：
- 无新增代码配置项。
- 本轮新增文档入口：
  - `backend-train-model/docs/total-run-method.md`
- 本轮新增数据集工件：
  - 三套统一 holdout 对比数据集的 `dataset.yaml`
  - 三套对应的 `manifest.csv`
  - 三套对应的 `build_report.json`

兼容性注意：
- 本轮不修改 `train_workwear.py`、`build_merged_clothes_dataset.py`、`config.py` 或 `project_config.json` 的逻辑。
- `unified_holdout_v1` 只有 `test` split，用于评估，不应用作训练数据集。
- `train_workwear.py train` 若使用相同 `--name` 且 run 已存在，Ultralytics 可能自动追加后缀；最终应以 train report 中的 `actual_run_name` 和 `best_weight` 为准。

不改动说明：
- 本轮不执行 cross-eval、strict holdout 重训或 strict eval。
- 本轮不重新生成 split manifest。
- 本轮不修改 `inspection-flask/` 代码与在线链路。

## 2026-04-10 同步数据集新路径到训练配置与文档入口

变更来源：
- 用户反馈数据集目录已从旧的 `E:\University_competition\...` 迁移到新的 `D:\University-Competition\...`，并明确给出了当前 `group3_1 / group3_2 / group3_3` 的图片根目录和标注根目录。
- 用户要求不仅更新 `backend-train-model/`，还要同步修改仓库内相关文档入口，避免后续继续沿用旧路径。

变更总览：
1. 更新 `backend-train-model/config.py` 与 `backend-train-model/project_config.json` 的默认单源数据入口，使其指向新的 `D:\University-Competition\...` 下的 `group3_1` 路径。
2. 更新 `backend-train-model/All-train-model/` 下与 merged / holdout 相关的构建配置，使 `group3_1 / group3_2 / group3_3` 的图片根目录与标注根目录全部切换到新的磁盘位置。
3. 更新 `docs/dataset.md`，明确区分：
   - 默认单源训练入口；
   - `All-train-model` 多源 merged 入口；
   - 两种入口各自对应的图片 / 标注配对方式。
4. 更新 `backend-train-model/docs/README.md` 中的项目根目录示例命令，避免继续提示旧盘符。

涉及文件：
- `backend-train-model/config.py`
- `backend-train-model/project_config.json`
- `backend-train-model/All-train-model/first_train_holdout_v1.build.json`
- `backend-train-model/All-train-model/merged_clothes_v1.build.json`
- `backend-train-model/All-train-model/merged_clothes_v2.build.json`
- `backend-train-model/All-train-model/merged_clothes_v2_balanced.build.json`
- `backend-train-model/All-train-model/unified_holdout_v1.build.json`
- `backend-train-model/docs/README.md`
- `backend-train-model/docs/update_log.md`
- `docs/dataset.md`

新增 / 变更配置项：
- 无新增字段。
- 本轮仅更新已有路径配置值：
  - `config.py` 中的 `IMAGE_ROOTS`、`LABEL_ROOT`
  - `project_config.json` 中的 `data.image_roots`、`data.label_root`
  - 各 `*.build.json` 中每个 `sequence` 的 `image_root`、`label_root`

兼容性注意：
- 本轮不改变训练、评估、导出或 merged 数据集构建逻辑，只更新默认路径指向。
- `train_workwear.py` 的默认入口仍然是单源 `group3_1` 基线配置；多源 merged 训练仍通过 `All-train-model/*.build.json` 驱动。
- 如果历史运行报告、历史命令记录或旧文档仍保留 `E:\University_competition\...`，它们只代表旧环境，不会影响当前代码读取的新路径。

不改动说明：
- 本轮不修改 `inspection-flask/` 源码；排查后未发现其中存在这批数据集路径的硬编码引用。
- 本轮不调整训练超参数、split 策略、holdout 逻辑或权重加载逻辑。
- 本轮不重建任何数据集，也不启动新的训练 / 评估任务。
## 2026-04-10 ?? `All-train-model` ???????? personcrop ????????????

?????
- ??????? `All-train-model` ??????????????????????`merged_v2` ????????????
- ?????????????????????????? `personcrop` ??`person` ????? `clothes` ?????????????? `clothes` ?????

?????
1. ?? `backend-train-model/docs/all_train_docs/status_and_next_steps.md`?? `merged_v2_from_first` ????? / ?? / ??????????????
2. ?? `backend-train-model/docs/????????.md`??? `merged_v2` ????????????????????????????? `first-train`??
3. ?? `backend-train-model/All-train-model/README.md`?????????????? merged ?????????? README?
4. ??????? person ????? person ??????????????????? person / personcrop ??????????

?????
- `backend-train-model/docs/all_train_docs/status_and_next_steps.md`
- `backend-train-model/docs/????????.md`
- `backend-train-model/All-train-model/README.md`
- `backend-train-model/docs/update_log.md`

?? / ??????
- ??
- ????????????????????CLI ???????????????????????

??????
- ????? `train_workwear.py`?`dataset_tools.py`?`build_merged_clothes_dataset.py`?`config.py` ????
- ????? `first-train`?`All-train-model` ?????????????????? review ???
- ?????????`merged_v2` ?????????`merged_v2_from_first` ??????????????????????????????????

??????
- ??????????????????
- ??????? merged ????
- ????? person ???????????????????????

## 2026-04-10 新增 `merged_v2` 提升方案文档，固化当前对 merged 路线的判断与实验优先级

变更来源：
- 用户在对比 `first-train` 与 `All-train-model` 第二次训练结果后，进一步追问：面向后续接入真实摄像头的生产铺垫，应该优先分开训练还是整合训练，以及当前 `merged_v2` 为什么明显落后于 `first-train`、接下来应该怎样提升。
- 用户明确补充说明：当前 `clothes_merged_v2_from_first` 的真实历史是“先用 `first-train` 的 `best.pt` 启动训练，后因中断才做 resume”，因此新文档需要避免把当前差距错误归因到“没有用对初始化权重”。

变更总览：
1. 新增 `backend-train-model/docs/all_train_docs/merged_v2_improvement_plan.md`。
2. 在新文档中明确区分：
   - 面向生产的长期方向应更偏向 merged 主模型；
   - `first-train` 当前仍是更稳的现成基线；
   - 当前 `merged_v2` 的主要问题更像数据构造、split 设计、review 空标签引入方式与比较口径，而不是单纯参数没调好。
3. 在文档中补充记录当前 `clothes_merged_v2_from_first` 的真实训练历史：初始起跑来自 `first-train` 的 `best.pt`，后续中断后再 resume；并明确说明 resume 本身不是当前主要问题。
4. 给出后续实验推进顺序：统一 holdout → 复核 review 空标签 → 重做 balanced split → 重跑一版可追溯的 merged 训练 → 最后再做参数实验。

涉及文件：
- `backend-train-model/docs/all_train_docs/merged_v2_improvement_plan.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无。
- 本轮仅新增分析与规划文档，不修改任何训练脚本、配置文件、数据集构建逻辑或现有训练产物。

兼容性注意：
- 本轮不改变 `train_workwear.py`、`build_merged_clothes_dataset.py`、`config.py`、`project_config.json` 的行为。
- 本轮不改变 `first-train`、`All-train-model` 下任何现有 `best.pt` / `last.pt` / `eval.json` / `export` 产物。
- 本轮文档中特别修正了对 `clothes_merged_v2_from_first` 起跑方式的解释，后续阅读结论时应以“先基于 `first-train` 的 `best.pt` 启动、后续再 resume”这一真实历史为准。

不改动说明：
- 本轮不启动新的训练、评估或导出命令。
- 本轮不重建任何 merged 数据集。
- 本轮不修改 `backend-train-model/docs/all_train_docs/run_method.md`、`status_and_next_steps.md` 或 `todo_list.md` 的既有内容，仅新增一份更聚焦当前问题的决策文档。


## 2026-04-10 续训前打印自动选中的 checkpoint 与来源

变更来源：
- 用户在自动续训逻辑修复完成后，进一步要求“补充一个”更直观的控制台提示，用于在真正开始续训前确认本次命中的 checkpoint。

变更总览：
1. 修改 `backend-train-model/train_workwear.py` 的 resume 分支。
2. 在调用 `model.train(resume=True)` 之前，增加控制台输出：
   - `resume_checkpoint`
   - `resume_source`
   - `resume_report`（如有）
3. 该输出只用于帮助用户确认 bare `--resume` 实际选中了哪个 run，不改变现有续训逻辑和训练参数。

涉及文件：
- `backend-train-model/train_workwear.py`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无。
- 本轮仅增加 resume 启动前的控制台提示信息。

兼容性注意：
- 不改变自动续训候选筛选规则。
- 不改变显式 `--resume some\\weights\\last.pt` 的行为。
- 不改变非 resume 的 `train`、`evaluate`、`export`、`all` 流程。

不改动说明：
- 本轮不修改数据集构建逻辑。
- 本轮不改动评估与导出逻辑。
- 本轮不启动新的训练，也不改动任何已有权重文件内容。

## 2026-04-10 自动续训跳过已完成 run，修复 bare `--resume` 误选旧 checkpoint

变更来源：
- 用户在执行 `python train_workwear.py train --project-config All-train-model\\merged_train_project_config.json --resume` 时，自动续训命中了历史已完成的 `clothes_merged_v1_fullframe/weights/last.pt`，随后被 Ultralytics 判定为“training is finished, nothing to resume”。
- 用户要求只修复自动续训逻辑，不改动其他训练流程。

变更总览：
1. 修改 `backend-train-model/train_workwear.py` 中的自动续训候选解析逻辑。
2. 为 `last.pt` 新增“是否仍保留严格断点续训状态”的检查：
   - 仅当 checkpoint 仍保留可续训的 `epoch` 与 `optimizer` 状态时，才会被 bare `--resume` 自动选中；
   - 已训练完成、或已被精简为不可续训状态的历史 `last.pt` 会被自动跳过。
3. 对显式传入的 `--resume path\\to\\weights\\last.pt` 也增加了前置校验，避免再次落到 Ultralytics 内部后才抛出较难读的断言错误。
4. 同步更新续训文档与进度文档，明确 bare `--resume` 现在会自动跳过已完成 run。

涉及文件：
- `backend-train-model/train_workwear.py`
- `backend-train-model/docs/README.md`
- `backend-train-model/docs/all_train_docs/run_method.md`
- `backend-train-model/docs/后端训练完成进度.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无新增 CLI 参数。
- 本轮仅修正 `train --resume` 不带值时的候选 `last.pt` 筛选规则。

兼容性注意：
- 原有显式 `--resume some\\weights\\last.pt` 的使用方式保持不变，但现在会更早提示“该 checkpoint 已不可续训”。
- 非 resume 的 `train`、`evaluate`、`export`、`all` 流程保持不变。
- 自动续训仍然只支持 `last.pt`，不会改成使用 `best.pt`。

不改动说明：
- 本轮不修改数据集构建逻辑。
- 本轮不改动评估与导出逻辑。
- 本轮不启动新的训练，也不改动任何已有权重文件内容。

## 2026-04-10 run_method 补充断点续训命令的直接可复制写法

变更来源：
- 用户要求把当前可用的断点续训命令明确补到 `backend-train-model/docs/all_train_docs/run_method.md` 中，方便后续直接复制执行。
- 现有文档虽然已经包含一条显式 `last.pt` 续训命令，但用户当前需求更偏向“直接看到就能用”的操作指引，因此需要进一步整理为自动续训与显式续训两种写法。

变更总览：
1. 修改 `backend-train-model/docs/all_train_docs/run_method.md` 的“如果训练中断，严格断点续训”小节。
2. 将续训命令明确拆分为两种：
   - 自动续训最近一次中断训练；
   - 显式续训当前推荐 run 的 `last.pt`。
3. 同步调整补充说明的表述，使“自动续训”和“显式指定 `last.pt`”的使用场景更清晰。

涉及文件：
- `backend-train-model/docs/all_train_docs/run_method.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无。
- 本轮仅补充文档中的命令展示方式，不修改训练脚本和 CLI 参数定义。

兼容性注意：
- 本轮不改变 `train --resume` 的实际行为。
- 本轮不改变 `All-train-model` 当前推荐训练主线，只增强文档可操作性。

不改动说明：
- 本轮不修改 `backend-train-model/train_workwear.py`。
- 本轮不启动新的训练、评估或导出命令。
- 本轮不修改任何已有训练产物。

## 2026-04-09 训练脚本新增严格断点续训 `train --resume`

变更来源：
- 用户在训练跑到中途后，明确要求支持“严格断点续训”，并强调不能改变现有其他训练逻辑。
- 当前脚本只有“基于 `.pt` 继续微调”的能力，还没有显式暴露原生 resume 入口，因此需要在保持原有非续训路径不变的前提下，补齐 `train --resume`。

变更总览：
1. 修改 `backend-train-model/train_workwear.py`，为 `train` 子命令新增 `--resume` 参数。
2. 新增严格断点续训路径解析逻辑：
   - `--resume` 不带值时，自动优先从最近训练报告中的 `last_weight` 恢复；
   - 如果报告不可用，再回退扫描最近的 `weights/last.pt`；
   - 也支持显式传入某个 `last.pt`。
3. 在训练入口中新增严格 resume 分支，调用 Ultralytics 原生 `model.train(resume=True)`，从而继续沿用 checkpoint 内保存的训练状态，而不是重新开启一轮新的微调。
4. 新增 resume 模式下的参数冲突校验，避免与 `--base-model`、`--from-scratch`、`--init-weights`、`--name`、`--project`、`--dataset-yaml`、`--epochs` 等训练起点参数混用，确保“严格断点续训”的语义不被破坏。
5. 更新 `backend-train-model/docs/README.md`、`backend-train-model/docs/all_train_docs/run_method.md` 与 `backend-train-model/docs/后端训练完成进度.md`，补充新的 resume 用法与当前能力状态。

涉及文件：
- `backend-train-model/train_workwear.py`
- `backend-train-model/docs/README.md`
- `backend-train-model/docs/all_train_docs/run_method.md`
- `backend-train-model/docs/后端训练完成进度.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 新增训练参数：`train --resume [last.pt]`
- 本轮不修改默认 `epochs`、`batch`、`imgsz`、`patience`、`device` 等训练默认值。

兼容性注意：
- 原有 `train`、`evaluate`、`export`、`all` 的非 resume 路径保持不变。
- 严格断点续训只支持 `last.pt`，不支持把 `best.pt` 当作 resume checkpoint 使用。
- `train --resume` 当前仅挂载在 `train` 子命令，不扩展到 `all`，避免改变现有一键全流程命令的既有语义。

不改动说明：
- 本轮不修改数据集构建逻辑。
- 本轮不改动评估与导出逻辑。
- 本轮不改变 `first-train`、`All-train-model` 下任何已有训练产物。

## 2026-04-09 新增后端训练完成进度文档，固化当前训练阶段完成度口径

变更来源：
- 用户要求在 `backend-train-model/docs/` 下新增一份名为 `后端训练完成进度.md` 的进度文档，用于持续记录后端训练“已经完成什么、还需要做什么、下一步做什么”。
- 用户明确说明后续每次完成部分内容后，都需要继续迭代这份进度文档，因此需要先把当前真实训练状态固化为可持续维护的基线版本。

变更总览：
1. 新增 `backend-train-model/docs/后端训练完成进度.md`。
2. 在新文档中按 `P0 ~ P5` 阶段整理当前后端训练完成度，并明确区分：
   - 已形成真实训练 / 评估 / 导出产物的部分；
   - 仅完成数据集构建、但尚未形成新模型产物的部分；
   - 仍未开始或前置条件不足的部分。
3. 在新文档中固化当前阶段的关键结论：
   - `first-train` 的 `clothes` `best.pt` 仍是当前更稳的基线；
   - `All-train-model` 已完成 `merged_v1` 一轮闭环；
   - `merged_v2_full_reviewed` 已吸收 `48` 张负样本，但尚未产生对应训练 / 评估 / 导出结果；
   - `person`、`personcrop`、链路级离线复盘与实时摄像头阶段尚未闭环。
4. 在新文档中加入后续维护要求，约束每次训练进度推进后都要同步更新该进度文档。

涉及文件：
- `backend-train-model/docs/后端训练完成进度.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无。
- 本轮只新增进度文档与更新日志，不修改任何训练脚本、配置文件、默认参数或数据集内容。

兼容性注意：
- 本轮新增的是“状态汇总文档”，不改变 `train_workwear.py`、`config.py`、`project_config.json`、`All-train-model/` 或 `first-train/` 下任何现有训练产物的行为。
- 文档中的完成度判断以当前仓库中已存在的真实产物为准；若后续新增了新的权重、评估报告或误报 / 漏报清单，需要同步迭代本文档，避免文档状态落后于真实项目进展。

不改动说明：
- 本轮不启动新的训练、评估或导出命令。
- 本轮不重建任何数据集。
- 本轮不修改 `backend-train-model/weights/` 下的模型文件。

## 2026-04-06 all_train_docs 新增 run_method，明确 merged_v2 当前推荐训练方式

变更来源：
- 用户在 `merged_v2_full_reviewed` 已构建完成后，进一步追问“训练命令是不是和原来一样”，并指出此前已经明确过“更推荐使用 `first-train` 的 `best.pt` 作为初始化权重”。
- 用户要求在 `backend-train-model/docs/all_train_docs/` 下新增一份新的 `run_method.md`，把当前 `All-train-model` 的实际运行方式重新梳理清楚。

变更总览：
1. 新增 `backend-train-model/docs/all_train_docs/run_method.md`。
2. 在新文档中明确区分了两层含义：
   - “训练命令框架没有变，仍然是 `train_workwear.py train/evaluate/export`”
   - “当前更推荐的正式训练方案，是在 `merged_clothes_v2_full_reviewed` 上显式传入 `first-train` 的 `best.pt` 作为 `--base-model`”
3. 在文档中补充了两套命令：
   - 方案 A：不显式传 `--base-model`，直接基于默认本地 `yolov8n.pt` 训练 `merged_v2`
   - 方案 B：显式用 `first-train/artifacts/runs/clothes_fullframe_baseline/weights/best.pt` 初始化后继续训练 `merged_v2`
4. 在文档中补充了每条命令的作用、关键参数含义、推荐 run 名称、预期输出位置、当前不推荐的做法和最短执行清单。

涉及文件：
- `backend-train-model/docs/all_train_docs/run_method.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无。
- 本轮不修改 `train_workwear.py`、`config.py`、`merged_train_project_config.json` 或任何训练默认参数，仅补充当前推荐运行方式的说明文档。

兼容性注意：
- 本轮只是把“默认可运行方案”和“当前更推荐方案”区分写清楚，不改变脚本现有行为。
- 不传 `--base-model` 的旧命令依然可以运行；新增文档只是明确：如果要做当前阶段更正式的 merged 训练，优先建议显式传 `first-train` 的 `best.pt`。

不改动说明：
- 本轮不重建数据集。
- 本轮不启动新的训练、评估或导出命令。
- 本轮不修改 `backend-train-model/All-train-model/` 下已有训练产物。

## 2026-04-06 merged_v2_full_reviewed 负样本空白标签补齐

变更来源：
- 用户已人工确认 `backend-train-model/All-train-model/review/merged_clothes_v1_positive_only/missing_review.csv` 中列出的 `48` 张缺失源标注图片均不存在需要保留的 `clothes` 目标。
- 用户要求先检查已复制到 `backend-train-model/All-train-model/review/merged_clothes_v2_full_reviewed/images/` 的图片是否与 `missing_review.csv` 对齐，再批量创建对应的空白 review 标签文件。

变更总览：
1. 校验 `backend-train-model/All-train-model/review/merged_clothes_v2_full_reviewed/images/` 中的图片文件名与 `missing_review.csv` 的 `merged_stem` 一一对应。
2. 校验结果为：`expected_count=48`、`actual_count=48`、`missing_count=0`、`extra_count=0`，说明这批 review 图片已全部放对。
3. 在 `backend-train-model/All-train-model/review/merged_clothes_v2_full_reviewed/labels/` 下批量创建 `48` 个同名空白 `.txt` 文件，作为明确的负样本 review 标签。
4. 创建完成后再次核对，`labels/` 中的 `.txt` 文件与 `missing_review.csv` 完全对齐，可直接用于后续 `merged_v2_full_reviewed` 构建。

涉及文件：
- `backend-train-model/All-train-model/review/merged_clothes_v2_full_reviewed/images/`（已由用户预先放入 `48` 张 review 图片，本轮仅完成一致性校验）
- `backend-train-model/All-train-model/review/merged_clothes_v2_full_reviewed/labels/*.txt`（新增 `48` 个空白负样本标签文件）
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无。
- 本轮不修改 `merged_clothes_v2.build.json`、训练参数、数据切分策略或任何训练代码逻辑。

兼容性注意：
- 这些空白 `.txt` 文件会被 `build_merged_clothes_dataset.py` 识别为 `resolved_negative`，并作为“确认无 `clothes` 目标”的负样本纳入 `merged_v2_full_reviewed`。
- 空白标签文件名必须继续保持与 `missing_review.csv` 中的 `merged_stem` 完全一致；若后续人工复核发现某张图其实存在 `clothes`，只需把对应空白文件改写为正常 YOLO 标注即可。

不改动说明：
- 本轮不回写原始 `label_clothes` / `labels` 目录。
- 本轮不修改 `backend-train-model/All-train-model/review/merged_clothes_v2_full_reviewed/images/` 中的图片内容，仅做文件名和数量校验。
- 本轮不启动 `merged_v2` 重建、训练、评估或导出命令。

## 2026-04-06 All-train-model 精度提升 TODO 清单补充到 all_train_docs

变更来源：
- 用户基于 `backend-train-model/docs/all_vs_first_train_review_2026-04-06.md` 的比较结论，要求把“`All-train-model` 还能做哪些改进来提升准确性”整理成一份新的 `todo_list.md`。
- 目标明确：把前面口头给出的优化方向落成可执行清单，并放入 `backend-train-model/docs/all_train_docs/`。

变更总览：
1. 新增 `backend-train-model/docs/all_train_docs/todo_list.md`。
2. 在新文档中把 `All-train-model` 当前最值得做的精度提升动作拆成分阶段 TODO，重点包括：
   - 先补齐缺标，构建 `merged_v2_full_reviewed`
   - 重做更合理的 balanced split
   - 使用 `first-train` 的 `best.pt` 作为 merged 训练初始化权重
   - 最后再考虑模型规模、输入尺寸和 patience 等训练策略增强
3. 在新文档中补充了每一阶段的：
   - 目标
   - TODO 清单
   - 推荐命令
   - 完成标准
   - 预期收益

涉及文件：
- `backend-train-model/docs/all_train_docs/todo_list.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无。
- 本轮只新增执行清单文档，不修改 `build_merged_clothes_dataset.py`、`train_workwear.py`、`config.py` 或任何训练默认参数。

兼容性注意：
- 新文档基于当前仓库内已经存在的 `All-train-model`、`first-train` 产物与评审结论整理，不改变现有命令行为。
- 文档中提到的 `merged_v2_balanced`、`merged_v2_from_first` 属于下一步建议路线，当前仓库尚未自动具备这些新 build config 或训练产物。

不改动说明：
- 本轮不修改 `backend-train-model/All-train-model/` 下现有数据集内容与训练产物。
- 本轮不修改 `inspection-flask/` 下任何代码。
- 本轮不重写已有评审文档，只在其结论基础上新增可执行 TODO。

## 2026-04-06 merged dataset.yaml 路径修复，解决 All-train-model 训练找不到 images 目录

变更来源：
- 用户在 `backend-train-model/` 目录下按文档执行 merged 训练命令时，Ultralytics 报错找不到 `images/val`。
- 需要区分是命令问题、工作目录问题，还是 `dataset.yaml` 本身写法存在兼容性缺陷。

变更总览：
1. 修复 `backend-train-model/build_merged_clothes_dataset.py` 生成 `dataset.yaml` 时的 `path` 字段写法。
2. 将 merged builder 生成的 `path: .` 改为数据集根目录的绝对路径，避免 Ultralytics 把 `images/train|val|test` 错误解析到当前工作目录下。
3. 同步修正现有 `backend-train-model/All-train-model/datasets/merged_clothes_v1_positive_only/dataset.yaml`，让当前这份 `merged_v1` 数据集无需重建即可继续训练。

涉及文件：
- `backend-train-model/build_merged_clothes_dataset.py`
- `backend-train-model/All-train-model/datasets/merged_clothes_v1_positive_only/dataset.yaml`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无。
- 本轮只修复 merged `dataset.yaml` 的 `path` 输出内容，不修改训练参数、项目配置或 CLI 参数定义。

兼容性注意：
- `backend-train-model/dataset_tools.py` 原有 `prepare` 流程生成的 `dataset.yaml` 本来就写的是绝对路径，本轮问题只存在于 merged 数据构建脚本。
- 修复后，新生成的 merged `dataset.yaml` 会显式指向真实数据集根目录，不再依赖运行命令时的当前工作目录。
- 现有 `merged_v1_positive_only` 已直接修正，可继续使用，无需因为这个问题重新构建整个 merged 数据集。

不改动说明：
- 本轮不修改 `backend-train-model/train_workwear.py`。
- 本轮不修改 `inspection-flask/` 下任何代码。
- 本轮不改动 merged 数据集的图片、标签、split 结果，仅修复 `dataset.yaml` 的路径解析问题。

## 2026-04-06 All-train-model README 路径修正与现状说明文档补充

变更来源：
- 用户要求“直接补好”当前 `backend-train-model/All-train-model` 的使用说明。
- 用户进一步要求新增一份文档，明确当前已经完成哪些步骤、接下来该做什么、需要哪些命令，以及每个参数的意义。

变更总览：
1. 修正 `backend-train-model/All-train-model/README.md` 中 merged 训练流程的推荐命令写法与文档跳转说明。
2. 在 README 中补充关键注意事项：
   - 推荐先切到 `backend-train-model/` 目录再执行命令
   - 不建议对 merged 流程使用 `train_workwear.py all`
   - `build_report.json` 中保存了可直接复制的绝对路径命令
   - 当前 `merged_v1` 已构建完成，但 `artifacts/` 尚不存在，因此训练 / 评估 / 导出尚未执行
3. 新增 `backend-train-model/All-train-model/status_and_next_steps.md`，系统说明：
   - 当前 `All-train-model` 已完成的步骤
   - merged 流程与原始 `audit / prepare` 的关系
   - 当前最稳妥的执行顺序
   - 每条关键命令的作用与参数意义
   - `merged_v2` 的后续补标与重建方式
   - `evaluate --inspection-validate` 与 `export --deploy` 这类后续扩展参数的使用时机

涉及文件：
- `backend-train-model/All-train-model/README.md`
- `backend-train-model/All-train-model/status_and_next_steps.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无。
- 本轮只修正文档与命令说明，不修改 `config.py`、`train_workwear.py`、`build_merged_clothes_dataset.py` 的实际行为。

兼容性注意：
- 本轮不改变任何 CLI 参数定义和默认值。
- 本轮主要修正“如何安全传入 `--project-config`”的文档描述，避免用户在仓库根目录直接执行时踩到相对路径解析问题。
- 本轮明确标注：merged 数据集训练不建议使用 `train_workwear.py all`，而应走 `train -> evaluate -> export` 的分步方式。

不改动说明：
- 本轮不修改 `backend-train-model/config.py`、`backend-train-model/train_workwear.py`、`backend-train-model/build_merged_clothes_dataset.py`。
- 本轮不修改 merged 数据集内容，不重新构建 `merged_v1` 或 `merged_v2`。
- 本轮不修改 `inspection-flask/` 下任何代码。

## 2026-04-06 backend-train-model merged 数据构建脚本与 All-train-model 训练目录落地

变更来源：
- 用户要求把前面已经确认的“三套 clothes 数据合并训练方案”真正落地为可执行脚本。
- 用户新增约束：新脚本放在 `backend-train-model/` 根目录下，且这次 merged 训练的产物尽量统一落到 `backend-train-model/All-train-model/` 下。

变更总览：
1. 新增 `backend-train-model/build_merged_clothes_dataset.py`，用于把三套 `clothes` 数据按预设 split 构建为标准 YOLO 数据集。
2. 新增 `backend-train-model/All-train-model/` 下的运行模板文件：
   - `README.md`
   - `merged_train_project_config.json`
   - `merged_clothes_v1.build.json`
   - `merged_clothes_v2.build.json`
   - `.gitignore`
3. 为运行时项目配置新增 `artifacts.root` 配置入口，使 `train_workwear.py` 的默认 `prepared / runs / reports / export` 根目录可以整体切到 `All-train-model/artifacts/`。
4. merged 构建脚本当前固定服务于单类 `clothes` 总数据集建设，支持：
   - `merged_v1_positive_only`：只纳入当前已有同名标注的样本
   - `merged_v2_full_reviewed`：对缺标样本从 review 目录读取补标结果后再构建
5. merged 构建脚本会输出：
   - `dataset.yaml`
   - `manifest.csv`
   - `build_report.json`
   - `missing_review.csv`

涉及文件：
- `backend-train-model/config.py`
- `backend-train-model/build_merged_clothes_dataset.py`
- `backend-train-model/All-train-model/.gitignore`
- `backend-train-model/All-train-model/README.md`
- `backend-train-model/All-train-model/merged_train_project_config.json`
- `backend-train-model/All-train-model/merged_clothes_v1.build.json`
- `backend-train-model/All-train-model/merged_clothes_v2.build.json`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- `artifacts.root`
  - 放在项目化 JSON 配置文件里
  - 用于整体覆盖默认产物根目录
  - 派生影响：
    - `prepared_root`
    - `runs_root`
    - `reports_root`
    - `export_root`
- `backend-train-model/All-train-model/merged_train_project_config.json`
  - 当前把运行产物统一切到 `backend-train-model/All-train-model/artifacts/`

兼容性注意：
- 旧的 `backend-train-model/project_config.json` 不受影响；如果不传新的 project config，现有默认产物目录仍然是 `backend-train-model/artifacts/`。
- 新增的 merged 构建脚本不会自动并入 `train_workwear.py` 主 CLI，仍然保持“先构建数据集，再用 `--dataset-yaml` 训练”的方式，避免直接改乱现有训练主流程。
- `All-train-model/.gitignore` 默认忽略 `datasets/`、`review/`、`artifacts/` 下的运行期产物，避免把大体量训练数据与模型产物误纳入版本控制。

不改动说明：
- 本轮不修改 `backend-train-model/train_workwear.py` 的训练、评估、导出主流程。
- 本轮不修改 `backend-train-model/dataset_tools.py` 的既有 `audit/prepare` 逻辑。
- 本轮不修改 `inspection-flask/` 下任何代码。
- 本轮仍然维持当前默认单类 `clothes` 训练口径，不把 `person`、`auto`、`personcrop` 强行并入 merged 基线阶段。

## 2026-04-06 backend-train-model 三套数据合并方案文档新增

变更来源：
- 用户要求：把“三套数据合并成一个总数据集的稳妥方案”整理成正式文档，并放到 `backend-train-model/docs/` 下。
- 范围明确：本轮采用“写文档”的方式落地，同时要求文档中包含前面口头方案里的目录规范和 `manifest` 设计。

变更总览：
1. 新增 `backend-train-model/docs/merged_dataset_plan.md`，系统说明三套 `clothes` 数据合并成总数据集的推荐路线。
2. 在新文档中明确说明：
   - 为什么不推荐直接采用 A -> B -> C 串行继续训练作为正式主路线
   - 为什么更推荐“先合并数据，再统一训练总模型”
3. 在新文档中补充了方案一的具体内容：
   - merged 数据集目录规范
   - `canonical / manifest / prepared` 三层结构职责
   - `samples.csv / source_stats.json / class_mapping.json / split_summary.json` 的设计建议
4. 在新文档中补充了合并前必须完成的数据清洗、按序列切分策略、以及 `merged_v1_all` 与 `merged_v1_balanced` 双版本方案。
5. 在新文档中给出了基于 merged 数据集的训练建议，明确当前阶段更推荐用 `--dataset-yaml` 直接训练，而不是先修改主训练代码。

涉及文件：
- `backend-train-model/docs/merged_dataset_plan.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无。
- 本轮只新增合并方案文档，不修改 `project_config.json`、`config.py`、训练 CLI 和默认参数。

兼容性注意：
- 本轮属于纯文档增量，不影响现有训练命令行为。
- 新文档描述的是当前推荐的 merged 数据建设方案，不代表仓库已经自动具备“三套数据自动合并脚本”；如果后续决定把合并流程工具化，仍需再单独补代码。

不改动说明：
- 本轮不修改 `backend-train-model/config.py`、`backend-train-model/dataset_tools.py`、`backend-train-model/train_workwear.py`。
- 本轮不修改 `inspection-flask/` 下任何代码。
- 本轮不改变当前默认单类 `clothes` 训练口径，也不把 merged 流程直接并入现有主训练流程。

## 2026-04-05 backend-train-model 运行方法文档新增

变更来源：
- 用户要求：新增一份更详细的运行说明文档，文件名指定为 `run_mathod.md`，要求把当前最稳妥的运行方式、自定义数据集方式、未来阶段扩展方式，以及命令和参数意义系统展开说明。
- 场景收敛：用户当前准备先把 `clothes` 模型训练好，因此文档需要明确区分“现阶段最稳妥方案”和“未来扩展方案”。

变更总览：
1. 新增 `backend-train-model/docs/run_mathod.md`，系统整理当前阶段的推荐运行方式。
2. 在新文档中明确：
   - 为什么 baseline 阶段更推荐显式使用 `--mode fullframe`
   - 为什么当前不建议一上来直接用 `all --deploy`
   - 当前最推荐的 `audit -> prepare -> train -> evaluate -> export` 顺序
3. 在新文档中补充了命令级说明：
   - 每条推荐命令的作用
   - 常用参数的意义
   - 现阶段哪些参数建议先不要乱改
4. 在新文档中补充了“如何自己指定数据集”的两种方式：
   - 直接使用 `--dataset-yaml`
   - 使用 `--project-config` 切换原始数据入口，再显式指定 prepare 产出的 `dataset.yaml`
5. 在新文档中补充了未来阶段的命令变化，包括：
   - 何时引入 `personcrop`
   - 何时使用 `auto`
   - 何时做 `inspection-flask` 链路级复核

涉及文件：
- `backend-train-model/docs/run_mathod.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无。
- 本轮只新增运行说明文档，不改动配置入口、CLI 参数定义和训练逻辑。

兼容性注意：
- 本轮属于纯文档增量，不影响现有 `backend-train-model` 的任何命令行为。
- 新文档中的“当前最稳妥方式”是基于当前项目状态给出的推荐执行路径，不代表代码自动强制改成该默认行为；例如文档推荐 baseline 阶段显式写 `--mode fullframe`，这是为了稳妥起见，而不是 CLI 默认值被修改。

不改动说明：
- 本轮不修改 `backend-train-model/config.py`、`backend-train-model/dataset_tools.py`、`backend-train-model/train_workwear.py`。
- 本轮不修改 `inspection-flask/` 下任何代码。
- 本轮不改变当前默认单类 `clothes` 训练口径，也不改变 `auto` 的现有判定逻辑。

## 2026-04-05 backend-train-model 可执行 TODO 清单文档新增

变更来源：
- 用户要求：在已有分阶段路线文档基础上，再补一份更“可执行”的清单文档，文件名明确指定为 `todo_list.md`。
- 目标收敛：把“分几个阶段、训几个模型、怎样搭链路”的高层建议，进一步落成按阶段推进的待办项、产物和完成标准。

变更总览：
1. 新增 `backend-train-model/docs/todo_list.md`，把当前推荐路线拆解成可执行的阶段性 TODO。
2. 在新文档中把任务分为：
   - `P0`：先固定 `clothes` baseline
   - `P1`：补 `person` 数据资产
   - `P2`：训练并固化 `person` 模型
   - `P3`：启用 `personcrop` 重训 `clothes`
   - `P4`：离线搭建完整链路
   - `P5`：接实时摄像头上线
3. 在新文档中补充了每一阶段的：
   - 目标
   - 待办项
   - 推荐命令
   - 产物
   - 完成标准
4. 在新文档中单独列出“哪些事情现在不要做”和“近期最推荐执行顺序”，便于后续直接按 checklist 推进。

涉及文件：
- `backend-train-model/docs/todo_list.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无。
- 本轮只新增执行清单文档，不修改任何配置入口、CLI 默认值和训练逻辑。

兼容性注意：
- 本轮属于纯文档增量，不改变现有 `backend-train-model` 的代码行为。
- `todo_list.md` 中的命令和阶段建议是当前推荐执行顺序，不代表仓库已经自动具备全部后续阶段能力；例如 `person` 训练任务仍需后续按阶段补齐数据资产与脚本。

不改动说明：
- 本轮不修改 `backend-train-model/config.py`、`backend-train-model/dataset_tools.py`、`backend-train-model/train_workwear.py`。
- 本轮不修改 `inspection-flask/` 下任何代码。
- 本轮不改变当前默认单类 `clothes` 训练口径。

## 2026-04-05 backend-train-model 分阶段链路规划文档新增

变更来源：
- 用户要求：允许调整既有后端训练思路，并在 `backend-train-model/docs/` 下补一份更明确的阶段规划文档，回答“该分几阶段、该训几个模型、如何搭完整链路”。
- 现状澄清：当前仓库文档和代码不是不可变真理，需要结合当前数据、当前业务目标和现有工程边界，给出更稳妥的推荐路线。

变更总览：
1. 新增 `backend-train-model/docs/pipeline_roadmap.md`，明确说明当前项目不建议一开始追求“一个模型吃掉整条业务链路”。
2. 在新文档中分开说明：
   - 真实生产目标
   - 当前阶段实现
   - 当前能力边界
   - 升级触发条件
   - 后续演进路线
3. 在新文档中给出推荐的阶段划分：
   - 阶段 0：数据资产分层
   - 阶段 1：先训 `clothes` baseline
   - 阶段 2：补 `person` 数据并训练 `person` 模型
   - 阶段 3：在 `personcrop` 方案上重训 `clothes`
   - 阶段 4：离线搭建完整链路
   - 阶段 5：接实时摄像头上线
4. 在新文档中明确说明：补 `person` 标签是有价值的，但 `auto` 模式真正依赖的是“是否已有可用 `person` 权重”，不是“标注里是否存在 `person` 类别”。

涉及文件：
- `backend-train-model/docs/pipeline_roadmap.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无。
- 本轮只新增方案文档，不修改 `project_config.json`、`config.py`、CLI 默认值和导出结构。

兼容性注意：
- 本轮不改动任何训练逻辑、评估逻辑、导出逻辑和配置入口；属于纯文档增量，不影响现有命令行为。
- 新文档中的推荐路线是“当前更优实践建议”，不是对现有代码行为的自动变更；若后续要按该路线推进，仍需要在未来分阶段落代码与数据资产。

不改动说明：
- 本轮不修改 `backend-train-model/config.py`、`backend-train-model/dataset_tools.py`、`backend-train-model/train_workwear.py`。
- 本轮不修改 `inspection-flask/` 下任何代码。
- 本轮不把当前默认单类 `clothes` 训练任务直接改成多类混标任务。

## 2026-04-05 backend-train-model 项目化配置、personcrop 对齐与训练报告增强

变更来源：
- 用户批准：只修改 `backend-train-model`，先聚焦后端模型训练链路，不修改 `inspection-flask`
- 方案参考：`docs/workwear_detection_final_solution.md` 明确当前阶段应贴合“person -> 候选目标 -> 工服检测 -> 时序确认”的业务链路
- 新增约束：用户要求在 `backend-train-model/docs/` 下建立独立 `update_log.md`，并确保以后每次修改后端训练代码都同步更新该日志

变更总览：
1. 重构 `backend-train-model/config.py`，引入项目化 JSON 配置加载机制，默认支持读取 `backend-train-model/project_config.json`，不再要求后续继续改代码硬编码数据入口与默认参数。
2. 新增 `backend-train-model/project_config.json`，把当前数据路径、类别定义、prepare 默认值、person 模型候选与训练默认参数外置。
3. 调整默认 person 模型候选来源：优先尝试 `backend-train-model/weights/person_detect_yolov8.pt`，其次尝试 `inspection-flask/weights/person_detect_yolov8.pt`，让 `auto` 模式更容易按项目链路落到 `personcrop`。
4. 增强 `backend-train-model/dataset_tools.py`：`prepare_report.json` 现在额外输出 `split_box_counts`，并且 `dataset.yaml` 的 `names` 由 `config.CLASS_NAMES` 动态生成，不再写死 `0: clothes`。
5. 增强 `backend-train-model/train_workwear.py`：增加项目配置启动引导、运行时配置快照、prepare 请求摘要、数据集元信息、导出元数据文件，并让训练时的 `single_cls` 根据 `dataset.yaml` 中的类别数自动决定。
6. 新增 `backend-train-model/AGENTS.md`，明确 future agent 在修改后端训练目录时必须同步更新本日志。

涉及文件：
- `backend-train-model/config.py`
- `backend-train-model/dataset_tools.py`
- `backend-train-model/train_workwear.py`
- `backend-train-model/project_config.json`
- `backend-train-model/AGENTS.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 新增 `backend-train-model/project_config.json`
  - `data.image_roots`：原始图片序列目录列表
  - `data.label_root`：统一标签目录
  - `data.class_names`：类别映射
  - `data.split_ratios` / `data.default_split_strategy`：数据切分默认值
  - `prepare.default_mode` / `prepare.person_conf` / `prepare.person_imgsz` / `prepare.assignment_min_ioa`：prepare 默认参数
  - `models.person_model_candidates`：默认 person 模型候选路径
  - `models.python_candidates`：跨项目调用 `inspection-flask` 时的 Python 解释器候选
  - `training.default_train_args`：默认训练参数
- `config.py` 新增运行时接口：
  - `apply_project_config(...)`
  - `reset_runtime_config()`
  - `get_runtime_config_snapshot()`
  - `resolve_class_id_by_name(...)`

兼容性注意：
- CLI 现在会在真正解析完整参数前先尝试加载项目配置；如果 `backend-train-model/project_config.json` 存在，则其值会成为新的 CLI 默认值来源。
- `train` 的 `single_cls` 不再无条件写死为 `True`，而是依据 `dataset.yaml` 中的类别数自动决定；这对未来扩展多类训练更安全。
- `prepare_report.json` 现在新增 `split_box_counts` 字段；旧读取方如果只关心原字段，不受影响。
- `export` 命令现在会在导出目录额外生成 `workwear_detect_yolov8.metadata.json`，属于新增工件，不影响旧 `.pt` 权重路径。
- `inspection-flask` 复核仍然按单类 `clothes-only` 口径运行，但 `clothes` 类别 ID 改为从后端配置动态解析，不再在训练侧写死为 `0`。

不改动说明：
- 本轮不修改 `inspection-flask/` 下任何代码；其只作为当前在线链路与权重命名约束的参考来源。
- 本轮不修改仓库根 `docs/` 下已有方案或日志文档；后端训练目录改动只在自身范围内落日志。
- 本轮不引入新的训练任务类型，仍以当前单类 `clothes` 工服检测为默认目标。

## 维护约束

以后每次更新 `backend-train-model/` 下的代码、配置或文档，都必须遵守以下规则：

1. **新记录放在最上方**：新增日志必须插入到旧记录上方，保持“最新在前，历史在后”。
2. **必须写明变更来源**：每条更新记录都要说明本次修改是由用户需求、方案调整、误报/漏报分析还是训练链路问题触发。
3. **必须列出涉及文件**：所有新增或修改的 `backend-train-model/` 文件都要逐项列出。
4. **必须列出新增 / 变更配置项**：凡是改动 `project_config.json`、`config.py` 默认值、CLI 默认参数、导出元数据结构，都要单独说明。
5. **必须标注兼容性影响**：如果改动影响 CLI 参数默认值、报告字段、导出文件名、权重寻找规则或日志结构，必须写“兼容性注意”。
6. **禁止删除历史记录**：历史日志只能追加，不能删除或重写旧日期条目。
7. **必须声明本轮不改动部分**：如果某些模块经过评估后故意不改，要写清原因，避免后续重复评估。
8. **代码改动必须同步日志**：只要修改了 `backend-train-model/` 下的代码或配置，就必须在同一轮提交中同步更新本文件。
9. **优先改配置入口，不要回退到硬编码**：新增路径、默认阈值、候选模型路径时，优先落到 `project_config.json` 或 `config.py` 的统一入口。
10. **训练报告要可追溯**：涉及 `prepare`、`train`、`evaluate`、`export` 输出结构改动时，要在日志里说明新增字段或新增文件的用途。
## 2026-04-10 落地 unified holdout / source-balanced split，并补齐评估报告追溯能力

变更来源：
- 用户要求根据 `backend-train-model/docs/all_train_docs/merged_v2_improvement_plan.md` 直接落地代码改造，优先解决两件事：
  1. 短期内怎样提升 `merged_v2` 的训练效果；
  2. 怎样让 `first-train` 与 `All-train-model` 在统一 holdout 下做同口径比较。

变更总览：
1. 扩展 `backend-train-model/build_merged_clothes_dataset.py`，新增样本级 split manifest 能力：
   - 支持 `split_manifest_csv`
   - 支持 `strict_split_manifest`
   - 支持样本级 `split=train / val / test / skip`
   - 输出 manifest 时同步记录 `assignment_source`、`assignment_note`、`holdout_group`、`sample_role`
   - 在 `build_report.json` 中补充 split/source/role 分布统计
2. 新增 `backend-train-model/generate_split_manifests.py`，可从 canonical `manifest.csv` 生成：
   - `trainval_balanced_v1.split.csv`
   - `unified_holdout_v1.split.csv`
   - `source_balanced_v1_summary.json`
3. 新增 unified holdout / balanced merged / first baseline 的构建配置：
   - `backend-train-model/All-train-model/merged_clothes_v2_balanced.build.json`
   - `backend-train-model/All-train-model/unified_holdout_v1.build.json`
   - `backend-train-model/All-train-model/first_train_holdout_v1.build.json`
4. 扩展 `backend-train-model/train_workwear.py`：
   - `evaluate` 新增 `--report-name`
   - 评估报告新增 `comparison_dataset_name`、`report_name`、`report_path`
   - train report 新增 `initial_base_model` / `initial_base_model_source`
   - `resume` 时继承首次启动信息与 `training_lineage`，避免只剩下 `last.pt` 断点信息
5. 新增统一 holdout 使用文档，并在 `All-train-model/README.md` 中补充新入口。

涉及文件：
- `backend-train-model/build_merged_clothes_dataset.py`
- `backend-train-model/generate_split_manifests.py`
- `backend-train-model/train_workwear.py`
- `backend-train-model/All-train-model/merged_clothes_v2_balanced.build.json`
- `backend-train-model/All-train-model/unified_holdout_v1.build.json`
- `backend-train-model/All-train-model/first_train_holdout_v1.build.json`
- `backend-train-model/All-train-model/splits/trainval_balanced_v1.split.csv`
- `backend-train-model/All-train-model/splits/unified_holdout_v1.split.csv`
- `backend-train-model/All-train-model/splits/source_balanced_v1_summary.json`
- `backend-train-model/All-train-model/README.md`
- `backend-train-model/docs/all_train_docs/unified_holdout_compare_method.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- `build_merged_clothes_dataset.py` 配置新增：
  - `split_manifest_csv`
  - `strict_split_manifest`
- `train_workwear.py evaluate` CLI 新增：
  - `--report-name`
- `manifest.csv` 新增列：
  - `assignment_source`
  - `assignment_note`
  - `holdout_group`
  - `sample_role`
- train report 新增字段：
  - `initial_base_model`
  - `initial_base_model_source`
  - `training_lineage`
- eval report 新增字段：
  - `comparison_dataset_name`
  - `report_name`
  - `report_path`

兼容性注意：
- 未传 `split_manifest_csv` 时，`build_merged_clothes_dataset.py` 仍按原来的 `sequences[].split` 行为工作。
- 未传 `--report-name` 时，`evaluate` 仍默认写入 `{run_name}_eval.json`。
- 现有 `merged_v1_positive_only`、`merged_v2_full_reviewed`、`first-train` 的既有权重与报告文件不会被自动改写。
- `resume` 流程本身没有改成新逻辑，只是把首次启动来源和后续 resume 链补记进 train report。

不改动说明：
- 本轮不修改 `dataset_tools.py`、`config.py`、`project_config.json` 的默认 prepare 行为。
- 本轮不改动 `inspection-flask/` 的在线推理链路。
- 本轮不直接启动新的长时间训练；真正的 `strict holdout` 训练仍由用户按新增文档中的命令触发。

## 2026-04-11 修复 `--project` / `--project-config` 前缀冲突，打通 strict holdout 训练命令

变更来源：
- 用户在执行 strict holdout 训练命令时反馈：
  - `python train_workwear.py train --project-config All-train-model\merged_train_project_config.json ... --project All-train-model\artifacts\runs ...`
  - 实际报错却变成“读取项目配置失败: ...\All-train-model\artifacts\runs”。
- 本轮目标是把相关代码和文档一起改正确，确保后续训练命令能顺利执行。

变更总览：
1. 在 `backend-train-model/train_workwear.py` 中引入禁用长参数缩写的 CLI 解析器，彻底避免 `--project` 被 bootstrap 阶段误识别为 `--project-config`。
2. 顶层 parser 与所有子命令 parser 同步禁用长参数缩写，统一 CLI 行为，减少后续新增长参数时再次出现前缀冲突的风险。
3. 更新 `backend-train-model/docs/total-run-method.md`，明确说明该问题已修复，保留并确认 strict holdout 命令中的 `--project` 写法现在可直接使用。
4. 更新 `backend-train-model/All-train-model/README.md`，补充“`--project` 不再误判、但 `--project-config` 仍按 `backend-train-model/` 相对解析”的说明，避免再次混淆。

涉及文件：
- `backend-train-model/train_workwear.py`
- `backend-train-model/docs/total-run-method.md`
- `backend-train-model/All-train-model/README.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无新增业务配置项。
- CLI 行为变更：
  - `train_workwear.py` 现在禁用长参数缩写匹配。

兼容性注意：
- 之后请使用完整长参数名，例如：
  - `--project-config`
  - `--project`
  - `--report-name`
- 之前如果有人依赖 `--proj`、`--project-conf` 这类缩写写法，现在将不再被接受；这是有意收紧，目的是消除歧义并提升训练命令稳定性。
- `--project-config` 的路径解析规则没有改：仍然建议先进入 `backend-train-model/`，再使用 `All-train-model\...` 相对路径运行命令。

不改动说明：
- 本轮不调整 `group3_1 / group3_2 / group3_3` 的数据集内容与 split 规则。
- 本轮不修改 `inspection-flask/` 代码，因为扫描后未发现与本次训练报错直接相关的训练入口或路径配置。
- 本轮不直接启动长时间训练，只修复入口和命令口径，并在本地做轻量解析验证。

## 2026-04-11 细化 unified holdout 实验设计，拆分“公平主对照”和“业务路线验证”

变更来源：
- 用户继续追问 unified holdout 训练方案时指出：
  - `clothes_first_train_holdout_v1` 的新权重输出在 `All-train-model/artifacts/runs/...`；
  - 但文档里 `All-train-model` 的 strict holdout 训练仍读取历史 `first-train/artifacts/runs/clothes_fullframe_baseline/weights/best.pt`。
- 因此需要把文档中的实验目标拆清楚：哪些命令是在做严格公平对照，哪些命令是在验证“先 first-train 再 merged”的业务路线。

变更总览：
1. 重写 `backend-train-model/docs/total-run-method.md`：
   - 保留 `cross-eval` 历史复评；
   - 将 strict holdout 主对照改为：
     - `first-train` 从 `weights/yolov8n.pt` 起跑；
     - `merged_v2_balanced` 也从 `weights/yolov8n.pt` 起跑；
   - 新增单独的 `route verification` 阶段，明确 warm-start merged 应读取本轮新生成的 `All-train-model/artifacts/runs/clothes_first_train_holdout_v1/weights/best.pt`。
2. 重写 `backend-train-model/docs/all_train_docs/unified_holdout_compare_method.md`：
   - 明确区分三层比较：
     - 历史复评；
     - strict holdout / fair compare；
     - route verification；
   - 明确说明 strict 主对照不再使用历史 `first-train/.../best.pt` 作为 merged 初始化。
3. 文档中补充并行性说明：
   - fair compare 两条重训命令可并行；
   - route verification 依赖本轮 `clothes_first_train_holdout_v1` 的新权重，不能并行。

涉及文件：
- `backend-train-model/docs/total-run-method.md`
- `backend-train-model/docs/all_train_docs/unified_holdout_compare_method.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无新增代码配置项。
- 文档口径变更：
  - strict holdout 主对照的 merged 初始化权重改为 `weights/yolov8n.pt`
  - route verification 的 merged 初始化权重改为本轮生成的 `All-train-model/artifacts/runs/clothes_first_train_holdout_v1/weights/best.pt`
- 新增推荐 run 名称：
  - `clothes_merged_v2_balanced_holdout_v1`
  - `clothes_merged_v2_balanced_from_first_holdout_v1`

兼容性注意：
- 历史 `cross-eval` 命令仍然保留 `first-train/artifacts/runs/clothes_fullframe_baseline/weights/best.pt`，因为它们复评的是历史产物，不是新的 strict 主对照。
- 如果你已经按旧文档跑过 `clothes_merged_v2_balanced_from_first`，它仍可作为历史参考，但不再建议把它当作当前 unified holdout 主结论。
- 从本轮起，更推荐按以下顺序解读结果：
  1. `cross-eval`
  2. `strict holdout / fair compare`
  3. `route verification`

不改动说明：
- 本轮不修改 `train_workwear.py`、`build_merged_clothes_dataset.py` 或任何数据集构建配置文件。
- 本轮不新增新的 holdout split 规则，只调整文档中的实验设计口径与命令组织方式。
- 本轮不直接启动训练，只更新推荐运行方法，方便用户后续自行执行。

## 2026-04-11 根据 strict holdout 结果更新 `todo_list.md` 阶段状态

变更来源：
- 用户已完成 `backend-train-model/docs/total-run-method.md` 中的第二、三、四阶段，并要求依据当前 `merged_v2_balanced_holdout_v1` 明显优于 `first_train_holdout_v1` 的结果，微调 `backend-train-model/docs/todo_list.md`。
- 用户同时确认后续是否应以 merged 作为 fullframe baseline，再进入 `person` / `personcrop` 路线。

变更总览：
1. 更新 `backend-train-model/docs/todo_list.md` 的总路线：
   - 将阶段 1 从泛化的“先训稳 clothes baseline”调整为“固定 merged fullframe clothes baseline”。
2. 更新 P0 阶段状态：
   - 标记 unified holdout / balanced split / strict holdout 主对照已完成；
   - 标记 `merged_v2_balanced_holdout_v1` 当前优于 `first_train_holdout_v1`；
   - 新增待办：继续执行 `total-run-method.md` 第五阶段 `route verification`；
   - 新增待办：在 `merged_v2_balanced_holdout_v1` 与 `merged_v2_balanced_from_first_holdout_v1` 之间选择最终 fullframe baseline。
3. 调整 `person` 数据阶段描述：
   - 将“当前三段序列”改为面向当前 merged 主数据的 `g31 / g32 / g33` 来源；
   - 继续保留“person 标签独立目录、不要污染 clothes 标签”的原则。
4. 更新近期执行顺序与里程碑：
   - 将 strict holdout 主对照标记为已完成；
   - 将 route verification、固定最终 merged baseline、整理误报 / 漏报样本作为近期第一优先级剩余任务；
   - 说明进入 personcrop 前仍需先补 person 数据并训练 / 固化 person 模型。

涉及文件：
- `backend-train-model/docs/todo_list.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无新增代码配置项。
- 文档路线口径变更：
  - 当前 clothes fullframe 主线候选从旧 `first-train` 转为 `merged_v2_balanced_holdout_v1`。
  - route verification 结果出来后，再最终固定 `clothes` fullframe baseline。

兼容性注意：
- 本轮只更新 TODO 状态与执行路线，不修改训练脚本、数据集构建脚本或现有权重文件。
- `personcrop` 仍不是当前可直接跳入的下一步；它依赖独立 `person` 标注数据和可用的 `person_detect_yolov8.pt`。

不改动说明：
- 本轮不创建新的 `person` 数据目录或标签规范文档。
- 本轮不执行 route verification 训练命令，只把它标为当前下一步。
- 本轮不导出或复制最终 baseline 权重，需等第五阶段结果后再确定最终权重。
## 2026-04-24 新增 ROI-aware v3 方案文档并补充“允许纠错”规则

变更来源：
- 用户要求把两个 ROI-aware v3 方案文档真正写入 `backend-train-model/person-train-model/train-docs/`，文件名分别为：
  - `person_roi_aware_v3_mask_then_crop_margin64.md`
  - `person_roi_aware_v3_crop_only_margin64.md`
- 用户进一步要求把一条长期规则写入 `AGENTS.md`：当用户的技术判断可能不准确时，AI Agent 可以明确纠正、提出异议并给出更合理建议，而不是默认附和。

变更总览：
1. 新增 `person_roi_aware_v3_mask_then_crop_margin64.md`，系统说明 `mask_then_crop + crop_margin_px=64` 方案的定义、优势、风险、验证重点和推荐定位。
2. 新增 `person_roi_aware_v3_crop_only_margin64.md`，系统说明 `crop_only + crop_margin_px=64` 方案的定义、优势、风险、验证重点和对照实验定位。
3. 在两份文档中明确区分：
   - 源 fullframe `person` 标注是完整存在的；
   - ROI-aware prepared 标签只保留满足 keep rule 的 person；
   - `crop-only` 的风险不在“源标签缺失”，而在“prepared 图像里可能出现可见但未保留为 ROI-aware 标签的 person”。
4. 同步更新根 `AGENTS.md` 与 `backend-train-model/AGENTS.md`，明确加入“当用户的技术判断可能不准确时，AI Agent 应基于代码与事实主动纠正并给出更合理建议”的长期规则。

涉及文件：
- `backend-train-model/person-train-model/train-docs/person_roi_aware_v3_mask_then_crop_margin64.md`
- `backend-train-model/person-train-model/train-docs/person_roi_aware_v3_crop_only_margin64.md`
- `backend-train-model/AGENTS.md`
- `AGENTS.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无新的代码配置项落地。
- 本轮新增的是方案文档，不代表 `crop_margin_px=64`、`crop_only` 或新的 ROI-aware v3 prepare 逻辑已经在代码中实现。

兼容性注意：
- 当前仓库代码仍然只实现 `roi.mode=mask_then_crop`；两份 v3 文档当前是方案说明，不是现成可直接运行的已落地配置。
- 两份文档都明确写出了：source fullframe 标签完整存在，但 ROI-aware prepare 后只保留符合 keep rule 的 person；后续讨论 `crop-only` 风险时不要再误写成“源数据里 ROI 外 person 没标注”。
- 本轮新增的“允许纠错与反驳”规则是长期协作口径，不代表 AI Agent 可以脱离用户目标擅自扩写或擅自改需求；它只用于在发现技术判断与代码/数据事实不一致时主动指出并修正。

本轮明确不改动：
- 不修改 `prepare_roi_aware_person_dataset.py`、`prepare_person_dataset.py` 或 `person_project_config.json`。
- 不实现新的 `crop_margin_px` 配置项与 ROI-aware v3 prepare 流程。
- 不启动新的训练、评估或数据重生成任务。
## 2026-04-25 新增 ROI cropped keep-positive 复核脚本并生成 review 产物

变更来源：
- 用户要求不要只凭单帧样本判断 `crop_margin_px=64` 是否必要，而是把当前 ROI-aware v2 中 `cropped_boxes=54` 里真正属于 keep-positive 的样本单独筛出来，并生成清单与可视化，作为后续是否实现 margin 的依据。

变更总览：
1. 新增 `backend-train-model/person-train-model/train-code/review_roi_cropped_keep_boxes.py`，用于复用当前 ROI-aware v2 keep rule 与 crop 逻辑，筛查“被保留但又被当前 crop bbox 裁剪”的样本。
2. 脚本会为每个命中的样本同时输出：
   - fullframe overlay（显示 ROI polygon、当前 crop bbox、模拟 margin64 bbox、原框与裁剪后框）
   - 当前 `mask_then_crop` 预览图
   - 模拟 `margin64` 后的 `mask_then_crop` 预览图
3. 已生成 review 产物目录：
   - `backend-train-model/person-train-model/train-result/review/roi_cropped_keep_positive_v2/`
4. 当前复核结果：
   - 扫描图片 `502` 张
   - 命中 affected images `52` 张
   - 命中 affected boxes `54` 个
   - 其中 `margin64` 可完全恢复 `31` 个
   - 仍然会被裁剪的还有 `23` 个

涉及文件：
- `backend-train-model/person-train-model/train-code/review_roi_cropped_keep_boxes.py`
- `backend-train-model/person-train-model/train-result/review/roi_cropped_keep_positive_v2/cropped_keep_positive_summary.json`
- `backend-train-model/person-train-model/train-result/review/roi_cropped_keep_positive_v2/cropped_keep_positive_summary.md`
- `backend-train-model/person-train-model/train-result/review/roi_cropped_keep_positive_v2/overlays/`
- `backend-train-model/person-train-model/train-result/review/roi_cropped_keep_positive_v2/current_mask_crops/`
- `backend-train-model/person-train-model/train-result/review/roi_cropped_keep_positive_v2/margin64_mask_crops/`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无新的训练配置项落地。
- 新增 review 脚本参数：
  - `--output-root`
  - `--margin-px`
  - `--overwrite`

兼容性注意：
- 该脚本当前是复核工具，不会修改 prepared 数据集，也不会自动回写 `prepare_report.json`。
- 脚本里的 `margin64` 结果是基于当前 `mask_then_crop` 逻辑做的模拟对照，不代表代码中已经正式实现了 `crop_margin_px=64`。
- 当前复核结果表明：`margin64` 对一部分 top-cut / side-cut 的 keep-positive 样本有明确帮助，但对 bottom-cut 样本并不总是有效；是否真正落地仍应结合 review 产物判断。

本轮明确不改动：
- 不修改 `prepare_roi_aware_person_dataset.py` 的正式 prepare 逻辑。
- 不修改 `person_project_config.json`。
- 不生成新的 prepared 数据集，也不启动新的训练或评估。
## 2026-04-25 落地 ROI-aware v3 的 `crop_margin_px=64` 与 `crop_only` / `mask_then_crop` 运行入口

变更来源：
- 用户确认继续推进 `crop_margin_px=64` 的正式落地，希望把 ROI-aware prepare 逻辑扩展到可运行的 v3 版本，并同步更新 `person_run_method.md`，把 `mask_then_crop` 与 `crop_only` 两条 v3 训练 / 评估方法按既有格式写入文档。

变更总览：
1. 扩展 `prepare_person_dataset.py` 中的 ROI 配置解析：
   - `roi.mode` 不再只允许 `mask_then_crop`，现在正式支持 `mask_then_crop` 与 `crop_only`。
   - 新增 `roi.crop_margin_px` 配置项，默认值为 `0`。
   - 新增 `apply_roi_setting_overrides(...)`，用于 wrapper / 独立脚本按命令行显式覆盖 ROI mode 与 crop margin。
2. 更新 `prepare_roi_aware_person_dataset.py`：
   - `build_mask_and_crop_bounds(...)` 正式支持 `margin_px` 扩边；
   - `prepare_roi_aware_dataset(...)` 正式支持两种图像处理流程：
     - `mask_then_crop`
     - `crop_only`
   - `prepare_report.json` 新增 `crop_margin_px` 字段，并按实际生效的 ROI mode / margin 记录。
3. 更新 `labelme_roi_to_config.py` 与 `run_person_flow.py`：
   - `extract-roi-config` 和 `prepare-roi-aware` 现在都支持显式传：
     - `--roi-mode`
     - `--crop-margin-px`
   - 便于为 `person_roi_aware_v2`、`person_roi_aware_v3_mask_then_crop_margin64`、`person_roi_aware_v3_crop_only_margin64` 分别生成带版本元数据的 ROI 配置与 prepared 数据集。
4. 更新 `person_project_config.json`，把 `roi.crop_margin_px` 显式补入默认配置，当前默认值为 `0`，保持历史 v2 行为不变。
5. 重写 `person_run_method.md` 的版本段顺序与运行命令，新增：
   - `person_roi_aware_v3_mask_then_crop_margin64`
   - `person_roi_aware_v3_crop_only_margin64`
   并保持“最新在前、历史在后”的版本管理约束。
6. 同步更新两份 v3 方案文档，去掉“代码尚未落地”的旧口径，改为说明：代码已支持 prepare 落地，文档继续承担方案定位、风险说明与验证口径记录。

涉及文件：
- `backend-train-model/person-train-model/train-code/prepare_person_dataset.py`
- `backend-train-model/person-train-model/train-code/prepare_roi_aware_person_dataset.py`
- `backend-train-model/person-train-model/train-code/labelme_roi_to_config.py`
- `backend-train-model/person-train-model/train-code/run_person_flow.py`
- `backend-train-model/person-train-model/person_project_config.json`
- `backend-train-model/person-train-model/train-docs/person_run_method.md`
- `backend-train-model/person-train-model/train-docs/person_roi_aware_v3_mask_then_crop_margin64.md`
- `backend-train-model/person-train-model/train-docs/person_roi_aware_v3_crop_only_margin64.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- `roi.crop_margin_px`
- 新增 CLI 参数：
  - `extract-roi-config --roi-mode`
  - `extract-roi-config --crop-margin-px`
  - `prepare-roi-aware --roi-mode`
  - `prepare-roi-aware --crop-margin-px`

兼容性注意：
- 当前 `person_project_config.json` 默认仍是 `mask_then_crop + crop_margin_px=0`，因此历史 v2 行为不会因为这次代码扩展而被被动改写。
- `crop_only` 现在是正式可运行模式，但它仍然更适合作为对照实验，而不是默认主线；原因仍然是 ROI 外可见但未保留为标签的 person 可能重新进入 crop 图。
- 版本化 ROI-aware 实验时，建议 `extract-roi-config` 与 `prepare-roi-aware` 两个阶段都显式传相同的 `--roi-mode` 与 `--crop-margin-px`，避免 ROI 配置元数据与最终 prepare 行为不一致。

本轮明确不改动：
- 不重写 `roi.keep_rule` 的当前默认值；仍保持 v2 的 `bottom_center_inside OR box_ioa >= 0.25`。
- 不直接生成完整的 v3 prepared 数据集。
- 不启动新的训练或评估任务；本轮只完成代码入口与运行文档落地。
## 2026-04-25 同步 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` 对比结果

变更来源：
- 用户已完成 `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` 的训练与评估，要求查看效果并把最新结果同步写入 `backend-train-model/person-train-model/train-docs/roi_compare.md`。
- 根据仓库级维护约束，本轮同时把 ROI-aware 当前长期结论同步更新到根 `AGENTS.md` 与 `backend-train-model/AGENTS.md`，避免后续上下文继续停留在旧版 v2。

变更总览：
1. 更新 `roi_compare.md`，新增一条最新对比记录：`2026-04-25 person_roi_aware_v3_mask_then_crop_margin64_from_fullframe 对比`。
2. 新增 v3 与 `person_roi_aware_v2`、`person_roi_aware`、`person_fullframe` 的 test / val 指标表，并明确写出：
   - fullframe vs ROI-aware 不是同 `dataset.yaml`
   - v3 vs v2 也不是完全相同的 `dataset.yaml`，但 keep rule、初始化方式和 split 结构相同，因此更接近“近似单因子工程对比”
3. 在对比文档中补充了 v3 的 ROI-aware 数据集统计：
   - `mode=mask_then_crop`
   - `crop_margin_px=64`
   - `kept_boxes=1335`
   - `dropped_boxes=316`
   - `cropped_boxes=23`
   - `empty_roi_negative_images=15`
4. 文档中明确写出本次最重要的工程观察：
   - v3 相比 v2 的 native test 指标只有很小优势（`mAP50-95 +0.0052`）
   - 但裁剪框从 `54` 明显降到 `23`
   - 因此更准确的结论应是“当前 test 领先但优势很小的 ROI-aware 候选版本”，而不是“显著优于 v2”
5. 同步更新根 `AGENTS.md` 与 `backend-train-model/AGENTS.md` 中关于“当前最佳 ROI-aware run / 当前结论 / 当前优先策略”的描述，改为与最新对比文档一致。

涉及文件：
- `backend-train-model/person-train-model/train-docs/roi_compare.md`
- `AGENTS.md`
- `backend-train-model/AGENTS.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无新的代码配置项。
- 无新的训练 CLI 参数。
- 本轮变更的是结果结论与长期上下文，不涉及 prepare / train / eval 逻辑改动。

兼容性注意：
- `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe` 当前虽然拿到了更高的 native test `mAP50-95`，但相对 v2 的提升幅度很小，不应直接把 v2 定性为“已被明确淘汰”。
- v3 与 v2 的 prepared 数据集目录不同，不能把这次结果表述为严格同数据集公平消融。
- 当前更适合把 v3 写成“test 领先但优势很小的候选版本”，同时继续保留 v2 作为稳定备选。

本轮明确不改动：
- 不修改 `prepare_roi_aware_person_dataset.py`、`run_person_flow.py` 或任何训练代码。
- 不改动已生成的 v3 prepared 数据集内容。
- 不启动 `crop_only` 新训练，也不在本轮直接把默认唯一上游结论改写成“只保留 v3”。
## 2026-05-14 完善 `person_with_new_labels` fullframe 修正计划文档

1. 变更来源：用户指出 `backend-train-model/person-train-model/train-docs/person_with_new_labels基线修正计划.md` 中原有 `4.2` 对“正确顺序”的说明过于抽象，没有真正写清楚当前 `new labels fullframe` 修正应如何按阶段推进，因此要求把这份计划文档补充完整。
2. 变更总览：
   - 更新 `backend-train-model/person-train-model/train-docs/person_with_new_labels基线修正计划.md`。
   - 将原本较抽象的 `4.2 当前真正要改的是“实验顺序”` 改写成更明确的反例 + 正确顺序说明，先写清“当前不该先做什么”，再写清“当前真正应该怎么做”。
   - 新增 `4.2.1 把上面这条顺序翻成真正可执行的阶段`，把 fullframe 修正拆成 `A ~ F` 六个阶段：先整理 `must_relabel_list / hard_positive_expand_list / defer_list`，再修源标签、补 hardest 邻近帧、刷新 prepared 数据、判断 fine-tune 还是重训、最后才决定是否进入 new labels ROI-aware。
   - 文档中进一步明确：当前“修改训练方式”的核心不是先改大配方，而是先把 `人工复核.md` 的 crowded / overlap、`second_person_no_response`、`visibility weak`、`annotation_problem` 结论落实成可执行的数据治理动作。
3. 涉及文件：
   - `backend-train-model/person-train-model/train-docs/person_with_new_labels基线修正计划.md`
   - `backend-train-model/docs/update_log.md`
4. 新增 / 变更配置项：
   - 无新增训练脚本参数。
   - 无新增 `project_config`、ROI 配置或 prepared 数据集。
   - 本轮只补充执行顺序与阶段口径，不修改现有训练代码与评估逻辑。
5. 兼容性注意：
   - 该文档更新的是当前阶段的执行顺序与数据治理优先级，不代表已经自动完成 `must_relabel_list`、`hard_positive_expand_list` 或任何源标签修订；实际修标、补样、重跑 prepare 与训练仍需按文档顺序单独执行。
   - 文档中提到的 `seed7 fine-tune` 与 `640` 干净重训是当前推荐的两条修正路径，但选择哪条仍应以本轮数据改动规模为准，而不是机械固定。
   - 当前仍不应把这份文档理解成“现在就切 ROI-aware”的许可；只有 fullframe 修正后上游效果成立、且 `new_person_labels` ROI 补齐后，才适合进入正式 ROI-aware 比较。
6. 本轮明确不改动：
   - 不修改 `run_person_flow.py`、`prepare_person_dataset.py`、ROI prepare 逻辑或任何训练代码。
   - 不修改 `person_project_config.fullframe_with_new_labels.json`、任何 `person_project_config.roi_*.json`、`roi_config*.generated.json` 或现有 prepared 数据集。
   - 不启动新的训练、评估、导出，也不修改在线检测链路与历史人工复核正文。

## 2026-04-27 同步 `person_roi_aware_v3_crop_only_margin64_from_fullframe` 对照结果

变更来源：
- 用户已完成 `person_roi_aware_v3_crop_only_margin64_from_fullframe` 的训练与评估，要求把这次 `crop_only` 对照结果补充到 `backend-train-model/person-train-model/train-docs/roi_compare.md`。
- 根据仓库级长期维护约束，本轮同时把“crop_only 已完成但不推荐作为默认主线”的结论同步更新到根 `AGENTS.md` 与 `backend-train-model/AGENTS.md`。

变更总览：
1. 更新 `roi_compare.md`，新增一条最新对比记录：`2026-04-27 person_roi_aware_v3_crop_only_margin64_from_fullframe 对比`。
2. 新增 `crop_only` 与 `mask_then_crop`、`v2`、`v1`、`fullframe` 的 `val/test` 指标表，并明确写出：
   - `crop_only` vs `mask_then_crop` 是当前最接近“单因子图像处理流程对比”的实验
   - 两条 v3 版本的 keep rule、crop margin、split 结构、保留框 / 丢弃框 / 裁剪框 / 空负样本统计完全一致
   - 主要差异只在 ROI 外像素是否置黑
3. 在对比文档中明确记录这次实验的核心结论：
   - `crop_only + margin64` 没有优于 `mask_then_crop + margin64`
   - 也没有优于 `person_roi_aware_v2_from_fullframe`
   - `margin64` 本身仍然有价值，因为两条 v3 路线都把裁剪框从 `54` 降到了 `23`
4. 文档中同步补充 `crop_only` 的训练过程信息：
   - `results.csv` 中 best epoch 约为 `72`
   - 最终停在第 `132` 轮
   - native val `mAP50-95` 与 `mask_then_crop` 接近，但 native test 没有转化为更优结果
5. 同步更新根 `AGENTS.md` 与 `backend-train-model/AGENTS.md` 中 ROI-aware 当前状态的长期口径，补入：
   - `person_roi_aware_v3_crop_only_margin64_from_fullframe` 的最终 test 指标
   - 当前 ROI-aware 优先顺序
   - `crop_only` 已完成但不推荐作为默认主线的结论

涉及文件：
- `backend-train-model/person-train-model/train-docs/roi_compare.md`
- `AGENTS.md`
- `backend-train-model/AGENTS.md`
- `backend-train-model/docs/update_log.md`

新增 / 变更配置项：
- 无新的代码配置项。
- 无新的训练 CLI 参数。
- 本轮只更新结果结论与长期上下文，不涉及 prepare / train / evaluate 流程代码改动。

兼容性注意：
- `crop_only` 与 `mask_then_crop` 这次对照虽然 prepared 输出目录不同，但统计上属于同一套 keep rule / crop margin / split 逻辑，不应把这轮差异误解为“样本数量差异导致”。
- 当前 `crop_only` 在 native test 上落后于 `mask_then_crop` 与 `v2`，因此不应再把它描述为“当前更贴近生产所以更可能更好”；这轮结果已经说明在当前数据与业务语义下，它至少不是默认主线的更优选择。
- 当前最稳妥的排序仍是：
  - `person_roi_aware_v3_mask_then_crop_margin64_from_fullframe`
  - `person_roi_aware_v2_from_fullframe`
  - `person_roi_aware_v3_crop_only_margin64_from_fullframe`

本轮明确不改动：
- 不修改任何训练代码、prepare 逻辑或配置文件。
- 不重新生成任何 prepared 数据集。
- 不在本轮启动 `imgsz=768` 新训练。

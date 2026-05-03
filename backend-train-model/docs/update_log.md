# Update Log

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

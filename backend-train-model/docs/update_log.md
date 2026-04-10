# Update Log

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

# Update Log

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

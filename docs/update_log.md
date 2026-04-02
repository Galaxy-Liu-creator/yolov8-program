# Update Log

## 2026-04-02 离线验证口径与告警措辞深度收敛

变更来源：
- 用户批准：基于 `docs/check_log.md` 最新问题分析结果，开始对离线验证链路做深度修改
- 数据集文档：`docs/dataset.md` 明确当前仓库样例是单类 `clothes` 标注
- 用户补充约束：以后代码修改只更新 `docs/update_log.md`，不再强制同步修改 `docs/check_log.md`

变更总览：
1. 收敛 `inspection-flask/main.py` 的 `validate` CLI 默认值、帮助文案和离线输出口径，默认改为 `--gt-mode clothes-only --clothes-cls 0`，与当前仓库数据集说明保持一致。
2. 增强离线真值评估链路：兼容 mirrored / flat 两种标签目录结构，增加标签类别扫描告警，并改为基于 IoU 的实例级匹配统计，避免把当前单类 `clothes` 数据误当成 `person + clothes` 配对数据。
3. 收紧离线与入库侧措辞，将绝对化“未穿工服”统一调整为“疑似未穿工服”或“作业区人员疑似未穿工服”，避免超出当前 ROI + 单帧判定能力边界。

涉及文件：
- `inspection-flask/main.py`
- `inspection-flask/applications/view/system/hk_camera.py`
- `inspection-flask/applications/models/admin_violate_photo.py`
- `docs/update_log.md`

新增 / 变更配置项：
- 无新增配置项；继续沿用 `inspection-flask/settings.py` 中既有的 `WORKWEAR_VIOLATION_NAME` 等配置。

不改动说明：
- `inspection-flask/violation_module/vio_workwear_missing.py` 本轮仅复核，不改动；现有实现已支持多条触发轨迹并行处理。
- `inspection-flask/applications/common/hk_recorder_threading.py` 本轮仅复核，不改动；现有实现已包含静态帧哈希去重，避免离线静态图重复累积时序计数。

兼容性注意：
- 离线 `validate` 在提供 `--labels` 时默认按单类 `clothes` 标注解释；如果你使用的是 `person + clothes` 配对标注，需显式传入 `--gt-mode paired --person-cls ... --clothes-cls ...`。
- `paired` 模式仍然保留，但当 `person_cls == clothes_cls` 时会直接报错，避免错误配置静默通过。
- 按当前用户维护约定，本次仅更新 `docs/update_log.md` 记录变更，不同步修改 `docs/check_log.md`。

## 2026-04-02 安装元数据与模板鉴权收尾

变更来源：
- 用户需求：继续按 `docs/run_todo_list.md` 收尾，提升 `inspection-flask` 的可运行性与严谨性
- 最小运行链路改造后的复核结果：需要补齐 `pyproject.toml` 的可编辑安装包发现，并修正模板侧 `authorize()` 在鉴权开启时恒为 `False` 的逻辑问题

变更总览：
1. 强化 `inspection-flask/pyproject.toml`，补充 `py-modules` 与包发现规则，降低执行 `pip install -e .` 时的工程化风险。
2. 修正 `inspection-flask/applications/extensions/init_template_directives.py`，使模板侧权限判断在 `AUTH_ENABLED=True` 时回退到与路由鉴权一致的权限计算逻辑，而不是一律返回 `False`。
3. 清理 `inspection-flask/settings.py` 中重复的启动兼容配置定义，避免后续维护时产生同名配置重复声明的歧义。
涉及文件：
- `inspection-flask/pyproject.toml`
- `inspection-flask/settings.py`
- `inspection-flask/applications/extensions/init_template_directives.py`
- `docs/update_log.md`

新增 / 变更配置项：
- 无新增配置项；本次仅对既有配置定义做去重整理。

兼容性注意：
- `AUTH_ENABLED=False` 时，模板仍保持最小可运行模式下的全放行逻辑。
- `AUTH_ENABLED=True` 时，模板里的 `authorize()` 现在会复用会话权限 / 角色权限计算逻辑，不再错误隐藏所有受控按钮。
- `pyproject.toml` 新增的是打包发现规则，不改变现有运行时导入路径，只提升依赖安装与可编辑安装的稳定性。

用于记录每次代码变更的详细内容、变更原因、涉及文件与配置项。

## 维护约束

以后每次更新都必须遵守以下规则：

1. **新记录在最上方**：新增的更新记录必须插入在旧记录的上方，保持"最新在前，历史在后"。
2. **必须写明变更来源**：每条更新记录必须注明触发变更的来源（如 check_log.md 的问题编号、check_detail_ROI.md 的条款、用户需求等）。
3. **必须列出涉及文件**：每条更新记录必须列出所有被修改或新增的文件路径。
4. **必须列出新增/变更的配置项**：如果变更涉及 `settings.py` 中的配置项，必须单独列出配置项名称、默认值和用途说明。
5. **必须标注兼容性影响**：如果变更修改了函数签名、数据结构、配置字段名等对外接口，必须在记录中标注"兼容性注意"。
6. **禁止删除历史记录**：历史更新记录不可删除，只可追加新记录。
7. **关联 check_log 但不强制回写**：如果本次变更源自 `check_log.md` 中的问题，必须在本日志注明对应问题编号或问题描述及修复状态；除非用户另行要求，否则不再强制同步修改 `docs/check_log.md`。
8. **保持一致性**：`settings.py` 中的配置项名称与代码中 `getattr(settings, ...)` 的引用必须一致。新增配置项后需全文检索是否有遗漏引用点。
9. **验证链路完整性**：涉及新文件创建（如 `utils/plots.py`）时，必须在记录中说明调用方、被调用签名以及已验证的兼容性。
10. **不改动的部分必须声明**：如果某些模块/逻辑被评估后决定不改动，必须在记录中说明原因，防止后续重复评估。
11. **CLI 与离线工具同步**：若修改 `main.py` 子命令、参数或离线输出格式，须在本日志中更新对应条目，并保持模块顶部 docstring 与 `argparse` 帮助一致。

---

## 2026-04-02 最小运行链路静态复核与字段策略说明补充

变更来源：
- 用户需求：继续按 `docs/run_todo_list.md` 收口，让项目先可运行，并按文档要求同步日志
- `docs/run_todo_list.md` — 问题 4（相机模型与运行时字段可能未对齐）
- `docs/file_todo_list.md` — 文档维护约束，要求同步更新当前真实状态

变更总览：
1. 在 `inspection-flask/settings.py` 中补入明确的启动兼容开关定义，确保 `AUTH_ENABLED` 等配置能被稳定读取。
2. 在 `docs/run_todo_list.md` 中补充问题 4 的“当前落地状态”，明确当前采用的是运行时覆盖策略，而不是数据库迁移已完成。
3. 在 `docs/check_log.md` 中增加本轮静态复核说明，写清最小启动前置条件和仍未闭环部分。

涉及文件：
- `inspection-flask/settings.py`
- `docs/run_todo_list.md`
- `docs/file_todo_list.md`
- `docs/check_log.md`
- `docs/update_log.md`

边界说明：
- 当前 `roi` / `frame_path` / `stream_url` 已能通过运行时参数驱动线程与采图链路。
- 当前仍未声称 `HKCamera` 表结构已经正式扩展；若要长期持久化这些字段，仍需后续数据库迁移。
- 当前仍未声称“检测正确性已闭环验证”；真实效果仍依赖权重、输入流与样例复核。

## 2026-04-02 最小可运行链文档同步

变更来源：
- `docs/run_todo_list.md`（新增关于 `inspection-flask/pyproject.toml`、虚拟环境与验证指令、BaseConfig 从环境变量读取、SQLAlchemy/调度器容错以及软降级检测路径的说明）
- `docs/file_todo_list.md`（同步状态视图，明确标注当前处于“部分推进 / 具备软降级能力”阶段，并提示 Hikvision SDK 与检测精度闭环尚未完成）
- `docs/update_log.md`（本条目本身）

变更总览：
1. 把依赖安装 + `python main.py check`/`create_app` 验证步骤写入文档，依赖 `pyproject` 里声明，以便重新搭建环境时不需翻代码。
2. 说明运行时兼容性保障：`BaseConfig` 环境变量驱动、SQLAlchemy 初始化对 DB 断开的容忍、调度器在数据库可用后才启动，以及检测线程可通过 HKStream 或本地帧目录的软降级跳过 Hikvision SDK。
3. 通过 `docs/file_todo_list.md` 的状态总结保持“软降级”可见度，提醒后续仍需补齐 HK SDK 接入与检测正确性验证，避免过度宣称完成。
4. 清理文档中的旧文件名引用，把残留的 `to_list.md` 统一更正为 `file_todo_list.md`，避免后续维护继续误指向不存在的文件。

## 2026-04-02 inspection-flask 最小运行链路落地改造

变更来源：
- 用户需求：按 `docs/run_todo_list.md` 中提到的问题推进，让 `inspection-flask` 先运行起来，并同步更新日志
- `docs/run_todo_list.md` — 问题 1（运行环境依赖未安装）
- `docs/run_todo_list.md` — 问题 3（真实海康取流链路未恢复）
- `docs/run_todo_list.md` — 问题 5（数据库仍是运行硬前提）
- `docs/run_todo_list.md` — 问题 6（当前后台是“最小骨架”，不是“完整后台”）
- `docs/file_todo_list.md` — P1 / P2 / P3 / P5 当前阶段落地路线

### 变更总览

| 序号 | 变更内容 | 对应来源 | 涉及文件 |
|------|---------|---------|---------|
| 1 | 新增项目依赖元数据文件 | `run_todo_list` 问题 1 | `inspection-flask/pyproject.toml`, `docs/run_todo_list.md` |
| 2 | 应用启动软降级 | `run_todo_list` 问题 5 | `inspection-flask/settings.py`, `inspection-flask/applications/config.py`, `inspection-flask/applications/extensions/init_sqlalchemy.py`, `inspection-flask/applications/__init__.py` |
| 3 | 最小后台运行兼容 | `run_todo_list` 问题 6 | `inspection-flask/applications/extensions/__init__.py`, `inspection-flask/applications/extensions/init_template_directives.py`, `inspection-flask/applications/common/utils/rights.py`, `inspection-flask/applications/common/user_auth.py`, `inspection-flask/applications/view/system/hk_camera.py`, `inspection-flask/templates/system/hk_camera/main.html`, `inspection-flask/templates/system/hk_camera/add.html`, `inspection-flask/templates/system/hk_camera/edit.html` |
| 4 | 采图链兼容增强 | `run_todo_list` 问题 3 | `inspection-flask/hk/hksdk/__init__.py`, `inspection-flask/hk/hksdk/device.py`, `inspection-flask/applications/common/hk_recorder_threading.py`, `inspection-flask/applications/common/hk_custom_threading_plus.py`, `inspection-flask/applications/view/system/hk_camera.py` |
| 5 | 文档状态同步 | 用户需求 | `docs/update_log.md`, `docs/file_todo_list.md`, `docs/run_todo_list.md` |

### 不改动的部分

| 模块 | 决定 | 原因 |
|------|------|------|
| `inspection-flask/utils/models.py` | 维持现状 | 当前 YOLOv8 双模型包装层已可用，本轮重点不在模型解析层 |
| `inspection-flask/utils/workwear_policy.py` | 维持现状 | 工服裁剪与合规判定主口径已统一，不应在“先跑起来”阶段再次分叉 |
| `inspection-flask/violation_module/vio_workwear_missing.py` | 维持现状 | 时序规则主逻辑已建立，本轮不夸大为“检测正确性已闭环” |
| 旧警务多违规则、人脸、枪库、躺卧链路 | 明确不迁入 | 不属于当前工服项目主线，避免范围漂移 |

---

### 变更 1：新增依赖元数据文件

**涉及文件**:
- `inspection-flask/pyproject.toml`
- `docs/run_todo_list.md`

**改动内容**:

- 新增 `inspection-flask/pyproject.toml`，统一维护当前项目最小运行依赖。
- 在 `docs/run_todo_list.md` 中补充虚拟环境创建、`pip install -e .`、验证命令等安装说明。

---

### 变更 2：应用启动软降级

**涉及文件**:
- `inspection-flask/settings.py`
- `inspection-flask/applications/config.py`
- `inspection-flask/applications/extensions/init_sqlalchemy.py`
- `inspection-flask/applications/__init__.py`

**改动内容**:

- 新增最小运行兼容配置：
  - `AUTH_ENABLED`
  - `DB_STRICT_STARTUP`
  - `ENABLE_BACKGROUND_SCHEDULER`
  - `ALLOW_SAVE_VIOLATION_WITHOUT_DB`
  - `DEFAULT_STREAM_URL`
  - `RTSP_PORT`
  - `RTSP_PATH_TEMPLATE`
- 数据库连接失败时默认不再直接退出，改为：
  - 记录 `database_ready=False`
  - 记录 `database_init_error`
  - 以降级模式继续启动
- 后台调度器仅在数据库就绪且配置允许时启动，避免数据库未连通时启动即持续报错。
- `BaseConfig` 增加：
  - `SUPERADMIN`
  - `SQLALCHEMY_TRACK_MODIFICATIONS = False`
  - 环境变量可覆盖数据库连接参数

---

### 变更 3：最小后台运行兼容

**涉及文件**:
- `inspection-flask/applications/extensions/__init__.py`
- `inspection-flask/applications/extensions/init_template_directives.py`
- `inspection-flask/applications/common/utils/rights.py`
- `inspection-flask/applications/common/user_auth.py`
- `inspection-flask/applications/view/system/hk_camera.py`
- `inspection-flask/templates/system/hk_camera/main.html`
- `inspection-flask/templates/system/hk_camera/add.html`
- `inspection-flask/templates/system/hk_camera/edit.html`

**改动内容**:

- 在插件初始化阶段补入最小模板全局指令 `authorize()`，避免模板渲染缺少旧指令时报错。
- `AUTH_ENABLED=False` 时，`authorize()` 直接放行，不再强依赖旧登录系统。
- `user_auth.py` 增加无鉴权模式下的安全兜底，避免角色链缺失时直接异常。
- `hk_camera.py` 增加：
  - 页面模板缺失时的 JSON 降级返回
  - `/hk_camera/health` 健康检查接口
  - 无数据库模式下的运行时摄像头启停
  - 无数据库模式下的内存相机列表与违规事件查询
  - 违规写库失败时的内存事件回退
- 补齐最小模板，避免页面路由直接 500。

---

### 变更 4：采图链兼容增强

**涉及文件**:
- `inspection-flask/hk/hksdk/__init__.py`
- `inspection-flask/hk/hksdk/device.py`
- `inspection-flask/applications/common/hk_recorder_threading.py`
- `inspection-flask/applications/common/hk_custom_threading_plus.py`
- `inspection-flask/applications/view/system/hk_camera.py`

**改动内容**:

- 新增最小 `HKStream` 兼容封装，保留旧项目接口风格，但先支持 OpenCV 可读输入源。
- `hk_recorder_threading.py` 改为兼容：
  - 本地单图
  - 本地图集目录
  - 本地视频
  - `stream_url`
  - 按海康常见格式构造的 RTSP 地址
- 采图管理器新增流客户端缓存与释放逻辑。
- 检测线程重启时，支持回退到 `camera_registry` 和运行时覆盖配置。

**边界说明**:

- 本轮新增的是“最小兼容取流层”，不是“海康原生 SDK 已完整恢复”。

---

### 变更 5：文档状态同步

**涉及文件**:
- `docs/update_log.md`
- `docs/file_todo_list.md`
- `docs/run_todo_list.md`

**改动内容**:

- 新增本轮更新记录。
- 同步 `file_todo_list` 的当前真实状态：
  - 应用已具备软降级启动能力
  - 最小模板已补齐
  - 采图层已支持 `frame_path` / `stream_url` / RTSP fallback
- 在 `run_todo_list` 中补充当前已落地状态，明确哪些问题已“部分推进”，哪些仍未闭环。

### 新增 / 变更配置项

| 配置项 | 默认值 | 用途 |
|--------|--------|------|
| `AUTH_ENABLED` | `False` | 控制是否启用旧登录权限链 |
| `DB_STRICT_STARTUP` | `False` | 数据库连接失败时是否阻断 Flask 启动 |
| `ENABLE_BACKGROUND_SCHEDULER` | `True` | 控制后台调度器是否允许启动 |
| `ALLOW_SAVE_VIOLATION_WITHOUT_DB` | `True` | 写库失败或数据库未就绪时，是否保留证据图并写入内存事件 |
| `DEFAULT_STREAM_URL` | `None` | 默认视频流输入源（可作为调试输入） |
| `RTSP_PORT` | `554` | RTSP 默认端口 |
| `RTSP_PATH_TEMPLATE` | `rtsp://{username}:{password}@{ip}:{port}/Streaming/Channels/{channel_code}` | 构造 RTSP 地址 |
| `BaseConfig.SUPERADMIN` | `"admin"` | 旧权限链下的超级管理员用户名 |
| `BaseConfig.SQLALCHEMY_TRACK_MODIFICATIONS` | `False` | 关闭 SQLAlchemy 变更跟踪警告 |

### 兼容性注意

- `AUTH_ENABLED=False` 时，接口和页面将绕过旧登录系统，这用于“先运行起来”的最小兼容，不等于完整权限体系已恢复。
- 数据库连接失败时应用可启动，但 DB 相关接口与持久化能力不等于已经完整可用。
- 后台调度器仅在 `database_ready=True` 时启动；无数据库模式下更适合手动启停运行时摄像头。
- 新增的 `stream_url` / RTSP fallback 只是最小兼容取流能力，不代表原生 HCNetSDK 已完全接回。
- 本轮没有把“检测正确性”宣布为已闭环；模型权重、真实在线闭环、准确率验证仍需后续继续完成。

---

## 2026-03-31 Analysis_For_yolov8.md 一致性复核修改

变更来源：
- [check_log.md](check_log.md) — 2026-03-31 `Analysis_For_yolov8.md` 一致性复核记录（问题 1–4）
- [一致性复核问题修改计划](../plans/一致性复核问题修改_c5e7b302.plan.md)

### 变更总览

| 序号 | 变更内容 | 对应复核问题 | 涉及文件 |
|------|---------|-------------|---------|
| 1a | 离线 `person_context` 补齐 `in_roi`，与在线结构对齐 | 问题 1（高） | `main.py` |
| 1b | 修复 `validate` 每张图二次完整推理的性能问题 | 问题 1（高） | `main.py` |
| 1c | `image` / `validate` 输出离线局限性说明 | 问题 1（高） | `main.py` |
| 2 | `validate` 可选 YOLO 标注真值对比（TP/FP/FN 等） | 问题 2（中高） | `main.py` |
| 3 | `logic_judge.py` 标记为废弃并写明与在线规则口径差异 | 问题 3（中） | `logic_judge.py` |
| 4 | `Analysis_For_yolov8.md` 三处过时表述旁行内标注 | 问题 4（中） | `Analysis_For_yolov8.md` |

### 不改动的部分

| 模块 | 决定 | 原因 |
|------|------|------|
| `hk_custom_threading_plus.py` | 维持现状 | 在线规则口径无误，本轮仅对齐离线侧 |
| `vio_workwear_missing.py` | 维持现状 | 上一轮已修复 |
| `settings.py` | 无新增项 | 离线 ROI 复用既有 `ROI_MIN_OVERLAP_RATIO` |
| `base.py` | 维持现状 | 与本轮无关 |

---

### 变更 1: 离线/在线口径对齐 + validate 去重推理

**涉及文件**: `inspection-flask/main.py`

**1a `in_roi` 与 ROI 命令行**

- 新增 `_parse_roi_arg()`、`_check_in_roi()`：与在线 `HKCustomThread._in_roi()` 使用相同的重叠比例算法，阈值来自 `settings.ROI_MIN_OVERLAP_RATIO`。
- `_build_person_contexts(..., roi=None)`：为每个 context 写入 `"in_roi": bool`；未传 `--roi` 时等价于全帧在区内（`in_roi=True`）。
- `image`、`validate` 子命令增加 `--roi x1,y1,x2,y2`。
- 单图打印中违规/合规行增加 `ROI外` 标记（当 `in_roi` 为 False 时）。

**1b 去除 validate 双重推理**

- `_process_single_image()` 返回值增加 `label_counts: dict[str, int]`（按工服检测标签聚合）。
- `cmd_validate()` 仅汇总各图的 `result["label_counts"]`，不再在循环内二次 `imread` + `infer`。

**1c 离线局限性提示**

- 模块 docstring 增加「离线模式局限性」说明。
- 常量 `_OFFLINE_NOTE`：`cmd_image`、`cmd_validate` 启动时打印，明确不含时序规则与 track。

**兼容性注意**

- `_build_person_contexts` 新增可选参数 `roi`，默认 `None`，旧调用方式仍有效。
- `_process_single_image` 成功路径返回值必含 `label_counts`（可能为空 dict）。

---

### 变更 2: validate 真值对比模式（可选）

**涉及文件**: `inspection-flask/main.py`

**新增 CLI**

| 参数 | 作用 |
|------|------|
| `--labels <dir>` | YOLO txt 标注目录，与图片同名 `stem.txt` |
| `--person-cls` | 标注中 person 的 class_id，默认 `0` |
| `--clothes-cls` | 标注中 clothes 的 class_id，默认 `0` |

**新增函数 `_load_ground_truth()`**

- 解析 YOLO 行格式 `class_id cx cy w h`（归一化中心与宽高）。
- 真值合规：某 person 框与任一 clothes 框存在正面积交集即视为该 person 合规；否则计入真值违规人数。
- 报告标题：无 `--labels` 时为「推理统计（无真值对比）」；有标注时为「真值对比」并输出 TP、FP、FN、Precision、Recall、F1。

**口径说明**

- TP/FP/FN 按「每张图上的预测违规人数 vs 真值违规人数」做逐图 min/max 聚合，属于**图像级人数对比**，非逐人 IoU 匹配；用于快速回归，精细评估需扩展匹配策略时应在后续迭代中单独记录。

**配置项**

- 本轮未改 `settings.py`；ROI 阈值仍用 `ROI_MIN_OVERLAP_RATIO`。

---

### 变更 3: logic_judge.py 废弃声明

**涉及文件**: `inspection-flask/applications/common/logic_judge.py`

- 文件顶部增加模块级说明：标记为**已废弃**、无仓库内引用；说明替代模块。
- 明确 `count_violation_frames()` 与当前在线规则（按 `track_id` + `MIN_TRACK_APPEAR_FRAMES` + `TEMPORAL_TRIGGER_RATIO`）的口径差异。
- **不删除**既有函数，供历史参考。

---

### 变更 4: Analysis_For_yolov8.md 行内标注

**涉及文件**: `docs/Analysis_For_yolov8.md`

- 「强烈建议不要改」列表中 ROI 中心点条目旁标注已改为重叠比例。
- 「6.1 hk_recorder_threading」小节旁标注已加入帧哈希去重。
- 「7.1 必做检查项」中 ROI 边缘人员条目旁标注已改为 `ROI_MIN_OVERLAP_RATIO`。

---

### check_log 一致性复核问题状态映射

| 复核问题 | 处理状态 | 本次变更编号 |
|---------|---------|-------------|
| 问题 1: main 离线/在线口径不一致 | 已修复（结构对齐 + 去重推理 + 提示） | 变更 1 |
| 问题 2: validate 非准确率验证 | 已增强（可选真值对比） | 变更 2 |
| 问题 3: logic_judge 落后 | 已标注废弃 | 变更 3 |
| 问题 4: 文档过时 | 已行内标注 | 变更 4 |

---

## 2026-03-31 复检问题深入修改

变更来源：
- [check_log.md](check_log.md) — 2026-03-31 `inspection-flask` 复检记录（问题 1–6）
- [check_detail_ROI.md](check_detail_ROI.md) — ROI 方案设计文档（第 3、4 条要求）
- [复检问题深入修改计划](../plans/复检问题深入修改_1f322e0b.plan.md)

### 变更总览

| 序号 | 变更内容 | 对应 check_log 问题 | 涉及文件 |
|------|---------|-------------------|---------|
| 1 | 帧内容哈希去重 | 问题 1（高） | `hk_recorder_threading.py` |
| 2a | ROI 判定升级为重叠比例 | 问题 7（中）+ ROI 文档第 3 条 | `hk_custom_threading_plus.py`, `settings.py` |
| 2b | 最小停留帧数过滤 | ROI 文档第 4 条 | `vio_workwear_missing.py`, `settings.py` |
| 2c | 告警名称收紧 | 问题 2（高）+ ROI 文档 | `settings.py`, `vio_workwear_missing.py` |
| 2d | 面积过滤口径统一 | 问题 5（中高） | `vio_workwear_missing.py` |
| 3 | 证据图绑定触发 track | 问题 3（高） | `vio_workwear_missing.py` |
| 4 | 新增 `utils/plots.py` | 问题 5（高） | `utils/plots.py`（新增）, `base.py`（被调用方） |
| 5 | 新增 `validate` 子命令 | 问题 6（中） | `main.py` |

### 不改动的部分

| 模块 | 决定 | 原因 |
|------|------|------|
| `SimpleIoUTracker` IoU 贪心匹配 | 维持现状 | `Analysis_For_yolov8.md` 明确保护此逻辑；固定机位 2 秒间隔场景下 IoU 贪心匹配够用（check_log 问题 4） |
| `TEMPORAL_WINDOW_SIZE` / `TEMPORAL_TRIGGER_RATIO` 窗口聚合 | 维持现状 | 帧去重修复后时序窗口语义恢复正常 |
| 告警抑制窗口逻辑 | 维持现状 | 功能正常，无需调整 |
| Flask 框架、线程模型、数据库模型 | 维持现状 | 不在本次修改范围内 |

---

### 变更 1: 帧内容哈希去重

**修复问题**: check_log 问题 1（严重级别：高）— 静态图重复当新帧

**变更原因**: `hk_recorder_threading.py` 每次读取 `frame_path` 后使用 `datetime.now()` 作为时间戳写入缓存，检测线程按时间戳判断新帧。同一张静态图会被重复计入时序窗口，导致 `TEMPORAL_WINDOW_SIZE` 和 `TEMPORAL_TRIGGER_RATIO` 的业务语义失真。

**涉及文件**:
- `inspection-flask/applications/common/hk_recorder_threading.py`

**具体改动**:

1. **新增函数 `_compute_frame_hash(image, size=8)`**（第 18–27 行）
   - 将图像缩放到 8×8 灰度图后做均值二值化，生成 64 字节的感知哈希
   - 性能开销极低（一次 resize + 一次均值比较），不影响采集频率

2. **修改 `get_img()` 缓存写入逻辑**（第 72–79 行）
   - 写入缓存前先计算 `new_hash`，与已有缓存的 `frame_hash` 比较
   - 哈希相同则跳过（不更新 `ts`），内容真正变化时才写入新的 `ts`、`frame` 和 `frame_hash`

**兼容性注意**:
- `hk_frame_cache` 字典结构新增 `frame_hash` 字段（原有 `frame` 和 `ts` 不变）
- 消费方 `HKCustomThread.fetch_frame()` 只读取 `frame` 和 `ts`，不受影响

---

### 变更 2a: ROI 判定从中心点升级为重叠比例

**修复问题**: check_log 问题 7（严重级别：中）+ check_detail_ROI.md 第 3 条要求

**变更原因**: 原 `_in_roi()` 只判断人框中心点是否落入 ROI，边界场景不够稳健。

**涉及文件**:
- `inspection-flask/applications/common/hk_custom_threading_plus.py` — `_in_roi()` 方法（第 146–167 行）
- `inspection-flask/settings.py` — 新增配置项

**具体改动**:

`_in_roi()` 方法重写为：
- 计算人框与 ROI 的交叠面积
- 交叠面积占人框面积的比例 >= `ROI_MIN_OVERLAP_RATIO` 即视为在 ROI 内
- 无交叠时直接返回 `False`

**新增配置项**:

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `ROI_MIN_OVERLAP_RATIO` | `0.5` | 人框与 ROI 交叠面积占人框面积的最低比例 |

**兼容性注意**:
- `_in_roi()` 的签名和返回类型不变，对调用方透明
- 行为变化：原来中心点刚好在 ROI 边界的人可能因重叠面积不足 50% 而被排除

---

### 变更 2b: 增加最小停留帧数过滤

**修复问题**: check_detail_ROI.md 第 4 条要求

**变更原因**: 短暂掠过 ROI 的目标（如路过的行人）不应进入违规判定。

**涉及文件**:
- `inspection-flask/violation_module/vio_workwear_missing.py` — `run()` 方法、新增 `_load_min_track_appear()`
- `inspection-flask/settings.py` — 新增配置项

**具体改动**:

1. **新增 `_load_min_track_appear()` 方法**（第 128–134 行）：读取 `MIN_TRACK_APPEAR_FRAMES`，最小值钳位为 1
2. **`run()` 方法**（第 77 行）：在遍历 `track_stats` 判定触发时，`stats["appear"] < min_appear` 的 track 直接跳过

**新增配置项**:

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `MIN_TRACK_APPEAR_FRAMES` | `2` | track 至少出现 N 帧才进入违规判定 |

---

### 变更 2c: 告警名称收紧

**修复问题**: check_log 问题 2（严重级别：高）的部分落地 + check_detail_ROI.md 告警口径要求

**变更原因**: 原告警名称"未穿工服"过于绝对，结合 ROI 方案设计文档，收紧为"作业区人员疑似未穿工服"。

**涉及文件**:
- `inspection-flask/settings.py` — `WORKWEAR_VIOLATION_NAME` 修改
- `inspection-flask/violation_module/vio_workwear_missing.py` — `rule_name` 修改

**具体改动**:

1. `settings.py` 第 77 行：`WORKWEAR_VIOLATION_NAME = "作业区人员疑似未穿工服"`（原值 `"未穿工服"`）
2. `vio_workwear_missing.py` 第 24 行：`rule_name` 改为从 `settings.WORKWEAR_VIOLATION_NAME` 动态读取

**兼容性注意**:
- 数据库中 `rule_name` 字段内容会变化，历史记录中仍为旧名称
- 如需查询历史告警，需兼容两种名称

---

### 变更 2d: 面积过滤口径统一

**修复问题**: check_log 问题 5（严重级别：中高）

**变更原因**: `build_person_contexts()` 支持 `absolute`/`relative` 两种面积模式，但 `_is_valid_person()` 只按绝对面积 `MIN_PERSON_BOX_AREA` 重复过滤，两层口径不一致。

**涉及文件**:
- `inspection-flask/violation_module/vio_workwear_missing.py`

**具体改动**:

1. **移除 `_load_min_person_area()` 方法**：不再由规则层独立加载面积阈值
2. **修改 `_is_valid_person()` 签名**（第 137 行）：移除 `min_area` 参数，改为仅校验 `area > 0`
3. **`run()` 方法**（第 48 行）：调用 `_is_valid_person(person)` 不再传入 `min_area`

**设计决策**: 面积过滤职责收敛到上游 `build_person_contexts()` 一处，规则层信任上游已过滤的 `area` 字段。

**兼容性注意**:
- `_is_valid_person()` 签名变化：从 `(person, min_area)` → `(person)`
- 仅内部调用，无外部依赖

---

### 变更 3: 证据图绑定触发 track

**修复问题**: check_log 问题 3（严重级别：高）— 触发 track 与证据图不绑定

**变更原因**: `_add_person_to_plot()` 会把所有违规人员加入 `plot_targets`，但 `base.py` 的 `save()` 从全部 `plot_targets` 中选最高置信度帧，不区分是哪个 track。可能出现 A 触发违规但保存 B 的证据图。

**涉及文件**:
- `inspection-flask/violation_module/vio_workwear_missing.py`

**具体改动**:

1. **修改 `_add_person_to_plot()`**（第 163–176 行）：
   - 读取 `person.get("track_id")` 并追加到 plot target 列表的第 4 个元素（索引 3）
   - 原结构 `[person_target, [], confidence]` → `[person_target, [], confidence, track_id]`

2. **新增 `_filter_plot_targets_by_track()` 方法**（第 178–188 行）：
   - 接受 `triggered_track` 参数
   - 遍历 `plot_targets`，仅保留 `t[3] == triggered_track` 的条目

3. **修改 `run()` 方法**（第 90 行）：
   - 确定 `triggered_track` 后调用 `_filter_plot_targets_by_track(triggered_track)`
   - 过滤后再检查 `plot_targets` 是否为空

**兼容性注意**:
- `plot_targets` 中每个 target list 长度从 3 增加到 4
- `base.py` 中 `_extract_plot_confidence()` 读取 `target_group[2]`（索引 2），`_iter_plot_boxes()` 读取 `target[:4]` 和 `target[5]`，均不受第 4 个元素影响

---

### 变更 4: 新增 `utils/plots.py`

**修复问题**: check_log 问题 5（严重级别：高）— `utils.plots` 模块缺失

**变更原因**: `violation_module/base.py` 第 7 行 `from utils.plots import plot_one_box, plot_txt_PIL` 引用了不存在的模块，运行到证据图保存路径时会崩溃。

**涉及文件**:
- `inspection-flask/utils/plots.py`（新增）

**调用方**: `inspection-flask/violation_module/base.py`（第 191、199 行）

**函数签名与 base.py 调用对应关系**:

| base.py 调用 | plots.py 函数签名 |
|-------------|------------------|
| `plot_one_box(target[:4], vio_image, color=color, label=f"...", line_thickness=1)` | `plot_one_box(box, img, color=None, label=None, line_thickness=2)` → `None`（原地修改） |
| `plot_txt_PIL(box=[20,20], img=vio_image, label=name, color=color)` | `plot_txt_PIL(box, img, label, color=None)` → `np.ndarray`（返回新图像） |

**实现细节**:
- `plot_one_box`: 基于 cv2 绘制矩形框和英文标签，原地修改图像
- `plot_txt_PIL`: 基于 PIL 绘制中文文本标签（cv2 不支持中文渲染），返回新图像
- 中文字体查找：按优先级尝试 Windows（微软雅黑/黑体/宋体）和 Linux（文泉驿/Noto CJK）系统字体，均不可用时 fallback 到 PIL 默认字体
- 字体缓存：`_FONT_CACHE` 字典按 size 缓存已加载的字体对象，避免重复 IO

---

### 变更 5: 新增 `validate` 子命令

**修复问题**: check_log 问题 6（严重级别：中）— 缺少验证集评估

**变更原因**: 缺少工程化手段验证模型升级或阈值调整前后的检测质量变化。

**涉及文件**:
- `inspection-flask/main.py` — 新增 `cmd_validate()` 函数和 `validate` 子命令注册

**使用方式**:
```
python main.py validate <dataset_dir> [-o <output_dir>]
```

**功能**:
- 递归遍历数据集目录中的所有图片（支持 jpg/jpeg/png/bmp/webp）
- 执行完整的人员检测 + 工服检测管线
- 输出统计报告：
  - 图片总数、成功/失败数
  - 检测人数（总/有效）、合规/违规人数
  - 全合规图片数、含违规图片数、合规率
  - 各工服标签分布（label → count）
  - 总耗时、平均耗时
- 可选 `-o` 参数输出可视化标注图到指定目录

---

### 新增配置项汇总

| 配置项 | 所在文件 | 默认值 | 说明 | 引用位置 |
|--------|---------|--------|------|---------|
| `ROI_MIN_OVERLAP_RATIO` | `settings.py:72` | `0.5` | 人框与 ROI 交叠面积占人框面积的最低比例 | `hk_custom_threading_plus.py` `_in_roi()` |
| `MIN_TRACK_APPEAR_FRAMES` | `settings.py:73` | `2` | track 至少出现 N 帧才进入违规判定 | `vio_workwear_missing.py` `_load_min_track_appear()` |
| `WORKWEAR_VIOLATION_NAME` | `settings.py:77` | `"作业区人员疑似未穿工服"` | 违规规则名称（写入数据库和证据图） | `vio_workwear_missing.py` `rule_name` |

### 变更配置项汇总

| 配置项 | 旧值 | 新值 | 变更原因 |
|--------|------|------|---------|
| `WORKWEAR_VIOLATION_NAME` | `"未穿工服"` | `"作业区人员疑似未穿工服"` | 告警口径收紧，匹配 ROI 方案设计文档 |

### 新增数据结构字段汇总

| 数据结构 | 新增字段 | 说明 |
|---------|---------|------|
| `hk_frame_cache[cid]` | `frame_hash` (`bytes`) | 帧内容感知哈希，用于去重 |
| `plot_targets` 中每个 target list | 索引 3: `track_id` | 标注归属的 track_id，用于证据图过滤 |

---

### check_log 问题修复状态映射

| check_log 问题 | 修复状态 | 本次变更编号 |
|---------------|---------|------------|
| 问题 1: 静态图重复当新帧 | 已修复 | 变更 1 |
| 问题 2: 检测对象是所有 person | 部分修复（告警口径收紧 + ROI 重叠比例 + 最小停留帧数） | 变更 2a/2b/2c |
| 问题 3: 触发 track 与证据图不绑定 | 已修复 | 变更 3 |
| 问题 4: SimpleIoUTracker 局限 | 维持现状（设计评估后决定不改） | — |
| 问题 5: utils/plots.py 缺失 | 已修复 | 变更 4 |
| 问题 6: 缺少验证集评估 | 已修复 | 变更 5 |
| 问题 7: ROI 只看中心点 | 已修复 | 变更 2a |
| 问题 5（中高）: 面积过滤口径不一致 | 已修复 | 变更 2d |

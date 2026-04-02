# inspection-flask To List

更新时间：2026-03-31

---

## 更新记录

### 2026-03-31 — 完成 P1（最小 Flask 骨架）+ P2（最小数据层与路由依赖）

**目标：** 补齐 `create_app()` 的全部 import 依赖，使 Flask 应用的模块导入链路可以完整执行。

**P1 — 最小 Flask 骨架（6 个文件）：**

| 文件 | 操作 | 说明 |
|------|------|------|
| `applications/config.py` | 新建 | 从旧项目裁剪，SYSTEM_NAME 改为"加油站工服检测"，去掉警务/人脸/面板配置 |
| `applications/extensions/__init__.py` | 新建 | 最小化，只初始化 SQLAlchemy + Marshmallow，暴露 `db`, `ma`, `init_plugs` |
| `applications/extensions/init_sqlalchemy.py` | 新建 | 从旧项目复制，提供 `db`, `ma`, `init_databases()`, 自定义 `Query` 类 |
| `applications/common/flask_log.py` | 新建 | 从旧项目复制，`handle_global_exceptions(app)` |
| `applications/common/script/__init__.py` | 新建 | 空壳，当前无 CLI 命令需注册 |
| `applications/view/__init__.py` | 修改 | 实现 `init_bps(app)`，只注册 `hk_camera` 蓝图 |

**P2 — 最小数据层与路由依赖（17 个文件）：**

| 文件 | 操作 | 说明 |
|------|------|------|
| `applications/models/__init__.py` | 新建 | 导出 Photo, HKCamera, Station, ViolateRule, ViolatePhoto, DeptRelations |
| `applications/models/admin_photo.py` | 新建 | Photo 模型 |
| `applications/models/admin_hk_camera.py` | 新建 | HKCamera 模型 |
| `applications/models/admin_police_station.py` | 新建 | Station 模型（comment 已适配加油站场景） |
| `applications/models/admin_violate_rule.py` | 新建 | ViolateRule 模型 |
| `applications/models/admin_dept_relations.py` | 新建 | DeptRelations 模型 |
| `applications/schemas/__init__.py` | 新建 | 空文件 |
| `applications/schemas/admin_police_station.py` | 新建 | StationSchema |
| `applications/schemas/admin_hk_camera.py` | 新建 | HkCameraOutSchema |
| `applications/common/curd.py` | 新建 | CRUD 工具函数 |
| `applications/common/user_auth.py` | 新建 | 权限判断函数 |
| `applications/common/utils/__init__.py` | 新建 | 空文件 |
| `applications/common/utils/http.py` | 新建 | success_api, fail_api, table_api |
| `applications/common/utils/rights.py` | 新建 | authorize 装饰器（裁剪掉 admin_log 依赖） |
| `applications/common/utils/validate.py` | 新建 | str_escape（escape 改用 markupsafe） |
| `applications/common/utils/upload.py` | 新建 | 最小空壳，hk_camera.py 有 import 但当前未调用 |
| `applications/common/utils/thread_camera.py` | 新建 | 最小空壳，已被 hk_custom_threading_plus.py 替代 |

**关键适配细节：**

- `rights.py` 裁剪掉 `admin_log` 依赖，避免引入 AdminLog 警务模型
- `validate.py` 将 `from flask import escape` 改为 `from markupsafe import escape`（Flask 2.3+ 兼容）
- `extensions/__init__.py` 只初始化 SQLAlchemy + Marshmallow，不引入 login/mail/upload/migrate/session 等扩展
- `upload.py` 和 `thread_camera.py` 为空壳，仅满足 `hk_camera.py` 的 import 需要

**验证结果：** 全部 23 个文件语法检查通过（`py_compile`）

---

## 1. 当前项目目标

结合当前背景，项目目标已经明确，不再保留分叉解释：

- `inspection-flask` 的目标是：做一个 **YOLOv8 风格的加油站工人未穿戴工服检测项目**。
- `inspection-flask_old` 的角色是：提供 **旧项目已经跑通过的基础业务逻辑骨架**，用于参考和迁移。
- `inspection-flask_old` 本身是 **YOLOv5 风格下的警务检查系统**，其中很多业务场景与当前项目无关。

所以当前正确的开发原则是：

- **继承旧项目的基础流程与工程骨架**
- **不继承旧项目的警务业务目标**
- **在新项目里保留已经完成的 YOLOv8 技术改进**

一句话总结：

- `inspection-flask_old` 是“逻辑参考项目”
- `inspection-flask` 是“工服检测目标项目”

## 2. 旧项目哪些要继承，哪些不要继承

### 2.1 要继承的内容

以下内容属于“基础逻辑骨架”，应当从 `inspection-flask_old` 借鉴并在 `inspection-flask` 中补齐或重构：

- Flask 应用工厂思路
  - `app.py`
  - `applications/__init__.py`

- 海康采图线程和检测线程分层
  - `applications/common/hk_recorder_threading.py`
  - `applications/common/hk_custom_threading_plus.py`

- 摄像头启停、线程管理、定时调度
  - `applications/view/system/hk_camera.py`
  - `applications/__init__.py`

- 违规保存链路
  - `violation_module/base.py`
  - `applications/view/system/hk_camera.py:save_violate_photo()`

- 数据库存储模型与后台最小支撑层
  - `applications/models/*`
  - `applications/extensions/*`
  - `applications/common/utils/*`

### 2.2 不要继承的内容

以下内容属于旧项目的“警务场景业务能力”，不是当前 `inspection-flask` 的目标，不应作为当前阶段的主线：

- 正式民警/非正式民警识别
- 枪库人数与枪库场景规则
- 单警询问规则
- 手机/抽烟/人员聚集等警务扩展违规则
- 人脸识别链路
- 躺卧/睡岗/脱岗动作识别链路

这些内容最多保留为未来参考，不进入当前版本的开发优先级。

## 3. inspection-flask 当前真实状态

## 3.1 已经完成的部分

- `DONE` YOLOv8 双模型结构已经建立
  - `inspection-flask/settings.py`
  - `inspection-flask/utils/models.py`
  - 当前已经明确区分：
    - 人员检测模型
    - 工服检测模型

- `DONE` 工服检测统一策略已经落地
  - `inspection-flask/utils/workwear_policy.py`
  - 已统一：
    - 人框裁剪
    - 白底裁剪开关
    - 工服标签口径
    - 合规判定模式

- `DONE` 在线工服检测主线程已经建立
  - `inspection-flask/applications/common/hk_custom_threading_plus.py`
  - 已实现：
    - 从缓存取帧
    - 人员检测
    - 工服检测
    - ROI 判断
    - track_id 分配
    - 时序窗口统计
    - 告警抑制

- `DONE` 工服未穿戴规则已经重写为 YOLOv8 版本
  - `inspection-flask/violation_module/vio_workwear_missing.py`
  - 相比旧版 `vio_zsmjwcjf.py`，已经完成以下技术升级：
    - 用 `track_id` 做时序聚合
    - 引入 `MIN_TRACK_APPEAR_FRAMES`
    - 引入 `TEMPORAL_TRIGGER_RATIO`
    - 证据图只绑定触发目标

- `DONE` 违规保存链路已经保留并适配当前场景
  - `inspection-flask/violation_module/base.py`
  - `inspection-flask/applications/view/system/hk_camera.py`
  - 已具备：
    - 证据帧选择
    - 目标框绘制
    - 证据图保存
    - `admin_violate_photo` 写库字段适配

- `DONE` 离线诊断工具已经建立
  - `inspection-flask/main.py`
  - 目前已经支持：
    - `check`
    - `image`
    - `validate`

- `DONE` 采图缓存层已经加了基础去重
  - `inspection-flask/applications/common/hk_recorder_threading.py`
  - 已增加静态图重复帧去重能力

## 3.2 已经有代码，但没有真正打通的部分

- `DONE` 应用工厂依赖已补齐
  - `inspection-flask/applications/__init__.py`
  - 已写出模型初始化、线程管理、调度初始化的结构
  - P1+P2 已补齐全部 import 依赖（config, extensions, flask_log, script, view/init_bps）
  - 待数据库配置和 Flask 依赖安装后可真正启动

- `DONE` 摄像头视图层依赖已补齐
  - `inspection-flask/applications/view/system/hk_camera.py`
  - P2 已补齐全部依赖模块（models, schemas, curd, user_auth, utils）

- `PARTIAL` 离线验证口径还不够严谨
  - `inspection-flask/main.py`
  - 当前还存在已记录的问题：
    - ROI 外目标统计口径问题
    - `validate --labels` 默认参数问题

## 3.3 当前明确缺失的部分

- `DONE` Flask 基础骨架（2026-03-31 P1 补齐）
  - `inspection-flask/applications/config.py`
  - `inspection-flask/applications/extensions/__init__.py`
  - `inspection-flask/applications/common/flask_log.py`
  - `inspection-flask/applications/common/script/__init__.py`
  - `inspection-flask/applications/view/__init__.py` 已实现 `init_bps()`

- `DONE` 摄像头管理所需的最小工具层（2026-03-31 P2 补齐）
  - `inspection-flask/applications/common/curd.py`
  - `inspection-flask/applications/common/user_auth.py`
  - `inspection-flask/applications/common/utils/http.py`
  - `inspection-flask/applications/common/utils/rights.py`
  - `inspection-flask/applications/common/utils/validate.py`

- `DONE` ORM / Schema 出口层（2026-03-31 P2 补齐）
  - `inspection-flask/applications/models/__init__.py`
  - `inspection-flask/applications/schemas/admin_hk_camera.py`
  - 已导出 `HKCamera`、`Station`、`ViolateRule`、`ViolatePhoto`、`DeptRelations`、`Photo`

- `MISSING` 海康实时 SDK 链路
  - `inspection-flask/hk/hksdk/device.py` 当前是空文件
  - `inspection-flask/hk/hksdk/HCNetSDK.py`
  - `inspection-flask/hk/hksdk/header.py`
  - SDK 依赖库文件

## 4. 当前必须统一的项目判断

以后不再使用“是否全量替代旧系统”作为当前阶段的待办前提，统一按下面判断执行：

- 当前项目目标固定为：
  - **加油站工人未穿戴工服检测**

- 当前项目对旧项目的使用方式固定为：
  - **借鉴旧项目的通用流程**
  - **不追求警务业务功能对等**

这意味着：

- 旧项目的 `hk_recorder_threading.py`、`hk_custom_threading_plus.py`、`base.py`、`save_violate_photo()` 等流程值得继承
- 旧项目的 `PhoneViolation`、`SmokeViolation`、`GunRoom*`、`FaceRecognition`、`Lying_Detect` 不进入当前优先级

## 5. 现在最应该做什么

以下待办按优先级排序，必须按顺序推进。

## P0：先把项目目标和代码边界彻底固定

- [ ] 保持 `inspection-flask` 只围绕“工服未穿戴”主线开发
- [ ] 在新代码中清理或注释掉所有会误导为“还要继续恢复警务多违规则”的表述
- [ ] 后续新增文件或模块时，先判断它是否服务于“工服检测主线”

完成标准：

- `to_list.md`、后续文档、代码注释中，项目目标统一为“加油站工服检测”
- 不再把 `inspection-flask_old` 视为需要全量恢复的目标项目

## P1：补齐最小 Flask 工程骨架，让 inspection-flask 真正能启动

- [x] 从 `inspection-flask_old` 借鉴并裁剪出最小可用版 `applications/config.py`
- [x] 从 `inspection-flask_old` 借鉴并裁剪出最小可用版 `applications/extensions/__init__.py`
- [x] 补齐 `applications/common/flask_log.py`
- [x] 补齐 `applications/common/script/__init__.py`
- [x] 重写 `applications/view/__init__.py`
  - 只注册当前真正需要的蓝图
  - 当前阶段优先保留：
    - `hk_camera`
    - 违规记录相关接口

完成标准：

- `inspection-flask/app.py` 可以成功导入
- `create_app()` 可以成功执行
- Flask 应用能创建，不因为缺文件直接报错

## P2：补齐最小数据层与路由依赖，让“摄像头启停 + 违规记录”能工作

- [x] 补齐 `applications/models/__init__.py`
- [x] 至少保证以下模型可被统一导出：
  - `HKCamera`
  - `Station`
  - `ViolateRule`
  - `ViolatePhoto`
  - `DeptRelations`

- [x] 补齐 `applications/schemas/admin_hk_camera.py`

- [x] 补齐 `hk_camera.py` 依赖的最小工具层
  - `applications/common/curd.py`
  - `applications/common/user_auth.py`
  - `applications/common/utils/http.py`
  - `applications/common/utils/rights.py`
  - `applications/common/utils/validate.py`

- [ ] 检查并精简 `hk_camera.py` 中与当前项目无关的旧后台逻辑
  - 只保留对工服项目必要的部分

完成标准：

- `hk_camera` 蓝图可以注册
- 摄像头启用/禁用接口可调用
- 违规记录查询接口可调用

## P3：恢复真实海康取流，让在线链路不再依赖 frame_path 调试图

- [ ] 恢复 `inspection-flask/hk/hksdk/device.py`
- [ ] 按需迁入：
  - `inspection-flask/hk/hksdk/HCNetSDK.py`
  - `inspection-flask/hk/hksdk/header.py`
  - SDK 依赖库

- [ ] 改造 `inspection-flask/applications/common/hk_recorder_threading.py`
  - 支持生产模式：真实海康实时取流
  - 支持调试模式：`frame_path` 本地图像回放

- [ ] 明确 `frame_path` 只是调试输入，不再把它视为线上链路

完成标准：

- 单个海康摄像头可持续写入 `hk_frame_cache`
- 检测线程能够消费真实实时帧
- 掉线、重连、空帧有明确日志

## P4：修当前工服检测主线的正确性问题，形成可验证闭环

- [ ] 修复 `inspection-flask/main.py` 中 ROI 外目标仍计入统计的问题
- [ ] 修复 `inspection-flask/main.py` 中 `validate --labels` 默认参数冲突问题
- [ ] 提升 `inspection-flask/applications/common/hk_custom_threading_plus.py` 的 track 稳定性
  - 至少增加丢帧容忍
  - 避免一次漏检就重置同一人轨迹

- [ ] 评估并增强 `inspection-flask/applications/common/hk_recorder_threading.py` 的去重策略
  - 当前 8x8 哈希只能算最小修复

- [ ] 为工服规则补样例测试
  - 至少覆盖：
    - ROI 内合规
    - ROI 内违规
    - ROI 外目标
    - 同一人持续违规
    - 短暂出现不触发
    - 告警抑制窗口

完成标准：

- 离线结果与在线规则说明一致
- 同一组样例重复运行结果稳定
- 能给出可信的工服检测验证结论

## P5：最后再做工程清理和部署前整理

- [ ] 清理当前残留的旧警务场景注释和误导性 import
- [ ] 检查 `settings.py` 中是否还有旧项目遗留配置名
- [ ] 给当前项目补最小运行说明
  - 环境依赖
  - 权重路径
  - 调试模式
  - 在线模式

完成标准：

- 新人只看 `inspection-flask` 就能知道这是“工服检测项目”
- 不会再误解成“警务 YOLOv5 系统全量迁移版”

## 6. 现在不应该做什么

当前阶段明确不进入主线的工作：

- [ ] 不优先恢复 `PhoneViolation`
- [ ] 不优先恢复 `SmokeViolation`
- [ ] 不优先恢复 `Crowd_Detect_Violation`
- [ ] 不优先恢复 `GunRoom*`
- [ ] 不优先恢复 `FaceRecognition`
- [ ] 不优先恢复 `Lying_Detect`
- [ ] 不优先恢复旧版姿态估计链

原因不是这些永远不做，而是：

- 它们不属于当前工服项目主目标
- 它们会把当前项目重新拉回旧警务系统方向
- 在 Flask 骨架和海康实时链路未打通前，做这些没有收益

## 7. 建议的实际开发顺序

按下面顺序推进，不要跳步：

1. 先补最小 Flask 骨架。
2. 再补最小模型出口、Schema 和工具层。
3. 再打通 `hk_camera` 路由与线程启停。
4. 再恢复海康实时取流。
5. 再修工服主线的统计与 tracker 问题。
6. 最后补验证、清理文档、准备部署。

## 8. 更新约束条件

每次更新 `to_list.md` 时必须遵循以下规则：

- 更新记录统一写在"更新记录"区域，**历史在后，最新在前**
- 每条更新记录必须包含：日期、完成了什么、修改/新建了哪些文件、关键适配细节
- 已完成的 checklist 项必须标记为 `[x]`
- "当前真实状态"（第 3 节）必须同步更新，将已补齐的 MISSING/PARTIAL 改为 DONE
- 不允许删除历史更新记录

## 9. 后续迭代约束

## 9.1 目标约束

- 以后任何新增代码，必须首先回答一个问题：
  - 它是否直接服务于“加油站工人未穿戴工服检测”？

- 如果答案是否定的：
  - 默认不进入当前迭代

## 9.2 旧项目使用约束

- `inspection-flask_old` 只能作为以下两类参考：
  - 工程结构参考
  - 通用流程参考

- 不允许直接因为旧项目里有某个模块，就默认把它列入当前待办。

## 9.3 数据结构约束

- 当前主链路统一使用 `person_context` 风格的数据结构。
- 不要为了“兼容旧逻辑”重新退回旧版列表式 `target` 作为核心结构。
- 如果必须兼容旧结构，必须额外写适配层，不能污染主链路。

## 9.4 规则口径约束

- 工服合规判断只能统一走：
  - `inspection-flask/utils/workwear_policy.py`

- 不允许在：
  - `main.py`
  - `hk_custom_threading_plus.py`
  - `vio_workwear_missing.py`
  中各写一套不同口径。

## 9.5 海康链路约束

- `frame_path` 只允许作为调试模式输入。
- 一旦进入在线模式，必须使用真实海康流或等价真实视频流输入。

## 9.6 文档维护约束

- 每次完成一轮代码修改后，至少同步检查：
  - `docs/to_list.md`
  - `docs/update_log.md`
  - `docs/check_log.md`

- 文档必须保持“当前项目目标明确，不漂移”。

## 10. 当前结论

当前最应该完成的代码，不是继续恢复旧警务项目的各种违规模块，而是以下三部分：

- 第一部分：补齐 `inspection-flask` 最小 Flask 骨架
- 第二部分：补齐海康实时取流链路
- 第三部分：把当前工服 YOLOv8 主线修到可验证、可运行、可部署

也就是说，接下来应该做的是：

- **用 `inspection-flask_old` 的基础流程把 `inspection-flask` 的工程骨架补齐**
- **保留 `inspection-flask` 已经完成的 YOLOv8 工服检测改进**
- **明确不再以“恢复旧警务系统全部业务”为当前阶段目标**

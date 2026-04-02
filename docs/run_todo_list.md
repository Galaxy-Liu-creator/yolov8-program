# inspection-flask 运行落地 TODO 清单

更新时间：2026-04-02

---

## 1. 文档目的

本清单用于把当前 `inspection-flask` 项目“还不能真正跑通”的核心问题、原因、解决方案和推荐执行顺序整理成一份明确的落地文档。

适用范围：

- 当前项目：`inspection-flask`
- 参考项目：`inspection-flask_old`

本文档的目标不是恢复旧警务项目的全部业务，而是：

- 继承 `inspection-flask_old` 的工程骨架与运行逻辑
- 完成 `inspection-flask` 的 **YOLOv8 加油站工服检测项目**
- 让项目达到“可安装、可启动、可取流、可检测、可告警、可存证、可验证”的最小可运行状态

---

## 2. 当前项目定位

### 2.1 当前目标

- `inspection-flask` 的目标已经明确为：**加油站工人未穿戴工服检测**
- 当前主链路已经收敛为：
  - 整帧人员检测
  - 人框裁剪
  - 工服二阶段检测
  - IoU 跟踪
  - 时间窗违规判定
  - 证据图保存与写库

### 2.2 旧项目的正确使用方式

- `inspection-flask_old` 是：
  - 已跑通过的 YOLOv5 警务项目
  - 当前项目的**逻辑参考仓库**
- 应继承的内容：
  - Flask 应用工厂思路
  - 海康采图线程与检测线程分层
  - 摄像头启停与定时调度
  - 违规保存链路
  - 数据层与后台最小支撑层
- 不应作为当前主线恢复的内容：
  - 人脸识别
  - 枪库相关规则
  - 单警询问
  - 手机/抽烟/聚集等旧警务规则
  - 躺卧/睡岗/脱岗链路

一句话总结：

- `inspection-flask_old` 提供 **工程骨架**
- `inspection-flask` 承担 **工服检测落地**

---

## 3. 当前已完成的部分

以下内容已经具备较清晰的代码基础，不属于“从零开始”：

- 已完成 YOLOv8 双模型配置与加载封装
  - `inspection-flask/settings.py`
  - `inspection-flask/utils/models.py`

- 已完成工服检测共享策略
  - `inspection-flask/utils/workwear_policy.py`

- 已完成在线检测线程主链
  - `inspection-flask/applications/common/hk_custom_threading_plus.py`

- 已完成工服未穿戴规则引擎
  - `inspection-flask/violation_module/vio_workwear_missing.py`

- 已完成证据图保存与写库主链
  - `inspection-flask/violation_module/base.py`
  - `inspection-flask/applications/view/system/hk_camera.py`

- 已完成离线命令行诊断工具
  - `inspection-flask/main.py`
  - 当前支持：
    - `check`
    - `image`
    - `validate`

这说明当前项目的主要问题已经不是“没有主链”，而是“主链的运行资源和工程闭环还没有补齐”。

### 3.1 2026-04-02 当前新增落地状态

- `DONE` 当前项目已经新增依赖元数据文件
  - `inspection-flask/pyproject.toml`

- `PARTIAL` 应用已支持软降级启动
  - 数据库连接失败时默认不再直接退出
  - 无数据库时跳过后台 scheduler
  - 这意味着应用更容易“先启动起来”，但不代表数据库链已经闭环

- `PARTIAL` 最小后台已具备兼容运行能力
  - 鉴权默认可绕过旧登录体系
  - 页面模板已补齐最小占位版本
  - `hk_camera` 已支持健康检查与无数据库运行时启停

- `PARTIAL` 采图链已具备最小兼容输入源
  - 当前已支持：
    - 单图
    - 图集目录
    - 本地视频
    - `stream_url`
    - RTSP fallback
  - 但这不是“海康原生 SDK 完整恢复”

---

## 4. 当前阻塞问题与对应解决方案

## 问题 1：运行环境依赖未安装

### 现象

- `main.py check` 会因为缺少 `cv2` 无法执行
- `create_app()` 会因为缺少 `apscheduler` 无法执行
- 当前项目也依赖 Flask、SQLAlchemy、Torch、Ultralytics、PostgreSQL 驱动等基础包

### 根因

- 仓库中尚未提供可直接复用的当前项目依赖清单
- 当前环境没有完成最小运行环境安装

### 解决方案

- 新增并维护当前项目专用依赖清单，例如：
  - `inspection-flask/requirements.txt`
  - 或 `pyproject.toml`
- 至少补齐以下运行依赖：
  - `flask`
  - `flask-cors`
  - `apscheduler`
  - `opencv-python`
  - `torch`
  - `ultralytics`
  - `flask-sqlalchemy`
  - `marshmallow`
  - `psycopg2` 或 `psycopg2-binary`
  - 若保留登录鉴权，还需补：
    - `flask-login`
    - `validators`

### 推荐安装命令（Windows / PowerShell）

- 在仓库根目录执行：
  - `cd inspection-flask`
  - `python -m venv .venv`
  - `.\.venv\Scripts\activate`
  - `python -m pip install --upgrade pip`
  - `pip install -e .`

### 安装后最小验证命令

- 依赖安装完成后，至少执行：
  - `python main.py check`
  - `python -c "from applications import create_app; app = create_app(); print({'database_ready': app.config.get('database_ready'), 'database_init_error': app.config.get('database_init_error')})"`
- 若只想先验证路由与最小后台链路，可继续检查：
  - `python -c "from applications import create_app; app = create_app(); print(app.url_map)"`

### 完成标准

- 在 `inspection-flask` 目录中执行：
  - `python main.py check`
- 不再出现基础依赖缺失错误
- 执行：
  - `from applications import create_app`
- 不再因基础包缺失失败

---

## 问题 2：YOLOv8 权重文件未落地

### 现象

- `settings.py` 已经定义了：
  - 人员检测权重
  - 工服检测权重
- 但当前仓库没有 `inspection-flask/weights` 目录

### 根因

- 模型接入代码已写好，但权重资源尚未进入当前项目目录

### 解决方案

- 创建目录：
  - `inspection-flask/weights`
- 至少放入两套权重：
  - `person_detect_yolov8.pt`
  - `workwear_detect_yolov8.pt`
- 同时核对以下配置是否与真实模型严格一致：
  - `YOLO_FAMILY`
  - `PERSON_WEIGHT`
  - `WORKWEAR_WEIGHT`
  - `MONITORED_PERSON_LABELS`
  - `WORKWEAR_LABELS`
  - `WORKWEAR_REQUIRED_LABELS`
  - `PERSON_CONF`
  - `WORKWEAR_CONF`

### 完成标准

- `python main.py check` 能成功加载两套模型
- 控制台能输出正确的模型路径、设备和类别信息
- 类别名与当前数据集约定一致：
  - 人员侧为 `person`
  - 工服侧为 `clothes`

---

## 问题 3：真实海康取流链路未恢复

### 现象

- 当前 `hk_recorder_threading.py` 只会优先读取 `frame_path` 指向的本地图片
- 当前 `inspection-flask/hk/hksdk/device.py` 是空文件
- 当前项目还没有恢复 `HCNetSDK.py`、`header.py` 和相关 SDK 依赖

### 根因

- 当前在线主链已经写好，但采图层仍停留在“本地图调试模式”
- 真实海康 SDK 取流逻辑还没有从旧项目迁回

### 解决方案

- 从 `inspection-flask_old` 迁移或裁剪恢复以下内容：
  - `inspection-flask_old/hk/hksdk/device.py`
  - `inspection-flask_old/hk/hksdk/HCNetSDK.py`
  - `inspection-flask_old/hk/hksdk/header.py`
- 改造：
  - `inspection-flask/applications/common/hk_recorder_threading.py`

推荐改造原则：

- 生产模式：
  - 优先走真实海康 SDK 取流
- 调试模式：
  - `frame_path` 仅作为本地图回放输入
- 不再把 `frame_path` 视为线上正式链路

### 当前落地状态

- 已补：
  - `inspection-flask/hk/hksdk/device.py` 的最小兼容实现
  - `inspection-flask/applications/common/hk_recorder_threading.py` 对单图 / 图集目录 / 本地视频 / `stream_url` / RTSP fallback 的支持
- 当前仍未完成：
  - 原生 `HCNetSDK.py`
  - 原生 `header.py`
  - SDK 动态库接回
  - 真实海康原生 SDK 完整闭环

### 完成标准

- 单路海康摄像头能持续写入 `hk_frame_cache`
- 帧缓存不是一次性静态图，而是持续更新
- 掉线、空帧、重连失败有明确日志

---

## 问题 4：相机模型与运行时字段可能未对齐

### 现象

- 当前启用摄像头时，线程会使用：
  - `roi`
  - `frame_path`
- 但当前 `HKCamera` 模型主要能确认的字段是：
  - `ip`
  - `port`
  - `username`
  - `password`
  - `channel`

### 根因

- 运行时对象和数据库模型之间的字段闭环可能还没补齐
- 即使逻辑层想用 `roi` / `frame_path`，数据库侧也未必能持久化

### 解决方案

- 检查并补齐 `HKCamera` 模型中与当前项目主链相关的字段
- 建议至少补齐：
  - `roi`
  - 若保留调试模式，则补：
    - `frame_path`
- 同步检查以下链路是否字段一致：
  - 数据库模型
  - Schema
  - 后台表单保存
  - 摄像头启用接口
  - 检测线程读取逻辑

### 当前落地状态

- 已补运行时字段兼容：
  - `inspection-flask/applications/view/system/hk_camera.py`
  - `inspection-flask/applications/common/hk_custom_threading_plus.py`
  - `inspection-flask/applications/common/hk_recorder_threading.py`
- 当前 `roi` / `frame_path` / `stream_url` 已可通过运行时参数传入，并由
  - `camera_runtime_overrides`
  统一缓存后传递给线程与采图链路
- 当前**没有**直接改动 `HKCamera` 数据表结构：
  - 这是有意保守处理，避免在未做正式迁移前破坏现有数据库
- 因此问题 4 当前状态是：
  - `PARTIAL` 运行时字段链路已打通
  - `MISSING` 正式持久化字段迁移与表结构闭环仍待完成

### 完成标准

- 后台保存摄像头后，`roi` 能稳定落库并被线程读到
- 调试模式下，`frame_path` 能稳定落库并被采图线程使用
- 字段命名在模型、接口、线程中保持一致

---

## 问题 5：数据库仍是运行硬前提

### 现象

- 当前项目使用 SQLAlchemy 扩展
- 初始化数据库失败时，应用无法继续启动
- 存证、摄像头管理、违规记录查询都依赖数据库表

### 根因

- 当前项目已经不是纯推理脚本，而是带管理后台和告警落库能力的应用

### 解决方案

- 准备 PostgreSQL 运行环境
- 确认数据库配置有效
- 至少准备以下表及对应基础数据：
  - 摄像头表
  - 违规图片表
  - 违规则表
  - 站点表
  - 部门关系表

如果当前阶段只想先跑检测链而不想先上完整后台，可以考虑两步走：

- 第一步：
  - 先让 `main.py` 离线工具和最小检测链跑通
- 第二步：
  - 再打通 Web + DB + 摄像头后台链路

### 当前落地状态

- 已补软降级能力：
  - 数据库失败时应用不再默认直接退出
  - 会记录 `database_ready` / `database_init_error`
  - 数据库未就绪时跳过后台 scheduler
  - 违规事件可回退到内存队列
- 当前仍未完成：
  - PostgreSQL 正式落地
  - 真实表结构验证
  - 正式环境下的完整写库闭环

### 完成标准

- `create_app()` 可以成功初始化数据库扩展
- 摄像头列表、启停、违规记录查询接口可正常访问
- 证据图写入后能生成数据库记录

---

## 问题 6：当前后台是“最小骨架”，不是“完整后台”

### 现象

- 当前项目已经有最小 Flask 工程结构
- 但并不等于已经恢复成旧项目那种完整后台系统

### 根因

- 当前阶段主要完成了最小骨架和工服主链
- 登录、权限、模板、完整页面能力未必全部恢复到旧项目水平

### 解决方案

先明确你的目标是哪一种：

#### 路线 A：只要最小可运行检测系统

- 优先级放在：
  - 采图
  - 检测
  - 告警
  - 存证
  - 查询接口
- 可以暂时不追求旧项目那套完整后台管理体验

#### 路线 B：要接近旧项目的后台可用程度

- 则需要进一步补：
  - 登录/用户/角色链
  - 完整模板页面
  - 会话与权限逻辑
- 更完善的后台管理功能

### 当前落地状态

- 已补：
  - 最小模板
  - 模板缺失时 JSON 降级
  - 健康检查接口
  - 无数据库模式下的运行时摄像头启停与违规事件查询
- 当前仍不是：
  - 旧项目级别的完整后台
  - 完整登录/角色/菜单/权限系统

### 完成标准

- 路线 A：
  - 后端接口和检测链稳定可用
- 路线 B：
  - 后台页面、权限、相机管理、违规查看都能形成完整使用闭环

---

## 问题 7：离线工具已具备，但不能替代在线验收

### 现象

- 当前已经有：
  - `check`
  - `image`
  - `validate`
- 但离线模式本身不包含完整的在线链路

### 根因

- 离线工具更适合做：
  - 模型加载验证
  - 数据集回归
  - 参数调试
- 在线告警还依赖：
  - 帧缓存
  - track
  - 时间窗
  - 告警抑制
  - 落库与证据图保存

### 解决方案

- 明确把离线工具作为“回归与调试工具”
- 不把 `validate` 输出直接当成线上验收结论
- 在线验收必须新增“单摄像头真实链路验证”

### 完成标准

- 离线工具用于模型回归
- 在线链路单独验收：
  - 抓图
  - 检测
  - 规则
  - 存图
  - 写库

---

## 问题 8：当前规则存在业务语义前提，需明确接受或后续增强

### 现象

- 当前系统的真实业务语义是：
  - **ROI 内 `person` 未检出 `clothes`，则判定为疑似未穿工服**
- 这并不天然等价于：
  - “一定是工人未穿工服”

### 根因

- 当前一级检测是 `person`
- 当前没有独立“员工/顾客/访客”分类模型
- 业务成立依赖前提：
  - ROI 尽量只覆盖作业区
  - ROI 内出现的人基本就是员工

### 解决方案

短期方案：

- 继续维持当前业务前提
- 通过合理配置 ROI 来控制误报来源
- 先把项目跑通

中期方案：

- 采集更贴近现场的验证集
- 校准以下参数：
  - `ROI_MIN_OVERLAP_RATIO`
  - `MIN_TRACK_APPEAR_FRAMES`
  - `TEMPORAL_WINDOW_SIZE`
  - `TEMPORAL_TRIGGER_RATIO`
  - `PERSON_CONF`
  - `WORKWEAR_CONF`

长期增强方向：

- 若业务确实需要区分“员工 vs 非员工”，再考虑：
  - 引入额外分类模型
  - 引入更强的场景/身份筛选策略

### 完成标准

- 当前阶段：
  - 误报水平在业务可接受范围内
- 后续阶段：
  - 形成更严格的员工识别前置条件

---

## 5. 推荐执行顺序

以下顺序建议严格执行，不要跳步：

### P1：先补运行环境

- [ ] 补依赖清单
- [ ] 安装运行依赖
- [ ] 验证 `python main.py check`
- [ ] 验证 `from applications import create_app`

### P2：补权重与配置一致性

- [ ] 创建 `inspection-flask/weights`
- [ ] 放入两套 YOLOv8 权重
- [ ] 核对类别名与 `settings.py` 一致
- [ ] 跑通模型加载检查

### P3：恢复真实海康取流

- [ ] 恢复 `hk/hksdk` 相关文件
- [ ] 迁回真实海康取流逻辑
- [ ] 保留 `frame_path` 作为调试 fallback
- [ ] 验证单摄像头持续出帧

### P4：补齐相机字段与数据闭环

- [ ] 检查 `HKCamera` 模型字段
- [ ] 补齐 `roi`
- [ ] 如有需要补齐 `frame_path`
- [ ] 打通模型、接口、Schema、线程之间的字段一致性

### P5：补数据库与基础数据

- [ ] 准备 PostgreSQL
- [ ] 建好所需核心表
- [ ] 准备至少一条可用摄像头数据
- [ ] 准备违规则基础数据

### P6：打通单摄像头在线闭环

- [ ] 抓图成功
- [ ] 缓存有新帧
- [ ] 检测线程取到帧
- [ ] 工服规则成功触发或稳定不触发
- [ ] 证据图保存成功
- [ ] 数据库记录生成成功

### P7：再做参数校准与稳定性验证

- [ ] 校准 `PERSON_CONF`
- [ ] 校准 `WORKWEAR_CONF`
- [ ] 校准 `ROI_MIN_OVERLAP_RATIO`
- [ ] 校准 `MIN_TRACK_APPEAR_FRAMES`
- [ ] 校准 `TEMPORAL_WINDOW_SIZE`
- [ ] 校准 `TEMPORAL_TRIGGER_RATIO`
- [ ] 验证重复运行结果稳定

---

## 6. 最小验收标准

当以下条件全部满足时，可以认为当前项目已经达到“最小可运行”：

- [ ] 依赖安装完成
- [ ] YOLOv8 权重能正常加载
- [ ] Flask 应用能启动
- [ ] 数据库连接正常
- [ ] 单路海康摄像头能持续供帧
- [ ] 检测线程能稳定处理帧
- [ ] 规则引擎能稳定工作
- [ ] 证据图能落盘
- [ ] 违规记录能写库
- [ ] 能通过接口或后台查询到违规结果

---

## 7. 当前阶段不建议做的事

在下面这些前置条件没完成前，不建议把时间投入到旧警务能力恢复上：

- [ ] 不优先恢复人脸识别链
- [ ] 不优先恢复枪库规则
- [ ] 不优先恢复单警询问规则
- [ ] 不优先恢复手机/抽烟/聚集规则
- [ ] 不优先恢复躺卧/睡岗/脱岗链
- [ ] 不优先恢复旧版姿态估计大链路

原因：

- 它们不属于当前工服项目的主目标
- 会显著拉大工程范围
- 会稀释“先把工服项目跑通”这一当前最高优先级目标

---

## 8. 一句话执行策略

当前最正确的落地策略不是：

- “把 `inspection-flask_old` 全部搬回来”

而是：

- **先用 `inspection-flask_old` 的工程逻辑补齐 `inspection-flask` 的运行闭环，再围绕工服检测主线完成上线前验证**


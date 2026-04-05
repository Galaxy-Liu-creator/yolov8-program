# inspection-flask 生产落地改造清单

## 文档定位

本文用于把当前讨论得到的推荐链路，拆成可执行的改造任务清单，供后续逐项实施、验收和回归。

本文默认对应的推荐链路为：

`person -> track_id -> ROI / area / stay filtering -> candidate worker -> workwear detection -> track-level temporal verification -> alarm`

说明：

- 这里的 `candidate worker` 在当前阶段表示“候选作业人员 / 需工服检查的目标”，不是最终意义上的真实工人身份识别。
- 当后续具备可靠的 worker/customer 数据和模型后，可将该模块升级为真实身份判断模块。

---

## 一、目标确认清单

- [ ] 统一生产目标表述为“加油站工人未穿戴工服检测”
- [ ] 统一当前阶段表述为“作业区候选作业人员工服合规检测”
- [ ] 统一告警文案与数据库规则名，避免把代理实现写成已完成工人身份识别
- [ ] 统一文档、代码注释、前端提示、日志文案中的核心术语

验收标准：

- 对外目标表述与当前实现表述分开
- 当前版本不再把“进入 ROI”直接等价写成“已识别员工”

---

## 二、链路重构清单

### 2.1 拆分当前 `build_person_contexts`

目标：

- 将当前“面积过滤 + ROI 判断 + 工服检测”的混合逻辑拆成更清晰的分阶段处理

建议改造：

- [ ] 从 `inspection-flask/applications/common/hk_custom_threading_plus.py` 中拆出“基础人目标上下文构建”
- [ ] 基础上下文阶段仅保留：
  - `bbox`
  - `confidence`
  - `label`
  - `area`
  - `track_id` 之前可用的基础字段
- [ ] 将 ROI / area / stay / candidate-worker 判断与工服检测解耦

验收标准：

- 基础人目标构建函数不再同时负责所有业务判断
- 各阶段职责明确，可单独调试

### 2.2 提前 `track_id`

目标：

- 把跨帧主体管理前置，避免后续业务状态都依赖单帧结果

建议改造：

- [ ] 在 `person` 检测之后、重业务判断之前完成 `track_id` 分配
- [ ] 保证后续 ROI、停留、工服、告警都可以按 track 聚合

验收标准：

- 当前帧中的业务判断结果均可回溯到稳定 `track_id`

### 2.3 引入 `candidate worker` 中间状态

目标：

- 在当前阶段用规则形成“候选作业人员”状态，为工服检测做更准确的输入筛选

建议改造：

- [ ] 在 person context 中新增候选状态字段，例如：
  - `candidate_worker`
  - `candidate_reason`
  - `stay_frames`
  - `roi_overlap_ratio`
- [ ] 候选判断至少考虑：
  - ROI
  - 面积阈值
  - 连续出现帧数
  - 最短停留时间 / 出现帧数

验收标准：

- 当前代码可区分：
  - 仅仅被检测到的人
  - 候选作业人员
  - 进入最终工服检查的人

### 2.4 工服检测后移

目标：

- 只对“有效且稳定的候选目标”执行工服检测，减少无意义推理

建议改造：

- [ ] 工服检测只对 `candidate_worker=True` 的 track 触发
- [ ] 明确记录“未进入工服检测”的原因，便于调试

验收标准：

- ROI 外、面积过小、短暂掠过目标不再大量触发工服推理

### 2.5 保留工服时序融合

目标：

- 不因后移工服检测而丢失“按 track 做时序确认”的稳定性

建议改造：

- [ ] 保留当前 `track-level temporal rule`
- [ ] 将“候选作业人员时序”和“工服缺失时序”分层处理
- [ ] 最终告警仍由 track 级时间窗触发，而不是单帧触发

验收标准：

- 单帧漏检、遮挡、背身、转身不会立即触发最终告警

---

## 三、数据结构改造清单

目标：

- 让 person context 可以承载“当前人目标、候选状态、工服状态、时序状态”

建议字段：

- [ ] `track_id`
- [ ] `area`
- [ ] `in_roi`
- [ ] `roi_overlap_ratio`
- [ ] `stay_frames`
- [ ] `candidate_worker`
- [ ] `candidate_reason`
- [ ] `workwear_items`
- [ ] `has_workwear`
- [ ] `workwear_checked`

验收标准：

- 任一目标在日志、调试输出、证据保存前，均可解释“为什么被纳入 / 排除”

---

## 四、规则引擎改造清单

目标：

- 将当前“ROI 内人员未检出工服”的规则，升级成“候选作业人员未检出工服”的规则

建议改造：

- [ ] 在 `inspection-flask/violation_module/vio_workwear_missing.py` 中增加对 `candidate_worker` 的检查
- [ ] 将 `appear` 与 `violation` 统计建立在“有效候选 track”上
- [ ] 保持证据图只标注真正触发的目标

验收标准：

- 最终触发对象是“已进入候选作业人员阶段且满足工服缺失时序条件的 track”

---

## 五、配置项清单

目标：

- 将新链路中的关键阈值显式配置化

建议新增配置：

- [ ] `MIN_CANDIDATE_STAY_FRAMES`
- [ ] `MIN_CANDIDATE_STAY_SECONDS`
- [ ] `CANDIDATE_ROI_MIN_OVERLAP_RATIO`
- [ ] `ENABLE_CANDIDATE_WORKER_STAGE`
- [ ] `WORKWEAR_CHECK_ONLY_FOR_CANDIDATES`

建议复用配置：

- [ ] `ROI_MIN_OVERLAP_RATIO`
- [ ] `MIN_PERSON_BOX_AREA`
- [ ] `MIN_TRACK_APPEAR_FRAMES`
- [ ] `TEMPORAL_WINDOW_SIZE`
- [ ] `TEMPORAL_TRIGGER_RATIO`

验收标准：

- 所有关键策略都可通过配置调整，而不是散落在硬编码逻辑里

---

## 六、日志、告警与证据清单

目标：

- 让线上调试时能看清每一步发生了什么

建议改造：

- [ ] 日志里输出目标从 `person` 到 `candidate_worker` 的流转情况
- [ ] 区分“未进入候选阶段”与“进入候选但未穿工服”的日志
- [ ] 证据图与落库文案保持和当前真实能力一致

建议当前阶段告警文案：

- [ ] `作业区候选作业人员疑似未穿工服`
- [ ] 或 `作业区目标疑似未按要求穿戴工服`

验收标准：

- 运营、调试、算法回溯时能区分：
  - 规则没进
  - 候选没进
  - 工服没检出
  - 时序没达标
  - 最终报警

---

## 七、离线验证清单

目标：

- 在不直接依赖在线摄像头的情况下先验证链路重排是否合理

建议改造：

- [ ] 为 `inspection-flask/main.py` 的离线验证补充 candidate-worker 阶段模拟
- [ ] 输出每张图中：
  - 总 person 数
  - 通过 area / ROI 数
  - 进入 candidate-worker 数
  - 被执行工服检测数
  - 最终疑似违规数

验收标准：

- 离线图像模式可以复盘链路中的每一步，而不只是最终结果

---

## 八、生产联调清单

目标：

- 在真实摄像头环境中验证新链路而不是只做离线推理

需要验证：

- [ ] 白天 / 夜间
- [ ] 背光 / 遮挡
- [ ] 顾客短暂进入 ROI
- [ ] 员工转身 / 背身 / 弯腰
- [ ] 多人同时出现
- [ ] ROI 边界附近穿越

关键统计：

- [ ] 顾客误报率
- [ ] 员工违规漏报率
- [ ] 候选阶段拦截比例
- [ ] 工服检测实际触发次数
- [ ] 单路摄像头推理耗时

---

## 九、升级到真实工人识别的准备清单

目标：

- 为后续真正进入“工人身份判断 + 工服检测”做好数据与接口准备

建议准备：

- [ ] 收集 worker/customer 标注样本
- [ ] 收集顾客误入 ROI 的误报样本
- [ ] 收集复杂姿态、遮挡、低清晰度员工样本
- [ ] 预留 `worker_score` / `identity_source` 字段
- [ ] 将 candidate-worker 规则接口设计成未来可替换为模型输出

验收标准：

- 将来新增 worker/customer 模型时，不需要重写整条告警链路

---

## 十、推荐实施顺序

### 第 1 批

- [ ] 统一术语和文档
- [ ] 提前 `track_id`
- [ ] 拆分基础 person context

### 第 2 批

- [ ] 增加 `candidate worker` 中间状态
- [ ] 后移工服检测
- [ ] 保留 track 级时序告警

### 第 3 批

- [ ] 补充离线验证
- [ ] 加强日志与证据输出
- [ ] 真实摄像头联调

### 第 4 批

- [ ] 收集 worker/customer 数据
- [ ] 升级真实身份判断模块

---

## 十一、当前最值得先改的代码位置

- `inspection-flask/applications/common/hk_custom_threading_plus.py`
- `inspection-flask/violation_module/vio_workwear_missing.py`
- `inspection-flask/settings.py`
- `inspection-flask/main.py`
- `inspection-flask/applications/view/system/hk_camera.py`

---

## 十二、当前结论

当前最合理的实施策略不是一步到位声称“已识别工人”，而是：

1. 先把 `candidate worker` 中间层补出来
2. 再把工服检测挂到候选 track 上
3. 保留 `track-level temporal rule`
4. 最后通过样本积累逐步升级到真实工人身份识别

这条路线更符合：

- 真实生产目标
- 当前代码基础
- 后续可演进性


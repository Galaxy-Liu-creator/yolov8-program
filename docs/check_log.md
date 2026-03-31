# Check Log

## 2026-03-31 `inspection-flask` 单正类标注前提补充复检修正记录

本次基于"基于 `clothes` 单正类标注前提的补充复检记录"提出的 6 个问题，逐一核实后处理。

### 已修复项

#### 补充复检 问题 1 — validate --labels 的 GT 逻辑与 clothes 单正类标注不兼容

状态：**已修复**

修改文件：`main.py` `_load_ground_truth()`、argparse 定义、P/R/F1 评估逻辑

修正内容：
- 新增 `--gt-mode` 参数，支持 `paired`（默认，person+clothes 两类标注）和 `clothes-only`（仅 clothes 正类标注）。
- `clothes-only` 模式下只读取 clothes 框数量作为 gt_compliant，不依赖 person 标注。
- P/R/F1 评估改为评估合规检出匹配度，输出标题标注 `[clothes-only 模式: 仅评估合规检出率，无法评估违规检出]`。

#### 补充复检 问题 5 — 在线时序窗口时间尺度不稳定

状态：**已补充日志**

修改文件：`hk_custom_threading_plus.py` `emit_event()` 及新增 `_compute_window_span()`

修正内容：
- 告警触发时计算窗口首尾帧时间差，在日志中输出窗口跨度（如"窗口跨度 440s（5帧）"）。
- 帮助现场调参人员直观理解窗口实际覆盖的真实时间。

#### 补充复检 问题 6 — 递归数据集可视化输出覆盖同名图片

状态：**已修复**

修改文件：`main.py` `_process_single_image()`

修正内容：
- 新增 `base_dir` 参数，传入后可视化输出路径保留相对目录结构。
- `cmd_validate()` 调用时传入 `dataset_dir` 作为 base_dir，避免子目录同名图片覆盖。

### 不做代码改动的问题

| 问题 | 处理 |
|---|---|
| 问题 2 — 监管对象是 person 非工人 | ROI = 作业区，区内 person 默认为员工是合理的业务假设；无工人分类模型，代码层面无法区分 |
| 问题 3 — 违规判定对正类召回敏感 | 单正类模式的内在结构，规则名已含"疑似"限定（`WORKWEAR_VIOLATION_NAME = "作业区人员疑似未穿工服"`） |
| 问题 4 — 离线/在线口径差异 | main.py 顶部 docstring 及 `_OFFLINE_NOTE` 已充分说明离线模式局限性 |

---

## 2026-03-31 `inspection-flask` 基于 `clothes` 单正类标注前提的补充复检记录

变更来源：
- 用户补充数据集前提：当前数据集**没有工人/顾客分类**，且**只对正常穿戴工服的工人标注 `clothes` 正类**。
- 复检依据：
  - [check_log.md](check_log.md)
  - [update_log.md](update_log.md)
  - [Analysis_For_yolov8.md](Analysis_For_yolov8.md)

本轮复检范围
- `inspection-flask/main.py`
- `inspection-flask/settings.py`
- `inspection-flask/utils/models.py`
- `inspection-flask/utils/workwear_policy.py`
- `inspection-flask/applications/common/hk_custom_threading_plus.py`
- `inspection-flask/applications/common/hk_recorder_threading.py`
- `inspection-flask/violation_module/vio_workwear_missing.py`
- `inspection-flask/applications/__init__.py`

本轮前提修正
- 之前关于“`clothes` 只是普通衣物标签、不能代表工服”的判断，在当前数据集前提下**不成立**。
- 当前代码里 `WORKWEAR_LABELS = ["clothes"]` 与你的数据集标注口径是一致的。
- 但在这个前提下，代码仍然存在“真值格式不匹配、在线监管对象过宽、违规判定过度依赖正类召回、离线/在线口径不一致、时序窗口时间语义不稳”等问题。

本轮先确认
- `python -m compileall inspection-flask` 通过，本轮未发现新的语法错误。
- 本轮仅补充复检记录，**未改动任何代码文件**。

### 问题 1

标题：`validate --labels` 的真值读取逻辑与当前 `clothes` 单正类标注格式不兼容

定位文件
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L358)
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L400)
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L488)
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L530)

问题说明
- 当前 `_load_ground_truth()` 的标注口径是：同时读取 `person` 框和 `clothes` 框，再通过“person 与 clothes 是否相交”推导真值合规/违规人数。
- 但你现在补充的真实数据前提是：数据集**只有正常穿戴工服的工人正类 `clothes` 标注**，并没有 `person` 标注，也没有“未穿工服”负类标注。
- 在这种前提下，`gt_total / gt_compliant / gt_violation` 的定义基础已经不存在；继续沿用当前 GT 读取逻辑，得到的真值统计天然失真。
- 后面的 `tp / fp / fn` 又继续使用 `pred_violations` 与 `gt_violation` 做数量对账，进一步放大了这个问题。

影响
- 当前 `validate --labels` 不能正确评估这套 `clothes` 单正类数据集，输出的 Precision / Recall / F1 不具备可靠业务意义。
- 如果后续继续把这组指标当成“未穿工服检测准确率”使用，会误导模型选择和阈值调参。

### 问题 2

标题：在线主链路监管对象仍然是 ROI 内所有 `person`，不是“已知工人”

定位文件
- [settings.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/settings.py#L45)
- [models.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/utils/models.py#L95)
- [hk_custom_threading_plus.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_custom_threading_plus.py#L186)
- [vio_workwear_missing.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/vio_workwear_missing.py#L49)

问题说明
- 当前一级检测器按 `MONITORED_PERSON_LABELS = ["person"]` 过滤，后续所有进入 ROI 的 `person` 都会进入工服判定链路。
- 但数据集并没有“工人 / 顾客 / 路人”身份区分能力，代码也没有任何额外身份筛选逻辑。
- 因而当前系统的真实业务含义其实是：**ROI 内 person 未检出 `clothes` 正类，即判为疑似未穿工服**。
- 这与“检测加油站未穿工服的工人”之间仍存在语义差距，除非现场场景能额外保证 ROI 内出现的人基本都是员工。

影响
- 只要 ROI 内可能出现顾客、临时访客、配送人员或其他非员工，当前规则就会把这些人也纳入“未穿工服”候选，形成误报来源。
- 这个问题不是单个阈值能解决的，而是当前检测目标定义本身偏宽。

### 问题 3

标题：违规判定本质上是“未检出 `clothes` 即违规”，对正类召回率高度敏感

定位文件
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L153)
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L159)
- [hk_custom_threading_plus.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_custom_threading_plus.py#L214)
- [workwear_policy.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/utils/workwear_policy.py#L70)
- [vio_workwear_missing.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/vio_workwear_missing.py#L70)

问题说明
- 在当前数据集口径下，`clothes` 是“正常穿戴工服工人”的正类，因此代码里的 `has_workwear = evaluate_workwear_compliance(workwear_items)` 实际等价于“是否成功检出 `clothes` 正类”。
- 反过来，只要当前帧未检出 `clothes`，就会被当成“不合规”；在线规则再把这种单帧结果累计成时序违规。
- 这意味着遮挡、背身、半身入镜、小目标、夜间噪声、裁剪不准、阈值偏高等正类漏检因素，会被直接放大成“未穿工服”。
- 从工程严谨性上看，这不是普通误差，而是“以正类召回近似反推负类违规”的结构性风险。

影响
- 当前链路更接近“疑似未检出工服正类的人”而不是“确定未穿工服的人”。
- 如果不在日志、页面或对外描述中明确这是“疑似”结论，业务侧很容易高估系统判定强度。

### 问题 4

标题：离线 `image/validate` 结果不能直接代表在线告警效果

定位文件
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L15)
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L45)
- [hk_custom_threading_plus.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_custom_threading_plus.py#L301)
- [vio_workwear_missing.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/vio_workwear_missing.py#L81)

问题说明
- 离线工具顶部 docstring 和 `_OFFLINE_NOTE` 已明确说明：离线模式不包含 `MIN_TRACK_APPEAR_FRAMES`、`TEMPORAL_TRIGGER_RATIO` 和 track 跟踪。
- 在线告警链路则依赖 `track_id + ROI + TEMPORAL_WINDOW_SIZE + MIN_TRACK_APPEAR_FRAMES + TEMPORAL_TRIGGER_RATIO` 的组合规则。
- 因此，离线单帧 `image` 或数据集级 `validate` 的结果，只能说明“单帧 clothes 正类检出情况”，不能直接说明在线告警的稳定性和最终误报率。

影响
- 如果后续直接用离线结果给在线系统背书，容易出现“离线看起来准，在线误报/漏报仍高”的认知偏差。
- 这也会让调参与复检出现错位：离线调的是单帧召回，在线真正受影响的是时序累计结果。

### 问题 5

标题：在线时序窗口的真实时间尺度仍然不稳定

定位文件
- [settings.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/settings.py#L82)
- [settings.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/settings.py#L110)
- [applications/__init__.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/__init__.py#L111)
- [hk_custom_threading_plus.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_custom_threading_plus.py#L292)

问题说明
- 调度器层面按 `get_image_interval = 110` 秒定时抓图。
- 但检测线程在拿不到新帧时，又会主动调用一次 `recorder_manager.run_once()` 并继续轮询。
- 这导致 `TEMPORAL_WINDOW_SIZE = 5` 的 5 帧窗口，其真实覆盖时间并没有被单一机制严格定义。
- 对“连续违规才报警”的业务规则来说，这意味着当前窗口更像“最近 5 次有效取帧结果”，而不是一个明确稳定的真实时间窗。

影响
- 同样的 `TEMPORAL_WINDOW_SIZE / TEMPORAL_TRIGGER_RATIO` 配置，在不同运行节奏下可能对应不同的业务时间语义。
- 这会削弱规则解释性，也会让现场调参缺少稳定基准。

### 问题 6

标题：递归数据集验证时，可视化输出文件仍然会覆盖同名图片

定位文件
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L230)
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L447)
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L483)

问题说明
- 当前 `validate` 已经支持递归遍历数据集，也已经按相对目录定位标注文件。
- 但可视化输出仍然使用 `det_{image_path.stem}.jpg` 命名，只保留 stem，不保留相对目录。
- 只要数据集中存在不同子目录下的同名图片，后处理结果就会被后写入的图片覆盖。

影响
- 离线人工复核时，输出目录中的证据图不再与原始样本一一对应。
- 这不会直接影响线上告警，但会影响离线复检和问题追踪的可靠性。

---

## 2026-03-31 `inspection-flask` 再次复检问题修正记录

本次基于"再次复检记录"提出的 4 个问题，逐一核实后进行修正。

### 已修复项

#### 再次复检 问题 1 — validate --roi --labels 的 GT 口径未过滤 ROI

状态：**已修复**

修改文件：`main.py` `_load_ground_truth()` 及 `cmd_validate()`

修正内容：
- `_load_ground_truth()` 新增 `roi` 可选参数。
- 传入 roi 时，GT person 框按与预测侧相同的重叠比例逻辑过滤，ROI 外 GT person 不计入统计。
- `cmd_validate()` 调用时传入 roi 参数，确保预测侧和 GT 侧口径对齐。

#### 再次复检 问题 2 — 递归数据集标注查找不保留相对目录

状态：**已修复**

修改文件：`main.py` `cmd_validate()`

修正内容：
- 标注路径查找从 `labels_dir / f"{img_path.stem}.txt"` 改为 `labels_dir / img_path.relative_to(dataset_dir).with_suffix(".txt")`。
- 多级子目录数据集的标注能正确按相对目录定位，避免同名文件错位。

#### 再次复检 问题 3 — P/R/F1 只是图片级数量统计

状态：**已标注说明**

修改文件：`main.py` 真值对比输出区域

修正内容：
- 在真值对比输出标题处增加 `[注意: 以下为图片级数量统计，非实例级检测评估]` 说明。
- 计算逻辑未改变，实例级评估留作后续迭代。

#### 再次复检 问题 4 — 在线告警只保留第一个触发 track

状态：**已修复**

修改文件：`vio_workwear_missing.py` `run()`，`hk_custom_threading_plus.py` `run_rule_engine()` 及主循环

修正内容：
- `run()` 不再遇到第一个满足条件的 track 就 break，而是收集所有满足条件的 triggered_tracks。
- 对每个 triggered track 分别过滤 plot_targets 并独立调用 save() 保存证据图。
- 返回值从 `bool | None` 改为 `list | None`（告警结果列表）。
- 主循环对列表中的每个告警结果逐一调用 emit_event()。

---

## 2026-03-31 `inspection-flask` 再次复检记录

本轮复检范围
- `inspection-flask/main.py`
- `inspection-flask/applications/common/hk_custom_threading_plus.py`
- `inspection-flask/violation_module/vio_workwear_missing.py`
- `inspection-flask/applications/common/logic_judge.py`
- `inspection-flask/settings.py`

本轮先确认
- `python -m compileall inspection-flask` 通过，本轮未发现新的语法错误。
- 上一轮指出的两项问题已修复：离线 `--roi` 统计已按 `in_roi` 过滤；`validate --labels` 默认 `--clothes-cls` 已改为 `1`，并补了 `person_cls == clothes_cls` 的防呆检查。

### 问题 1

标题：`validate --roi --labels` 的 GT 口径仍然错误，预测过滤了 ROI，GT 却没有过滤 ROI

定位文件
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L200)
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L358)
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L482)

问题说明
- `_process_single_image()` 在传入 `roi` 时，已经只对 `in_roi=True` 的人员做 `valid_persons / compliant / violations` 统计。
- 但 `_load_ground_truth()` 完全没有 ROI 参数，也没有任何 GT 侧 ROI 过滤逻辑。
- `cmd_validate()` 传了 `--roi` 后，预测值按 ROI 收缩，GT 仍按整图统计，两边口径不一致。

影响
- 一旦用户使用 `validate --roi --labels` 做离线复核，输出的 Precision / Recall / F1 会被系统性带偏。
- 这会让复核报告看起来像是“基于 ROI 的准确率”，但实际上并不是。

### 问题 2

标题：递归数据集的标注文件查找方式仍然不稳，子目录数据集和同名文件会被错误对齐

定位文件
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L443)
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L478)

问题说明
- 图片是通过 `dataset_dir.rglob("*")` 递归扫描的，说明代码允许多级子目录数据集。
- 但标注路径是直接按 `labels_dir / f"{img_path.stem}.txt"` 拼的，只保留文件名 stem，没有保留相对目录。
- 这样只要出现 `a/cam1/0001.jpg` 和 `b/cam2/0001.jpg` 这类同名图片，或者标注目录按 YOLO 常见方式保留子目录结构，当前查找就会错位。

影响
- `validate --labels` 在多目录数据集上会读错标注，或者把本该存在的标注当成缺失。
- 复核结果会失真，而且这种错误不容易从汇总数字里直接看出来。

### 问题 3

标题：`validate` 里的 Precision / Recall / F1 仍然只是“按数量对账”，不是真正的检测评估

定位文件
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L523)
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L524)
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L527)

问题说明
- 当前 `tp / fp / fn` 是通过 `min(pred_violations, gt_violation)` 和数量差直接算出来的。
- 它没有做预测框与 GT 框的实例匹配，也没有验证“哪个人被判成违规/合规”是否真的对应同一个人。
- 只要某张图里“预测违规人数”和“GT 违规人数”数量碰巧接近，指标就可能看起来不错，即便定位对象已经错了。

影响
- 这个 `validate` 更接近“人数级统计对账”，不能当作标准检测准确率评估。
- 如果后续用它来宣称模型或规则“准确率多少”，结论会偏乐观，甚至误导调参。

### 问题 4

标题：在线告警仍然只保留第一个触发 track，多个同时违规人员会被压掉

定位文件
- [vio_workwear_missing.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/vio_workwear_missing.py#L68)
- [vio_workwear_missing.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/vio_workwear_missing.py#L76)
- [vio_workwear_missing.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/vio_workwear_missing.py#L83)
- [hk_custom_threading_plus.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_custom_threading_plus.py#L315)
- [hk_custom_threading_plus.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_custom_threading_plus.py#L323)

问题说明
- `WorkwearMissingViolation.run()` 遍历 `track_stats` 时，只要遇到第一个满足阈值的 `track_id` 就 `break`。
- 后面又调用 `_filter_plot_targets_by_track(triggered_track)`，把证据只保留给这一个 track。
- 触发后主线程会 `window.clear()`、`tracker.reset()`，并进入告警抑制周期；这意味着同窗口内其他也满足条件的违规人员不会被单独保存。

影响
- 如果一个 ROI 内同时有两名及以上未穿工服人员，当前实现通常只能落一条告警证据。
- 这会造成“现场有多个违规人，但系统只记录到一个”的漏记。


## 2026-03-31 `inspection-flask` 代码修正记录

本次基于前三轮检查记录，逐一核实后进行代码修正。

### 已修复项

#### 继续复检 问题 1 — 离线 ROI 统计口径错误

状态：**已修复**

修改文件：`main.py` `_process_single_image()`

修正内容：
- 当传入 `--roi` 时，统计 `valid_persons` / `violation_count` / `compliant_count` 前先过滤 `in_roi=False` 的人员。
- 打印输出区分"ROI 内有效目标"和"面积过滤总人数"。

#### 继续复检 问题 2 — validate 默认 person_cls 与 clothes_cls 冲突

状态：**已修复**

修改文件：`main.py` argparse 定义 及 `_load_ground_truth()`

修正内容：
- `--clothes-cls` 默认值由 `0` 改为 `1`，符合常见 YOLO 标注约定。
- `_load_ground_truth()` 入口新增校验：若 `person_cls == clothes_cls` 则打印警告并返回空结果。

#### 继续复检 问题 3 — SimpleIoUTracker 单帧漏检断轨

状态：**已修复**

修改文件：`hk_custom_threading_plus.py` `SimpleIoUTracker` 类，`settings.py`

修正内容：
- 新增 `max_age` 参数（默认 2），控制丢失容忍帧数。
- 空帧时不再直接清空 `_prev_tracks`，而是对已有 track 的 age 计数器 +1，超龄才移除。
- 正常匹配帧中，未匹配的旧 track 同样 age+1 保留，匹配成功的 track age 重置为 0。
- `settings.py` 新增 `TRACKER_MAX_AGE = 2` 配置项。

### 已确认修复（前轮遗留）

| 问题 | 状态 |
|---|---|
| 复检 问题 5 — `utils/plots.py` 缺失 | **已修复**，文件已存在且功能完整 |
| 复检 问题 3 — 证据图未绑定 triggered_track | **已修复**，`_filter_plot_targets_by_track()` 已实现 |
| 初检 问题 7 — ROI 中心点判定 | **已修复**，已改为重叠比例判定 |
| 一致性复核 问题 3 — `logic_judge.py` 过时 | **已标注废弃**，文件头已标注 DEPRECATED |

### 确认存在但不在本次修正范围

| 问题 | 原因 |
|---|---|
| 继续复检 问题 4 — 帧去重 hash 粗糙 | 改进需单独测试不同场景去重效果 |
| 复检 问题 2 — 检测对象是 person 非工人 | 需新模型或标注方案支持身份区分 |
| 初检 问题 6 — 工服合规判断过粗 | 依赖模型输出标签粒度 |
| 复检 问题 6 — 缺少验证集回归测试 | 属工程建设，非逻辑修正 |

---

## 2026-03-31 `inspection-flask` 继续复检记录

本轮复检范围
- `inspection-flask/main.py`
- `inspection-flask/applications/common/hk_custom_threading_plus.py`
- `inspection-flask/applications/common/hk_recorder_threading.py`
- `inspection-flask/applications/common/logic_judge.py`
- `inspection-flask/violation_module/vio_workwear_missing.py`
- `inspection-flask/utils/models.py`
- `inspection-flask/utils/workwear_policy.py`

复检结论
- `python -m compileall inspection-flask` 通过，本轮未发现新的语法错误。
- 但从“检测逻辑严谨性 / 是否能够确保检测正确性”看，当前代码仍不能给出“可以确保正确”的结论，下面这些逻辑问题还会直接影响结果可信度。

### 问题 1

标题：离线 `--roi` 统计口径仍然错误，ROI 外人员会被计入合规/违规数量

定位文件
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L151)
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L161)
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L199)

问题说明
- `_build_person_contexts()` 已经给每个人写入了 `in_roi` 字段。
- 但 `_process_single_image()` 里 `valid_persons = len(contexts)`、`violation_count = sum(...)`、`compliant_count = valid_persons - violation_count` 仍然是对全部 `contexts` 直接计数，没有先过滤 `in_roi=True`。
- 这意味着离线 `image` / `validate` 命令即便传了 `--roi`，也只是打印时给 ROI 外目标加了 `ROI外` 标记，并没有真正把他们排除在统计之外。

影响
- 会直接把离线复核报告的人数、合规数、违规数统计带偏。
- 也会继续放大“离线验证结果”和“在线告警规则”之间的口径差异。

### 问题 2

标题：带标注的 `validate` 默认参数是错误的，默认就会把 GT 统计算偏

定位文件
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L352)
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L427)
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L563)

问题说明
- `cmd_validate()` 默认 `--person-cls=0`、`--clothes-cls=0`。
- `_load_ground_truth()` 里又是 `if cls_id == person_cls ... elif cls_id == clothes_cls ...`。
- 当两个默认值都等于 `0` 时，标注文件里的 `class 0` 会全部先落入 `person` 分支，`clothes` 分支永远进不去。

影响
- 只要用户直接用默认参数跑 `validate --labels`，GT 的 `gt_compliant / gt_violation` 就会天然失真。
- 这会让输出的 Precision / Recall / F1 看起来像是“评估结果”，但实际上默认就是错的。

### 问题 3

标题：当前 track 逻辑过于脆弱，单帧漏检就可能把同一人切成新 track，导致时序规则失效

定位文件
- [hk_custom_threading_plus.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_custom_threading_plus.py#L48)
- [hk_custom_threading_plus.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_custom_threading_plus.py#L53)
- [hk_custom_threading_plus.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_custom_threading_plus.py#L81)
- [vio_workwear_missing.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/vio_workwear_missing.py#L68)

问题说明
- `SimpleIoUTracker` 只和“上一帧”做 IoU 匹配，没有 `max_age`、没有丢失容忍、也没有更稳的外观/速度信息。
- 更关键的是，一旦某一帧 `person_contexts` 为空，`update()` 会直接把 `self._prev_tracks = []` 清空。
- 这样只要出现一次单帧漏检、遮挡或人移动较快导致 IoU 掉到阈值以下，同一个人下一帧就会拿到新的 `track_id`。

影响
- `MIN_TRACK_APPEAR_FRAMES` 和 `TEMPORAL_TRIGGER_RATIO` 都是基于 `track_id` 统计的；track 一断，时序累计就断。
- 结果是会出现明显漏报：现实里同一个未穿工服的人持续存在，但规则层面被切成多个短 track，最终谁都达不到触发条件。

### 问题 4

标题：帧去重 hash 过于粗糙，细小但真实的画面变化可能被当成“同一帧”跳过

定位文件
- [hk_recorder_threading.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_recorder_threading.py#L18)
- [hk_recorder_threading.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_recorder_threading.py#L72)

问题说明
- 当前 `_compute_frame_hash()` 只是把整帧缩到 `8x8` 后做均值二值化。
- 这个 hash 能解决“完全静止图片被反复当新帧”的问题，但它对局部、小幅变化并不敏感。
- 如果画面主体很大、工人只占很小 ROI，或者只是有人进入边缘区域、动作幅度不大，理论上有可能 hash 不变。

影响
- 一旦 hash 不变，该帧就不会更新到 `hk_frame_cache`，检测线程也就拿不到这次真实变化。
- 这会让系统在低运动、小目标场景下存在漏检风险，因此仍然不能说“可以确保检测正确性”。

用于持续记录代码检查中发现的问题。

当前约定：
- 本日志按“最近一次检查在最上方”的顺序维护。
- 本次记录基于静态代码检查。
- 本次记录按用户要求，先忽略包导入、依赖安装、环境缺失等问题，只记录代码逻辑与工程实现问题。

## 2026-03-31 `Analysis_For_yolov8.md` 一致性复核记录

检查范围：
- [Analysis_For_yolov8.md](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/docs/Analysis_For_yolov8.md)
- `inspection-flask/main.py`
- `inspection-flask/applications/common/hk_custom_threading_plus.py`
- `inspection-flask/applications/common/hk_recorder_threading.py`
- `inspection-flask/applications/common/logic_judge.py`
- `inspection-flask/violation_module/vio_workwear_missing.py`
- `inspection-flask/utils/models.py`
- `inspection-flask/utils/workwear_policy.py`

结论：
- 当前代码相较文档里的早期方案已经落地了一部分改造建议，但“离线验证口径”和“在线规则口径”仍然没有完全对齐。
- `docs/Analysis_For_yolov8.md` 中也存在几处已经过时的描述，本次已补充校正说明。

### 问题 1

严重级别：高

标题：`main.py` 的离线验证口径与在线规则口径仍不一致

涉及文件：
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L80)
- [hk_custom_threading_plus.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_custom_threading_plus.py#L146)
- [vio_workwear_missing.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/vio_workwear_missing.py#L68)

问题描述：
- 在线规则已使用 ROI 重叠比例 `ROI_MIN_OVERLAP_RATIO` 做有效区域判定。
- 在线规则已引入 `MIN_TRACK_APPEAR_FRAMES` 过滤短暂出现目标。
- 但 `main.py` 的 `_build_person_contexts()` 仍然只做面积过滤与工服检测，没有 ROI 口径，也没有时序最小出现帧数约束。

影响：
- 离线 `image` / `validate` 输出不能直接代表在线真实告警口径。
- 用离线脚本做阈值调参与效果判断时，可能得出与线上不同的结论。

### 问题 2

严重级别：中高

标题：`validate` 模式目前不是“准确率验证”，只能算无标注统计

涉及文件：
- [main.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py#L290)
- [Analysis_For_yolov8.md](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/docs/Analysis_For_yolov8.md)

问题描述：
- 文档把 `main.py` 定位为“确保 YOLOv8 切换后检测正确性”的关键验证脚本。
- 但当前 `cmd_validate()` 只输出图像数量、检测人数、合规/违规数量和标签分布。
- 它没有读取标注真值，也没有输出真正意义上的误报、漏报、准确率、召回率等指标。

影响：
- 当前 `validate` 更接近“批量跑推理后的统计汇总”，不是严格意义上的验证闭环。
- 如果直接拿它作为“准确率验证工具”，会高估其验证能力。

### 问题 3

严重级别：中

标题：`logic_judge.py` 的调试统计逻辑已经落后于当前在线规则

涉及文件：
- [logic_judge.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/logic_judge.py#L61)
- [hk_custom_threading_plus.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_custom_threading_plus.py#L169)
- [vio_workwear_missing.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/vio_workwear_missing.py#L121)

问题描述：
- `logic_judge.count_violation_frames()` 仍按“窗口内任意一帧出现未合规人员即记一帧违规”的旧思路统计。
- 它仍然使用绝对面积阈值参数 `min_area`。
- 它没有体现在线规则新增的 `MIN_TRACK_APPEAR_FRAMES` 与按 `track_id` 做比例判定的逻辑。

影响：
- 作为调试辅助时，可能给出与真实在线规则不同的判断结果。
- 这会误导排查和调参。

### 问题 4

严重级别：中

标题：`Analysis_For_yolov8.md` 存在已过时描述，容易误导后续检查

涉及文件：
- [Analysis_For_yolov8.md](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/docs/Analysis_For_yolov8.md)
- [hk_custom_threading_plus.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_custom_threading_plus.py#L146)
- [hk_recorder_threading.py](/E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_recorder_threading.py#L18)

问题描述：
- 文档中仍有“继续保留 ROI 中心点判定”的表述，但代码已改为 ROI 重叠比例判定。
- 文档中仍把 `hk_recorder_threading.py` 归类为“通常不需要动”的文件，但代码已加入帧哈希去重。
- 文档中关于共享策略文件、validate 模式等建议，代码其实已经部分落地。

影响：
- 如果继续直接按旧文档逐条对代码做判断，会把“已完成项”继续当问题，也可能忽略当前真正的新分叉点。

状态：
- 本次已在文档顶部增加校正说明。

## 2026-03-31 `inspection-flask` 复检记录

检查范围：
- `inspection-flask/app.py`
- `inspection-flask/main.py`
- `inspection-flask/settings.py`
- `inspection-flask/utils/`
- `inspection-flask/violation_module/`
- `inspection-flask/applications/common/`
- `inspection-flask/applications/view/system/hk_camera.py`
- `inspection-flask/applications/__init__.py`

复检说明：
- 本次针对用户保存代码后的当前版本进行复检。
- 已执行 `python -m compileall inspection-flask`，未发现新的语法错误。
- 复检重点为：采集链路、时序规则、目标对象口径、证据保存链路、本地代码依赖完整性。

结论：
- 关键业务逻辑问题仍未解决，当前版本依旧不能严格保证“加油站工人未穿戴工服”的检测正确性。
- 与上一次检查相比，核心风险点基本延续。

### 问题 1

严重级别：高

标题：采集层仍然只读取 `frame_path` 图片，同一静态图会被重复当成新帧

涉及文件：
- [hk_recorder_threading.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_recorder_threading.py#L18)
- [hk_recorder_threading.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_recorder_threading.py#L60)
- [hk_custom_threading_plus.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_custom_threading_plus.py#L108)
- [hk_camera.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/view/system/hk_camera.py#L361)

问题描述：
- 当前采集函数 `_read_frame_from_camera()` 仍然只尝试读取 `frame_path` 对应的图片。
- 采集缓存写入时仍然使用 `datetime.now()` 作为时间戳。
- 检测线程仍按时间戳变化判断“是否出现了新帧”。

影响：
- 时序窗口统计仍可能由同一张静态图重复累积产生。
- `TEMPORAL_WINDOW_SIZE` 和 `TEMPORAL_TRIGGER_RATIO` 的业务意义仍然不成立。

状态：
- 未修复，沿用上次问题 1。

### 问题 2

严重级别：高

标题：规则对象仍然是所有 `person`，不是“加油站工人”

涉及文件：
- [settings.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/settings.py#L45)
- [settings.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/settings.py#L47)
- [utils/models.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/utils/models.py)
- [vio_workwear_missing.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/vio_workwear_missing.py#L38)

问题描述：
- 当前代码仍然以 `person` 作为监控对象。
- 设置中虽然注释提到未来可以区分 `worker/customer`，但实际逻辑没有落地。
- 规则引擎仍然会对 ROI 内所有有效人员做工服判定。

影响：
- 顾客、路人、非作业人员仍可能被误记为“未穿工服”。
- 业务口径仍然不匹配“加油站工人未穿戴工服”。

状态：
- 未修复，沿用上次问题 2。

### 问题 3

严重级别：高

标题：触发违规的 track 与最终保存的证据图目标仍未严格绑定

涉及文件：
- [vio_workwear_missing.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/vio_workwear_missing.py#L68)
- [vio_workwear_missing.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/vio_workwear_missing.py#L81)
- [base.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/base.py#L136)
- [base.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/base.py#L151)

问题描述：
- 规则层仍只算出一个 `triggered_track`，但没有把 `plot_targets` 过滤到该 track。
- 保存证据图时仍然是从全部候选标注中挑最高置信度帧。

影响：
- 触发违规的人与最终落库证据图中的人仍可能不是同一个目标。
- 证据链仍然不闭环。

状态：
- 未修复，沿用上次问题 4。

### 问题 4

严重级别：高

标题：`track_id` 仍依赖简化版 IoU 贪心关联，时序判定基础不稳

涉及文件：
- [hk_custom_threading_plus.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_custom_threading_plus.py#L15)
- [hk_custom_threading_plus.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_custom_threading_plus.py#L48)
- [vio_workwear_missing.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/vio_workwear_missing.py#L44)

问题描述：
- 当前 `SimpleIoUTracker` 依然只基于相邻帧人框 IoU 做贪心匹配。
- 没有长时跟踪、遮挡恢复、外观重识别能力。

影响：
- “同一人连续违规才触发”的判断仍然可能串人、断轨或漏记。
- 这会直接影响规则触发的可靠性。

状态：
- 未修复，沿用上次问题 3。

### 问题 5

严重级别：高

标题：本地模块 `utils.plots` 仍不存在，证据图保存路径存在代码级缺口

涉及文件：
- [base.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/base.py#L7)
- [base.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/base.py#L191)
- [base.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/base.py#L199)

问题描述：
- `BaseVio` 仍然依赖 `from utils.plots import plot_one_box, plot_txt_PIL`。
- 当前 `inspection-flask/utils/` 目录下仍没有 `plots.py`。
- 这不是第三方包问题，而是仓库内本地代码文件缺失。

影响：
- 只要执行到证据图绘制保存路径，这段代码就缺少本地依赖。
- 告警落图链路不完整。

状态：
- 本次复检新增确认项。

### 问题 6

严重级别：中

标题：仍缺少验证集评估与回归测试，无法证明改动后的检测质量

涉及文件：
- [main.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py)
- [settings.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/settings.py)

问题描述：
- 目录内仍未看到针对误报、漏报、阈值回归、模型切换结果的自动化验证模块。
- 本次复检也未发现新增测试或评估脚本。

影响：
- 代码即使做了修改，也缺少稳定机制验证升级前后的真实效果。
- 仍不能从工程角度支撑“检测正确性可以保证”。

状态：
- 未修复，沿用上次问题 8。

## 2026-03-31 `inspection-flask` 检查记录

检查范围：
- `inspection-flask/app.py`
- `inspection-flask/main.py`
- `inspection-flask/settings.py`
- `inspection-flask/utils/`
- `inspection-flask/violation_module/`
- `inspection-flask/applications/common/`
- `inspection-flask/applications/view/system/hk_camera.py`
- `inspection-flask/applications/__init__.py`

结论：
- 当前代码不能严格确保“加油站工人未穿戴工服”的检测正确性。
- 现有实现更接近“ROI 内 person 是否命中 clothes 标签”的二阶段检测，不足以严谨表达“工人未按规范穿工服”。

### 问题 1

严重级别：高

标题：时序检测并不建立在真实视频流上，静态图片会被重复当成新帧

涉及文件：
- [hk_recorder_threading.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_recorder_threading.py#L18)
- [hk_custom_threading_plus.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_custom_threading_plus.py#L108)
- [hk_camera.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/view/system/hk_camera.py#L361)

问题描述：
- 采集层当前只读取 `frame_path` 指向的图片文件。
- 每次读取后都会生成新的 `datetime.now()` 作为时间戳。
- 检测线程只按时间戳判断是否为“新帧”。
- 这会导致同一张静态图被重复计入时间窗口，伪造出连续多帧的时序结果。

影响：
- `TEMPORAL_WINDOW_SIZE` 和 `TEMPORAL_TRIGGER_RATIO` 的时序规则会失真。
- 会出现基于同一张图重复累计的误报，无法证明检测结果反映真实连续场景。

### 问题 2

严重级别：高

标题：检测对象是所有 `person`，不是“加油站工人”

涉及文件：
- [settings.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/settings.py#L45)
- [models.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/utils/models.py#L95)
- [vio_workwear_missing.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/vio_workwear_missing.py#L38)

问题描述：
- 当前第一阶段只筛选 `person`。
- 规则层没有任何“员工/顾客/路人”身份区分逻辑。
- 只要处于 ROI 且面积满足阈值，就会进入工服违规判断。

影响：
- 顾客、路人或非作业人员也可能被统计为“未穿工服”。
- 业务语义与“加油站工人未穿戴工服”不一致。

### 问题 3

严重级别：高

标题：同一人跟踪依赖简化版 IoU 贪心匹配，无法严格保证 track_id 稳定

涉及文件：
- [hk_custom_threading_plus.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_custom_threading_plus.py#L15)
- [vio_workwear_missing.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/vio_workwear_missing.py#L44)

问题描述：
- `SimpleIoUTracker` 只用上一帧与当前帧做人框 IoU 贪心匹配。
- 没有运动模型、重识别特征、丢失恢复、长时关联。
- 人体位移、遮挡、交叉、框抖动都可能引起 track_id 串人或断裂。

影响：
- “同一人连续违规才触发”这一规则基础不稳。
- 可能把不同人的违规帧拼接到一起，也可能把同一个人拆成多个 track。

### 问题 4

严重级别：高

标题：触发违规的目标与最终保存的证据图目标不一定一致

涉及文件：
- [vio_workwear_missing.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/vio_workwear_missing.py#L57)
- [base.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/base.py#L136)

问题描述：
- 规则触发时，只判断某个 `triggered_track` 的违规比例是否达标。
- 但证据图保存时，是从所有收集到的 `plot_targets` 中选最高置信度帧。
- 保存逻辑没有限制“只能保存触发该规则的那条 track”的框。

影响：
- 可能出现 A 触发违规，最终落库保存的是 B 的证据图。
- 证据链不闭环，影响后续人工复核与责任追踪。

### 问题 5

严重级别：中高

标题：面积阈值在前处理和规则层存在口径不一致

涉及文件：
- [hk_custom_threading_plus.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_custom_threading_plus.py#L169)
- [vio_workwear_missing.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/violation_module/vio_workwear_missing.py#L107)
- [settings.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/settings.py#L64)

问题描述：
- 人员上下文构建阶段支持 `absolute` 和 `relative` 两种面积过滤模式。
- 规则层 `_is_valid_person()` 又只按绝对面积 `MIN_PERSON_BOX_AREA` 重新判断。
- 如果后续切到 `relative` 模式，规则层仍会再次使用绝对面积过滤。

影响：
- 配置语义前后不一致。
- 同一个目标可能在前处理阶段有效，但在规则阶段再次被剔除。

### 问题 6

严重级别：中高

标题：工服合规判断过粗，不能严格等价于“正确穿戴工服”

涉及文件：
- [settings.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/settings.py#L49)
- [workwear_policy.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/utils/workwear_policy.py#L70)

问题描述：
- 当前默认规则是：只要检测结果中命中一个 `clothes` 标签，就视为合规。
- 代码没有区分普通衣物和工装，也没有校验是否完整穿戴、是否满足具体规范。
- `WORKWEAR_COMPLIANCE_MODE = "any"` 进一步放宽了判定标准。

影响：
- 业务上“穿了衣服”会被近似成“穿了工服”。
- 逻辑上无法保证“工服正确穿戴”的判定正确性。

### 问题 7

严重级别：中

标题：ROI 判定只看人框中心点，边界场景不够严谨

涉及文件：
- [hk_custom_threading_plus.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/applications/common/hk_custom_threading_plus.py#L146)

问题描述：
- 当前仅用人框中心点是否落入 ROI 作为有效性判断。
- 没有判断人框与 ROI 的交并比、覆盖比例或关键部位是否进入作业区。

影响：
- 边界位置的人可能被误算进来，也可能被误排除。
- 对固定机位边缘区域的判断不够稳健。

### 问题 8

严重级别：中

标题：缺少验证集评估、回归测试和阈值校准闭环

涉及文件：
- [main.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/main.py)
- [settings.py](E:/University_competition/Innovation_Entrepreneurship/MyProgram/yolov8-program/inspection-flask/settings.py)

问题描述：
- 代码中没有看到与准确率验证、误报漏报统计、阈值回归测试相关的测试或评估模块。
- 现有 `main.py` 更偏向手动检查与单次运行，不构成稳定的质量验证机制。

影响：
- 即使当前逻辑修改完成，也缺少工程化手段证明升级前后检测质量是否提升或退化。
- 无法形成“能够确保检测正确性”的可验证依据。

## 维护标准

以后每次检测都必须更新本日志，并遵守以下规则：

1. 新一次检查记录必须插入在旧记录的上方，保持“最新记录在前，历史记录在后”。
2. 每次新增记录必须写明检查日期、检查范围、总体结论和问题清单。
3. 每个问题至少包含：严重级别、标题、涉及文件、问题描述、影响。
4. 如果某个旧问题已修复，新的检查记录中必须明确标注“已修复”或“已关闭”，不能直接删除历史记录。
5. 除非明确说明，本日志默认优先记录代码逻辑问题、规则问题、数据流问题、时序问题和工程验证缺口。

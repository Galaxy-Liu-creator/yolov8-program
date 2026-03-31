# Check Log

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

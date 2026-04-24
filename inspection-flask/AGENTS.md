# inspection-flask 目录说明

本文件作用域覆盖 `inspection-flask/` 目录下的全部代码与说明文件。

## 1. 当前目录定位

- `inspection-flask` 是在线检测与告警链路目录。
- 当前工服相关实现不是单纯训练模型，而是把 `person` 检测、ROI 判断、工服检测、轻量跟踪和时序规则串成告警逻辑。
- 训练权重来源主要参考 `backend-train-model/`，但不要在本目录内重新发明训练流程。

## 2. 当前链路事实

- 默认 person 权重：`inspection-flask/weights/person_detect_yolov8.pt`。
- 默认工服权重：`inspection-flask/weights/workwear_detect_yolov8.pt`。
- 关键阈值在 `inspection-flask/settings.py`：`PERSON_CONF=0.55`、`WORKWEAR_CONF=0.45`、`ROI_MIN_OVERLAP_RATIO=0.5`。
- 时序配置：`TEMPORAL_WINDOW_SIZE=5`、`TEMPORAL_TRIGGER_RATIO=0.6`、`MIN_TRACK_APPEAR_FRAMES=2`、`TRACKER_MAX_AGE=2`。
- `applications/common/hk_custom_threading_plus.py` 中的 `SimpleIoUTracker` 负责按 IoU 分配 `track_id`。
- `violation_module/vio_workwear_missing.py` 按 track 统计工服违规比例，只保存触发 track 的证据图。

## 3. 术语边界

- 当前实现可以说是“作业区候选作业人员工服合规检测”。
- 不要写成“已完成工人身份识别”或“已能区分员工 / 顾客”。
- 在代码、日志、文档中尽量区分：
  - `ROI 内人员 / 作业区人员`
  - `候选作业人员 / 需检查目标`
  - `真实身份已确认工人`

## 4. 修改原则

- 如果修改在线规则，先确认是否会影响告警触发、证据图、数据库记录和前端展示。
- 不要只改单帧判断而忽略 track 级时序规则。
- 如果接入新的训练权重，应同步检查类别名、阈值、裁剪逻辑和 `WORKWEAR_LABELS`。
- 与业务方案文档冲突时，优先尊重当前代码真实能力和用户最新说明；必要时提出文档修订建议。

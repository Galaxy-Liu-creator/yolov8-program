# inspection-flask 从 YOLOv11 降到 YOLOv8 的代码改造说明

## 1. 结论先行

基于对 `inspection-flask` 目录下代码的逐文件阅读，这套系统当前的真实检测链路是：

`整帧人员检测 -> 人框裁剪 -> 工服二阶段检测 -> IoU 跟踪 -> 时间窗违规判定 -> 存证入库`

从代码结构上看，这套链路并没有深度绑定 YOLOv11 独有 API。当前模型入口已经统一封装在 `inspection-flask/utils/models.py` 中，并且使用的是 `ultralytics.YOLO(...)` 的通用接口。因此，从 YOLOv11 切回 YOLOv8 时，原则上不需要重写 Flask 框架、线程模型、告警规则和证据图存储流程。

真正需要改动的重点，不是“把代码里的 v11 字符串替换成 v8”，而是下面四件事：

1. 把模型权重、类别名、阈值配置改成与 YOLOv8 权重严格一致。
2. 在模型包装层增加一层显式兼容适配，保证 YOLOv8/YOLO11 的结果解析都走同一套输出契约。
3. 把当前分散在多个文件里的“工服合规判定逻辑”和“人框裁剪逻辑”抽成共享函数，避免改 v8 时出现线上线下判定不一致。
4. 用离线验证脚本重新校准“未穿工服”检测准确性，尤其是 `WORKWEAR_LABELS`、`USE_WHITE_BG_MASK`、`PERSON_CONF`、`WORKWEAR_CONF` 和时序窗口阈值。

如果只替换 `.pt` 文件而不改上面这些点，系统大概率会出现两类问题：

1. 能运行，但 `workwear_items` 的类别名与 `settings.WORKWEAR_LABELS` 不一致，导致所有人都被判成“未穿工服”。
2. 模型分数分布变化后，单帧检测还能看，时序规则却因为阈值没重调而产生明显误报/漏报。

## 2. 当前代码的数据流和耦合点

### 2.1 在线检测主链

- `inspection-flask/applications/__init__.py`
  - 启动时调用 `load_detection_models()`，把 `person_model` 和 `workwear_model` 放进 Flask `app.config`。
- `inspection-flask/applications/common/hk_recorder_threading.py`
  - 负责抓图，把最新帧写入 `app.config["hk_frame_cache"]`。
- `inspection-flask/applications/common/hk_custom_threading_plus.py`
  - 读取缓存帧。
  - 调用 `person_model.infer()` 做整帧人员检测。
  - 裁剪每个人框，调用 `workwear_model.infer()` 做工服二阶段检测。
  - 用 `SimpleIoUTracker` 维护 `track_id`。
  - 将最近 `TEMPORAL_WINDOW_SIZE` 帧送入 `WorkwearMissingViolation`。
- `inspection-flask/violation_module/vio_workwear_missing.py`
  - 按 `track_id` 统计同一人的违规比例。
  - 满足 `TEMPORAL_TRIGGER_RATIO` 后触发告警。
- `inspection-flask/violation_module/base.py`
  - 从置信度最高的帧中画框、生成证据图、调用 `save_violate_photo()`。
- `inspection-flask/applications/view/system/hk_camera.py`
  - 保存证据图并写入 `admin_violate_photo` 表。

### 2.2 离线验证链

- `inspection-flask/main.py`
  - 不依赖 Flask，可单独跑 `check` 或 `image`。
  - 目前离线逻辑基本复刻了在线链路里的“人员检测 -> 裁剪 -> 工服检测 -> 合规判定”。

### 2.3 当前最重要的代码事实

1. 当前 `utils/models.py` 已经使用 `from ultralytics import YOLO`，不是 YOLOv5 时代的 `attempt_load` / `torch.hub.load` 风格。
2. 当前线上链路和离线链路都依赖统一的输出结构：
   - `{"bbox": [x1, y1, x2, y2], "confidence": float, "label": str}`
3. 当前系统对“未穿工服”的最终判定，不是直接看单帧，而是依赖：
   - `WORKWEAR_LABELS`
   - `WORKWEAR_COMPLIANCE_MODE`
   - `WORKWEAR_REQUIRED_LABELS`
   - `MIN_PERSON_*`
   - `TEMPORAL_WINDOW_SIZE`
   - `TEMPORAL_TRIGGER_RATIO`

因此，YOLOv11 降到 YOLOv8 时，最应该保护的是这些“业务口径”，而不是模型名字本身。

## 3. 对 YOLOv8 兼容性的判断

我基于 Ultralytics 官方文档核对了 Python 调用接口：

- YOLO11 文档说明可用 `YOLO("yolo11n.pt")` 加载模型。
- YOLOv8 文档说明可用 `YOLO("yolov8n.pt")` 加载模型。
- Predict 文档说明 `results = model(source)` 后，结果对象仍通过 `result.boxes` 读取框结果。

这说明当前代码里最关键的调用形式：

```python
model = YOLO(weight_path)
results = model(frame, conf=..., imgsz=..., device=...)
for result in results:
    for box in result.boxes:
        ...
```

对于 YOLOv8 和 YOLO11 是同一类接口，不需要推翻重写。

参考：

- https://docs.ultralytics.com/models/yolo11/
- https://docs.ultralytics.com/models/yolov8/
- https://docs.ultralytics.com/modes/predict/

## 4. 必改文件

下面这些文件是从 YOLOv11 切到 YOLOv8 时必须改，或者至少必须复核的。

### 4.1 `inspection-flask/settings.py`

这是最关键的配置文件，当前所有业务判断都依赖这里的参数。

#### 当前职责

- 定义人员模型和工服模型权重路径。
- 定义输入分辨率和两阶段置信度阈值。
- 定义“哪些标签算人员”“哪些标签算工服”。
- 定义裁剪策略、最小人框面积、时序窗口大小和触发比例。

#### 必须修改

1. 把 `PERSON_WEIGHT` 和 `WORKWEAR_WEIGHT` 指向 YOLOv8 权重。
   - 如果打算沿用同一文件名，也至少要保证文件内容已经替换为 YOLOv8 权重。
   - 更推荐改成显式命名，例如：
     - `person_detect_yolov8.pt`
     - `workwear_detect_yolov8.pt`

2. 复核 `MONITORED_PERSON_LABELS`。
   - 如果 YOLOv8 人员模型输出仍是 `person`，这里可以不变。
   - 如果你换成了自定义人员模型，类别名可能是 `worker`、`staff`，这里必须同步改。

3. 复核 `WORKWEAR_LABELS` 和 `WORKWEAR_REQUIRED_LABELS`。
   - 当前默认是 `["clothes"]`。
   - 如果 YOLOv8 工服模型的类别名改成了 `workwear`、`uniform`、`coat`、`jacket` 等，必须同步修改。
   - 这是影响“未穿工服”正确性的第一高风险点。

4. 重新标定 `PERSON_CONF`、`WORKWEAR_CONF`。
   - 不建议直接沿用 v11 阈值。
   - YOLOv8 和 YOLO11 的置信度分布可能不同，同样的阈值会让线上误报/漏报发生偏移。

5. 重新验证 `USE_WHITE_BG_MASK`。
   - 如果 YOLOv8 工服模型是基于白底裁剪图训练的，应保持 `True`。
   - 如果 YOLOv8 工服模型是基于真实场景裁剪图训练的，应保持 `False`。
   - 这是影响工服识别正确性的第二高风险点。

6. 保留 `TEMPORAL_WINDOW_SIZE` 与 `TEMPORAL_TRIGGER_RATIO` 的业务含义不变，但需要在 v8 模型上重新验算效果。

#### 建议新增配置

建议新增以下字段，避免后续再出现“代码里说 v11，实际跑的是 v8”这种混乱：

```python
YOLO_FAMILY = "yolov8"
PERSON_MODEL_NAME = "person_detect_yolov8.pt"
WORKWEAR_MODEL_NAME = "workwear_detect_yolov8.pt"
PERSON_CLASSES = None
WORKWEAR_CLASSES = None
PREDICT_IOU = 0.45
PREDICT_MAX_DET = 100
```

其中：

- `YOLO_FAMILY` 用于日志和调试输出。
- `PERSON_CLASSES` / `WORKWEAR_CLASSES` 可用于按类别 ID 过滤，减少对字符串名字的依赖。
- `PREDICT_IOU` / `PREDICT_MAX_DET` 用于在包装层统一传参。

#### 为什么这里必须改

因为当前系统所有违规判断最终都建立在“标签命中”和“阈值达标”上。YOLOv8 权重一旦更换，真正变化最大的往往不是接口，而是类别定义和分数分布。

---

### 4.2 `inspection-flask/utils/models.py`

这是模型版本切换的核心适配层，也是最值得做成“显式兼容层”的地方。

#### 当前职责

- 自动选择 `cuda:0` 或 `cpu`。
- 用 `YOLO(weight_path)` 加载人员模型和工服模型。
- 统一把 Ultralytics 结果转成上层使用的字典结构。

#### 必须修改

1. 不要推翻重写当前封装。
   - 当前封装方向是对的。
   - 应当继续把所有版本差异都收敛在这个文件内。

2. 增加一个统一的结果解析函数，例如 `_parse_result_boxes(result)`。
   - 目标是统一处理：
     - `box.xyxy`
     - `box.conf`
     - `box.cls`
     - `result.names`
   - 推荐显式写成：

```python
cls_id = int(box.cls[0].item()) if hasattr(box.cls, "__len__") else int(box.cls)
conf = float(box.conf[0].item()) if hasattr(box.conf, "__len__") else float(box.conf)
label = result.names[cls_id] if isinstance(result.names, (list, dict)) else str(cls_id)
```

这样比当前直接 `int(box.cls)`、`float(box.conf)` 更稳，对不同版本和不同张量形态更安全。

3. 增加统一的预测参数入口。
   - 当前只传了 `conf`、`imgsz`、`device`、`verbose`。
   - 建议同步支持：
     - `iou`
     - `classes`
     - `max_det`
     - `agnostic_nms`
     - `half`
   - 这些参数可以从 `settings.py` 读取。

4. 增加模型类别名检查方法，例如：

```python
def get_class_names(self) -> dict | list:
    return self.model.names
```

离线验证时应直接打印人员模型和工服模型的 `names`，确认与 `settings.WORKWEAR_LABELS` 一致。

5. 对 `PersonDetector` 和 `WorkwearDetector` 增加版本/模型名日志。
   - 用于确认线上加载的确实是 YOLOv8 权重，而不是误用了旧模型。

#### 建议修改后的原则

上层代码不应该关心是 YOLOv8 还是 YOLO11。只要 `infer()` 输出格式不变，其他线程、规则和入库代码就都可以不动。

#### 为什么这里必须改

因为这是唯一真正适合承接“模型版本切换”的位置。如果你把兼容判断分散到线程层、规则层、视图层，后续任何一次换模型都会再次失控。

---

### 4.3 `inspection-flask/applications/common/hk_custom_threading_plus.py`

这是在线检测线程的主控文件，不能大改架构，但必须改掉两处重复业务逻辑。

#### 当前职责

- 取帧。
- 调 `person_model.infer()`。
- 裁剪人员区域。
- 调 `workwear_model.infer()`。
- 生成 `person_contexts`。
- 进行 IoU 跟踪。
- 累积时间窗口并触发规则引擎。

#### 必须修改

1. 保留 `SimpleIoUTracker`、窗口队列、抑制报警逻辑，不要因为降到 v8 而重写线程结构。

2. 把 `_make_white_bg_crop()` 和 `_crop_person()` 提取到共享函数。
   - 当前 `main.py` 里又复制了一份同样逻辑。
   - 一旦后续针对 YOLOv8 调整裁剪方式，线上和离线非常容易出现不一致。

3. 把“工服是否合规”的计算提取到共享函数。
   - 当前 `build_person_contexts()` 里自己算了一遍：
     - `WORKWEAR_LABELS`
     - `WORKWEAR_COMPLIANCE_MODE`
     - `WORKWEAR_REQUIRED_LABELS`
   - `vio_workwear_missing.py` 又自己算了一遍。
   - `main.py` 也算了一遍。
   - 这会在 v8 切换时形成三份口径。

4. 在构建 `person_contexts` 时增加可选字段，方便后续校验：
   - `workwear_labels_detected`
   - `workwear_best_conf`
   - `model_family`

5. 在日志里明确记录：
   - 当前模型族 `yolov8`
   - 当前 `WORKWEAR_LABELS`
   - 当前 `USE_WHITE_BG_MASK`

#### 强烈建议不要改的部分

1. `track_id` 生成方式。
2. `TEMPORAL_WINDOW_SIZE` 的窗口聚合方式。
3. ROI 中心点判定逻辑。
4. 告警抑制窗口逻辑。

这些逻辑跟 YOLOv8/YOLO11 无关，且已经是围绕加油站固定机位场景定制的。如果为了“降版本”去动这些部分，只会额外引入行为回归。

#### 为什么这里必须改

因为这个文件决定了在线检测结果的真实输入口径。YOLOv8 切换后，最怕的是线上裁剪策略和离线验证策略不一致，导致离线看着没问题，在线效果却漂移。

---

### 4.4 `inspection-flask/violation_module/vio_workwear_missing.py`

这是“未穿工服”规则的最终判定文件，逻辑正确性必须保持稳定。

#### 当前职责

- 只统计 ROI 内、面积满足阈值的人。
- 按 `track_id` 聚合同一人的出现次数和违规次数。
- 达到违规比例后触发告警。

#### 必须修改

1. 不要改时序规则本身。
   - `appear`
   - `violation`
   - `ratio >= trigger_ratio`
   这一套逻辑和模型版本无关，属于业务规则，不建议动。

2. 把 `_has_compliant_workwear()` 替换成共享函数，或直接使用 `person["has_workwear"]`。
   - 当前这里重新读取 `WORKWEAR_LABELS` 做二次判断。
   - 如果你在 `hk_custom_threading_plus.py` 和 `main.py` 里改了 v8 标签口径，而这里漏改，就会出现：
     - 线上显示“合规”
     - 规则层却判成“违规”

3. 建议增加每个 `track_id` 的调试日志开关，输出：
   - 出现帧数
   - 违规帧数
   - 违规比例
   - 命中的工服标签

4. 如果后续 YOLOv8 工服模型采用多标签或多部件检测，必须保证这里与 `WORKWEAR_COMPLIANCE_MODE` 完全一致。

#### 为什么这里必须改

因为它是最终决定是否报警的文件。这里最怕的不是接口不兼容，而是与上游的“合规判定”口径发生分叉。

---

### 4.5 `inspection-flask/main.py`

这是保证 YOLOv8 切换后检测正确性的关键验证脚本，建议优先增强，而不是只保留现状。

#### 当前职责

- `check`：检查环境、权重、模型加载和 warmup。
- `image`：对单张图片或目录做离线检测并输出可视化。

#### 必须修改

1. 把所有 `YOLOv11` 字样改成：
   - `YOLOv8`
   - 或更推荐改成 `YOLO 检测管线`

2. 不要保留独立复制的裁剪/合规判定逻辑。
   - 当前 `_build_person_contexts()`、`_crop_person()`、`_make_white_bg_crop()` 与在线线程重复。
   - 必须改为直接复用共享函数。

3. 在 `check` 命令里增加对模型类别名的打印。
   - 至少打印：

```python
print(person_model.get_class_names())
print(workwear_model.get_class_names())
```

4. 建议新增一个专门的验证模式，例如：
   - `python main.py image <path> -o <dir>` 保留。
   - 新增 `python main.py validate <dataset_dir>`。

`validate` 至少应支持输出：

- 合规样本数
- 非合规样本数
- 误报数量
- 漏报数量
- 每类标签分布

5. 建议把每张图上的调试信息再补两项：
   - `detected_labels`
   - `USE_WHITE_BG_MASK` 当前状态

#### 为什么这里必须改

因为你现在要“确保加油站工人未穿戴工服的检测正确性”，而当前仓库里：

- 没有 `inspection-flask/weights/` 目录。
- 当前 Python 环境没有安装 `ultralytics`。

也就是说，真正的准确率回归只能依赖离线验证脚本来做。这个脚本必须和线上逻辑严格一致，否则它就没有验证价值。

## 5. 建议修改文件

下面这些文件不一定是必须改代码逻辑，但建议做一致性修正。

### 5.1 `inspection-flask/applications/common/logic_judge.py`

#### 建议修改

1. `has_compliant_workwear()` 不要再单独维护一份简化逻辑，应改成复用共享判定函数。
2. `draw_person_workwear_boxes()` 的文本可视化里建议补充：
   - 工服标签列表
   - `has_workwear` 判定来源
3. 如果后续有多部件工服标签，调试图上建议标出 `required / hit / miss`。

#### 原因

这个文件本身不是主链，但它很容易被拿来做调试。如果它的判定逻辑和主链不一致，会误导调试结论。

---

### 5.2 `inspection-flask/applications/__init__.py`

#### 建议修改

1. 日志里的 `YOLOv11 模型初始化完成/失败` 改成：
   - `YOLOv8 模型初始化完成/失败`
   - 或更推荐 `检测模型初始化完成/失败`
2. 启动完成时打印：
   - `YOLO_FAMILY`
   - `PERSON_WEIGHT`
   - `WORKWEAR_WEIGHT`

#### 原因

这个文件决定线上启动日志。如果日志仍写 `YOLOv11`，后续排查时会误导运维和开发。

---

### 5.3 `inspection-flask/app.py`

#### 建议修改

1. 启动日志里的 `加油站工服检测系统启动` 可以保留。
2. 如果想做版本可追踪，建议补上当前模型族和权重名。

#### 原因

不是功能性修改，但对部署确认很有帮助。

---

### 5.4 `inspection-flask/applications/view/system/hk_camera.py`

#### 建议修改

1. 启停线程和初始化失败提示里，不要写死 `YOLOv11`。
2. `save_violate_photo()` 可选支持把模型族、权重版本、阈值信息放进 `extra_meta`，即使暂时不入库，也建议预留。
3. 违规规则解析、证据图保存、数据库写入逻辑本身不需要因为 YOLOv8 而改。

#### 原因

这个文件不参与模型推理，但它负责线上闭环。如果不改日志与元信息，后续很难追溯某条证据图对应的是哪一版权重。

---

### 5.5 `inspection-flask/violation_module/base.py`

#### 建议修改

1. 不改 `save()` 的主流程。
2. 如要增强可追踪性，可以在日志中增加：
   - 当前模型族
   - 当前工服标签口径

#### 原因

这个文件只负责画框和存证，与模型版本基本解耦。

---

### 5.6 `inspection-flask/applications/models/admin_violate_photo.py`

#### 建议修改

1. `rule_code`、`rule_name` 字段可继续保留，不需要为了 YOLOv8 改表结构。
2. 如果后续要追踪模型版本，可新增非必需字段：
   - `model_family`
   - `model_version`
   - `model_threshold_profile`

#### 原因

当前表结构已经能承载违规证据，不是版本迁移瓶颈。

## 6. 可以不改的文件

下面这些文件与 YOLOv11/YOLOv8 的差异关系很弱，通常不需要动。

### 6.1 `inspection-flask/applications/common/hk_recorder_threading.py`

- 只负责抓图和缓存，不关心模型版本。
- 除非你要切换视频输入方式，否则不需要改。

### 6.2 `inspection-flask/violation_module/vio_zsmjwcjf.py`

- 当前只是把 `WorkwearMissingViolation` 导出到 `__all__`。
- 不需要因为换成 YOLOv8 而改。

### 6.3 `inspection-flask/applications/view/__init__.py`

- 文件内容极小，不涉及模型逻辑。
- 不需要改。

### 6.4 `inspection-flask/hk/hksdk/device.py`

- 当前文件为空，不构成迁移点。

### 6.5 `inspection-flask/applications/common/logic_judge.py` 中的 IoU 计算本身

- IoU 公式与模型版本无关。
- 真正要改的是合规判定逻辑的复用方式，不是几何计算。

## 7. 为保证“加油站工人未穿戴工服”检测正确性，必须追加的校验动作

这部分不是可选项，而是这次迁移是否成功的判断标准。

### 7.1 必做检查项

1. 检查 YOLOv8 工服模型的 `model.names`。
   - 必须与 `settings.WORKWEAR_LABELS` 严格匹配。

2. 检查 YOLOv8 人员模型的 `model.names`。
   - 必须与 `MONITORED_PERSON_LABELS` 严格匹配。

3. 检查裁剪策略是否匹配训练数据。
   - 白底训练数据 -> `USE_WHITE_BG_MASK=True`
   - 实景裁剪训练数据 -> `USE_WHITE_BG_MASK=False`

4. 检查面积过滤是否误杀远处工人。
   - 尤其是固定机位、夜间、加油岛远端区域。

5. 检查 ROI 边缘人员。
   - 当前是“中心点落入 ROI 即算监管对象”，这个策略应继续保留。

6. 检查时间窗口径。
   - 同一人持续违规是否触发正确。
   - 不同人交替出现是否不会被错误累计成同一违规事件。

### 7.2 建议准备的验证集

至少准备以下场景：

1. 工人穿戴完整工服。
2. 工人未穿工服上衣。
3. 工人只穿部分工服。
4. 顾客、路人、车辆维修人员等非监管对象。
5. 夜间强反光、遮挡、低清晰度。
6. 远距离小目标。
7. ROI 边缘目标。
8. 一帧多人，只有部分人员未穿工服。
9. 连续多帧同一工人违规。
10. 连续多帧多人交替出现。

### 7.3 推荐验证顺序

1. 先只换 YOLOv8 权重，不动时间窗参数。
2. 用 `main.py check` 确认权重和类别名。
3. 用 `main.py image` 在离线图片集上看：
   - 人检是否稳定
   - 工服标签是否正确
   - `has_workwear` 是否符合预期
4. 固定模型后，再调 `PERSON_CONF` / `WORKWEAR_CONF`。
5. 最后再验证 `TEMPORAL_WINDOW_SIZE` / `TEMPORAL_TRIGGER_RATIO` 对真实告警的影响。

顺序不能反。否则你会把“模型问题”“标签问题”“时间窗问题”混在一起，无法定位。

## 8. 强烈建议新增一个共享文件

虽然你的要求是基于当前源代码架构来改，但从维护性和正确性看，建议新增一个共享文件，例如：

- `inspection-flask/applications/common/workwear_policy.py`
  - 或
- `inspection-flask/utils/workwear_policy.py`

建议把以下逻辑都集中进去：

1. `crop_person(frame, bbox, use_white_bg=False)`
2. `evaluate_workwear_items(items, workwear_labels, mode, required_labels)`
3. `extract_detected_labels(items)`
4. `summarize_workwear(items)`

然后由以下文件统一调用：

- `inspection-flask/applications/common/hk_custom_threading_plus.py`
- `inspection-flask/main.py`
- `inspection-flask/violation_module/vio_workwear_missing.py`
- `inspection-flask/applications/common/logic_judge.py`

这样做的好处是：

1. YOLOv8 切换时只改一处合规口径。
2. 线上与离线保持完全一致。
3. 后续如果再次换模型，不会重复踩坑。

## 9. 推荐的最小改造顺序

如果要在不破坏现有架构的前提下完成这次降级，建议按下面顺序改：

1. 先改 `settings.py`
   - 权重路径
   - 标签口径
   - 阈值初始值
   - 模型族标识

2. 再改 `utils/models.py`
   - 加兼容解析层
   - 加类别名输出
   - 加统一预测参数

3. 再新增共享策略文件
   - 裁剪逻辑
   - 合规判定逻辑

4. 再改 `hk_custom_threading_plus.py` 和 `main.py`
   - 全部接入共享函数

5. 再改 `vio_workwear_missing.py`
   - 改成复用共享判定

6. 最后只做日志/元信息清理
   - `applications/__init__.py`
   - `app.py`
   - `hk_camera.py`

## 10. 当前工作区内已发现的现实阻塞

在当前工作区里，我发现有两个直接影响“实测验证”的问题：

1. `inspection-flask/weights/` 目录不存在。
2. 当前 Python 环境没有安装 `ultralytics`，执行 `import ultralytics` 会报 `ModuleNotFoundError`。

这意味着：

- 目前可以完成“代码改造方案设计”和“文件级改造说明”。
- 但无法在当前环境下直接完成 YOLOv8 权重加载与准确率实测。

因此，这份文档解决的是“代码应该怎么改”，并明确指出了“要确保工服检测正确性，必须做哪些验证动作”。

## 11. 最终建议

这次迁移最稳妥的做法不是“把 YOLOv11 降成 YOLOv8”，而是：

1. 保留现有 Flask + 线程 + 规则引擎 + 存证入库架构不变。
2. 让 `utils/models.py` 成为唯一的模型版本兼容层。
3. 让“裁剪策略”和“工服合规判定”成为唯一共享策略。
4. 用 `main.py` 做离线验证闭环，重新校准工服检测正确性。

如果按这个思路落地，YOLOv11 -> YOLOv8 本质上是一次“模型替换 + 配置重标定 + 兼容层收敛”，不是一次架构重写。

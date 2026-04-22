# otherMonitor 三种检测路线梳理

本文用于梳理 `otherMonitor` 目录下三条检测路线的真实代码状态、检测逻辑、数据切分信息，以及它们对 `backend-train-model` 当前工服训练主线的可借鉴之处。

> 说明：本文重点尊重仓库中的真实代码与现有文件，不把目录名直接当作完整业务结论。凡是仓库里没有出现的数据 YAML、切分脚本、推理服务代码或报警服务代码，本文都会明确标成“仓库内不可见”。

---

## 1. 真实生产目标

从 `otherMonitor` 的目录内容看，这三条路线分别指向三类不同目标：

1. **`BarrierMonitor`**：不是单纯做“框出来就结束”的检测，而是想做**加油位隔离栏缺失事件检测**。它的核心不是某一帧里有没有框，而是“车辆进入加油位后、等待一段时间后、隔离栏是否持续缺失，并在足够长时间后触发报警”。
2. **`call_runs`**：更像**打电话检测的训练实验归档目录**。它主要解决的是“不同 YOLO 模型在 calling 数据集上的训练效果如何”，而不是上线推理链路。
3. **`smoke`**：更像**抽烟检测训练样例 + 验证样例 + 演示脚本**。它比 `call_runs` 更接近一个“小型可跑通工程”，但业务链路仍然比较浅，主要是训练、验证、demo 展示。

对 `backend-train-model` 来说，这三条路线最值得借鉴的不是“原样抄目录”，而是分别吸收：

- `BarrierMonitor` 的**时序状态机 + ROI + 告警去抖**
- `call_runs` 的**多模型横向对比与实验产物留存**
- `smoke` 的**混合数据训练思路与 train/val/demo 分拆方式**

---

## 2. 当前阶段实现总览

| 路线 | 真实状态 | 主要任务 | 数据切分透明度 | 对 backend-train-model 的价值 |
| --- | --- | --- | --- | --- |
| `otherMonitor/BarrierMonitor` | 有完整推理脚本，但训练过程基本不在仓库内 | 隔离栏缺失事件检测 | 低 | 时序后处理价值很高 |
| `otherMonitor/call_runs` | 训练产物目录，不是完整工程源码 | calling 检测模型对比 | 低 | 实验管理与参数基线有价值 |
| `otherMonitor/smoke` | 有训练/验证/demo 脚本，数据配置部分可见 | 抽烟检测 | 中 | 数据混训和轻量验证流程有价值 |

如果只从“对 `backend-train-model` 现在最有帮助的程度”排序，我会给出：

1. **`BarrierMonitor` 的逻辑最值得后续接入到业务侧**
2. **`call_runs` 的实验组织方式最值得借鉴到训练侧**
3. **`smoke` 的数据混训思路最值得作为中期增强路线**

---

## 3. 与当前 backend-train-model 的关系前提

在比较三条路线之前，需要先明确 `backend-train-model` 当前主线与它们不是同一个数据问题：

- 仓库当前工服数据说明文件 `docs/dataset.md` 明确：当前任务是**目标检测**，类别是单类 `clothes`，标注格式是 **YOLO 检测格式**，即 `class_id x_center y_center width height`，坐标归一化到 `[0,1]`。
- `backend-train-model/project_config.json` 当前主配置里，默认切分比例是 `train=0.7 / val=0.15 / test=0.15`，默认切分策略是 `sequence_contiguous`，说明后端训练主线已经在强调**按序列切分、防止连续帧泄漏**。
- `backend-train-model/All-train-model` 里已经存在：
  - `build_merged_clothes_dataset.py`：负责合并多源工服数据、生成 `dataset.yaml`、`manifest.csv`、`missing_review.csv`
  - `generate_split_manifests.py`：负责生成 source-balanced / holdout split manifests
  - `review/`、`splits/`、`artifacts/`：说明当前后端训练主线已经有比较规范的数据治理能力

因此，本文的结论不是“用 `otherMonitor` 替换 `backend-train-model`”，而是：

- **保留 backend 现有的数据治理与切分主线**
- **吸收 otherMonitor 中对检测逻辑、实验流程、混合训练更实用的部分**

---

## 4. `BarrierMonitor`：隔离栏缺失检测逻辑

### 4.1 当前阶段实现

这个目录最核心的文件是：

- `otherMonitor/BarrierMonitor/BarrierMonitor.py`
- `otherMonitor/BarrierMonitor/best.pt`
- `otherMonitor/BarrierMonitor/test_video_2.mp4`
- `otherMonitor/BarrierMonitor/test_video_3.mp4`
- `otherMonitor/BarrierMonitor/D15_20260116111912_labels/`

这说明它不是一个纯训练目录，而是一个**已经在做视频检测 + 事件判断 + 结果输出**的业务化脚本。

### 4.2 检测对象与类别语义

`BarrierMonitor.py` 中写死了 4 个类别映射：

- `0 -> barrier_post`
- `1 -> compliant_barrier`
- `2 -> idle_barrier`
- `3 -> car`

这四类的设计非常关键，因为它说明该模型不是在做“一个 barrier 类别”，而是在做**隔离栏部件/状态 + 车辆**的联合检测。也就是说，它不是只靠单一障碍物框来判断，而是把“车辆是否在位”“隔离栏是否处于合规状态”“隔离栏是否闲置/收起”一起建模了。

对业务来说，这比单纯检测一个框更有表达力，因为报警条件不是“看到某个物体”，而是“**车辆在 ROI 内稳定停住后，合规隔离栏没有出现**”。

### 4.3 推理总流程

`BarrierMonitor.py` 的总流程可以概括为：

1. **整帧送入 YOLO 模型推理**
2. **按类别把结果拆成车辆和隔离栏相关框**
3. **针对每个加油位 ROI 分别跑状态机**
4. **基于时间、移动趋势、是否存在合规隔离栏，决定是否报警**
5. **把报警状态持续保存到 `active_alarms`**
6. **将可视化结果写入输出视频**

这说明它不是“单帧检测脚本”，而是“**检测 + 时序事件判定 + 报警管理 + 可视化输出**”的完整闭环。

### 4.4 更详细的逻辑拆解

#### 4.4.1 输入层

- 输入是视频帧，来自 `cv2.VideoCapture(video_path)`
- 推理时直接把整帧传给 YOLO：`self.model(frame, verbose=False, device='cpu')[0]`
- 当前脚本把推理设备固定成了 `cpu`

这说明当前实现更偏验证/演示，而不是高吞吐部署版本。

#### 4.4.2 目标拆分层

推理返回后，代码会遍历 `results.boxes`，按类别拆成：

- `vehicles`：只接收 `cls_id == 3`
- `barriers`：接收 `cls_id in [0,1,2]`

这个拆分非常重要，因为后续的业务状态机并不是在“所有检测框”上运行，而是分别处理：

- 车辆：决定加油位里是否有车、车是否开始移动
- 隔离栏：决定当前 ROI 里是否有**合规隔离栏**

#### 4.4.3 ROI 判断层

脚本不是全图统一判断，而是为每个站位维护一块 ROI，比如：

- `station_1: [190, 300, 700, 700]`
- `station_2: [500, 400, 1200, 900]`

一个框是否属于该 ROI，不是简单判断左上角，而是用了双条件：

1. 框中心点落在 ROI 内
2. 或者框与 ROI 的重叠比例大于 `0.5`

这比单纯中心点判断稳健，因为一些大框可能中心点刚好偏出 ROI，但本体大部分还在 ROI 内。

#### 4.4.4 车辆运动判断层

代码对每个 station 保存 `last_vehicle_position`，然后用当前车框中心点与上一帧中心点的位移来判断是否移动：

- 位移阈值：`moving_threshold = 15.0`

如果位移大于这个阈值，就把 `vehicle_moving = True`。

这意味着：

- 它没有上复杂跟踪器
- 也没有用多帧 Kalman 轨迹
- 只是用“上一帧中心点 vs 当前帧中心点”的轻量规则做移动判断

这种方式实现成本低，但也有边界：

- 相机抖动时可能误判
- 同一 ROI 多车时可能混淆
- 只取 `station_vehicles[0]`，默认每个 ROI 里只有一个主要车辆
- 脚本里虽然还定义了更严格的 `_is_stationary()` 多帧停稳判断，但主流程实际没有调用，说明当前实现仍是“单帧位移阈值版”

#### 4.4.5 状态机层

这是 `BarrierMonitor` 最有价值的部分。

它定义了这些状态：

- `IDLE`
- `VEHICLE_ENTERED`
- `VEHICLE_STATIONARY`
- `TIMER_WAITING`
- `BARRIER_CHECKING`
- `ALARM_TRIGGERED`
- `BARRIER_DETECTED`
- `VEHICLE_LEAVING`

真正的业务逻辑不是“有框就报警”，而是下面这条状态链：

##### 阶段 A：车辆进入并停稳

- 初始状态是 `IDLE`
- 一旦 ROI 内出现车辆，就进入 `VEHICLE_STATIONARY`
- 记录 `stationary_start = timestamp`

##### 阶段 B：等待时间窗口

当车辆处于 `VEHICLE_STATIONARY` 一段时间后：

- 如果持续时间超过 `wait_duration = 1.0` 秒
- 状态进入 `TIMER_WAITING`
- 再等一个 `wait_duration = 1.0` 秒
- 之后才进入 `BARRIER_CHECKING`

这个设计非常像“延时确认”：

- 避免车辆刚停进来就立刻判断
- 给隔离栏放下/移动留出缓冲时间

##### 阶段 C：检查合规隔离栏

进入 `BARRIER_CHECKING` 后，代码并不是检查任意 barrier，而是调用 `_check_barrier_in_roi()`：

- 只把 `cls_id == 1` 当成 **compliant_barrier**
- 同时要求 `conf >= 0.3`
- 且该 barrier 必须在 ROI 内

也就是说：

- `barrier_post`
- `idle_barrier`

都**不能**直接解除“缺失隔离栏”的风险，只能 `compliant_barrier` 才算真正“隔离栏已到位”。

这是非常明确的业务建模，不是纯视觉上的“检测到了某个杆子就算成功”。

##### 阶段 D：缺失持续计时

如果在 `BARRIER_CHECKING` 里没有检测到合规隔离栏：

- 第一次缺失时，记录 `barrier_missing_start = timestamp`
- 后续每帧都计算 `missing_duration = timestamp - barrier_missing_start`
- 只有当缺失持续超过 `leaving_buffer_time = 10.0` 秒后，才进入 `ALARM_TRIGGERED`

这里的精髓是：

- **不是一帧没看到就报警**
- 而是“持续缺失足够久”才报警

这对真实场景非常重要，因为遮挡、漏检、人员经过、光照变化都会导致短时丢框。

##### 阶段 E：报警后的恢复逻辑

进入 `ALARM_TRIGGERED` 后：

- 如果车开始移动，直接转入 `VEHICLE_LEAVING`，并清理报警
- 如果之后重新检测到合规隔离栏，则累计 `barrier_detect_count`
- 当累计达到 `barrier_confirm_frames = 1` 后，恢复到 `BARRIER_DETECTED`

也就是说当前版本的“报警解除门槛”很低：

- 只要 1 帧重新看到合规隔离栏就能恢复

这在演示环境里足够，但如果用于线上，通常建议提高为 3~5 帧，以降低单帧误检带来的抖动恢复。

#### 4.4.6 active_alarms 机制

脚本额外维护了一个 `active_alarms` 字典：

- 某个 station 一旦出报警，会把报警对象写进去
- 后续帧即使当前帧没有新生成 alarm，也会继续把旧 alarm 带出来
- 只有在状态恢复为 `BARRIER_DETECTED` 或 ROI 无车时，才会清理

这说明作者已经意识到一个现实问题：

- 报警不是“一帧事件”
- 而是需要跨帧持续显示和管理的业务状态

这也是 `BarrierMonitor` 比另两个目录更接近“真实业务检测”的地方。

#### 4.4.7 计时方式的一个隐含问题

`BarrierMonitor` 的所有“等待 1 秒”“缺失 10 秒”都是用 `time.time()` 算的，也就是**按处理时钟**而不是按视频真实时间戳算。

这意味着：

- 如果离线跑视频时处理速度快于真实帧率，1 秒业务等待会被“加速”
- 如果机器慢，处理速度低于真实帧率，1 秒等待会被“拉长”

所以它当前更像“演示型时间逻辑”，如果以后迁到线上或严格离线评估，建议改成：

- 使用视频原始帧时间戳
- 或使用 `frame_index / fps`

这样业务时间才更稳定。

### 4.5 可视化与输出层

`ResultVisualizer` 会把以下内容画到帧上：

- ROI 框
- 车辆框
- 隔离栏框
- 报警文字
- 帧号与时间
- 车辆数 / 隔离栏数 / 报警数

主函数还会：

- 打开测试视频
- 创建输出目录
- 写出结果视频 `barrier_detection_result.mp4`
- 统计报警历史
- 在终端打印每次新报警

说明它已经是一个“可跑 demo + 可留结果视频 + 可看日志”的完整验证脚本。

### 4.6 数据如何切分

从仓库现有文件看，`BarrierMonitor` 的数据信息并不完整：

- 目录里能看到的是 `D15_20260116111912_labels/` 下的 **146 个 YOLO 标注 txt**
- 标签里实际出现的类别 ID 为 `0/1/2/3`
- 我本地统计到的框数量约为：
  - `0`: 875
  - `1`: 241
  - `2`: 634
  - `3`: 776

但这个目录里**没有**看到：

- `dataset.yaml`
- train/val/test 清单
- 训练脚本
- 图片目录
- 数据切分策略说明

因此关于 `BarrierMonitor` 的数据切分，本文只能下这个结论：

1. 仓库里只保留了**一批标签文件和测试视频**
2. **训练集/验证集/测试集如何划分，在当前仓库中不可见**
3. 从命名上看，这些标签很可能来自某个视频序列抽帧后的样本，但无法确认是否按时间切分、按视频切分，还是只保留了某一段做演示

所以 `BarrierMonitor` 更像：

- **推理验证代码在仓库里**
- **训练准备过程在仓库外**

### 4.7 对 backend-train-model 的可取之处

这是三条路线里，对后续线上工服业务最值得借鉴的一条，但借鉴点主要不在“训练参数”，而在**业务后处理结构**。

#### 值得借鉴 1：检测与事件逻辑分层

`BarrierMonitor` 很清楚地区分了两层：

- 第一层：YOLO 负责提供视觉检测结果
- 第二层：状态机负责把视觉结果翻译成业务报警

`backend-train-model` 当前主线还是单类 `clothes` 检测训练。后续如果要做“未穿工服报警”，也不应该直接把“某帧没检测到 clothes”当成报警，而应该像 `BarrierMonitor` 一样，把：

- 人员存在
- 人员在 ROI 内
- 连续多帧未见工服
- 是否刚进入区域
- 是否已经离开区域

放进一个单独的业务状态机里。

#### 值得借鉴 2：ROI + 时间缓冲

工服检测在线上场景里也会遇到这些问题：

- 人员刚进入画面，框不稳定
- 遮挡造成短时漏检
- 回头、蹲下、弯腰造成局部缺失

所以直接单帧报警会非常抖。`BarrierMonitor` 的“等待窗口 + 缺失持续时间 + 恢复确认帧”这套思路，适合未来接入工服报警。

#### 值得借鉴 3：事件级评估思路

当前 `backend-train-model` 更关注检测指标，例如 precision / recall / mAP。  
但如果进入业务阶段，还需要引入：

- 事件级 TP / FP / FN
- 报警持续时长
- 平均触发延迟
- 每站位/每相机误报率

`BarrierMonitor` 虽然还没有成体系评估脚本，但它已经有了事件对象和报警历史，这一步很容易扩展成事件级评估。

#### 不建议直接照搬的部分

也要明确它当前的限制：

- ROI 写死在代码里
- 输出目录是绝对路径
- 推理设备固定 `cpu`
- 默认一个 ROI 里只处理一辆车
- 恢复确认只要 1 帧，线上可能过于激进
- 相对路径依赖当前工作目录，不够稳健
- `VEHICLE_ENTERED` 这个状态被定义了，但主流程基本没真正进入它
- 报警计数更偏 demo 统计，不是严格事件日志体系

所以结论是：

> `BarrierMonitor` 最值得借鉴的是“检测结果如何升格为业务报警”的逻辑，而不是它现在这份脚本的具体硬编码实现。

---

## 5. `call_runs`：calling 检测训练实验归档

### 5.1 当前阶段实现

`call_runs` 目录的真实状态并不是一个完整检测工程，而更像是 **Ultralytics YOLO 的训练产物归档**。其核心内容在：

- `otherMonitor/call_runs/calling/`
- 里面有多组 run：
  - `yolo11m-gpu`
  - `yolo11m-gpu2`
  - `yolo11n-gpu`
  - `yolo11s-gpu`
  - `yolov8s-gpu`
  - `yolov8s-gpu2`

每组 run 下常见的文件有：

- `args.yaml`
- `results.csv`
- `weights/best.pt`
- `weights/last.pt`
- `BoxPR_curve.png`
- `BoxF1_curve.png`
- `confusion_matrix.png`
- `val_batch*_pred.jpg`

这说明它重点在做：

- 多模型版本横向对比
- 保留完整训练指标与可视化产物

但目录里**没有看到完整推理服务逻辑**。

### 5.2 这条路线的“检测逻辑”到底是什么

这里要特别说明：`call_runs` 的“检测逻辑”并不像 `BarrierMonitor` 那样体现在 Python 服务脚本里，而是体现在 **训练配置与实验矩阵** 里。

也就是说，它更像在回答：

- YOLO11n / YOLO11s / YOLO11m / YOLOv8s 哪个更合适？
- 在 calling 数据集上用哪些默认增强和训练参数？
- 哪个 run 的 best.pt 最值得保留？

而不是回答：

- 视频怎么读？
- 帧率怎么控？
- 报警怎么做？
- 结果怎么上报？

所以如果严格说“检测逻辑”，`call_runs` 当前体现的是：

1. 采用 **Ultralytics YOLO detect** 标准检测任务
2. 使用统一数据集配置 `data_calling.yaml`
3. 用统一训练 recipe 跑多个模型族
4. 用验证集比较指标，择优保留 `best.pt`

它是**训练逻辑强、业务逻辑弱**的一条路线。

### 5.3 更详细的训练逻辑

从 `args.yaml` 看，`call_runs` 的主要完整 run 具有这些共同特征：

- `task: detect`
- `mode: train`
- 模型包括 `yolo11m.pt`、`yolo11s.pt`、`yolo11n.pt`、`yolov8s.pt`
- 多数完整 run：
  - `epochs: 120`
  - `patience: 30`
  - `imgsz: 960`
  - `batch: 16`
  - `device: 0`
  - `workers: 8`
  - `seed: 42`
  - `deterministic: true`
  - `amp: true`
  - `close_mosaic: 10`

增强策略也相对统一：

- `mosaic: 1.0`
- `scale: 0.4`
- `translate: 0.1`
- `fliplr: 0.3`
- `hsv_s: 0.4`
- `hsv_v: 0.25`
- `auto_augment: randaugment`
- `erasing: 0.4`

这说明它想做的是：

- 用**尽量一致的训练条件**
- 横向比较不同模型架构

从训练工程角度看，这是比较规范的。

### 5.4 指标表现与异常点

从仓库里现有 `results.csv` 和 `summary-gpu.json` 看，大致可以得到这些现象：

- `yolo11m-gpu2`、`yolov8s-gpu2` 是较完整的对比 run
- `yolo11s-gpu` 后段结果出现 `0` 和 `nan`，说明训练或验证过程中存在明显异常
- `yolo11n-gpu` 只有很少结果，像是中断或未完整训练
- `summary-gpu.json` 只汇总了一条 `yolo11m-gpu` 记录，不足以作为完整 leaderboard
- `run_summary.csv` 还是空文件，说明最终汇总脚本没有收尾好

也就是说，这条路线**实验意识是对的**，但**最终收口文档和汇总自动化还不够完整**。

### 5.5 数据如何切分

这是 `call_runs` 最大的不透明点。

仓库里能看到：

- `args.yaml` 中写的是外部数据集 YAML：
  - `/root/merged_calling_dataset/processed_calling/data_calling.yaml`
  - 或 Windows 路径版本
- `split: val` 说明训练过程中验证集是存在的

但仓库里看不到：

- `data_calling.yaml`
- train/val/test 目录定义
- 数据合并脚本
- split manifest
- 按序列切分还是随机切分

因此只能得出：

1. **它明确存在验证集**
2. **它用外部 calling 数据集配置训练**
3. **train / val / test 的比例与切分原则，在仓库内不可见**

对 `backend-train-model` 来说，这一点非常重要：

> 不能把 `call_runs` 的结果直接当成“可无脑复用的切分范式”，因为它的切分过程没有被保存在仓库里。

### 5.6 对 backend-train-model 的可取之处

#### 值得借鉴 1：多模型横向对比机制

`backend-train-model` 当前已经有较好的数据治理，但如果只固定一个模型尺寸，后续容易把“数据问题”和“模型容量问题”混在一起。

`call_runs` 的优势在于：

- 同一数据集
- 同一训练 recipe
- 多个模型家族并行对比

这对 backend 很有价值。未来可以在工服训练里固定：

- 一套统一的 `dataset.yaml`
- 一套统一的 split manifests
- 然后对比 `yolov8s / yolo11s / yolo11m`

这样更容易看出：

- 误报是不是因为模型太小
- 漏报是不是因为分辨率不够
- 训练不稳定是不是模型/参数不匹配

#### 值得借鉴 2：高分辨率训练意识

`call_runs` 大部分完整 run 采用 `imgsz: 960`。  
对于监控场景的小目标，这种思路是合理的。

工服检测尤其在全身较远、画面拥挤时，也可能需要比较：

- `640`
- `960`

而不是固定认为 `640` 一定够用。

#### 值得借鉴 3：保留完整训练 artifacts

这条路线保留了：

- `results.csv`
- PR/F1 曲线
- confusion matrix
- val batch 可视化图

这些东西对 `backend-train-model` 很有现实价值，因为后续做 FP/FN 复盘时，不能只看一个最终 JSON 指标。

#### 值得借鉴 4：坚持用 `best.pt` 而非 `last.pt`

从这些 run 的现象看，后期 epoch 并不总是更好。  
这提醒 backend 主线在自动化流程里要明确：

- 训练结束后默认使用 `best.pt`
- `last.pt` 只用于续训或排查

#### 当前能力边界

也要明确这条路线现在**不适合直接当业务模板**：

- 没有推理入口
- 没有报警逻辑
- 没有切分脚本
- 数据 YAML 不在仓库
- 汇总文件不完整

所以它更适合被视为：

> “训练实验组织方式的参考目录”，而不是“上线检测方案模板”。

---

## 6. `smoke`：抽烟检测训练 / 验证 / 演示样例

### 6.1 当前阶段实现

`smoke` 是三条路线中最接近“完整小工程”的一条。目录里能看到：

- `otherMonitor/smoke/42_demo/1_train.py`
- `otherMonitor/smoke/42_demo/2_val.py`
- `otherMonitor/smoke/42_demo/3_webcam.py`
- `otherMonitor/smoke/ultralytics/cfg/datasets/A_my_data.yaml`
- `otherMonitor/smoke/picture/data/`
- `otherMonitor/smoke/picture/labels/`

这说明它至少在形式上把流程拆成了三段：

1. 训练
2. 验证
3. demo 推理

这种拆法虽然简单，但比把所有东西揉成一个脚本更清楚。

### 6.2 训练逻辑

`1_train.py` 当前实际启用的是：

- `YOLO("yolov8s.yaml").load("yolov8s.pt")`
- 使用预训练权重微调
- 数据配置来自 `A_my_data.yaml`
- `epochs = 100`
- `imgsz = 960`
- `batch = 4`
- `workers = 0`
- `resume = True`
- `amp = True`
- 输出目录 `./runs`

脚本里还保留了注释掉的其他实验版本：

- `yolo11n`
- `yolo11s`
- `yolov5n`

这说明作者做过一定程度的模型尝试，但最终当前激活版本是 `yolov8s`。

### 6.3 验证逻辑

`2_val.py` 逻辑非常直接：

- 加载 `runs/detect/yolov8n/weights/best.pt`
- 调用 `model.val(...)`
- 使用：
  - `imgsz = 640`
  - `batch = 4`
  - `conf = 0.25`
  - `iou = 0.6`
  - `device = "0"`
  - `workers = 0`

它的特点是：

- 没有额外业务逻辑
- 没有后处理状态机
- 完全是标准 YOLO 验证接口

也就是说，`smoke` 当前强调的是“**训练可跑通、验证可跑通**”，而不是业务事件判定。

### 6.4 demo 推理逻辑

`3_webcam.py` 更像一个最小演示脚本：

1. 加载 `yolov8s.pt`
2. 打开视频 `images/resources/demo.mp4`
3. 每帧调用 `model(frame)`
4. 用 `results[0].plot()` 直接画框
5. 用 `cv2.imshow` 显示结果

它体现出来的不是复杂工程能力，而是：

- 先快速验证模型能跑
- 先看视觉效果

这对早期项目迭代其实很有用，因为很多时候先看 demo，能比先读一堆指标更快发现问题。

但也正因为它过于简单，反而暴露出一个很重要的边界：

- `1_train.py` 当前训练的是 `yolov8s` 自定义烟雾模型
- `2_val.py` 却去验证 `runs/detect/yolov8n/weights/best.pt`
- `3_webcam.py` 又直接加载通用的 `yolov8s.pt`

也就是说，这三个脚本在当前仓库里**并没有形成完全一致的一套“同一模型训练 -> 同一模型验证 -> 同一模型 demo”闭环**。  
它更像是作者在不同阶段留下的几个脚本样例，而不是已经完全收拢好的统一工程入口。

### 6.5 数据如何切分

这是 `smoke` 相比 `call_runs` 更透明一点的地方，因为它至少把数据 YAML 放进了仓库里。

`A_my_data.yaml` 中明确写了：

- 数据根目录：`smoke42_yolo_format/`
- `train`：`images/train`，约 **16551** 张图
- `val`：`images/test`，约 **4952** 张图
- `test`：也是 `images/test`
- 类别：`smoking`

这说明它的数据切分特征很清楚：

1. 它有显式的 train / val / test 字段
2. 但 **val 和 test 指向同一个目录**

这一点要特别提醒：

> 从训练工程角度，这种写法不够严谨，因为它等于把验证集和测试集复用了。

如果只是 demo 或小型项目，这样写可能为了省事；  
但如果是 `backend-train-model` 这种要稳定做 baseline 的训练主线，**不建议照搬**。

### 6.6 仓库内本地样本子集

除了外部 `smoke42_yolo_format` 数据集外，仓库里还保留了一份本地样本子集：

- `otherMonitor/smoke/picture/data/`
- `otherMonitor/smoke/picture/labels/`

我本地统计到：

- 图片数：**448**
- 标签数：**448**
- 类别：单类 `smoke`

这份本地数据更像：

- 项目内留样
- 或某一批场景样本

但它**不是完整训练集**，因为 YAML 中的训练规模远大于 448。

### 6.7 混合训练信息

`otherMonitor/smoke/42_demo/runs/readme.txt` 中能读到一个关键信息：

- `train5` 是**公共数据集 + 加油站数据集混合训练**
- 其余模型更偏向**公共数据集训练**

这点非常有价值，因为它反映了一个很常见、也很实用的路线：

1. 用公共数据集学通用特征
2. 再用现场数据拉近域差异
3. 通过混合训练提升真实场景表现

从现有 `results.csv` 粗看：

- `train5`（混合训练）最终 `mAP50-95` 大约在 `0.705`
- 只基于公共数据集的几组结果，大约在 `0.683 ~ 0.698`

不能说这就是严格公平对比，因为图像尺寸、AMP、模型版本也有差异；  
但它至少提供了一个方向：

> **现场数据混入训练后，通常会比只靠公共数据更贴近真实部署场景。**

### 6.8 对 backend-train-model 的可取之处

#### 值得借鉴 1：公共数据 + 现场数据混训

这是 `smoke` 路线最值得 backend 借鉴的地方。

对于工服检测来说，未来也可能遇到：

- 自有现场数据量不够
- 场景多样性不足
- 某些姿态或光照很少见

这时可以考虑：

- 先引入外部公共人/工装/作业服相关数据
- 再与加油站现场工服数据做混训

但要注意，backend 当前已经有较成熟的 manifest 和 split 体系，所以应该：

- 在 backend 的 manifest / split / holdout 体系内混入公共数据
- 而不是像 `smoke` 一样只在外部 YAML 里简单指路径

#### 值得借鉴 2：训练、验证、demo 分拆

`smoke` 虽然简单，但把：

- train
- val
- demo

分成了三个文件。  
这对后续维护和排查很方便。

`backend-train-model` 主线偏训练自动化；后续如果要给业务侧或算法侧做快速验证，也可以考虑补一层：

- 轻量验证脚本
- demo 视频脚本

方便在不跑完整训练链路时快速看效果。

#### 值得借鉴 3：保留项目内小样本可视检查集

`smoke/picture/` 这种做法也有现实意义：

- 不一定作为正式训练全集
- 但非常适合作为项目内固定检查样本

`backend-train-model` 后续也可以保留一小批“固定复核图”，用于：

- 每次模型升级后快速人工复看
- 跟踪典型误报 / 漏报场景

#### 当前能力边界

也要看清这条路线的不足：

- `val` 与 `test` 复用同一目录
- 数据根目录是外部绝对路径
- demo 仍是单帧级可视化，没有业务时序逻辑
- 训练脚本里保留了不少注释式试验代码，规范性一般
- `train / val / demo` 三个脚本当前使用的权重入口并不完全一致

所以 `smoke` 更适合作为：

> “小型检测项目如何快速起步”的参考，而不是“严格训练基线体系”的最终模板。

---

## 7. 三条路线对 backend-train-model 的综合启发

### 7.1 当前最应该吸收的部分

如果只看对 `backend-train-model` 当前工服主线最有价值的能力，我认为优先级是：

#### 第一优先级：吸收 `BarrierMonitor` 的时序后处理

原因是：

- backend 现在已经有比较完整的数据构建和 split 体系
- 真正欠缺的不是再来一套不透明训练目录
- 而是未来如何把检测模型接成“业务报警”

所以最值得前移设计的是：

- ROI 约束
- 连续帧确认
- 缺失持续时间
- 报警恢复逻辑
- 事件级指标

#### 第二优先级：吸收 `call_runs` 的实验组织方式

backend 已经能构建 dataset 和 holdout，接下来最该补的是：

- 同数据、同 split 下的多模型 benchmark
- 自动汇总每个 run 的关键指标
- 固定保留训练 artifacts

这能让 baseline 更可复现、更可比较。

#### 第三优先级：吸收 `smoke` 的混训思路

这适合作为中期增强路线：

- 当现场工服数据的覆盖不足时
- 引入公共数据做混合训练
- 但必须保留 backend 自己的 holdout 隔离规则

### 7.2 不建议吸收的部分

也要明确哪些做法不建议迁移：

- `BarrierMonitor` 的硬编码 ROI、硬编码输出路径
- `call_runs` 的“数据 YAML 在仓库外、切分逻辑不在仓库内”
- `smoke` 的“val 与 test 共用同一目录”

对 `backend-train-model` 来说，现有最宝贵的资产之一就是：

- 切分过程可追踪
- manifest 可回溯
- holdout 可复现

这部分不能因为借鉴 `otherMonitor` 而退化。

---

## 8. 当前能力边界

结合三条路线和 backend 当前主线，可以把当前能力边界总结为：

1. **训练侧**
   - `backend-train-model` 已经强于 `otherMonitor` 三条路线的数据治理方式
   - 但在“多模型 benchmark 自动汇总”和“轻量 demo 验证”上还可以继续补

2. **业务侧**
   - `BarrierMonitor` 已经展示了时序告警的雏形
   - `backend-train-model` 当前仍主要停留在检测训练 baseline 阶段
   - 还没有完整走到“检测 -> 事件 -> 报警”的闭环

3. **数据侧**
   - `smoke` 展示了混合数据训练的潜力
   - `call_runs` 展示了多模型对比的必要性
   - 但两者在“数据切分可审计性”上都不如 backend 当前主线

---

## 9. 升级触发条件

如果出现下面这些需求，建议把本文提到的借鉴点转成实际代码或流程升级：

### 9.1 触发 `BarrierMonitor` 风格升级的条件

- 工服检测从“离线评估”转向“在线报警”
- 需要按加油位、ROI、人员停留状态做事件判断
- 误报来自单帧抖动，而不是模型完全看不见

### 9.2 触发 `call_runs` 风格升级的条件

- 当前 baseline 接近瓶颈
- 需要比较不同模型尺寸、不同输入分辨率
- 团队开始频繁问“为什么选这个模型而不是另一个模型”

### 9.3 触发 `smoke` 风格升级的条件

- 现场工服样本不足
- 长尾场景越来越多
- 纯现场数据训练出现泛化瓶颈

---

## 10. 后续演进路线

如果把这三条路线的优点有序吸收进 `backend-train-model`，我建议按下面的顺序推进：

### 第一步：保留 backend 当前 split/holdout 主线不动

继续把：

- `sequence_contiguous`
- source-balanced split
- unified holdout
- manifest / review / report

作为训练侧基础设施，先不要动摇。

### 第二步：补一层 `call_runs` 风格的 benchmark 矩阵

在同一套 backend 数据与 split 下，对比：

- `yolov8s`
- `yolo11s`
- `yolo11m`

并自动汇总：

- precision / recall / mAP50 / mAP50-95
- 推理速度
- 权重大小
- FP/FN 典型样本

### 第三步：补一层 `smoke` 风格的混合训练分支

在 backend 的 manifest 体系内引入：

- 公共数据 source
- 现场数据 source
- 分 source 的统计报表

严格保证：

- holdout 不泄漏
- 公共数据不会把现场 test 污染

### 第四步：接入 `BarrierMonitor` 风格的业务时序后处理

当检测模型稳定后，再往业务层叠加：

- ROI
- 连续帧确认
- 进入/离开状态
- 报警持续与恢复
- 事件级评估指标

这个阶段才是真正从“训练模型”走向“可上线检测方案”。

---

## 11. 最终结论

一句话总结三条路线：

- **`BarrierMonitor`** 最像真实业务检测，最有价值的是 **ROI + 状态机 + 告警去抖**
- **`call_runs`** 最像训练实验归档，最有价值的是 **多模型 benchmark 与 artifacts 留存**
- **`smoke`** 最像小型可跑通工程，最有价值的是 **公共数据 + 现场数据混训思路**

一句话总结对 `backend-train-model` 的建议：

> 训练主线继续坚持 backend 现有的可审计切分与 baseline 体系，不要退回到外部 YAML + 不透明 split；但可以有计划地吸收 `call_runs` 的实验管理、`smoke` 的混训思路，以及 `BarrierMonitor` 的时序告警逻辑。

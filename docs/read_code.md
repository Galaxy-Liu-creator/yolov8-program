# inspection-flask 代码阅读顺序

这份文档的目标不是“把所有文件都读一遍”，而是帮你先抓住 `inspection-flask` 的主链路，再按优先级补细节。  
如果你想**最快理解代码逻辑**，建议始终围绕下面这条主线去看：

`启动 Flask -> 注册应用组件 -> 启用摄像头线程 -> 拉取帧 -> 人员检测 -> 工服检测 -> 时序判定 -> 保存违规图片/记录 -> 前端/接口查询结果`

---

## 1. 先用一句话理解这个项目

`inspection-flask` 本质上是一个 **基于 Flask 的摄像头巡检服务**：

- 一部分代码负责 **Web/API/摄像头管理**
- 一部分代码负责 **视频帧采集与缓存**
- 一部分代码负责 **YOLOv8 两阶段检测**
  - 先检出 `person`
  - 再对人员框裁剪后检出 `clothes`
- 一部分代码负责 **时序规则判断**
- 最后把违规截图保存到磁盘，并在可用时写入数据库

所以它不是单纯的“模型推理脚本”，而是一个 **Flask + 线程调度 + 检测规则 + 存储查询** 的组合系统。

---

## 2. 阅读前先知道的几个关键事实

### 2.1 主运行链路有两条

- **在线主链路**：`inspection-flask/app.py` + `inspection-flask/applications/...`
  - 这是实际的 Flask 服务、摄像头线程、违规事件处理主线
- **离线辅助链路**：`inspection-flask/main.py`
  - 这是一个独立的诊断/验证工具，不依赖 Flask 上下文
  - 用于离线检查权重、单图推理、批量验证

换句话说，**如果你的目标是理解系统在线运行逻辑，先不要从 `main.py` 开始。**

### 2.2 这个项目支持“无数据库降级运行”

很多逻辑都不是“数据库必须可用”：

- 数据库不可用时，接口会退化到内存数据
- 违规事件也可以只保存在内存列表和磁盘图片里

这意味着你读代码时要特别关注：

- `database_ready`
- `camera_registry`
- `violation_events`
- `camera_runtime_overrides`

这些运行时内存状态在 `create_app()` 里初始化，后面很多分支都依赖它们。

### 2.3 当前检测是“两阶段”

不是“一次模型推理直接判断工服”：

1. 先做人检测
2. 再截取 person 区域
3. 再跑工服检测
4. 再做 ROI、面积阈值、时序窗口等规则判断

所以读代码时不要只盯模型封装，要连着线程、窗口和违规规则一起看。

### 2.4 有一个环境版本提示值得注意

- 仓库说明里默认 Python 环境是 Conda `yolo_code`，版本 `3.9.25`
- 但 `inspection-flask/pyproject.toml` 声明 `requires-python = ">=3.10"`

这不影响你阅读代码，但如果后续你要跑 `pyproject.toml` 里的依赖安装或打包流程，这里可能需要额外确认环境版本。

---

## 3. 推荐阅读顺序（最快理解版）

如果你现在是第一次整体熟悉代码，建议按下面顺序看。

### 第 1 步：先看启动入口和全局配置

先读这 4 个文件：

1. `inspection-flask/app.py`
2. `inspection-flask/applications/__init__.py`
3. `inspection-flask/applications/config.py`
4. `inspection-flask/settings.py`

### 为什么先看这组

因为这组文件决定了整个系统的“骨架”：

- Flask 怎么创建
- 日志怎么初始化
- 数据库和检测模型什么时候加载
- 调度器什么时候启动
- 运行时共享状态放在哪里
- 所有阈值、权重、ROI、时序参数从哪来

### 看这一步时重点回答 6 个问题

1. `create_app()` 初始化了哪些 `app.config` 运行时对象？
2. 检测模型在哪里加载？失败后系统怎么退化？
3. 数据库连不上时，系统是否还能继续启动？
4. 哪两个 manager 负责“拉帧”和“处理帧”？
5. 定时任务 scheduler 会定时做什么？
6. 关键阈值都集中在 `settings.py` 的哪些字段？

### 你应该重点盯的变量

- `detection_pipeline_ready`
- `detection_model_init_error`
- `database_ready`
- `hk_threadManager`
- `hk_recorder_thread_manager`
- `hk_frame_cache`
- `violation_events`
- `camera_registry`

---

## 4. 第二步：看接口层，理解“系统怎么被操作”

接着读：

1. `inspection-flask/applications/view/__init__.py`
2. `inspection-flask/applications/view/system/hk_camera.py`

这个阶段你要把它当成“业务入口控制器”来看。

### 为什么这一步很关键

因为你真正想理解系统如何运行，最直接的问题其实是：

- 摄像头从哪里启用？
- 线程从哪里启动？
- 违规记录从哪里查询？
- 无数据库时系统怎么工作？

这些都集中在 `hk_camera.py`。

### 建议重点看这些接口

- `/hk_camera/health`
  - 看系统健康状态怎么暴露
- `/hk_camera/data`
  - 看摄像头列表是来自数据库还是内存
- `/hk_camera/enable`
  - 看一个摄像头是如何被真正“拉起检测线程”的
- `/hk_camera/disable`
  - 看线程如何停止，运行时状态如何清理
- `/hk_camera/violations`
  - 看违规事件查询是怎么从 DB / 内存里取的
- `save_violate_photo(...)`
  - 这是“结果落盘/落库”的关键收口函数

### 看完这一步后，你应该已经能回答

- 一个摄像头从“配置对象”变成“运行中线程”的过程是什么？
- 运行时是优先走数据库，还是优先走内存？
- 违规图片保存后，哪些字段会被记录下来？
- 为什么这个文件既有路由，又有保存违规图的逻辑？

### 这一阶段的阅读技巧

不要一上来通读 `hk_camera.py` 全文件。  
建议按下面顺序跳读：

1. 先看辅助函数
   - `_database_ready`
   - `_collect_runtime_overrides`
   - `_build_runtime_camera`
2. 再看核心接口
   - `health`
   - `table`
   - `enable`
   - `dis_enable`
   - `violations`
3. 最后看结果保存相关
   - `_resolve_violate_rule`
   - `save_violate_photo`

---

## 5. 第三步：看“帧从哪里来”

接着读：

1. `inspection-flask/applications/common/hk_recorder_threading.py`
2. `inspection-flask/hk/hksdk/device.py`（按需）

### 这一步要解决的问题

你要先搞清楚：  
**检测线程处理的 frame，并不是自己直接拉流拿到的，而是先由 recorder manager 放进缓存，再由检测线程消费。**

### 重点看什么

- `get_img(...)`
  - 真正负责取图并写入 `hk_frame_cache`
- `HKRecorderThreadManager`
  - 管理“拉帧”这一侧的生命周期
- `_read_from_frame_path(...)`
  - 支持本地图片/目录输入，便于调试
- 与 `HKStream` 相关的逻辑
  - 对接海康或 RTSP 的来源

### 读完这一步你要形成的理解

可以把这一层理解成：

- **输入层**
  - 摄像头流 / RTSP / 本地图片目录 / 本地单张图
- **统一输出**
  - `app.config["hk_frame_cache"][camera_id] = {"frame": ..., "ts": ..., "frame_hash": ...}`

检测线程并不关心帧来自哪里，只关心缓存里有没有新的 frame。

---

## 6. 第四步：看最核心的“检测线程主循环”

这是最重要的一步，读：

1. `inspection-flask/applications/common/hk_custom_threading_plus.py`

如果只能精读一个文件，就精读这个文件。

### 为什么它最重要

因为这个文件把以下内容都串起来了：

- 帧消费
- 人员检测
- 工服检测
- ROI 过滤
- 面积过滤
- track 关联
- 时序窗口
- 违规判定
- 告警抑制
- 线程启停

### 推荐阅读顺序

#### 6.1 先看 `ThreadManager`

先从后往前看：

- `ThreadManager.add_thread`
- `ThreadManager.stop_thread`
- `ThreadManager.restart_all_threads`

因为这部分决定了摄像头线程的生命周期，能帮你把 `hk_camera.py` 里的 `/enable`、`/disable` 接起来。

#### 6.2 再看 `HKCustomThread.run`

这是主循环，建议按“while 每轮做了什么”去读：

1. 检查检测流水线是否 ready
2. 从 `hk_frame_cache` 取最新帧
3. 没帧就触发 recorder 再拉一次
4. 跑 `detect_persons`
5. 跑 `build_person_contexts`
6. 用 `SimpleIoUTracker` 关联 `track_id`
7. 把当前帧结果放入时间窗口 `self.window`
8. 窗口满了以后执行 `run_rule_engine`
9. 如果触发违规：
   - 更新 `last_alert_ts`
   - 清空窗口
   - reset tracker
   - 发事件 / 记录日志

#### 6.3 然后看 3 个辅助逻辑

- `SimpleIoUTracker`
  - 解决“同一个人跨帧是不是同一个 track”
- `_in_roi`
  - 解决“人在不在感兴趣区域里”
- `build_person_contexts`
  - 解决“每个人最后会被封装成什么结构”

### 读完这一步后你应该记住一个核心数据结构

窗口里每一项大致是：

```python
{
    "camera_id": camera.id,
    "timestamp": timestamp,
    "frame": frame,
    "persons": [
        {
            "bbox": [...],
            "confidence": ...,
            "label": "person",
            "area": ...,
            "in_roi": True/False,
            "workwear_items": [...],
            "has_workwear": True/False,
            "track_id": ...
        }
    ]
}
```

只要你吃透这个结构，后面的违规规则代码会好读很多。

---

## 7. 第五步：看模型封装和“工服合规策略”

接着读：

1. `inspection-flask/utils/models.py`
2. `inspection-flask/utils/workwear_policy.py`

### 为什么这一步要放在线程主循环之后

因为如果你先看模型封装，很容易陷入“这是个 YOLO 包装类”的局部细节，反而不知道它在主链路里扮演什么角色。  
先看完线程主循环，再回来看这两个文件，会非常顺。

### 重点看什么

#### `utils/models.py`

- `select_runtime_device`
- `PersonDetector`
- `WorkwearDetector`
- `load_detection_models`

要理解的重点：

- 人和工服是两个模型
- 阈值和类别过滤来自 `settings.py`
- 返回格式都被统一成 `{"bbox", "confidence", "label"}`

#### `utils/workwear_policy.py`

- `get_person_crop`
- `extract_detected_labels`
- `evaluate_workwear_compliance`

要理解的重点：

- 人框裁剪是否使用白底背景
- 合规判定是 `any` 还是 `all`
- `WORKWEAR_LABELS` 和 `WORKWEAR_REQUIRED_LABELS` 的区别

---

## 8. 第六步：看违规规则模块

接着读：

1. `inspection-flask/violation_module/vio_workwear_missing.py`
2. `inspection-flask/violation_module/base.py`

### 为什么先看 `vio_workwear_missing.py`

因为当前主规则就是它。  
`base.py` 更像公共基类和存图辅助，你先知道规则怎么判，再回头看基类更容易理解。

### 你要重点抓的规则逻辑

`WorkwearMissingViolation.run()` 不是“单帧判断”，而是“按 track 做时间窗口统计”：

1. 遍历窗口内每一帧
2. 提取每个 person
3. 跳过无效 person
   - bbox 不合法
   - 不在 ROI
   - 面积不满足
4. 按 `track_id` 统计：
   - 出现次数 `appear`
   - 违规次数 `violation`
5. 只有满足：
   - `appear >= MIN_TRACK_APPEAR_FRAMES`
   - `violation / appear >= TEMPORAL_TRIGGER_RATIO`
   才真正触发
6. 触发后调用 `save(...)`，最终会走到 `save_violate_photo(...)`

### 这一层的本质

这一层是在回答：

> “这个人在最近几帧里，多大比例都没有穿工服，是否足以判成一次稳定违规？”

所以它是一个 **时序规则层**，不是检测模型层。

### `base.py` 里重点看什么

- `BaseVio.init`
- `BaseVio.add_plot_targets`
- `BaseVio.save`

你会看到：

- 违规框如何被选中
- 最终哪一帧被拿来画框存图
- 存图后如何回调到 `hk_camera.py` 的 `save_violate_photo(...)`

---

## 9. 第七步：再补数据库模型和扩展初始化

接着读：

1. `inspection-flask/applications/extensions/__init__.py`
2. `inspection-flask/applications/extensions/init_sqlalchemy.py`
3. `inspection-flask/applications/models/admin_hk_camera.py`
4. `inspection-flask/applications/models/admin_violate_photo.py`
5. `inspection-flask/applications/models/admin_violate_rule.py`
6. `inspection-flask/applications/schemas/admin_hk_camera.py`

### 这一步的目标

不是研究 ORM 细节，而是建立“数据存储映射关系”：

- 摄像头配置落在哪张表
- 违规结果落在哪张表
- 规则 ID / rule_code / rule_name 怎么关联
- 为什么部分查询会查 DB，部分情况下改走内存

### 阅读建议

这里只要读字段和关系，别深挖太久。  
主逻辑不在这里，这一层主要是帮你把接口返回和数据库结构对应起来。

---

## 10. 第八步：最后再看模板和低优先级辅助代码

最后按需读：

- `inspection-flask/templates/system/hk_camera/main.html`
- `inspection-flask/templates/system/hk_camera/add.html`
- `inspection-flask/templates/system/hk_camera/edit.html`
- `inspection-flask/applications/common/user_auth.py`
- `inspection-flask/applications/common/utils/rights.py`
- `inspection-flask/applications/common/utils/http.py`
- `inspection-flask/applications/common/curd.py`
- `inspection-flask/applications/common/utils/validate.py`

### 为什么放最后

这些文件能帮助你补齐：

- 前端页面怎么调接口
- 权限装饰器怎么工作
- 通用 API 返回格式是什么

但它们不是“检测主逻辑”的关键路径，所以不适合作为第一次阅读入口。

---

## 11. 不建议一开始优先看的文件

第一次熟悉项目时，这些文件建议延后：

- `inspection-flask/main.py`
  - 它更像离线诊断工具，不是在线主链路
- `inspection-flask/applications/common/utils/thread_camera.py`
  - 当前基本是占位
- `inspection-flask/inspection-flask_old` 对应旧目录（如果你只是理解现版本逻辑）
  - 先忽略，避免混淆

---

## 12. 一条最推荐的实际阅读路线

如果你准备真的开始看，我建议你按下面顺序打开文件：

1. `inspection-flask/app.py`
2. `inspection-flask/applications/__init__.py`
3. `inspection-flask/settings.py`
4. `inspection-flask/applications/view/system/hk_camera.py`
5. `inspection-flask/applications/common/hk_custom_threading_plus.py`
6. `inspection-flask/applications/common/hk_recorder_threading.py`
7. `inspection-flask/utils/models.py`
8. `inspection-flask/utils/workwear_policy.py`
9. `inspection-flask/violation_module/vio_workwear_missing.py`
10. `inspection-flask/violation_module/base.py`
11. `inspection-flask/applications/models/admin_hk_camera.py`
12. `inspection-flask/applications/models/admin_violate_photo.py`
13. `inspection-flask/applications/extensions/init_sqlalchemy.py`
14. `inspection-flask/main.py`（最后作为离线辅助工具补读）

这是我认为**最快进入主逻辑**的一条路线。

---

## 13. 按“问题驱动”去读，会更快

### 如果你最关心“摄像头启用后发生了什么”

按这个顺序读：

1. `hk_camera.py` 里的 `enable`
2. `hk_custom_threading_plus.py` 里的 `ThreadManager.add_thread`
3. `HKCustomThread.run`
4. `hk_recorder_threading.py` 里的 `get_img`

### 如果你最关心“为什么会判定为没穿工服”

按这个顺序读：

1. `HKCustomThread.build_person_contexts`
2. `utils/workwear_policy.py`
3. `vio_workwear_missing.py`
4. `settings.py` 里的工服标签、阈值、时序参数

### 如果你最关心“违规结果最后保存到哪里”

按这个顺序读：

1. `vio_workwear_missing.py` 里的 `run`
2. `base.py` 里的 `save`
3. `hk_camera.py` 里的 `save_violate_photo`
4. `admin_violate_photo.py`

### 如果你最关心“没有数据库时系统还能不能跑”

按这个顺序读：

1. `init_sqlalchemy.py`
2. `applications/__init__.py`
3. `hk_camera.py` 里的 `_database_ready`、`table`、`violations`、`save_violate_photo`

---

## 14. 你读完后，应该能在脑子里画出这张图

```text
HTTP/API
  -> hk_camera.py
      -> ThreadManager.add_thread()
          -> HKCustomThread.run()
              -> hk_frame_cache 取帧
              -> PersonDetector.infer()
              -> get_person_crop()
              -> WorkwearDetector.infer()
              -> evaluate_workwear_compliance()
              -> WorkwearMissingViolation.run()
                  -> BaseVio.save()
                      -> save_violate_photo()
                          -> 磁盘图片 + DB/内存事件
```

如果这张图你已经能复述出来，说明主逻辑已经掌握住了。

---

## 15. 给你的一个“30 分钟速读方案”

如果你现在时间不多，只读下面 6 个文件：

1. `inspection-flask/applications/__init__.py`
2. `inspection-flask/settings.py`
3. `inspection-flask/applications/view/system/hk_camera.py`
4. `inspection-flask/applications/common/hk_custom_threading_plus.py`
5. `inspection-flask/utils/models.py`
6. `inspection-flask/violation_module/vio_workwear_missing.py`

这 6 个文件读完，你基本就能掌握：

- 系统怎么启动
- 摄像头怎么启用
- 检测线程怎么工作
- 违规是怎么判的
- 结果怎么流转

然后再回头补：

- `hk_recorder_threading.py`
- `workwear_policy.py`
- `base.py`
- `save_violate_photo(...)`

---

## 16. 总结：最重要的 4 个文件

如果只让我挑 4 个最值得优先读的文件，我会选：

1. `inspection-flask/applications/__init__.py`
   - 看应用怎么装配
2. `inspection-flask/applications/view/system/hk_camera.py`
   - 看业务入口和结果落点
3. `inspection-flask/applications/common/hk_custom_threading_plus.py`
   - 看检测线程主循环
4. `inspection-flask/violation_module/vio_workwear_missing.py`
   - 看真正的违规判定规则

这 4 个文件串起来，就是整个系统的核心逻辑。


# Update Log

用于记录每次代码变更的详细内容、变更原因、涉及文件与配置项。

## 维护约束

以后每次更新都必须遵守以下规则：

1. **新记录在最上方**：新增的更新记录必须插入在旧记录的上方，保持"最新在前，历史在后"。
2. **必须写明变更来源**：每条更新记录必须注明触发变更的来源（如 check_log.md 的问题编号、check_detail_ROI.md 的条款、用户需求等）。
3. **必须列出涉及文件**：每条更新记录必须列出所有被修改或新增的文件路径。
4. **必须列出新增/变更的配置项**：如果变更涉及 `settings.py` 中的配置项，必须单独列出配置项名称、默认值和用途说明。
5. **必须标注兼容性影响**：如果变更修改了函数签名、数据结构、配置字段名等对外接口，必须在记录中标注"兼容性注意"。
6. **禁止删除历史记录**：历史更新记录不可删除，只可追加新记录。
7. **关联 check_log**：如果本次变更修复了 `check_log.md` 中的问题，必须在记录中注明对应问题编号和修复状态，并在后续复检时更新 `check_log.md` 中该问题的状态。
8. **保持一致性**：`settings.py` 中的配置项名称与代码中 `getattr(settings, ...)` 的引用必须一致。新增配置项后需全文检索是否有遗漏引用点。
9. **验证链路完整性**：涉及新文件创建（如 `utils/plots.py`）时，必须在记录中说明调用方、被调用签名以及已验证的兼容性。
10. **不改动的部分必须声明**：如果某些模块/逻辑被评估后决定不改动，必须在记录中说明原因，防止后续重复评估。

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

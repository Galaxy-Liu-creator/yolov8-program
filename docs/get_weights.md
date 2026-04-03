# inspection-flask 权重获取说明

这份文档说明 `inspection-flask` 当前需要的两个权重文件分别是什么、为什么需要它们、以及最实际的获取方式。

当前项目要求把两个 `.pt` 文件放到：

- `inspection-flask/weights/person_detect_yolov8.pt`
- `inspection-flask/weights/workwear_detect_yolov8.pt`

---

## 1. 先明确这两个权重分别做什么

当前 `inspection-flask` 的在线检测链路不是“一个模型直接判断是否违规”，而是两阶段：

1. 先检测整帧中的 `person`
2. 再裁剪出 `person crop`
3. 再在 `person crop` 里检测 `clothes`
4. 如果 ROI 内的 `person` 没检出 `clothes`，则判定为“疑似未穿工服”

所以这两个模型的职责分别是：

- `person_detect_yolov8.pt`
  - 用来做**人员检测**
- `workwear_detect_yolov8.pt`
  - 用来做**工服 / clothes 检测**

---

## 2. 为什么不能随便放两个 `.pt`

代码虽然只要求文件名和路径固定，但模型内容不能乱放。

至少要满足下面几点：

### 2.1 `person_detect_yolov8.pt`

- 必须能被 `ultralytics.YOLO(...)` 正常加载
- 检测结果中要能输出 `person`
- 最好是 YOLOv8 / Ultralytics 当前路线兼容的权重

### 2.2 `workwear_detect_yolov8.pt`

- 也必须能被 `ultralytics.YOLO(...)` 正常加载
- 检测结果中最好输出标签名 `clothes`
- 如果标签名不是 `clothes`，则需要同步修改 `inspection-flask/settings.py` 里的 `WORKWEAR_LABELS`

---

## 3. 当前项目的业务背景

结合代码和现有文档，当前项目的业务逻辑可以概括为：

- 监控 ROI 内的所有 `person`
- 对每个 `person` 裁剪图做工服检测
- 如果该人未命中 `clothes`，则视为当前帧不合规
- 再通过时间窗口和时序规则，决定是否生成最终违规事件

也就是说，这个项目当前不是训练“未穿工服”这个类别，而是：

- 一个 `person` 检测模型
- 一个 `clothes` 正类检测模型

由这两个模型组合出最终业务结果。

---

## 4. `person_detect_yolov8.pt` 怎么得到

这是最容易获取的一个。

### 推荐方案：直接使用官方 YOLOv8 检测权重

你可以直接使用官方通用检测权重，例如：

- `yolov8n.pt`
- `yolov8s.pt`
- `yolov8m.pt`

这些模型本身就支持 COCO 类别中的 `person`，因此通常可以直接用于当前项目的人检测阶段。

### 最实用的做法

拿到一个官方 YOLOv8 检测权重后，把它复制并重命名为：

- `inspection-flask/weights/person_detect_yolov8.pt`

### 这条路适合什么场景

- 先把系统跑起来
- 先验证主链路是否畅通
- 先调试 Flask、线程、ROI、告警逻辑

### 后续优化方向

如果后面你希望更贴合当前场景，比如：

- 加油站监控视角
- 特定分辨率
- 夜间 / 背光 / 遮挡较多

可以再基于你自己的场景数据微调一个专门的人检测模型，但这不是第一优先级。

---

## 5. `workwear_detect_yolov8.pt` 怎么得到

这个通常不能直接用官方通用权重代替，更实际的方式是**自己训练**。

因为当前项目里需要识别的是你们业务定义下的：

- `clothes`

根据当前仓库文档，数据集的口径是：

- 单类检测
- 类别只有：
  - `0 -> clothes`

所以 `workwear_detect_yolov8.pt` 本质上应该是一个：

- **YOLOv8 单类检测模型**
- 检测目标是 `clothes`

---

## 6. 训练 `workwear_detect_yolov8.pt` 时应该用什么数据

从当前在线推理逻辑来看，更推荐使用：

- **人物裁剪图**

原因是在线阶段不是在整张监控图里直接检测工服，而是：

1. 先检测 `person`
2. 再裁剪 `person crop`
3. 再在 `person crop` 里跑 `workwear_model`

所以训练数据如果也是“人物裁剪图 + `clothes` 标注”，训练分布会更接近推理分布。

### 理想训练数据

- 输入：人物裁剪图
- 标注：裁剪图中的 `clothes` 框
- 类别：只有 `clothes`

### 如果你现在只有整图标注

也不是完全不能训练，但效果可能不如“人物 crop 数据训练”的版本稳定。

原因是：

- 训练输入是整图
- 推理输入是 person crop

两者分布不完全一致。

---

## 7. 当前仓库的数据，能不能训练 `workwear_detect_yolov8.pt`

可以，但要理解清楚它训练出来的到底是什么。

根据 `docs/dataset.md` 和当前项目逻辑：

- 数据集是单类 `clothes`
- 它标注的是“正常工服正类”
- 它不是“穿工服 / 未穿工服”双类检测数据

所以你训练出来的是：

- **`clothes` 检测模型**

而不是：

- “未穿工服检测模型”

这与当前项目逻辑是匹配的，因为项目本来就是通过：

- `person` 检出
- `clothes` 未检出

来推断违规。

---

## 8. 最推荐的获取路径

### 方案 A：最快跑通项目

这是最现实、最推荐的路线。

#### `person_detect_yolov8.pt`

- 直接使用官方 YOLOv8 检测权重
- 复制并改名为：
  - `person_detect_yolov8.pt`

#### `workwear_detect_yolov8.pt`

- 使用当前 `clothes` 单类数据训练一个 YOLOv8 单类检测模型
- 将训练输出的 `best.pt` 改名为：
  - `workwear_detect_yolov8.pt`

这是最适合当前代码结构的方案。

---

## 9. `workwear_detect_yolov8.pt` 的训练流程示意

如果你使用 Ultralytics YOLOv8，基本流程如下。

### 9.1 准备数据集

保证数据满足 YOLO 检测格式：

- 图片文件：`.jpg` / `.png`
- 标注文件：`.txt`
- 每行格式：
  - `class_id x_center y_center width height`

当前类别口径应为：

- `0 -> clothes`

### 9.2 准备 `dataset.yaml`

示例：

```yaml
path: E:/your_dataset_root
train: images/train
val: images/val

names:
  0: clothes
```

### 9.3 训练命令示例

```bash
yolo detect train model=yolov8n.pt data=dataset.yaml imgsz=640 epochs=100 batch=16
```

训练结束后，通常会得到：

- `runs/detect/train/weights/best.pt`

把这个文件复制并改名为：

- `inspection-flask/weights/workwear_detect_yolov8.pt`

---

## 10. `person_detect_yolov8.pt` 的训练 / 获取方式

如果你的目标是尽快跑通项目，**不需要先自己训练**。

最直接的做法是：

- 直接使用官方 YOLOv8 检测权重

常见选择：

- `yolov8n.pt`
  - 最轻量，启动快
- `yolov8s.pt`
  - 通常更稳一点
- `yolov8m.pt`
  - 更大、更慢，但可能更准

拿到之后，复制为：

- `inspection-flask/weights/person_detect_yolov8.pt`

如果后续你对人检测效果不满意，再考虑基于自有场景数据做微调。

---

## 11. 放入项目后的目录结构

最终目录应该是：

```text
inspection-flask/
  weights/
    person_detect_yolov8.pt
    workwear_detect_yolov8.pt
```

放好之后，可以执行：

```bash
D:\Miniconda3_python\envs\yolo_code\python.exe inspection-flask\main.py check
```

如果自检通过，再启动服务：

```bash
D:\Miniconda3_python\envs\yolo_code\python.exe inspection-flask\app.py
```

---

## 12. 当前项目最短可执行方案

如果你的目标是“先跑起来”，建议按下面做：

### 第一步

先准备 `person_detect_yolov8.pt`

- 直接用官方 `yolov8n.pt` 或 `yolov8s.pt`
- 重命名为：
  - `person_detect_yolov8.pt`

### 第二步

准备 `workwear_detect_yolov8.pt`

- 使用你当前的 `clothes` 单类数据集训练一个 YOLOv8 检测模型
- 将 `best.pt` 重命名为：
  - `workwear_detect_yolov8.pt`

### 第三步

把两个文件都放进：

- `inspection-flask/weights/`

### 第四步

执行：

```bash
D:\Miniconda3_python\envs\yolo_code\python.exe inspection-flask\main.py check
```

### 第五步

如果 `check` 通过，再启动：

```bash
D:\Miniconda3_python\envs\yolo_code\python.exe inspection-flask\app.py
```

---

## 13. 额外提醒

### 13.1 标签名要对齐

当前代码默认要求：

- 人模型输出：`person`
- 工服模型输出：`clothes`

如果你的工服模型输出的不是 `clothes`，需要同步调整：

- `inspection-flask/settings.py`
  - `WORKWEAR_LABELS`

### 13.2 裁剪策略要和训练口径尽量一致

当前项目支持：

- `USE_WHITE_BG_MASK = True`
- `USE_WHITE_BG_MASK = False`

含义是：

- 如果你的工服模型是基于“白底裁剪图”训练的，倾向于设为 `True`
- 如果你的工服模型是基于“真实场景裁剪图”训练的，倾向于设为 `False`

### 13.3 离线验证要用当前数据集口径

当前仓库文档指出：

- 数据集是单类 `clothes`

因此做离线验证时，要优先使用与当前数据集一致的方式，例如：

```bash
python inspection-flask/main.py validate <images_dir> --labels <labels_dir> --gt-mode clothes-only --clothes-cls 0
```

---

## 14. 总结

当前项目需要的两个权重，推荐这样得到：

- `person_detect_yolov8.pt`
  - 直接使用官方 YOLOv8 通用检测权重
- `workwear_detect_yolov8.pt`
  - 使用当前 `clothes` 单类数据集训练得到

这是最符合当前项目逻辑、也最容易落地的一套方案。


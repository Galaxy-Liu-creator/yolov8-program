# backend-train-model

> 当前如果只想了解“现在该跑什么、哪个模型是 baseline、文档先看什么”，请先读：
> - `backend-train-model/README.md`
> - `backend-train-model/docs/todo_list.md`
> - `backend-train-model/docs/total-run-method.md`
> - `backend-train-model/All-train-model/00_CURRENT_BASELINE/README.md`
>
> 本文件主要保留 `train_workwear.py` 的命令与 CLI 说明。

本目录提供一套面向当前项目的 YOLOv8 训练工具链，目标是让训练流程尽量与 `inspection-flask` 的双阶段推理链路保持一致。

当前训练目标为单类别检测：

- 类别 ID：`0`
- 类别名称：`clothes`

注意：

- 当前训练出来的是 **`clothes` 单类检测模型**
- 它可以作为后续“未穿工服检测”系统里的工服子模型
- 但它本身**不直接等于**“疑似未穿工服告警器”
- 如果后续接真实摄像头，仍然需要再叠加 `person` 检测、ROI 和时序规则

主入口脚本：

- `backend-train-model/train_workwear.py`

支持的子命令：

- `audit`
- `prepare`
- `train`
- `evaluate`
- `export`
- `all`

## 运行前准备

### 1. 进入项目根目录

```powershell
cd D:\University-Competition\Innovation_Entrepreneurship\MyProgram\yolov8-program
```

### 2. 使用约定的 Python 环境

仓库默认使用：

- Conda 环境：`yolo_code`
- Python：`D:\Miniconda3_python\envs\yolo_code\python.exe`

下文中的命令都默认基于这个解释器。

### 3. 依赖前提

默认假设 `yolo_code` 环境中已经具备以下核心依赖：

- `ultralytics`
- `torch`
- `opencv-python`
- `PyYAML`

### 4. 本地模型资产约定

当前仓库已经固定了两类默认模型资产位置：

- 本地结构文件：`backend-train-model/model_defs/yolov8n.yaml`
- 本地微调权重：`backend-train-model/weights/yolov8n.pt`

推荐做法：

- 日常训练优先准备本地 `yolov8n.pt`
- 想改结构时再编辑 `backend-train-model/model_defs/yolov8n.yaml`
- 默认**不**隐式联网下载模型，避免离线环境下行为不可控

如果你明确允许 Ultralytics 自动下载默认模型，需要显式加：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --allow-remote-model-download
```

## 默认训练策略

当前脚本已经调整为：

- **默认使用本地 `backend-train-model/weights/yolov8n.pt` 做微调**
- 如需从零开始训练，再显式加 `--from-scratch`

这样更适合当前项目这种样本量不算大的检测任务，通常比默认从 `yolov8n.yaml` 随机初始化起训更稳定。

### 默认训练命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train
```

这条命令现在等价于：以 `yolov8n.pt` 为默认起点继续训练。
如果本地权重缺失，脚本会直接报中文提示，而不会默认静默联网下载。

### 从零开始训练

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --from-scratch
```

这条命令会默认改为从 `yolov8n.yaml` 结构开始训练，而不是加载 `yolov8n.pt`。
默认使用的本地结构文件路径为：`backend-train-model/model_defs/yolov8n.yaml`

## 数据划分策略

当前代码已经把数据划分策略显式做成可配置项 `--split-strategy`，支持两种方式：

### 1. 默认：`sequence_contiguous`

- 含义：在**每个原始序列内部**按时间顺序连续切成 `train / val / test`
- 优点：
  - 当前只有 3 个原始序列时，这种方式能让每个序列都参与训练
  - 能保留更多训练样本
  - 更适合当前项目这种序列数很少的情况

### 2. 严格模式：`sequence_holdout`

- 含义：按**整个序列**分配到 `train / val / test`，不同 split 之间不混序列
- 优点：
  - 更严格
  - 更能避免同一序列带来的时序相似性泄漏
- 缺点：
  - 当前序列数太少时，训练集可能会明显变小

当前实现说明：

- 该模式按 `config.py` 中 `IMAGE_ROOTS` 的书写顺序分配
- 以当前仓库为例，实际就是：
  - `D04_20260123074846 -> train`
  - `D05_20260123074841 -> val`
  - `D15_20260123074848 -> test`

### 3. 当前默认为什么保留 `sequence_contiguous`

当前数据源只有 3 个序列。如果直接做完整的三路 `sequence_holdout`，训练集可能只剩下 1 个序列，训练数据太少，不利于模型学习。  
因此当前代码默认保留更实用的：

- `--split-strategy sequence_contiguous`

如果你后续拿到更多独立序列，再切到 `sequence_holdout` 会更有意义。

### 4. 显式指定严格切分

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py prepare --split-strategy sequence_holdout
```

## `yolov8n.pt` 和 `yolov8n.yaml` 的区别

### 1. `yolov8n.pt`

- 是**带有训练权重的模型检查点**
- 一般表示“模型结构 + 已训练参数”
- 拿来继续训练，本质上是**迁移学习 / 微调**
- 对小数据集通常更友好，常见表现是：
  - 收敛更快
  - 更稳定
  - 更容易拿到更好的 `recall` 和 `mAP`

### 2. `yolov8n.yaml`

- 是**模型结构定义文件**
- 不包含训练好的参数
- 直接用它训练，本质上是**从零开始训练**
- 更适合：
  - 做 scratch 对照实验
  - 数据量比较大
  - 你准备修改网络结构

### 3. 什么时候选哪一个

- 日常项目训练：优先用 `yolov8n.pt`
- 想做纯 scratch 实验：用 `yolov8n.yaml`
- 要改网络结构：先从 `.yaml` 起模型，再决定是否加载兼容的旧权重

## 常用命令

### 1. 审核原始数据

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py audit
```

作用：

- 检查图片与标签是否一一对应
- 检查标签文件是否为合法 YOLO 检测格式
- 统计各序列样本数与框数

### 2. 准备训练数据

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py prepare
```

默认说明：

- `--mode auto`
- 默认切分：`--split-strategy sequence_contiguous`
- 未提供 `--person-model` 时默认走 `fullframe`
- 提供 `--person-model` 后可切到 `personcrop`

#### 使用 personcrop 模式

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py prepare --mode personcrop --person-model your_person_model.pt
```

#### 使用严格序列隔离切分

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py prepare --split-strategy sequence_holdout
```

#### 做小样本 smoke prepare

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py prepare --limit-per-sequence 3 --overwrite
```

补充说明：

- 如果你后续还要继续执行 `train + evaluate`，建议 `--limit-per-sequence` 至少为 `3`
- `1` 张/序列只适合测试 `prepare` 本身
- `2` 张/序列可以训练，但测试集可能为空，评估信息会不完整

### 3. 默认微调训练

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train
```

默认训练参数：

- `imgsz=640`
- `epochs=180`
- `batch=4`
- `patience=40`
- `workers=0`
- `device=cpu`
- `seed=42`
- `split-strategy=sequence_contiguous`

### 4. 从零开始训练

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --from-scratch
```

如果你想指定其他结构文件：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --base-model your_model.yaml --from-scratch
```

### 5. 指定其他预训练权重继续微调

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --base-model your_model.pt
```

### 6. 修改网络结构后，加载兼容权重初始化

如果你未来修改了网络结构，推荐方式是：

- 用你自己的结构文件 `.yaml` 创建模型
- 再加载旧模型里**能够匹配上的权重**
- 不匹配的新层继续保持随机初始化

当前脚本已经支持这种方式：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --base-model your_model.yaml --init-weights backend-train-model\weights\yolov8n.pt
```

这个模式适合：

- 你修改了 backbone / neck / head 的一部分
- 但仍希望尽量继承旧模型里能复用的参数

注意：

- `--init-weights` 只适用于 `.yaml/.yml` 结构文件
- `--from-scratch` 与 `--init-weights` 不能同时使用

### 7. 自定义训练参数

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --epochs 120 --batch 2 --imgsz 640
```

### 7.1 严格断点续训

如果训练中途被你手动终止，或因为环境原因中断，现在可以直接基于上一次 run 的 `last.pt` 做**严格断点续训**：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --resume
```

如果你想显式指定某一次 run 的 checkpoint，也可以直接传入对应的 `last.pt`：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --resume path\to\weights\last.pt
```

补充说明：

- `--resume` 不带值时，会自动尝试续训最近一次训练留下的 `last.pt`
- 自动续训会跳过已经训练完成、或已被精简为不可续训状态的旧 `last.pt`
- 严格断点续训只支持 `last.pt`，不支持拿 `best.pt` 伪装成断点续训
- `--resume` 会严格沿用 checkpoint 内保存的训练状态，不应再同时传 `--base-model`、`--from-scratch`、`--init-weights`、`--name`、`--project`、`--dataset-yaml`、`--epochs` 等训练起点参数
- 当前严格断点续训入口是 `train` 子命令

### 8. 评估模型

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py evaluate
```

默认行为：

- 不传 `--weights` 时，会优先读取最近一次训练报告里的 `best_weight`
- 如果训练报告不可用，才回退到 `backend-train-model/artifacts/runs/` 下扫描最新的 `best.pt`
- 原生评估会在 `val / test` 中自动跳过空 split，只评估非空 split

默认会输出：

- Recall
- Precision
- mAP50
- mAP50-95

补充说明：

- 上述指标评估的是 `clothes` 检测效果
- 它不直接代表最终“疑似未穿工服”业务告警准确率

### 9. 使用 `inspection-flask` 额外复核

在当前仓库里，这一步有一个**额外前提**：

- 你需要显式传入 `--person-model your_person_model.pt`
- 或者本地已经存在 `inspection-flask/weights/person_detect_yolov8.pt`

推荐命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py evaluate --inspection-validate --person-model your_person_model.pt
```

这个命令会额外调用 `inspection-flask/main.py validate`，用于检查模型在项目真实双阶段链路里的表现。

### 10. 导出权重

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py export
```

默认行为：

- 不传 `--weights` 时，会优先读取最近一次训练报告里的 `best_weight`
- 如果训练报告不可用，才回退到 `backend-train-model/artifacts/runs/` 下扫描最新的 `best.pt`

导出结果默认位于：

- `backend-train-model/artifacts/export/workwear_detect_yolov8.pt`

### 11. 导出并同步到 `inspection-flask`

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py export --deploy
```

同步目标：

- `inspection-flask/weights/workwear_detect_yolov8.pt`

如果目标文件已存在并需要覆盖：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py export --deploy --overwrite
```

### 12. 一键跑完整链路

更稳妥的默认命令是：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py all --deploy --skip-inspection-validate
```

完整流程依次执行：

1. `prepare`
2. `train`
3. `evaluate`
4. `export`

补充说明：

- `all` 会固定使用**本轮训练刚产出的** `best.pt` 做后续 `evaluate` 和 `export`
- `all` 默认会执行 `inspection-flask` 复核
- 如果你没有可用的人体检测权重，推荐显式加 `--skip-inspection-validate`

如果你想一键从零开始训练：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py all --from-scratch --deploy --skip-inspection-validate
```

如果你想一键切到严格序列隔离切分：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py all --split-strategy sequence_holdout --deploy --skip-inspection-validate
```

如果你想跳过 `inspection-flask` 复核：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py all --skip-inspection-validate
```

如果你已经准备好了人体检测权重，也可以直接完整跑通双阶段复核：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py all --deploy --person-model your_person_model.pt
```

## 产物位置

### 1. 准备后的数据集

- `backend-train-model/artifacts/prepared/...`

默认会按：

- 准备模式 `mode`
- 切分策略 `split-strategy`

分别放到不同子目录，避免相互覆盖。

### 2. 训练运行目录

- `backend-train-model/artifacts/runs/...`

重点关注：

- `best.pt`
- `last.pt`

### 3. 评估与汇总报告

- `backend-train-model/artifacts/reports/...`

### 4. 导出权重

- `backend-train-model/artifacts/export/workwear_detect_yolov8.pt`

## 推荐使用顺序

### 方式一：分步骤执行

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py audit
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py prepare
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py evaluate --inspection-validate --person-model your_person_model.pt
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py export --deploy --overwrite
```

如果暂时没有人体检测权重，可改为：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py evaluate
```

### 方式二：一键执行

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py all --deploy --overwrite --skip-inspection-validate
```

## 说明

- `audit` 会忽略 `classes.txt`
- `personcrop` 模式依赖可用的人体检测权重；没有时建议先使用 `fullframe`
- `evaluate --inspection-validate` 与默认 `all` 复核链路，都需要可用的人体检测权重
- 自定义 `--project` / `--output-root` / `--export-root` 时，当前脚本会自动解析为绝对路径，避免产物落到意外目录
- 自定义 `--project` 后，`evaluate` / `export` 默认也会优先回看训练报告，不再只盯 `artifacts/runs/`
- 本仓库默认以 `Python 3.9` / `yolo_code` 环境为基准
- 当前默认参数面向 CPU 环境，若后续切到 GPU，可再单独调整批大小与输入尺寸

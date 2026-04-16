# `backend-train-model` 运行方法说明（run_mathod）

本文档用于回答下面几个非常实际的问题：

- 当前阶段到底怎么跑最稳妥
- 第一次训练 `clothes` 模型时应该走哪条命令链
- `auto`、`fullframe`、`personcrop` 分别适合什么场景
- 如果想自己指定数据集，应该怎么做
- 哪些参数现在值得改，哪些参数暂时不建议乱改
- 以后当项目进入下一阶段时，命令应该怎么调整

本文档会尽量把“推荐做法”和“可选做法”区分开，避免把现阶段最稳妥方案和未来扩展方案混在一起。

---

## 1. 先给结论

如果你当前的目标是：

- 先把 `clothes` 模型训练好
- 先做出一个稳定 baseline
- 暂时还没有可用的 `person` 权重
- 暂时不追求接入完整实时链路

那么当前**最稳妥的运行方式**是：

1. 先跑 `audit`
2. 显式用 `fullframe` 做 `prepare`
3. 显式用 `fullframe` 做 `train`
4. 再跑 `evaluate`
5. 最后 `export`

推荐命令顺序如下：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py audit
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py prepare --mode fullframe --overwrite
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --mode fullframe --name clothes_fullframe_baseline
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py evaluate
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py export
```

当前最不建议的做法是：

- 直接默认用 `auto` 跑 baseline，却不关心后续 `person` 权重接入后行为会不会变化
- 一开始就用 `all --deploy ...` 把训练、评估、导出、部署绑死在一起
- 还没形成 baseline，就急着切 `personcrop`
- 还没明确数据口径，就直接改成多类混标训练

---

## 2. 当前阶段为什么推荐显式使用 `fullframe`

### 2.1 当前你真正想得到的是什么

你现在最需要的不是“功能最复杂”的训练链路，而是：

- 一个稳定、可复现的 `clothes` baseline
- 一组后续可对比的训练 / 评估报告
- 一条以后能和 `personcrop` 做公平比较的基准线

### 2.2 为什么不用默认 `auto` 直接做 baseline

`auto` 的逻辑本身没有问题，但它有一个特点：

- **它会根据当前是否有可用 `person` 权重，自动决定走 `fullframe` 还是 `personcrop`**

这意味着：

- 你今天没有 `person` 权重，`auto` 可能落到 `fullframe`
- 你以后某天把 `person_detect_yolov8.pt` 放到默认目录，**同样一条命令** 可能就变成 `personcrop`

如果你想做一个稳定 baseline，这种“命令没变，但行为可能变”的情况并不理想。

因此，当前更稳妥的建议是：

- **baseline 阶段显式写 `--mode fullframe`**

这样最清楚，也最利于后续对比。

### 2.3 什么时候再考虑 `personcrop`

推荐等下面条件成立后，再切到 `personcrop`：

- 你已经有稳定的 `clothes fullframe` baseline
- 你已经准备好了可用的 `person` 权重
- 你准备比较 `fullframe` 和 `personcrop` 的优劣

---

## 3. 当前最稳妥的运行顺序

当前阶段最推荐用**分步骤执行**，而不是一上来用 `all`。

原因很简单：

- 分步骤更容易定位问题
- 更容易看清每一步产物
- 更容易知道失败发生在：
  - 数据审计
  - 数据准备
  - 训练
  - 评估
  - 导出

下面按步骤展开说明。

---

## 4. 第一步：`audit`

### 4.1 推荐命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py audit
```

### 4.2 作用

这一步只做数据审计，不写训练集，也不训练模型。

它主要负责检查：

- 图片目录是否存在
- 标签目录是否存在
- 图片与标签能否按文件名一一对应
- 标签是否符合当前 YOLO 检测格式
- 类别 ID 是否落在当前配置允许范围内
- 各序列样本数、标注框数是否合理

### 4.3 为什么这一步不能省

如果原始数据本身有问题，而你直接去 `prepare` 或 `train`，后面出现的报错会更难定位。

`audit` 的价值在于：

- 把“数据错了”这件事，尽量提前暴露出来

### 4.4 参数说明

当前最常用的是不带额外参数直接运行。

如需快速烟雾验证，也可用：

```powershell
--project-config PROJECT_CONFIG
```

含义：

- 指定一份自定义 JSON 配置，而不是默认读取 `backend-train-model/project_config.json`

适用场景：

- 你想临时切换到另一套原始数据路径
- 你不想修改仓库默认配置文件

---

## 5. 第二步：`prepare`

### 5.1 当前最推荐命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py prepare --mode fullframe --overwrite
```

### 5.2 作用

把当前原始图片目录和标签目录，整理成一套可以直接给 YOLOv8 训练的标准数据集目录。

主要会做：

- 按 `train / val / test` 切分样本
- 重写图片与标签到标准目录
- 生成 `dataset.yaml`
- 生成 `prepare_report.json`

### 5.3 为什么当前推荐 `fullframe`

因为你现在的目标是：

- 先把 `clothes` 模型训稳

而 `fullframe`：

- 更简单
- 不依赖 `person` 权重
- 更适合做 baseline

### 5.4 为什么加 `--overwrite`

因为 `prepare` 会往输出目录里写文件。

如果目标目录已经存在旧内容：

- 不加 `--overwrite`，脚本会拒绝覆盖
- 加了 `--overwrite`，脚本才会允许清理旧目录后重新生成

因此，当你重复做同一套 baseline 时，通常建议显式加：

```powershell
--overwrite
```

### 5.5 常用参数解释

#### `--mode`

可选值：

- `fullframe`
- `personcrop`
- `auto`

含义：

- `fullframe`：直接用整图训练
- `personcrop`：先做人检测，再裁人，再生成工服训练样本
- `auto`：如果发现可用 `person` 权重就走 `personcrop`，否则走 `fullframe`

当前阶段推荐：

- `--mode fullframe`

#### `--split-strategy`

可选值：

- `sequence_contiguous`
- `sequence_holdout`

含义：

- `sequence_contiguous`：每个原始序列内部按时间连续切成 `train / val / test`
- `sequence_holdout`：按整个序列切分，不同 split 之间不混序列

当前阶段推荐：

- 保持默认 `sequence_contiguous`

原因：

- 你当前序列数量还不多，默认方式更实用

#### `--output-root`

含义：

- 指定本次 `prepare` 的输出目录

适用场景：

- 你想并行保留多套 prepared 数据
- 你想避免覆盖默认 prepared 目录
- 你在做不同实验版本

示例：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py prepare --mode fullframe --output-root backend-train-model\artifacts\prepared\clothes_fullframe_v1 --overwrite
```

#### `--limit-per-sequence`

含义：

- 仅用于快速测试时，对每个序列只取前 N 张图片

适用场景：

- 你想先测试流程能不能跑通

不适合：

- 正式训练

当前阶段建议：

- 正式训练时不要用

---

## 6. 第三步：`train`

### 6.1 当前最推荐命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --mode fullframe --name clothes_fullframe_baseline
```

### 6.2 作用

这一步会：

1. 解析最终要用的 `dataset.yaml`
2. 如果默认 prepared 数据不存在，就自动触发一次 `prepare`
3. 解析训练起点模型
4. 调用 Ultralytics 开始训练
5. 记录训练报告

### 6.3 为什么建议显式写 `--name`

因为训练 run 默认会自动拼时间戳。

如果你希望后续看目录、看报告时更清楚，推荐显式写上实验名。

例如：

- `clothes_fullframe_baseline`
- `clothes_fullframe_v2`
- `clothes_personcrop_compare`

### 6.4 当前默认训练参数

当前配置默认值大致是：

- `imgsz=640`
- `epochs=180`
- `batch=4`
- `patience=40`
- `workers=0`
- `device=cpu`
- `seed=42`

### 6.5 当前哪些参数建议先别动

如果你现在只是第一轮 baseline，通常建议先不要乱改：

- `imgsz`
- `epochs`
- `patience`
- `seed`

原因：

- 先建立一个默认基线更重要

### 6.6 当前哪些参数可能值得你之后再调

后续如果你已经跑出 baseline，再考虑逐步调整：

#### `--device`

含义：

- 指定训练设备，例如 `cpu`、`0`

当前默认：

- `cpu`

如果你后续切到 GPU，才建议改。

#### `--batch`

含义：

- 单次训练的 batch size

建议：

- 先保持默认
- 切换 GPU 后再根据显存调整

#### `--epochs`

含义：

- 最大训练轮数

建议：

- 第一轮 baseline 先不动
- 当你开始做多轮实验对比时再调整

#### `--base-model`

含义：

- 指定训练起点模型
- 可以是 `.pt`
- 也可以是 `.yaml`

当前推荐：

- 继续使用默认本地 `yolov8n.pt`

#### `--from-scratch`

含义：

- 从 `.yaml` 结构文件起模型，不加载默认 `.pt` 微调权重

当前建议：

- 第一轮 baseline 不用

适用场景：

- 你明确要做 scratch 对照实验
- 你准备修改网络结构

#### `--project`

含义：

- 指定训练 runs 输出目录

适用场景：

- 你想把不同实验写到不同目录

示例：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --mode fullframe --project backend-train-model\artifacts\runs\baseline_group --name clothes_fullframe_v1
```

---

## 7. 第四步：`evaluate`

### 7.1 当前最推荐命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py evaluate
```

### 7.2 作用

这一步会对当前权重进行评估，并输出检测指标。

常见会看到：

- Recall
- Precision
- mAP50
- mAP50-95

### 7.3 当前为什么先不推荐 `--inspection-validate`

因为那一步会额外调用 `inspection-flask` 的双阶段链路复核。

而它通常需要：

- 可用的 `person` 权重

你当前既然是先专注把 `clothes` baseline 跑稳，那么更推荐：

- 先跑原生 `evaluate`

等你以后拥有 `person` 权重，再补跑：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py evaluate --inspection-validate --person-model your_person_model.pt
```

### 7.4 常用参数解释

#### `--weights`

含义：

- 显式指定要评估的 `best.pt`

适用场景：

- 你不想让脚本自动猜最近的训练权重

#### `--dataset-yaml`

含义：

- 显式指定本轮评估使用的数据集配置

适用场景：

- 你有多套 prepared 数据集
- 你要评估某个自定义数据集

---

## 8. 第五步：`export`

### 8.1 当前最推荐命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py export
```

### 8.2 作用

导出当前 best 权重到统一位置，便于后续部署或接入其他链路。

默认导出目标是：

- `backend-train-model/artifacts/export/workwear_detect_yolov8.pt`

### 8.3 当前为什么不急着 `--deploy`

因为 `--deploy` 的含义是：

- 同步复制到 `inspection-flask/weights/`

在你当前只是做 baseline 的阶段，还不一定需要立即同步部署。

因此当前建议：

- 先 `export`
- 后面确认结果满意后，再考虑 `export --deploy`

### 8.4 常用参数解释

#### `--weights`

含义：

- 显式指定要导出的 `best.pt`

#### `--export-root`

含义：

- 指定导出目录

适用场景：

- 你想为不同实验保存不同导出结果

#### `--deploy`

含义：

- 导出后，同时复制到 `inspection-flask/weights/workwear_detect_yolov8.pt`

#### `--overwrite`

含义：

- 如果导出目标已经存在，允许覆盖

---

## 9. 为什么当前不推荐一开始就用 `all`

### 9.1 `all` 适合什么场景

`all` 适合：

- 你已经比较清楚当前链路状态
- 你希望一条命令串行完成：
  - `prepare`
  - `train`
  - `evaluate`
  - `export`

### 9.2 为什么当前 baseline 阶段不把它放在第一推荐位

因为它把多步串在一起之后：

- 一旦失败，你要额外回看是哪一步报错
- 第一轮排查时不如分步骤清晰

### 9.3 当前如果你一定想用 `all`

当前更稳妥的写法是：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py all --mode fullframe --skip-inspection-validate --name clothes_fullframe_allinone
```

参数含义：

- `--mode fullframe`：显式固定 baseline 模式
- `--skip-inspection-validate`：跳过需要 `person` 权重的链路级复核
- `--name`：给本轮训练 run 一个清晰名字

### 9.4 当前什么时候再推荐 `all --deploy`

等下面条件成立后，再考虑：

- 你已经有稳定 baseline
- 你已经确认导出权重就是本轮要接入的版本
- 你清楚是否要同步覆盖 `inspection-flask` 侧权重

---

## 10. 如果你想自己指定数据集，当前有两种稳妥方式

这一部分非常重要。

当前代码已经支持你**不改代码**地切换数据集，只是 README 以前没有完全展开讲清楚。

---

## 11. 方式 A：直接指定现成的 `dataset.yaml`

### 11.1 适用场景

当你已经有一套准备好的 YOLO 数据集时，最推荐这种方式。

也就是说，你手里已经有：

- `dataset.yaml`
- `images/train`
- `images/val`
- `images/test`
- `labels/train`
- `labels/val`
- `labels/test`

### 11.2 当前最推荐命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --dataset-yaml E:\your_dataset\dataset.yaml --name clothes_custom_dataset
```

### 11.3 作用

这会让脚本：

- 直接用你指定的 `dataset.yaml`
- 不再依赖默认 prepared 目录去推导数据集

### 11.4 这是当前最直接、最稳定的自定义数据集方法

因为它最明确：

- 数据集是谁
- 路径在哪

完全由你指定，不需要脚本再猜。

### 11.5 评估时怎么指定

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py evaluate --dataset-yaml E:\your_dataset\dataset.yaml --weights E:\your_runs\best.pt
```

### 11.6 参数解释

#### `--dataset-yaml`

含义：

- 显式指定当前命令使用的数据集配置文件

适用命令：

- `train`
- `evaluate`
- `all`

当前推荐指数：

- **最高**

因为最明确、最不容易误用。

---

## 12. 方式 B：通过 `--project-config` 切换“原始数据入口”

### 12.1 适用场景

当你手里不是现成 YOLO 数据集，而是：

- 原始图片目录
- 原始标签目录
- 希望继续复用当前仓库的 `audit + prepare + train` 流程

那么推荐用：

- 自定义 `project_config.json`

### 12.2 你要改哪些内容

通常至少改下面这些项：

- `data.image_roots`
- `data.label_root`
- `data.class_names`
- 必要时改 `data.split_ratios`
- 必要时改 `prepare.default_mode`

### 12.3 当前更稳妥的推荐做法

更推荐分两步：

#### 第一步：先 `prepare` 到独立目录

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py prepare --project-config E:\your_config\my_dataset_config.json --mode fullframe --output-root backend-train-model\artifacts\prepared\my_dataset_v1 --overwrite
```

#### 第二步：再显式指定这份 `dataset.yaml` 去训练

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --dataset-yaml backend-train-model\artifacts\prepared\my_dataset_v1\dataset.yaml --name clothes_my_dataset_v1
```

### 12.4 为什么不推荐只传 `--project-config` 后直接 `train`

因为 `train` 在没有 `--dataset-yaml` 时，会先尝试按默认规则找 prepared 数据。

如果默认目录里已经有旧的 `dataset.yaml`，它可能直接复用旧数据，而不是你以为的新数据。

所以更稳妥的顺序是：

1. `prepare --project-config ... --output-root ...`
2. `train --dataset-yaml ...`

这样最明确，也最不容易混淆。

### 12.5 参数解释

#### `--project-config`

含义：

- 指定一份自定义 JSON 配置文件

适用场景：

- 切换原始数据路径
- 切换类别定义
- 切换默认 prepare 参数

#### `--output-root`

含义：

- 指定本次 `prepare` 生成的数据集目录

推荐理由：

- 让不同实验互不覆盖

---

## 13. 当前什么时候需要改代码

大多数情况下，**现在不需要改代码**。

当前已经有两种成熟的切换数据集方式：

1. `--dataset-yaml`
2. `--project-config`

只有当你想实现下面这种更激进的用法时，才需要考虑改代码：

- 直接在 CLI 上传：
  - `--image-roots`
  - `--label-root`
  - `--class-names`
- 不想写任何 JSON 配置文件
- 也不想先自己准备 `dataset.yaml`

这类需求不是做不到，但当前并不是最优先。

因为在你现阶段，“先把 `clothes` 训练稳定跑通”明显更重要。

---

## 14. 当前阶段最推荐的命令分层

下面给出一套从“最推荐”到“可选扩展”的命令层次。

### 14.1 第一层：当前 baseline 必跑

#### 1）审计数据

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py audit
```

作用：

- 检查当前原始数据是否符合训练前提

#### 2）准备 baseline 数据集

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py prepare --mode fullframe --overwrite
```

作用：

- 生成 `fullframe` baseline 的 YOLO 标准数据集

#### 3）启动 baseline 训练

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --mode fullframe --name clothes_fullframe_baseline
```

作用：

- 训练第一版 `clothes` baseline

#### 4）评估训练结果

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py evaluate
```

作用：

- 输出基础检测指标

#### 5）导出最终权重

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py export
```

作用：

- 把当前 best 权重导出到统一目录

---

### 14.2 第二层：当前可选但不必立刻做

#### 使用严格切分策略

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py prepare --mode fullframe --split-strategy sequence_holdout --overwrite
```

作用：

- 用完整序列隔离方式切分数据

当前建议：

- 暂不作为第一轮 baseline 首选

#### 运行一键串行流程

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py all --mode fullframe --skip-inspection-validate --name clothes_fullframe_allinone
```

作用：

- 一条命令串行完成 `prepare -> train -> evaluate -> export`

当前建议：

- 第二轮或流程熟悉后再用

---

### 14.3 第三层：未来阶段再做

#### 启用 `personcrop`

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py prepare --mode personcrop --person-model backend-train-model\weights\person_detect_yolov8.pt --overwrite
```

作用：

- 基于 `person` 模型先裁人，再生成 `clothes` 训练数据

前提：

- 你已经有可用的 `person` 权重

#### 使用 `auto`

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --mode auto --person-model backend-train-model\weights\person_detect_yolov8.pt --name clothes_personcrop_auto
```

作用：

- 让脚本根据 person 权重情况自动选择最终 prepare 模式

当前建议：

- 以后有 person 权重后再用它做“完整链路对齐版”训练

#### 做链路级复核

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py evaluate --inspection-validate --person-model backend-train-model\weights\person_detect_yolov8.pt
```

作用：

- 额外调用 `inspection-flask` 做链路级复核

前提：

- 你已经进入更接近完整业务链路的阶段

---

## 15. 当前最推荐的实际执行方案

如果你准备现在就开始训练，并且你问我“按当前项目，最稳妥到底怎么跑”，我的推荐是：

### 方案 A：最稳妥的 baseline 方案

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py audit
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py prepare --mode fullframe --overwrite
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --mode fullframe --name clothes_fullframe_baseline
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py evaluate
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py export
```

这是当前我最推荐你直接执行的一套。

### 方案 B：你已经有现成 `dataset.yaml`

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --dataset-yaml E:\your_dataset\dataset.yaml --name clothes_custom_dataset
```

适合：

- 你已经准备好了标准 YOLO 数据集

### 方案 C：你想切换原始数据源，但不改代码

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py prepare --project-config E:\your_config\my_dataset_config.json --mode fullframe --output-root backend-train-model\artifacts\prepared\my_dataset_v1 --overwrite
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --dataset-yaml backend-train-model\artifacts\prepared\my_dataset_v1\dataset.yaml --name clothes_my_dataset_v1
```

适合：

- 你还想继续复用当前仓库的原始数据审计与 prepare 流程

---

## 16. 未来阶段命令应该怎么变

等你以后进入下一阶段，命令建议会发生这些变化。

### 16.1 当你已有 `person` 权重后

推荐开始比较：

- `fullframe clothes`
- `personcrop clothes`

示例：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --mode personcrop --person-model backend-train-model\weights\person_detect_yolov8.pt --name clothes_personcrop_compare
```

### 16.2 当你要做链路级验证时

示例：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py evaluate --inspection-validate --person-model backend-train-model\weights\person_detect_yolov8.pt
```

### 16.3 当你确认某版权重可以进入部署链路时

示例：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py export --deploy --overwrite
```

---

## 17. 一句话总建议

如果把整份文档压缩成一句话，那么当前最稳妥的建议是：

> **先显式用 `fullframe` 跑出 `clothes` baseline，再决定是否接入 `personcrop`；如果要切换数据集，优先用 `--dataset-yaml`，其次用 `--project-config + prepare --output-root + train --dataset-yaml`，当前阶段通常不需要先改代码。**


# [归档] All-train-model 运行方法

> 归档说明（2026-04-15）：
> - 本文保留的是 `All-train-model` 早期阶段的运行口径，其中仍包含“以旧 `first-train` baseline 初始化 merged”的历史表述。
> - 当前 unified holdout 主线下，正式重跑口径已经收敛到 `backend-train-model/docs/total-run-method.md`。
> - 因此本文仅用于回溯历史，不再作为当前训练命令的首选说明。

## 1. 这份文档解决什么问题

这份文档专门回答下面这几个问题：

1. `All-train-model` 现在到底应该怎么训练
2. 之前说“可以直接训练”和“更推荐用 `first-train` 的 `best.pt` 初始化”之间是什么关系
3. 当前阶段最稳妥的训练、评估、导出命令分别是什么
4. 每条命令里的关键参数分别是什么意思

---

## 2. 先说结论

### 2.1 训练命令框架没有变

现在还是用同一个训练入口：

```powershell
train_workwear.py train
```

没有换脚本，也没有额外改主训练代码。

你之前已经用过的这一套命令体系仍然成立：

- `train`
- `evaluate`
- `export`

变化的核心只有两点：

1. 训练数据集现在建议切到 `merged_clothes_v2_full_reviewed`
2. 如果追求当前阶段更稳妥的效果，建议用 `first-train` 的稳定 `best.pt` 作为 `--base-model`

### 2.2 “还能直接训练” 和 “建议用 first-train 的 best.pt” 不冲突

这两个说法其实是两个层级：

- **能跑通的命令**：不加 `--base-model`，直接训练，脚本会默认使用本地 `backend-train-model/weights/yolov8n.pt`
- **当前更推荐的命令**：显式加上 `--base-model first-train/artifacts/runs/clothes_fullframe_baseline/weights/best.pt`

也就是说：

- **不加 `--base-model`**：命令是对的，能跑
- **加 `--base-model first-train/.../best.pt`**：当前更推荐，更符合我们前面给出的优化路线

### 2.3 当前最推荐的训练起点

当前阶段，最推荐你正式训练时使用下面这个思路：

1. 数据集使用 `merged_clothes_v2_full_reviewed`
2. 初始化权重使用 `first-train` 的 `best.pt`
3. 单独执行 `train`、`evaluate`、`export`
4. 不建议现在改成 `--from-scratch`

原因很直接：

- `first-train` 目前是你手头更稳定、更像可靠 baseline 的结果
- `merged_v2` 已经比 `merged_v1` 更完整，但还没有充分证明“直接从默认 `yolov8n.pt` 起训”一定优于“从 `first-train best.pt` 继续微调”
- 先用稳定 checkpoint 继续 fine-tune，更符合当前“先把效果做稳”的目标

---

## 3. 当前已经就绪的关键文件

### 3.1 当前 merged_v2 数据集

已经构建好的数据集路径：

```text
backend-train-model/All-train-model/datasets/merged_clothes_v2_full_reviewed/dataset.yaml
```

对应构建报告：

```text
backend-train-model/All-train-model/datasets/merged_clothes_v2_full_reviewed/build_report.json
```

当前这版数据集已经把那 `48` 张“无 `clothes` 目标”的图片纳入为负样本。

### 3.2 当前推荐初始化权重

推荐用作初始化权重的模型：

```text
backend-train-model/first-train/artifacts/runs/clothes_fullframe_baseline/weights/best.pt
```

这不是“评估时用的权重路径”，而是本轮 merged 训练时建议显式传给：

```powershell
--base-model
```

### 3.3 当前 merged 训练配置

当前 merged 训练项目配置：

```text
backend-train-model/All-train-model/merged_train_project_config.json
```

这份配置当前提供的默认训练参数是：

- `imgsz=640`
- `epochs=180`
- `batch=4`
- `patience=40`
- `workers=0`
- `device=cpu`
- `seed=42`

如果你不额外覆盖这些参数，训练时就会默认用这组值。

---

## 4. 最稳妥的执行位置

最稳妥的做法是先进入：

```powershell
cd backend-train-model
```

然后再执行下面的命令。

这样做的好处是：

- `All-train-model\...` 这类相对路径最清晰
- `--project-config` 的相对路径不会写乱
- 后续训练、评估、导出命令都能统一保持一个写法

如果你从仓库根目录执行，也不是不行，但路径会更长，不如先 `cd backend-train-model` 稳妥。

---

## 5. 方案 A：直接训练 merged_v2，不额外指定 first-train 权重

## 5.1 什么时候用

这个方案适合：

- 你只想确认 `merged_v2_full_reviewed` 能否正常跑通
- 你想和“默认本地 `yolov8n.pt` 起训”的效果做一版对照
- 你暂时不想把 `first-train` 的权重带进来

这个方案**能跑、合法、没有问题**。

但从当前阶段的推荐级别来说，它不是第一优先。

## 5.2 训练命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py train --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\merged_clothes_v2_full_reviewed\dataset.yaml --name clothes_merged_v2_full_reviewed
```

### 参数说明

- `train_workwear.py train`
  - 启动训练阶段
- `--project-config All-train-model\merged_train_project_config.json`
  - 读取 merged 训练配置
  - 当前默认训练参数、输出目录根路径等都从这里取
- `--dataset-yaml All-train-model\datasets\merged_clothes_v2_full_reviewed\dataset.yaml`
  - 显式指定要训练的数据集
  - 这是当前最稳妥的做法，因为路径清晰、不会误拿旧 prepared 数据
- `--name clothes_merged_v2_full_reviewed`
  - 指定本次训练 run 名称
  - 最终权重会进入这个 run 对应的目录

### 训练产物位置

训练完成后，常见输出路径是：

```text
backend-train-model/All-train-model/artifacts/runs/clothes_merged_v2_full_reviewed/
```

权重通常在：

```text
backend-train-model/All-train-model/artifacts/runs/clothes_merged_v2_full_reviewed/weights/best.pt
```

## 5.3 评估命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py evaluate --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\merged_clothes_v2_full_reviewed\dataset.yaml --weights All-train-model\artifacts\runs\clothes_merged_v2_full_reviewed\weights\best.pt
```

### 参数说明

- `evaluate`
  - 用训练完成后的 `best.pt` 做评估
- `--weights`
  - 显式指定要评估的模型权重
  - 这里建议不要省略，避免误拿其他 run 的权重

## 5.4 导出命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py export --project-config All-train-model\merged_train_project_config.json --weights All-train-model\artifacts\runs\clothes_merged_v2_full_reviewed\weights\best.pt --overwrite
```

### 参数说明

- `export`
  - 导出训练好的模型
- `--overwrite`
  - 如果导出目标已存在，允许覆盖

---

## 6. 方案 B：推荐方案，用 first-train 的 best.pt 初始化 merged_v2

## 6.1 为什么这是当前更推荐的跑法

这是当前更推荐的原因：

1. `first-train` 已经产出了一版相对更稳定的 `best.pt`
2. `merged_v2` 现在已经补完 review 负样本，数据完整性比之前更好
3. 当前阶段更合理的策略，不是重新从默认基模盲起，而是站在更稳定 baseline 上继续 fine-tune

所以如果你现在准备做“下一轮正式 merged 训练”，更推荐这套。

## 6.2 训练命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py train --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\merged_clothes_v2_full_reviewed\dataset.yaml --base-model first-train\artifacts\runs\clothes_fullframe_baseline\weights\best.pt --name clothes_merged_v2_from_first
```

### 这条命令比方案 A 多了什么

多出来的关键参数只有一个：

- `--base-model first-train\artifacts\runs\clothes_fullframe_baseline\weights\best.pt`

它的意思是：

- 不再用默认的 `backend-train-model/weights/yolov8n.pt` 作为起点
- 而是直接把 `first-train` 已经训练好的 `best.pt` 作为本轮 merged 训练的初始化 checkpoint

### 为什么这里是 `--base-model`，不是 `--init-weights`

因为：

- `--base-model xxx.pt` 表示“直接从一个已有 checkpoint 继续微调”
- `--init-weights` 只适用于“你先用 `.yaml` 起模型结构，再额外加载兼容权重”

当前这个场景明显属于前者，所以应该用：

```powershell
--base-model xxx.pt
```

而不是：

```powershell
--init-weights
```

## 6.3 训练产物位置

建议把 run 名称单独区分出来：

```text
backend-train-model/All-train-model/artifacts/runs/clothes_merged_v2_from_first/
```

最终 `best.pt` 预期在：

```text
backend-train-model/All-train-model/artifacts/runs/clothes_merged_v2_from_first/weights/best.pt
```

## 6.4 评估命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py evaluate --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\merged_clothes_v2_full_reviewed\dataset.yaml --weights All-train-model\artifacts\runs\clothes_merged_v2_from_first\weights\best.pt
```

## 6.5 导出命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py export --project-config All-train-model\merged_train_project_config.json --weights All-train-model\artifacts\runs\clothes_merged_v2_from_first\weights\best.pt --overwrite
```

---

## 7. 当前阶段应该优先用哪一套

如果你问的是“**现在更推荐怎么跑**”，答案是：

### 推荐优先级

1. **优先推荐**

```powershell
train --dataset-yaml merged_v2_full_reviewed --base-model first-train/.../best.pt
```

也就是本文的**方案 B**。

2. **次优先**

```powershell
train --dataset-yaml merged_v2_full_reviewed
```

也就是本文的**方案 A**。

### 简单判断标准

- 如果你现在是要做“正式下一轮 merged 训练”，用**方案 B**
- 如果你现在只是想补一版“默认基模起训”的对照实验，用**方案 A**

---

## 8. 当前不推荐的做法

## 8.1 不推荐现在直接 `--from-scratch`

不推荐命令示意：

```powershell
train_workwear.py train --from-scratch ...
```

原因：

- 当前你不是在做网络结构探索
- 现在的核心目标是把 merged 数据训练稳定起来
- 从零训练变量更多，不利于对照

## 8.2 不推荐把 run 名称继续写成旧的 merged_v1 名称

比如不要再写：

```powershell
--name clothes_merged_v1_fullframe
```

否则很容易和旧结果混淆。

## 8.3 不推荐省略 `--dataset-yaml`

虽然脚本内部有默认解析逻辑，但当前阶段最好显式传：

```powershell
--dataset-yaml All-train-model\datasets\merged_clothes_v2_full_reviewed\dataset.yaml
```

原因：

- 路径更清楚
- 不容易误拿到别的数据集
- 后续复盘训练时最容易回溯

---

## 9. 运行前检查清单

正式训练前，建议你按下面检查一遍：

### 9.1 数据集是否存在

确认：

```text
backend-train-model/All-train-model/datasets/merged_clothes_v2_full_reviewed/dataset.yaml
```

### 9.2 first-train 权重是否存在

如果你准备走推荐方案，确认：

```text
backend-train-model/first-train/artifacts/runs/clothes_fullframe_baseline/weights/best.pt
```

### 9.3 运行目录是否正确

建议先执行：

```powershell
cd backend-train-model
```

### 9.4 是否给了新的 run 名称

建议使用：

- `clothes_merged_v2_full_reviewed`
- `clothes_merged_v2_from_first`

不要继续复用老 run 名称。

---

## 10. 最短执行清单

如果你只想看最短版本，按下面做就行。

### 10.1 当前最推荐训练

```powershell
cd backend-train-model
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py train --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\merged_clothes_v2_full_reviewed\dataset.yaml --base-model first-train\artifacts\runs\clothes_fullframe_baseline\weights\best.pt --name clothes_merged_v2_from_first
```

### 10.2 训练完成后评估

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py evaluate --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\merged_clothes_v2_full_reviewed\dataset.yaml --weights All-train-model\artifacts\runs\clothes_merged_v2_from_first\weights\best.pt
```

### 10.3 训练完成后导出

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py export --project-config All-train-model\merged_train_project_config.json --weights All-train-model\artifacts\runs\clothes_merged_v2_from_first\weights\best.pt --overwrite
```

### 10.4 如果训练中断，严格断点续训

#### 自动续训最近一次中断训练

```powershell
cd backend-train-model
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py train --project-config All-train-model\merged_train_project_config.json --resume
```

#### 显式续训当前推荐 run

```powershell
cd backend-train-model
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py train --project-config All-train-model\merged_train_project_config.json --resume All-train-model\artifacts\runs\clothes_merged_v2_from_first\weights\last.pt
```

补充说明：

- 这会严格沿用 `last.pt` 内保存的训练状态继续跑，不是重新从 `best.pt` 开一轮新微调
- 如果你当前机器上“最近一次中断训练”就是目标 run，优先直接用上面的“自动续训最近一次中断训练”命令即可
- 自动续训会自动跳过那些已经训练完成、或已经不再保留续训状态的旧 `last.pt`
- 严格断点续训时，不要再同时传 `--base-model`、`--dataset-yaml`、`--name`、`--epochs` 等训练起点参数

---

## 11. 一句话结论

一句话总结就是：

> **训练命令体系没变，当前最推荐的是继续用 `train_workwear.py train`，但把数据集切到 `merged_clothes_v2_full_reviewed`，并显式用 `first-train` 的 `best.pt` 作为 `--base-model`。**

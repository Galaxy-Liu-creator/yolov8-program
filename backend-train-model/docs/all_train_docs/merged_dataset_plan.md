# [归档] `backend-train-model` 三套数据合并为总数据集方案

> 归档说明（2026-04-15）：
> - 本文形成于 unified holdout 主线落地之前，主要用于回溯 merged 数据集最初的规划思路。
> - 它不再直接代表当前 baseline 或当前训练入口。
> - 当前主线请优先查看：
>   - `backend-train-model/README.md`
>   - `backend-train-model/docs/todo_list.md`
>   - `backend-train-model/docs/total-run-method.md`
>   - `backend-train-model/All-train-model/00_CURRENT_BASELINE/README.md`

本文档用于回答下面这个问题：

> 当前已经有多套 `clothes` 数据，如果最终想训练一个覆盖多套数据来源的总模型，怎样合并数据集才最稳妥。

这份文档采用的是前面讨论里的**方案二**：

- 把方案写成一份正式文档，放在 `backend-train-model/dos/` 下

同时文档内容中也包含前面说的**方案一**：

- 给出一套明确的目录规范
- 给出 `manifest` / 元数据字段设计
- 给出从原始数据到 merged 数据集的落地步骤

本文档的目标不是追求“最省事”的合并，而是追求：

- 更稳妥
- 更容易复现
- 更容易回溯问题
- 更适合作为最终正式模型的数据基础

---

## 1. 先给结论

如果你手里现在已经有三套 `clothes` 数据，并且最终目标是：

- 只保留 **一个正式 clothes 模型**
- 这个模型尽量同时适配三套数据来源

那么最推荐的路线不是：

- 先训练 A
- 再接着训练 B
- 再接着训练 C

而是：

1. 先分别审计 A / B / C
2. 先把三套数据统一规范化
3. 先做一个 merged 总数据集
4. 再基于 merged 数据集训练总模型

也就是：

```text
数据集 A 审计
数据集 B 审计
数据集 C 审计
-> 类别与标注口径统一
-> 命名去重
-> 生成 canonical 数据池
-> 生成 manifest
-> 切 train / val / test
-> 生成 merged_v1 dataset.yaml
-> 训练 clothes_merged_v1 模型
```

这条路线的核心好处是：

- 不容易出现“后来的数据把前面的能力覆盖掉”
- 更容易做域差异分析
- 更适合作为未来正式部署版本的训练基础

---

## 2. 当前适用前提

在开始合并之前，先确认三套数据满足下面几个前提。

### 2.1 任务类型一致

三套数据必须都是：

- 目标检测任务
- 当前阶段都用于训练 `clothes / workwear` 检测器

当前不适合直接混在一起的情况包括：

- 一套标的是 `clothes`
- 一套标的是 `person`
- 一套标的是事件级“未穿工服”

如果语义不同，必须先拆开。

### 2.2 标注格式一致

当前推荐的统一标准是：

- YOLO 检测格式
- 每行 `class_id x_center y_center width height`
- 坐标归一化到 `[0,1]`

### 2.3 类别语义一致

当前阶段推荐统一为：

- `0: clothes`

如果某套数据里写的是：

- `0: workwear`
- `0: uniform`

但本质上和当前任务一致，那么在 merged 阶段应统一映射成：

- `0: clothes`

### 2.4 文件命名必须可全局唯一

当前仓库的数据说明已经明确：

- 统一标签目录时，图片文件名应全局唯一
- 如果不同来源存在同名文件，不能直接靠文件名做唯一配对

因此，三套数据合并时，**绝对不要直接原样拷到一个共同目录里**。

---

## 3. 为什么不推荐 A -> B -> C 串行继续训练

这种路线的问题不是“完全不能用”，而是它更适合做：

- 增量微调实验
- 域适应实验

不太适合直接拿来做“最终正式模型”的主路线。

### 3.1 主要风险：灾难性遗忘

如果你先用 A 训出一个模型，再接着用 B 去训，再接着用 C 去训，常见问题是：

- 模型会越来越偏向后面的数据
- 在前面数据上的效果反而下降

### 3.2 中间状态不够透明

串行继续训练会让你很难回答这些问题：

- 当前模型到底更像 A、B 还是 C
- 某个误报是因为 merged 不合理，还是因为后续微调偏置

### 3.3 不利于构建正式基线

如果你最终需要：

- 一个清晰可复现的正式模型

那么“统一数据后重新训练”通常比“多轮串行继续训”更稳。

---

## 4. 总体方案分层

推荐把 merged 数据集方案分成四层。

### 第 1 层：原始数据层

这一层保留三套数据原始结构，不做覆盖性修改：

- 数据集 A
- 数据集 B
- 数据集 C

### 第 2 层：规范化 canonical 层

这一层做的事情是：

- 重命名
- 统一类别
- 标签合法化
- 去重

输出的是一套**规范化后的统一样本池**。

### 第 3 层：manifest / 元数据层

这一层记录每个样本：

- 来自哪套数据
- 原始路径是什么
- 最终改成了什么名字
- 分到了哪个 split
- 是否有效

### 第 4 层：prepared 训练层

这一层输出最终训练所需的标准结构：

- `images/train`
- `images/val`
- `images/test`
- `labels/train`
- `labels/val`
- `labels/test`
- `dataset.yaml`

---

## 5. 推荐目录规范（方案一的核心内容）

下面是一套我推荐你采用的 merged 数据集目录规范。

```text
backend-train-model/
  datasets/
    merged_v1_all/
      manifest/
        samples.csv
        source_stats.json
        class_mapping.json
        split_summary.json
      canonical/
        images/
        labels/
      prepared/
        fullframe/
          images/
            train/
            val/
            test/
          labels/
            train/
            val/
            test/
          dataset.yaml
    merged_v1_balanced/
      manifest/
      canonical/
      prepared/
        fullframe/
          images/
          labels/
          dataset.yaml
```

---

## 6. 各目录的职责

### 6.1 `datasets/merged_v1_all/`

这是第一版总数据集，保留三套数据的全部有效样本。

适合：

- 先看合并后的总体效果上限
- 作为“全量 merged”实验

### 6.2 `datasets/merged_v1_balanced/`

这是平衡版总数据集。

适合：

- 防止某一套数据量明显过大
- 让三套数据来源更均衡

### 6.3 `manifest/`

用于存放结构化元数据。

建议至少包含：

- `samples.csv`
- `source_stats.json`
- `class_mapping.json`
- `split_summary.json`

### 6.4 `canonical/`

这是合并后的“规范化原始池”。

特点是：

- 图片和标签都已经改成统一命名
- 已完成合法性检查
- 仍然不等于最终训练 split

### 6.5 `prepared/fullframe/`

这是最终真正用于训练的标准 YOLO 数据集。

这里的 `dataset.yaml` 才建议直接喂给：

- `train --dataset-yaml ...`

---

## 7. 命名规范设计

这是 merged 方案里最重要的一件事之一。

### 7.1 目标

命名必须同时满足：

- 全局唯一
- 一眼能看出来源
- 能回溯到原始序列

### 7.2 推荐命名模板

推荐改名为：

```text
{source_id}__{sequence_name}__{original_stem}.jpg
{source_id}__{sequence_name}__{original_stem}.txt
```

例如：

```text
A__D04_20260123074846__frame_0001.jpg
A__D04_20260123074846__frame_0001.txt
B__site02_seq07__000532.jpg
B__site02_seq07__000532.txt
C__night_cam01__img_1208.jpg
C__night_cam01__img_1208.txt
```

### 7.3 `source_id` 推荐写法

建议固定使用：

- `A`
- `B`
- `C`

也可以写得更清楚：

- `SRC_A`
- `SRC_B`
- `SRC_C`

关键是后续全程统一。

### 7.4 为什么一定要加前缀

因为如果三套数据里都存在：

- `frame_0001.jpg`

那直接合并就会冲突。

加来源前缀后，冲突风险会大幅下降，同时更利于后续误报回溯。

---

## 8. manifest 设计（方案一的第二个核心内容）

我建议你至少为 merged 数据集维护一份 `samples.csv`。

### 8.1 推荐字段

建议至少包含以下字段：

- `sample_id`
  - 每个样本的唯一 ID
- `source_dataset`
  - 样本来自哪套数据，例如 `A/B/C`
- `sequence_name`
  - 原始序列名
- `camera_id`
  - 如果有摄像头标识，可以补上
- `original_image_path`
  - 原始图片完整路径
- `original_label_path`
  - 原始标签完整路径
- `merged_image_path`
  - merged 后图片路径
- `merged_label_path`
  - merged 后标签路径
- `merged_stem`
  - merged 后统一文件名 stem
- `class_names`
  - 当前样本实际保留的类别映射
- `bbox_count`
  - 标注框数量
- `image_width`
  - 图片宽度
- `image_height`
  - 图片高度
- `is_valid`
  - 是否通过校验
- `invalid_reason`
  - 如果无效，原因是什么
- `duplicate_group`
  - 如果判定为重复样本，可记录重复组 ID
- `split`
  - `train/val/test`
- `notes`
  - 备注

### 8.2 额外 JSON 文件建议

#### `source_stats.json`

记录每套数据的统计信息，例如：

- 样本数
- 框数
- 平均每图框数
- 无效样本数

#### `class_mapping.json`

记录类别统一映射关系，例如：

```json
{
  "A": {"0": "clothes"},
  "B": {"0": "workwear"},
  "C": {"0": "uniform"},
  "merged": {"0": "clothes"}
}
```

#### `split_summary.json`

记录 merged 后 split 统计，例如：

- train 来自 A/B/C 的数量
- val 来自 A/B/C 的数量
- test 来自 A/B/C 的数量

---

## 9. 合并前必须完成的数据清洗

合并前，不建议直接复制文件；建议先完成以下清洗。

### 9.1 坏图排查

需要排除：

- 无法读取的图片
- 截断损坏图片
- 宽高为 0 的图片

### 9.2 非法标签排查

需要排除或修复：

- 字段数量不是 5
- `class_id` 非法
- 坐标字段不是数字
- `width <= 0` 或 `height <= 0`
- 严重越界框

### 9.3 类别统一

当前 merged 阶段的推荐口径是：

- 先统一成单类 `clothes`

如果三套数据中某一套有额外类别：

- 当前总模型阶段先不要强行一起训
- 先裁剪成当前任务口径

### 9.4 重复样本排查

至少建议做：

- 文件 hash 去重

如果后续想更严格，还可以增加：

- 感知哈希去重
- 相邻帧高相似样本筛查

### 9.5 空标签策略

当前如果三套数据里存在空标签图片，要先明确：

- 是否允许保留
- 是否全部剔除

对当前 `clothes` 检测来说，建议不要混乱处理，先在 manifest 里标记清楚。

---

## 10. train / val / test 的切分策略

这是 merged 方案里另一个非常关键的部分。

### 10.1 不推荐直接按单张图片随机打散

如果三套数据里包含大量连续帧，那么单纯随机打散会导致：

- 训练集和验证集高度相似
- 指标虚高
- 泛化能力被高估

### 10.2 推荐按序列切分

更稳妥的切法是：

- 以 `sequence` 为单位做切分

目标是让：

- train
- val
- test

尽量来自不同的时间片段或不同的完整序列。

### 10.3 当前最推荐切法

如果三套数据内部都有多个序列，推荐：

- `train = 70%`
- `val = 15%`
- `test = 15%`

但分配单位是：

- 序列

### 10.4 每套数据都尽量参与三个 split

更稳妥的原则是：

- A/B/C 三套数据都尽量在 `train/val/test` 中有代表

不要做成：

- A 只在 train
- B 只在 val
- C 只在 test

否则你很难区分：

- 是模型学不会
- 还是数据域从来没见过

### 10.5 如果某套数据只有一个长序列

那就退而求其次：

- 在该长序列内部按连续区间切分

推荐增加“缓冲带”思想：

- 前段 train
- 中间留一个小 buffer
- 再取 val
- 再留一点 buffer
- 最后取 test

这样可以减少相邻帧信息泄漏。

---

## 11. 推荐同时做两版 merged 数据集

我不建议只做一个 merged 数据集版本。

### 11.1 `merged_v1_all`

特点：

- 保留三套数据的全部有效样本

适合：

- 看总体效果上限
- 得到最大训练集版本

### 11.2 `merged_v1_balanced`

特点：

- 控制三套数据来源占比更平衡

适合：

- 防止某一套数据样本量过大，压制其他来源

### 11.3 为什么要两版一起做

因为实际很容易出现：

- A 数据量特别大
- B 和 C 明显更少

如果直接全量 merged，模型可能会明显偏向 A 的场景特征。

做一版 balanced，后续你就能比较：

- `merged_all`
- `merged_balanced`

谁更适合真实部署。

---

## 12. 推荐的执行步骤

下面给出一套稳妥的落地步骤。

### 步骤 1：分别审计 A / B / C

目标：

- 先弄清每套数据自己的质量
- 不要一开始就混在一起

建议产出：

- 每套数据的样本数
- 每套数据的框数
- 每套数据的非法标签数
- 每套数据的坏图数

### 步骤 2：统一类别映射

目标：

- 把三套数据统一映射到当前总任务口径

当前阶段推荐：

- 统一为 `0: clothes`

### 步骤 3：统一命名并写入 canonical 层

目标：

- 生成全局唯一文件名
- 建立规范化样本池

### 步骤 4：写入 manifest

目标：

- 后续每个误报 / 漏报都能回溯来源

### 步骤 5：做去重和清洗

目标：

- 不把明显重复或明显异常样本带进最终训练集

### 步骤 6：按序列切 split

目标：

- 形成 merged 的 `train/val/test`

### 步骤 7：生成 `merged_v1_all`

目标：

- 形成第一版全量 merged 数据集

### 步骤 8：生成 `merged_v1_balanced`

目标：

- 形成平衡版 merged 数据集

### 步骤 9：基于两版 merged 数据分别训练

目标：

- 比较 `merged_all` 和 `merged_balanced` 哪个更适合真实部署

---

## 13. 基于 merged 数据集的训练建议

当前总模型训练推荐依旧优先使用：

- `fullframe`

原因：

- 你当前主要是在做 `clothes` 总模型合并
- 不需要在 merged 阶段再引入 `personcrop` 变量

### 13.1 推荐训练实验

建议至少做三组对比：

#### 实验 A：当前已有 baseline

目的：

- 保留单套数据 baseline 作为对照组

#### 实验 B：`merged_v1_all`

目的：

- 看全量 merged 后的总体表现

#### 实验 C：`merged_v1_balanced`

目的：

- 看平衡版 merged 是否更适合真实部署

### 13.2 推荐训练命令形式

当 merged 数据集准备完成后，最推荐直接使用：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --dataset-yaml backend-train-model\datasets\merged_v1_all\prepared\fullframe\dataset.yaml --name clothes_merged_v1_all
```

以及：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --dataset-yaml backend-train-model\datasets\merged_v1_balanced\prepared\fullframe\dataset.yaml --name clothes_merged_v1_balanced
```

### 13.3 为什么这里推荐直接 `--dataset-yaml`

因为 merged 阶段的数据已经是：

- 规范化后的总数据集
- 准备好的标准 YOLO 数据集

此时最稳妥的方式就是：

- 显式指定 `dataset.yaml`

而不是再让脚本去猜原始数据入口。

---

## 14. 当前阶段需不需要改训练代码

### 14.1 当前最推荐：先不改

短答：

- 当前不建议为了 merged 数据集，立刻改 `backend-train-model` 的主训练代码

### 14.2 原因

当前代码已经支持：

- 直接通过 `--dataset-yaml` 训练任意标准 YOLO 数据集

这意味着：

- 你完全可以把 merged 数据准备成标准结构
- 然后直接训练

### 14.3 什么时候再考虑加代码

等后续你确认 merged 流程已经稳定，并且反复会用到时，再考虑新增：

- `merge_datasets.py`
- 或独立的 merged 构建脚本

当前阶段更重要的是：

- 先把 merged 规则定清楚
- 先把 merged_v1 做出来

---

## 15. 当前最推荐的落地顺序

如果只考虑“从今天开始怎么推进最稳”，我建议你按这个顺序来：

### 第一优先级

- 保留当前第一轮 baseline 结果
- 不要覆盖掉

### 第二优先级

- 分别审计 A / B / C
- 输出每套数据的统计

### 第三优先级

- 建立 `merged_v1_all` 的目录规范
- 先把 canonical 和 manifest 跑通

### 第四优先级

- 再建立 `merged_v1_balanced`

### 第五优先级

- 用两版 merged 数据分别训练总模型

### 第六优先级

- 比较：
  - 当前 baseline
  - `merged_v1_all`
  - `merged_v1_balanced`

### 第七优先级

- 选定当前正式主模型路线

---

## 16. 一句话总结

如果把整份文档压缩成一句话，那么当前最稳妥的方案是：

> **先分别审计三套 `clothes` 数据，再通过统一类别、统一命名、manifest 回溯、按序列切分的方式构建 `merged_v1_all` 和 `merged_v1_balanced` 两版总数据集，最后使用 `--dataset-yaml` 分别训练总模型；当前阶段先不要把“数据合并逻辑”硬塞进主训练代码。**

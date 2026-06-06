# 数据集说明

本文档用于让 AI Agent 与开发者快速理解本项目的数据集结构、标注方式、类别定义和示例文件位置。

建议：

- 当你替换为真实数据集时，优先修改本文档中的路径、类别名、标注格式和示例说明。
- 如果整个数据集都遵循同一套规则，只需要保留一组示例图片和示例标注即可。

## 1. 数据集用途

- 任务类型：`目标检测`
- 应用场景：`加油站工人未穿戴工服检测`
- 数据集状态：`已整理`

## 2. 路径约定

本文档默认采用 sibling layout：父目录下同时存在 `yolov8-program/` 与 `frame_label/`，因此仓库外数据根目录统一写作相对于仓库根的 `../frame_label`。如果某台机器的绝对路径不同，只做本地映射，不改本文档默认口径；如需特殊兼容，可通过环境变量 `YOLO_FRAME_LABEL_ROOT` 覆盖。

### 默认单源训练入口（`backend-train-model/config.py` / `backend-train-model/project_config.json`）

- 图片根目录 1：`../frame_label/clothes_labels/group3_1/clo/D04_20260123074846`
- 图片根目录 2：`../frame_label/clothes_labels/group3_1/clo/D05_20260123074841`
- 图片根目录 3：`../frame_label/clothes_labels/group3_1/clo/D15_20260123074848`
- 标注根目录：`../frame_label/clothes_labels/group3_1/clo/label-clo`

### 多源 merged / All-train-model 入口（`backend-train-model/All-train-model/*.build.json`）

- 图片根目录 4：`../frame_label/clothes_labels/group3_2/clo/1`
- 图片根目录 5：`../frame_label/clothes_labels/group3_2/clo/D15_20260119203927`
- 图片根目录 6：`../frame_label/clothes_labels/group3_3/clo/D02_20260123070624`
- 图片根目录 7：`../frame_label/clothes_labels/group3_3/clo/D02_20260123074836`
- `group3_1` 标注根目录：`../frame_label/clothes_labels/group3_1/clo/label-clo`
- `group3_2` 标注根目录：`../frame_label/clothes_labels/group3_2/clo/label_clothes`
- `group3_3` 标注根目录：`../frame_label/clothes_labels/group3_3/clo/labels`
- 数据集配置文件：
  - 单源 clothes 入口：`backend-train-model/project_config.json`
  - merged 公共训练入口：`backend-train-model/All-train-model/merged_train_project_config.json`
  - merged 数据集构建入口：`backend-train-model/All-train-model/*.build.json`
  - person 训练入口：`backend-train-model/person-train-model/person_project_config*.json`
- 示例图片：`docs/dataset_examples/sample_001.jpg`
- 示例标注：`docs/dataset_examples/sample_001.txt`

补充说明：

- 当前仓库同时保留两种数据入口：
  - 默认单源入口：`group3_1` 的 `3` 个图片根目录 + `1` 个统一标注根目录；
  - merged 多源入口：`7` 个图片根目录，按 `group3_1 / group3_2 / group3_3` 映射到 `3` 个标注根目录。
- 当前 clothes 图片文件实际直接位于各序列目录本身；更新配置时应把 `image_root` 指向序列目录，而不是额外拼接 `frames/`。
- 当前单源 clothes 入口仍未单独沉淀仓库内 `dataset.yaml`，训练、校验、转换脚本仍需以本文档中的路径约定和配对规则为准。
- merged clothes 与 person 训练线已经存在项目配置 / build 配置文件；更新这些配置时，也需要保证其内容与本文档保持一致。
- 配置文件内部的相对路径会相对于各自所在目录解析，例如：`backend-train-model/project_config.json` 相对于 `backend-train-model/`，`backend-train-model/person-train-model/person_project_config*.json` 相对于 `backend-train-model/person-train-model/`。
- `person` prepared 数据集的 `dataset.yaml` 应避免写入机器绝对 `path:`；`train: images/train`、`val: images/val`、`test: images/test` 默认按 `dataset.yaml` 所在目录解析，便于在不同盘符或训练机之间迁移。

## 3. 文件配对规则

默认示例规则如下，请按实际情况修改：

- 图片扩展名：`.jpg`
- 标注扩展名：`.txt`
- 默认单源入口中，`group3_1` 的三个图片根目录共同组成同一个数据集
- 默认单源入口中，所有标注文件统一存放在同一个标注根目录中
- merged 多源入口中，每个 `sequence` 通过各自配置里的 `image_root + label_root` 进行配对
- `All-train-model` 是否使用哪个 `sequence_name`，以各 `*.build.json` 中的显式配置为准，不要直接把末级目录 `frames` 当成序列名
- 图片与标注按“文件名（不含扩展名）相同”进行配对
- 示例：`sample_001.jpg` 对应 `sample_001.txt`

特别说明：

- 对默认单源入口，由于标注根目录是统一的，因此要求 `group3_1` 的三个图片根目录中的图片文件名全局唯一。
- 对 merged 多源入口，共用同一个 `label_root` 的多个图片根目录，也要求在该 `label_root` 的覆盖范围内避免同名冲突。
- 如果不同图片根目录中存在同名图片，则当前结构无法仅靠文件名唯一匹配标注。
- 如存在重名样本，应优先采用以下任一方式修正：
  - 重命名图片及对应标注，确保全局唯一
  - 按图片目录结构镜像存放标注
  - 为不同图片根目录拆分独立标注目录

## 4. 类别定义

请将下面内容替换成你的真实类别表。

- `0`: `clothes`

补充要求：

- 类别 ID 是否从 0 开始：`是`
- 是否允许未标注类别：`否`
- 是否存在忽略区域或特殊类别：`请填写`

## 5. 标注格式

这里必须写清楚，不要只写“标准 YOLO 格式”。

当前模板以 YOLO 检测任务为例：

- 每一行表示一个目标
- 字段顺序为：`class_id x_center y_center width height`
- 坐标单位：`归一化到 [0, 1]`
- `class_id` 为 `0` 开始的整数

示例：

```txt
0 0.422135 0.453241 0.047396 0.091667
```

## 6. 全数据集统一假设

如果整个数据集都遵循同一套规则，请保留并确认以下说明：

- 默认三个图片根目录中的样本使用相同标注方式
- 默认三个图片根目录中的样本使用相同类别定义
- 默认统一标注根目录覆盖三个图片根目录的全部图片
- 默认所有样本与示例文件使用相同标注方式
- 默认所有类别定义与上文一致
- 默认所有图片尺寸允许不同，但标注规则一致

## 7. 示例文件

以下文件用于帮助 AI Agent 快速理解数据格式：

- 示例图片：`docs/dataset_examples/sample_001.jpg`
- 示例标注：`docs/dataset_examples/sample_001.txt`

注意：

- 这两个文件名是推荐固定名称，便于 AI Agent 稳定读取。
- 如果你还没放入真实示例，请先补充这两个文件，再让 Agent 编写依赖数据格式的代码。

如果你已经把示例图片放到仓库中，Markdown 预览时可以直接看到：

![示例图片](./dataset_examples/sample_001.jpg)

建议至少提供：

- 1 张示例图片
- 1 个与该图片严格对应的标注文件

只提供图片、不提供标注时，Agent 只能把图片当作视觉参考，无法可靠推断完整标注规则。

## 8. 数据质量与特殊规则

如有以下情况，请明确写出：

- 是否允许空标注文件
- 是否存在损坏图片
- 是否存在多标签重叠规则
- 是否存在需要忽略的小目标、边缘目标、遮挡目标
- 是否有命名异常样本
- 三个图片根目录之间是否存在重名图片

这部分信息会直接影响 Agent 编写的数据清洗脚本、校验脚本和训练配置。

## 9. 给 AI Agent 的执行指令

当任务涉及数据集处理时，请遵循以下规则：

1. 先读取本文档。
2. 再读取示例图片与示例标注。
3. 以本文档中的任务类型、类别表、标注格式、路径规则为准。
4. 如本文档与代码实现不一致，优先指出冲突，不要自行假设。
5. 在编写数据转换、训练、验证、可视化代码前，先确认示例标注格式已被正确理解。
6. 如果使用统一标注根目录，先检查图片文件名是否全局唯一，再执行自动配对。

## 10. 维护建议

每次你更换数据集或修改标注方案时，至少同步更新以下内容：

- `路径约定`
- `类别定义`
- `标注格式`
- `示例文件`
- `特殊规则`

如果你只想维护一个最小版本，请确保下面四项始终正确：

- 数据集任务类型
- 类别表
- 标注格式字段顺序
- 一组真实可读的示例图片与示例标注

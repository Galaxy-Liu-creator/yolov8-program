# new_clothes_train 运行说明

## 1. 本次任务目标

本轮在 `backend-train-model/new_clothes_train/` 下新增了一套面向 `clothes` 的扩样整理流程，用于把：

- 旧的 `All-train-model` 7 个 legacy clothes source
- 新增的 `new_clothes_labels`

统一整理成一套新的 merged 数据集配置与切分清单，后续可直接复用现有 `build_merged_clothes_dataset.py` 与 `train_workwear.py` 训练链路。

## 2. 新数据来源

### 2.1 新增图片根目录

- `D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\new_clothes_labels\images`

### 2.2 新增标注根目录

- `D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\new_clothes_labels\clothes_labels`

### 2.3 标注补全规则

对新增数据源，图片与标注按“同名文件 stem”配对：

- 图片：`.jpg / .jpeg / .png`
- 标注：`.txt`

如果某张图片没有对应标注 txt，则自动在：

- `backend-train-model/new_clothes_train/train-result/working/new_source_completed_labels/`

下补一个空白 txt，避免训练时把“缺标图片”误当成异常脏样本或漏配对样本。

## 3. 本次新增文件

### 3.1 配置文件

- `backend-train-model/new_clothes_train/new_clothes_train_project_config.json`
- `backend-train-model/new_clothes_train/clothes_merged_with_new_labels_v1.build.json`

### 3.2 数据整理脚本

- `backend-train-model/new_clothes_train/train-code/prepare_new_clothes_dataset.py`

### 3.3 生成产物

- `backend-train-model/new_clothes_train/train-result/working/new_source_prepare_summary.json`
- `backend-train-model/new_clothes_train/train-result/splits/clothes_merged_with_new_labels_v1.split.csv`
- `backend-train-model/new_clothes_train/train-result/splits/clothes_merged_with_new_labels_v1_summary.json`
- `backend-train-model/new_clothes_train/train-result/working/new_source_completed_labels/*.txt`

## 4. 数据整理结果

根据本轮整理结果：

- 新增图片总数：`2507`
- 原始已有标注文件数：`2188`
- 自动补空白标注数：`319`
- 正样本标注文件数：`2185`
- 空标注文件总数：`322`
- 孤立标注文件数：`1`
- 孤立标注 stem：`classes`

说明：

- `classes.txt` 被视为说明类文件，不参与样本配对；
- `322` 个空标注文件 = 原本就为空的标注文件 + 本轮自动补齐的空白 txt。

## 5. 数据切分方式

### 5.1 legacy 旧数据

旧 7 个 clothes source **保持原有切分不变**，不重新打乱：

- train/val 继承：`All-train-model/splits/trainval_balanced_v1.split.csv`
- test 继承：`All-train-model/splits/unified_holdout_v1.split.csv`

也就是说，旧数据仍沿用当前项目已验证过的：

- balanced train/val
- unified holdout test

### 5.2 新增 new_clothes 数据

新增源：

- `source_id = gnew`
- `sequence_name = new_clothes_flat_2507`

当前已不再使用最初的 `sequence_contiguous_by_sorted_stem`。

结合 `check_log.md` 中确认的问题，以及你补充的“`gnew` 由 3~4 个不同视频/场景拼接而成”的事实，
现已改为：

- `stratified_random_by_positive_empty`
- `seed = 42`

即先按标签文件是否为空把样本分成两层：

- `positive`（有框）
- `empty`（空标注负样本）

再在每一层内部独立随机分配到 `train / val / test`，比例为：

- `train = 0.70`
- `val = 0.15`
- `test = 0.15`

对应新源样本数现在为：

- train：`1754`
- val：`375`
- test：`378`

对应 gnew 当前分布验证结果：

| split | 图像数 | 空标注数 | 空标注率 | 总框数 | 平均每图框数 |
| --- | ---: | ---: | ---: | ---: | ---: |
| train | 1754 | 225 | 12.83% | 2991 | 1.7052 |
| val | 375 | 48 | 12.80% | 644 | 1.7173 |
| test | 378 | 49 | 12.96% | 650 | 1.7196 |

说明：

- 这一步的目标不是“还原真实视频时序切分”，而是先消除原 contiguous 切分下明显的分布失衡；
- 从当前统计看，`val / test` 的空标注率与框密度已经非常接近，可作为更稳妥的训练与评估入口。

### 5.3 合并后的总切分结果

合并 legacy + new source 后，总 split 统计现在为：

- train：`2106`
- val：`450`
- test：`453`

按 source 细分：

| split | g31 | g32 | g33 | gnew | total |
| --- | ---: | ---: | ---: | ---: | ---: |
| train | 67 | 209 | 76 | 1754 | 2106 |
| val | 14 | 45 | 16 | 375 | 450 |
| test | 14 | 45 | 16 | 378 | 453 |

## 6. 构建配置说明

新的 merged 构建配置文件为：

- `backend-train-model/new_clothes_train/clothes_merged_with_new_labels_v1.build.json`

其风格与当前 `All-train-model/*.build.json` 保持一致，核心设计为：

- `split_manifest_csv` 显式指向本轮新生成的 split 清单
- `strict_split_manifest = true`
- 新增源使用已补齐空标注后的 `new_source_completed_labels`
- 训练参数入口单独落在 `new_clothes_train_project_config.json`

当前还应注意：

- merged builder 的 `missing_label_policy` 仍为 `skip`；
- 因此 legacy 旧数据里仍有 `48` 张缺失 source label 的历史样本不会被纳入本轮 merged 数据集；
- 这不影响 `gnew` 新源的全部纳入，但会使最终 build 后的 `included_images` 小于 split manifest 的总行数。

训练参数默认与当前 clothes 主线保持一致：

- `imgsz=640`
- `epochs=180`
- `batch=4`
- `patience=40`
- `workers=4`
- `device=0`
- `seed=42`

## 7. 推荐执行顺序

建议先进入：

```powershell
Set-Location .\backend-train-model
```

### 7.1 先整理新增标签与 split manifest

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe new_clothes_train\train-code\prepare_new_clothes_dataset.py
```

作用：

- 补齐新增图片缺失的空白 txt
- 生成新的 split manifest
- 生成整理摘要 JSON

### 7.2 构建 merged 数据集

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe build_merged_clothes_dataset.py --config new_clothes_train\clothes_merged_with_new_labels_v1.build.json --overwrite
```

正常构建后，目标数据集会落在：

- `backend-train-model/new_clothes_train/train-result/datasets/clothes_merged_with_new_labels_v1/`

其中应包含与现有风格一致的：

- `dataset.yaml`
- `manifest.csv`
- `build_report.json`

本轮已实际 build 成功，并确认生成以上文件。

当前 build 后的关键统计为：

- `source_images = 3009`
- `included_images = 2961`
- `included_boxes = 5265`
- `missing_source_labels = 48`

当前 merged 数据集 split 图像数为：

- train：`2072`
- val：`443`
- test：`446`

说明：

- split manifest 总行数仍是 `3009`；
- 但 legacy 历史源中 `48` 张缺失 source label 的样本在 `missing_label_policy=skip` 下不会进入最终数据集；
- 因此最终 `included_images = 2961` 是符合当前 build 策略的正常结果。

## 8. 训练命令

构建完成后，使用下面命令训练：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py train --project-config new_clothes_train\new_clothes_train_project_config.json --dataset-yaml new_clothes_train\train-result\datasets\clothes_merged_with_new_labels_v1\dataset.yaml --name clothes_merged_with_new_labels_v1_baseline
```

## 9. 评估命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py evaluate --project-config new_clothes_train\new_clothes_train_project_config.json --dataset-yaml new_clothes_train\train-result\datasets\clothes_merged_with_new_labels_v1\dataset.yaml --weights new_clothes_train\train-result\artifacts\runs\clothes_merged_with_new_labels_v1_baseline\weights\best.pt
```

## 10. 导出命令

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py export --project-config new_clothes_train\new_clothes_train_project_config.json --weights new_clothes_train\train-result\artifacts\runs\clothes_merged_with_new_labels_v1_baseline\weights\best.pt --overwrite
```

## 11. 结果目录约定

本轮 `new_clothes_train` 下的职责划分如下：

- `train-code/`：新增整理脚本
- 根目录：build 配置与训练 project config 等入口文件
- `train-result/splits/`：本轮新的 split manifest 与统计
- `train-result/working/`：补齐标签与整理摘要
- `train-result/datasets/`：构建后的标准 YOLO 数据集
- `train-result/review/`：merged builder 输出的缺标审计结果
- `train-result/artifacts/`：训练 / 评估 / 导出结果

另外，本轮新增了新源数据检查脚本与报告：

- 脚本：`backend-train-model/new_clothes_train/train-code/validate_new_clothes_source.py`
- 原始检查报告 JSON：`backend-train-model/new_clothes_train/train-result/working/new_source_validation_report.json`
- 原始检查报告 MD：`backend-train-model/new_clothes_train/train-result/working/new_source_validation_report.md`
- 训练结果评审：`backend-train-model/new_clothes_train/train-docs/clothes_merged_with_new_labels_v1_eval_review.md`

当前检查结论：

- 图片可读数：`2507 / 2507`
- 损坏图片数：`0`
- 非法标注文件数：`0`
- 非法标注行数：`0`

## 12. 兼容性说明

- 旧 7 个 legacy source 的 split 口径未改，避免破坏当前已验证的 baseline 对照基础。
- `gnew` 现已从连续切分调整为“按 `positive / empty` 分层随机切分”，这是为了解决原 contiguous 方案下 `val/test` 分布失衡的问题。
- 你已明确说明 `gnew` 确实由 3~4 个不同视频/场景拼接而成；因此当前分层随机方案可作为更稳妥的训练入口，但它仍不是“按真实视频场景整段切分”的最终治理终态。
- 若后续能明确每个视频对应的 stem 范围，建议进一步升级为“按场景整段切分 + 场景级分配 split”。
- 当前这套 merged 配置是 `clothes` 单类检测数据集，不应直接表述成“未穿工服告警器”。

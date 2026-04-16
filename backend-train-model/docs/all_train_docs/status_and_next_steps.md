# [归档] All-train-model 当前状态与下一步

> 归档说明（2026-04-15）：
> - 本文描述的是 merged 早期阶段“尚未证明优于 `first-train`”时的状态快照。
> - 当前主线状态已经更新，现阶段请优先查看：
>   - `backend-train-model/docs/后端训练完成进度.md`
>   - `backend-train-model/docs/todo_list.md`
>   - `backend-train-model/All-train-model/00_CURRENT_BASELINE/README.md`

本文档专门回答三个问题：

1. `backend-train-model/All-train-model/` 现在到底已经完成了哪些步骤
2. merged 流程和原来的 `audit / prepare / train / evaluate / export` 是什么关系
3. 你接下来最稳妥应该运行哪些命令，每个参数是什么意思

## 1. 先说结论

当前 `All-train-model/` 已经完成的是：

- 三套 `clothes` 数据的合并配置已经落地
- merged 数据集构建脚本已经落地
- `merged_v1_positive_only` 已经成功构建，并完成过一轮 `train / evaluate / export`
- `merged_v2_full_reviewed` 已经吸收 48 张 review 空标签样本并成功构建
- `clothes_merged_v2_from_first` 已经完成至少一轮训练、评估与导出；该 run 的真实历史是先用 `first-train` 的 `best.pt` 启动，后因中断再通过 `last.pt` resume
- merged 训练专用的产物目录切换方案已经落地

当前 `All-train-model/` 还没完成的是：

- 证明 `merged_v2_from_first` 能稳定优于 `first-train`
- 建立统一 holdout / 分源评估口径，减少 `first-train` 与 merged 路线比较时的 split 噪声
- 复核 48 张 review 空标签样本是否全部是真负样本
- 重做 source-balanced split，并在同一口径下重新比较 `first-train`、`merged_v1` 与 `merged_v2`

换句话说，你现在已经从“可以直接开训 merged_v1”推进到“merged_v2 已有训练闭环，但还不足以替代 `first-train` 基线”的节点上。

## 2. 截止当前已完成的具体步骤

### 2.1 已完成：合并训练目录与配置模板

已经具备以下固定文件：

- `All-train-model/merged_train_project_config.json`
- `All-train-model/merged_clothes_v1.build.json`
- `All-train-model/merged_clothes_v2.build.json`

它们分别负责：

- 指定 merged 训练时的默认产物根目录
- 指定 `merged_v1_positive_only` 的构建规则
- 指定 `merged_v2_full_reviewed` 的构建规则

### 2.2 已完成：`merged_v1_positive_only` 数据集构建

已经实际生成：

- `All-train-model/datasets/merged_clothes_v1_positive_only/dataset.yaml`
- `All-train-model/datasets/merged_clothes_v1_positive_only/manifest.csv`
- `All-train-model/datasets/merged_clothes_v1_positive_only/build_report.json`
- `All-train-model/review/merged_clothes_v1_positive_only/missing_review.csv`

这说明 merged 数据集并不是“只写了方案”，而是已经真正构建出来了。

### 2.3 已完成：源数据扫描、筛选、切分和统计

以 `build_report.json` 为准，目前统计结果是：

- 总源图片数：`502`
- 当前纳入 merged_v1 的图片数：`454`
- 当前纳入标注框数：`980`
- 缺失源标注的图片数：`48`

split 结果如下：

- `train`：`330` 张
- `val`：`62` 张
- `test`：`62` 张

### 2.4 已完成：缺标样本 review 清单输出

已经生成：

- `All-train-model/review/merged_clothes_v1_positive_only/missing_review.csv`

这个 CSV 就是你后续做 `merged_v2` 时的待办清单。

### 2.5 已完成：merged 训练产物改写到独立目录

`All-train-model/merged_train_project_config.json` 已经把默认产物根目录配置到：

- `backend-train-model/All-train-model/artifacts/prepared`
- `backend-train-model/All-train-model/artifacts/runs`
- `backend-train-model/All-train-model/artifacts/reports`
- `backend-train-model/All-train-model/artifacts/export`

这意味着后续 merged 训练不会再把产物混回默认的 `backend-train-model/artifacts/`。

## 3. 现在还没有完成的步骤

从当前目录实际产物看，merged 训练闭环已经不再是“完全没跑”的状态。

当前已经能看到两套 merged run：

- `All-train-model/artifacts/runs/clothes_merged_v1_fullframe/`
- `All-train-model/artifacts/runs/clothes_merged_v2_from_first/`

也已经能看到对应报告：

- `All-train-model/artifacts/reports/clothes_merged_v1_fullframe_train.json`
- `All-train-model/artifacts/reports/clothes_merged_v1_fullframe_eval.json`
- `All-train-model/artifacts/reports/clothes_merged_v2_from_first_train.json`
- `All-train-model/artifacts/reports/clothes_merged_v2_from_first_eval.json`
- `All-train-model/artifacts/reports/clothes_merged_v2_from_first_export.json`

当前真正还没完成的是：

- `merged_v2_from_first` 尚未证明整体优于 `first-train`
- 当前比较口径还没有统一 holdout / 分源评估闭环
- 48 张 review 空标签样本尚未按“真负样本 / 难负样本 / 疑似漏标 / 边界样本”分层复核
- 下一版 source-balanced merged 数据集尚未落地

## 4. merged 流程和原始 `audit / prepare` 的关系

这是当前最容易混淆的地方。

### 4.1 merged 流程不是走默认的 `prepare` 路线

原始 `train_workwear.py` 的标准链路是：

- `audit`
- `prepare`
- `train`
- `evaluate`
- `export`

但你现在这个 merged 流程不是直接拿原始散数据去 `prepare`，而是先通过：

- `build_merged_clothes_dataset.py`

把三套数据合并成一个标准 YOLO 数据集，然后再把这个现成的：

- `dataset.yaml`

交给 `train_workwear.py train --dataset-yaml` 去训练。

### 4.2 所以当前阶段应该怎么理解

对于 `All-train-model/` 这条 merged 训练链路，可以这样理解：

- “源数据扫描 / 筛选 / 切分 / 生成 dataset.yaml”这一步，已经由 `build_merged_clothes_dataset.py` 完成了
- 所以 merged 流程下，不需要再额外跑 `train_workwear.py prepare`
- 也不建议再跑 `train_workwear.py audit`

### 4.3 为什么 `train --dataset-yaml` 可以直接开训

`train_workwear.py` 在训练时会优先看：

- 你有没有显式传 `--dataset-yaml`

只要传了，它就直接使用那个现成的数据集 YAML，而不是再去推导或触发一次 `prepare`。

所以当前 merged 路线最稳妥的入口就是：

- 直接从 `train --dataset-yaml ...` 开始

### 4.4 为什么不建议用 `train_workwear.py all`

因为 `all` 命令内部会先强制执行一次：

- `prepare`

然后再：

- `train`
- `evaluate`
- `export`

这和 merged 流程的“先独立构建 merged 数据集，再直接训练”并不一致。

所以当前 merged 路线最稳妥的用法是：

- `train`
- `evaluate`
- `export`

分别单独执行。

## 5. 现在最稳妥的运行方式

### 5.1 推荐先切换目录

最稳妥的方式，是先切到：

- `backend-train-model/`

再执行后面的命令。这样做的好处是：

- `build_merged_clothes_dataset.py` 的 `--config` 相对路径更直观
- `train_workwear.py` 的 `--project-config` 不会踩到相对路径解析坑
- 你复制命令时不需要混用长短路径

建议先执行：

```powershell
Set-Location .\backend-train-model
```

如果你当前已经在仓库根目录，这一条就够了。

### 5.2 第 0 步：确认现成数据还在

如果下面三个文件都还在，你就可以直接进入训练：

- `All-train-model/datasets/merged_clothes_v1_positive_only/dataset.yaml`
- `All-train-model/datasets/merged_clothes_v1_positive_only/build_report.json`
- `All-train-model/review/merged_clothes_v1_positive_only/missing_review.csv`

### 5.3 第一步：如需重建 `merged_v1_positive_only`

如果你已经确认 `dataset.yaml`、`manifest.csv`、`build_report.json` 都在，而且不打算重建，这一步可以跳过。

命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe build_merged_clothes_dataset.py --config All-train-model\merged_clothes_v1.build.json --overwrite
```

作用：

- 重新扫描三套源数据
- 只纳入“当前已有同名标注”的样本
- 重新生成 merged 数据集目录
- 重新输出缺标 review 清单

参数说明：

- `build_merged_clothes_dataset.py`
  - merged 数据集构建脚本
- `--config`
  - 指定使用哪份 merged 构建配置
- `All-train-model\merged_clothes_v1.build.json`
  - 当前使用 `merged_v1_positive_only` 方案
- `--overwrite`
  - 允许覆盖已有输出目录；如果不加，而目标目录已存在，脚本会拒绝执行

### 5.4 第二步：训练 merged_v1 总模型

命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py train --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\merged_clothes_v1_positive_only\dataset.yaml --name clothes_merged_v1_fullframe
```

作用：

- 直接使用已经构建好的 merged 数据集开始训练
- 不再走原始 `prepare`
- 训练产物会写到 `All-train-model/artifacts/runs/`
- JSON 报告会写到 `All-train-model/artifacts/reports/`

参数说明：

- `train`
  - 调用训练子命令
- `--project-config`
  - 加载 merged 训练专用项目配置
- `All-train-model\merged_train_project_config.json`
  - 把默认产物根目录切到 `All-train-model/artifacts/`
- `--dataset-yaml`
  - 显式告诉训练脚本使用哪一个现成数据集
- `All-train-model\datasets\merged_clothes_v1_positive_only\dataset.yaml`
  - 当前 merged_v1 的数据集入口
- `--name clothes_merged_v1_fullframe`
  - 指定本次 run 名称，后续评估和导出都会依赖这个名字形成的目录

当前模板默认训练参数来自 `merged_train_project_config.json`：

- `imgsz=640`
- `epochs=180`
- `batch=4`
- `patience=40`
- `workers=0`
- `device=cpu`
- `seed=42`

现阶段最稳妥建议：

- 先按默认参数跑通一版
- 如果你确认 CUDA 环境稳定，再手动追加：

```powershell
--device 0
```

训练完成后，最关键的权重文件应该出现在：

- `All-train-model/artifacts/runs/clothes_merged_v1_fullframe/weights/best.pt`

### 5.5 第三步：评估 merged_v1 总模型

先跑原生 YOLO 指标评估：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py evaluate --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\merged_clothes_v1_positive_only\dataset.yaml --weights All-train-model\artifacts\runs\clothes_merged_v1_fullframe\weights\best.pt
```

作用：

- 用刚训练好的 `best.pt` 在 `dataset.yaml` 指向的数据集上做评估
- 输出 `val / test` 的原生 YOLO 指标
- 写出评估 JSON 报告

参数说明：

- `evaluate`
  - 调用评估子命令
- `--project-config`
  - 保证评估报告仍然写入 merged 专用 artifacts 目录
- `--dataset-yaml`
  - 指定评估所使用的数据集
- `--weights`
  - 显式指定待评估权重，避免误拿到旧权重

如果你后面要做链路级复核，再额外加：

```powershell
--inspection-validate --python-exe D:\Miniconda3_python\envs\yolo_code\python.exe
```

也就是：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py evaluate --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\merged_clothes_v1_positive_only\dataset.yaml --weights All-train-model\artifacts\runs\clothes_merged_v1_fullframe\weights\best.pt --inspection-validate --python-exe D:\Miniconda3_python\envs\yolo_code\python.exe
```

这个附加参数的含义是：

- `--inspection-validate`
  - 额外调用 `inspection-flask` 做链路级复核
- `--python-exe`
  - 指定用于调用 `inspection-flask` 的 Python 解释器

现阶段建议顺序：

1. 先跑原生评估
2. 再决定要不要跑 `inspection-flask` 复核

### 5.6 第四步：导出最终权重

命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py export --project-config All-train-model\merged_train_project_config.json --weights All-train-model\artifacts\runs\clothes_merged_v1_fullframe\weights\best.pt --overwrite
```

作用：

- 把最终使用的权重复制到导出目录
- 同时生成导出元数据 JSON

参数说明：

- `export`
  - 调用导出子命令
- `--project-config`
  - 保证导出产物写入 merged 专用目录
- `--weights`
  - 指定要导出的训练结果
- `--overwrite`
  - 若导出文件已存在，则允许覆盖

如果你想自定义导出目录，还可以额外加：

```powershell
--export-root 你的导出目录
```

如果你确认这版模型要直接给 `inspection-flask` 联调，再额外加：

```powershell
--deploy
```

## 6. 一定要注意的路径坑

`train_workwear.py` 对 `--project-config` 的相对路径解析，不是相对你当前终端目录，而是相对：

- `backend-train-model/`

所以如果你在仓库根目录直接运行这条命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --project-config backend-train-model\All-train-model\merged_train_project_config.json ...
```

它很可能会把路径错误解析成类似：

- `backend-train-model/backend-train-model/All-train-model/...`

所以当前最稳妥的规避方法就是

- 先 `Set-Location .\backend-train-model`
- 再执行文档里的短路径命令

如果你不想切目录，也可以直接使用：

- `backend-train-model/All-train-model/datasets/merged_clothes_v1_positive_only/build_report.json`

里面保存的绝对路径命令。

## 7. 训练完成后，下一阶段该做什么

当前建议顺序如下：

1. 先把 `merged_v1_positive_only` 训练、评估、导出完整走通
2. 看训练结果和效果，如果 baseline 已经明显优于单套数据训练结果，再进入补标阶段
3. 根据 `missing_review.csv` 补完那 `48` 张缺标图片
4. 构建 `merged_v2_full_reviewed`
5. 再对 `merged_v2` 重训、评估、导出

## 8. 后续做 `merged_v2` 的命令

先补标到：

- `All-train-model/review/merged_clothes_v2_full_reviewed/labels/`

规则：

- 文件名使用 `missing_review.csv` 里的 `merged_stem`
- 如果某张图确认没有 `clothes`，也要放一个空白 `.txt`

然后执行：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe build_merged_clothes_dataset.py --config All-train-model\merged_clothes_v2.build.json --overwrite
```

执行成功后，再把上面的 `train / evaluate / export` 命令里的数据集路径和 run 名称切换成 `merged_v2` 版本即可。

## 9. 当前最短执行清单

如果你现在就准备开始训练，最短只需要做这三件事：

```powershell
Set-Location .\backend-train-model
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py train --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\merged_clothes_v1_positive_only\dataset.yaml --name clothes_merged_v1_fullframe
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py evaluate --project-config All-train-model\merged_train_project_config.json --dataset-yaml All-train-model\datasets\merged_clothes_v1_positive_only\dataset.yaml --weights All-train-model\artifacts\runs\clothes_merged_v1_fullframe\weights\best.pt
D:\Miniconda3_python\envs\yolo_code\python.exe train_workwear.py export --project-config All-train-model\merged_train_project_config.json --weights All-train-model\artifacts\runs\clothes_merged_v1_fullframe\weights\best.pt --overwrite
```

如果你只是担心数据集是不是已经准备好了，可以先检查这两个文件是否存在：

- `All-train-model/datasets/merged_clothes_v1_positive_only/dataset.yaml`
- `All-train-model/datasets/merged_clothes_v1_positive_only/build_report.json`

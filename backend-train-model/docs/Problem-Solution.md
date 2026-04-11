# Problem-Solution 审查记录

> **约束条件**
> - 每次代码审查后更新本文档，追加新的审查记录。
> - 采用**最近在前、历史在后**的顺序排列。
> - 每条记录须包含：审查日期、审查范围、发现的问题、解决方案、当前状态。
> - 问题按优先级标注：`[P0]` 阻塞性 / `[P1]` 高优 / `[P2]` 中优 / `[P3]` 低优。

---

## 审查记录 #002 — 2026-04-11

**审查范围：** `backend-train-model/` 统一 holdout 数据集构建结果复核，确认后续训练与评估入口是否已打通。

---

### 问题列表

#### [P0] 三套统一 holdout 对比数据集已构建完成，`dataset.yaml` 已就绪

**现象：**
以下三套数据集均已成功生成：
- `backend-train-model/All-train-model/datasets/merged_clothes_v2_balanced/`
- `backend-train-model/All-train-model/datasets/unified_holdout_v1/`
- `backend-train-model/All-train-model/datasets/first_train_holdout_v1/`

**验证结果：**
- `merged_clothes_v2_balanced`
  - `included_images = 427`
  - `train = 352`
  - `val = 75`
- `unified_holdout_v1`
  - `included_images = 75`
  - `test = 75`
- `first_train_holdout_v1`
  - `included_images = 81`
  - `train = 67`
  - `val = 14`

**解决方案：**
已执行以下三条构建命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe build_merged_clothes_dataset.py --config All-train-model\merged_clothes_v2_balanced.build.json --overwrite
D:\Miniconda3_python\envs\yolo_code\python.exe build_merged_clothes_dataset.py --config All-train-model\unified_holdout_v1.build.json --overwrite
D:\Miniconda3_python\envs\yolo_code\python.exe build_merged_clothes_dataset.py --config All-train-model\first_train_holdout_v1.build.json --overwrite
```

**当前状态：** 已解决 — 三套数据集的 `dataset.yaml`、`manifest.csv`、`build_report.json` 均已生成，可继续进入 cross-eval 与 strict holdout 训练阶段。

---

### 已确认项（本次审查）

| 检查项 | 状态 |
|---|---|
| `merged_clothes_v2_balanced/dataset.yaml` | ✅ 已生成 |
| `unified_holdout_v1/dataset.yaml` | ✅ 已生成 |
| `first_train_holdout_v1/dataset.yaml` | ✅ 已生成 |
| 三套数据集的 `manifest.csv` | ✅ 已生成 |
| 三套数据集的 `build_report.json` | ✅ 已生成 |
| `merged_clothes_v2_balanced` 的 split 分布（352 / 75） | ✅ 与 `trainval_balanced_v1.split.csv` 一致 |
| `unified_holdout_v1` 的 holdout 分布（75） | ✅ 与 `unified_holdout_v1.split.csv` 一致 |
| `first_train_holdout_v1` 的 split 分布（67 / 14） | ✅ 与 `g31` 子集预期一致 |

---

### 后续行动（按优先级）

1. **[P1]** 按 `total-run-method.md` 的 cross-eval 命令，先统一现有 `first-train` 与 `merged_v2_from_first` 的评估口径。
2. **[P1]** 按 `total-run-method.md` 的 strict holdout 命令，分别重训 `clothes_first_train_holdout_v1` 与 `clothes_merged_v2_balanced_from_first`。
3. **[P1]** 在 `unified_holdout_v1` 上执行 strict eval，形成最终比较口径。
4. **[P2]** 如 balanced merged 仍无明显改善，优先复核 `48` 张 review 空标签与 `g32 / g33` 标注一致性。
5. **[P3]** 数据与口径稳定后，再做参数实验（`imgsz`、`patience`、学习率等）。

---

## 审查记录 #001 — 2026-04-11

**审查范围：** `backend-train-model/` 整体，重点核查 `first-train` 与 `All-train-model` 是否已具备统一 holdout 训练条件。

---

### 问题列表

#### [P0] 三套对比数据集尚未构建，无法启动统一 holdout 训练

**现象：**
`backend-train-model/All-train-model/datasets/` 目录下缺少以下三个数据集：
- `merged_clothes_v2_balanced/`
- `unified_holdout_v1/`
- `first_train_holdout_v1/`

**根因：**
Split manifests（`trainval_balanced_v1.split.csv`、`unified_holdout_v1.split.csv`）已生成，三个 `.build.json` 配置文件的关键配置项已就绪，但 `build_merged_clothes_dataset.py` 的构建命令尚未执行。

**解决方案：**
在 `backend-train-model/` 目录下依次执行：

```powershell
# 1. balanced merged 训练集
D:\Miniconda3_python\envs\yolo_code\python.exe build_merged_clothes_dataset.py --config All-train-model\merged_clothes_v2_balanced.build.json --overwrite

# 2. unified holdout 评估集
D:\Miniconda3_python\envs\yolo_code\python.exe build_merged_clothes_dataset.py --config All-train-model\unified_holdout_v1.build.json --overwrite

# 3. first-train 对照训练集
D:\Miniconda3_python\envs\yolo_code\python.exe build_merged_clothes_dataset.py --config All-train-model\first_train_holdout_v1.build.json --overwrite
```

**当前状态：** 未解决 — 等待执行构建命令。

**构建后验收标准：**
每套输出数据集目录下都必须存在：
- `dataset.yaml`
- `manifest.csv`
- `build_report.json`

---

### 已就绪项（本次审查确认）

| 检查项 | 状态 |
|---|---|
| `splits/trainval_balanced_v1.split.csv`（502 条样本记录，CSV 含表头为 503 行） | ✅ 已生成 |
| `splits/unified_holdout_v1.split.csv`（502 条样本记录，CSV 含表头为 503 行） | ✅ 已生成 |
| `splits/source_balanced_v1_summary.json` | ✅ 已生成 |
| 三个 `.build.json` 配置文件 | ✅ 关键配置项已就绪，待构建验证 |
| `build_merged_clothes_dataset.py` 支持 `split_manifest_csv` / `strict_split_manifest` | ✅ 已支持 |
| `train_workwear.py evaluate` 支持 `--report-name` | ✅ 已支持 |
| `merged_clothes_v2_full_reviewed/manifest.csv`（canonical pool，502 条样本记录，CSV 含表头为 503 行） | ✅ 存在 |
| `first-train` 权重 `best.pt` | ✅ 存在 |
| `merged_v2_from_first` 权重 `best.pt` | ✅ 存在 |

---

### 后续行动（按优先级）

1. **[P0]** 执行上述三条 build 命令，完成数据集构建。
2. **[P1]** 按 `unified_holdout_compare_method.md` 第 5.1 节执行 cross-eval，统一现有权重的评估口径。
3. **[P1]** 按第 5.2 节执行 strict holdout 重训比较。
4. **[P2]** 根据 `merged_v2_improvement_plan.md` P1 项，对 48 张 review 空标签进行分层复核（真负样本 / 难负样本 / 疑似漏标 / 边界不清晰）。
5. **[P3]** 数据与 split 稳定后，再考虑参数实验（`imgsz`、`patience`、学习率等）。

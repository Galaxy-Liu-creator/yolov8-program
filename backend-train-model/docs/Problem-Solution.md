# Problem-Solution 审查记录

> **维护约束**
> - 每次代码或文档审查后更新本文件，并追加新的审查记录。
> - 采用**最近在前、历史在后**的顺序排列。
> - 每条记录包含：审查日期、审查范围、发现的问题、解决方案、当前状态。
> - 问题优先级统一标记为：`[P0]` 阻塞 / `[P1]` 高优 / `[P2]` 中优 / `[P3]` 低优。

---

## 审查记录 #003 — 2026-04-15

**审查范围：** `backend-train-model/` 当前文档体系与 unified holdout / merged baseline 当前状态是否一致。

### 问题列表

#### [P0] 文档树中同时存在“旧阶段结论”和“当前主线结论”，容易误导当前 baseline 判断

**现象：**

- `backend-train-model/docs/all_vs_first_train_review.md` 仍保留 `2026-04-06` 时点“`first-train` 更稳”的历史结论；
- `backend-train-model/docs/后端训练完成进度.md` 仍停留在“merged baseline 尚未固定、baseline FP/FN 清单未落地”的旧状态；
- 缺少一份放在 `backend-train-model/` 根目录的总入口 README，导致读者一进入目录后不清楚当前该看哪份文档、也不清楚当前 baseline 是哪一个 run。

**解决方案：**

1. 新增 `backend-train-model/README.md`，集中说明：
   - 当前训练进度；
   - 当前 merged baseline；
   - `docs/` 当前主线与历史文档的区别；
   - 推荐阅读顺序。
2. 重写 `backend-train-model/docs/后端训练完成进度.md`，同步为当前真实状态：
   - baseline 已固定；
   - FP/FN 资产已生成；
   - `person` 是“数据入口已具备、权重未产出”的状态。
3. 在 `backend-train-model/docs/all_vs_first_train_review.md` 中增加历史说明，明确其不再代表当前 baseline 结论。
4. 在 `backend-train-model/docs/total-run-method.md` 中增加状态说明，明确它当前是“统一 holdout 重跑手册”。

**当前状态：** 已解决。

#### [P1] `docs/` 的阅读入口不清晰，当前主线与历史归档没有被显式区分

**现象：**

- `backend-train-model/docs/README.md` 更偏向 CLI 使用说明；
- `docs/todo_list.md`、`docs/total-run-method.md`、`All-train-model/00_CURRENT_BASELINE/README.md` 才是当前主线文档；
- `docs/all_train_docs/*` 与 `docs/first_train_docs/*` 主要是历史阶段资料，但没有统一入口提醒。

**解决方案：**

1. 在新建的 `backend-train-model/README.md` 中写明推荐阅读顺序；
2. 在 `backend-train-model/docs/README.md` 顶部增加“当前主线先读哪里”的说明；
3. 在根 README 中明确将：
   - `docs/todo_list.md`
   - `docs/total-run-method.md`
   - `All-train-model/00_CURRENT_BASELINE/README.md`
   定义为当前主线文档；
4. 将：
   - `docs/all_vs_first_train_review.md`
   - `docs/all_train_docs/*`
   - `docs/first_train_docs/*`
   明确标注为历史阶段归档。

**当前状态：** 已解决。

### 本次审查确认的当前结论

- 当前 clothes fullframe baseline 为 `clothes_merged_v2_balanced_from_first_holdout_v1`；
- 当前 baseline 入口为 `backend-train-model/All-train-model/00_CURRENT_BASELINE/README.md`；
- 当前统一对照集为 `unified_holdout_v1`，规模为 `75` 张图、`150` 个 GT 框；
- 当前 `person` prepared 数据与运行文档已存在，但 `backend-train-model/weights/person_detect_yolov8.pt` 仍不存在；
- 因此下一步应进入 `person` 模型训练，而不是回到旧的 `first-train` 基线争论。

---

## 审查记录 #002 — 2026-04-11

**审查范围：** `backend-train-model/` 统一 holdout 数据集构建结果复核，确认后续训练与评估入口是否已打通。

### 关键信息

当时已完成三套统一对照数据集构建：

- `backend-train-model/All-train-model/datasets/merged_clothes_v2_balanced/`
- `backend-train-model/All-train-model/datasets/unified_holdout_v1/`
- `backend-train-model/All-train-model/datasets/first_train_holdout_v1/`

对应统计：

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

### 当时结论

- 三套数据集的 `dataset.yaml`、`manifest.csv`、`build_report.json` 均已生成；
- 可以继续进入 cross-eval 与 strict holdout 阶段。

**当前状态：** 已解决，且后续 strict holdout / route verification 已完成。

---

## 审查记录 #001 — 2026-04-11

**审查范围：** `backend-train-model/` 整体，重点核查 `first-train` 与 `All-train-model` 是否已具备统一 holdout 训练条件。

### 当时问题

#### [P0] 三套对比数据集尚未构建，无法启动统一 holdout 训练

**现象：**

`backend-train-model/All-train-model/datasets/` 当时缺少：

- `merged_clothes_v2_balanced/`
- `unified_holdout_v1/`
- `first_train_holdout_v1/`

**解决方案：**

当时要求执行三条 `build_merged_clothes_dataset.py` 命令，生成三套统一对照数据集。

**当前状态：** 已解决；此记录仅保留为历史上下文。

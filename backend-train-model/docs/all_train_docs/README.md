# `all_train_docs` 使用说明

本目录主要保存 `All-train-model` 早期阶段的方案、待办和实验方法文档。

请注意：

- 这些文档大多形成于 unified holdout 主线落地之前；
- 其中不少结论仍然站在“`first-train` 是主 baseline”的历史阶段；
- 因此它们更适合用于**回溯问题来源、理解早期决策**，而不是直接作为当前主线结论。

当前真正应该优先阅读的是：

1. `backend-train-model/README.md`
2. `backend-train-model/docs/todo_list.md`
3. `backend-train-model/docs/total-run-method.md`
4. `backend-train-model/All-train-model/00_CURRENT_BASELINE/README.md`

如果需要回溯 merged 方案为什么会经历 `merged_v1 -> merged_v2 -> unified holdout -> route verification` 这条路线，再回来看本目录。

---

## 文件索引

| 文件 | 当前定位 | 当前替代入口 |
| --- | --- | --- |
| `merged_dataset_plan.md` | 历史数据集合并方案 | `backend-train-model/README.md` |
| `merged_v2_improvement_plan.md` | 历史问题拆解与提升假设 | `backend-train-model/All-train-model/00_CURRENT_BASELINE/README.md` |
| `run_method.md` | 历史 merged 运行方法 | `backend-train-model/docs/total-run-method.md` |
| `status_and_next_steps.md` | 历史状态快照 | `backend-train-model/docs/后端训练完成进度.md` |
| `todo_list.md` | 历史 merged 专项 TODO | `backend-train-model/docs/todo_list.md` |
| `unified_holdout_compare_method.md` | unified holdout 初版说明 | `backend-train-model/docs/total-run-method.md` |

建议理解方式：

- 想看“现在该怎么做” → 看项目根 README、`docs/todo_list.md`、`docs/total-run-method.md`
- 想看“当时为什么这么改” → 回到本目录查历史文档

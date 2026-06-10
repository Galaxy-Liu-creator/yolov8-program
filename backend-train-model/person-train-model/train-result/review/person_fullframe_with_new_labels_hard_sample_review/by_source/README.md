# 按 8 个来源整理的人工复核素材

## 1. 本目录作用

这个目录专门存放已经筛出来、需要人工复核的图片素材，按 `prepare_report.json` 中的 8 个来源进行整理。

每个来源目录下再按具体 `sequence_name` 拆分，方便本地查看和后续继续扩展。

## 2. 目录约定

每个 `source_*` 目录内，通常包含：

- `README.md`：说明这个来源对应什么、当前放了哪些待复核样本
- `sequence_*/images/`：原图 jpg
- `sequence_*/labels/`：对应 YOLO txt
- `sequence_*/overlays/`：按 run 生成的 overlay 图

## 3. 发送建议

如果只需要发给 1 个组员，优先发送 `send_packages/all_sources__review_bundle.zip`。
不要再按单条序列分别发 zip 包。

## 4. 当前说明

如果某个来源目录下当前没有图片，表示这轮优先人工复核名单里暂时没有从该来源挑出来的样本，不代表该来源永远不需要复核。

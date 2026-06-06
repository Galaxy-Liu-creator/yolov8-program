# 样本数据说明

- `images/`：从 `frame_label/clothes_labels` 抽取的简单工服样本图片。
- `labels/`：与图片一一对应的 YOLO 检测标注。
- 类别：`0 -> clothes`。
- 标注格式：`class_id x_center y_center width height`，坐标归一化到 `[0, 1]`。
- 这些样本仅用于文档撰写和格式理解，不代表完整训练集。

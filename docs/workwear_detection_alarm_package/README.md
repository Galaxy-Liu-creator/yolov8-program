# 工服检测报警资料包

## 目录结构

- `01_docs/`：工服检测报警方式概述、数据集说明、训练主线说明和当前 baseline 说明。
- `02_training_code/`：后端训练核心代码和配置文件，保留原仓库中的相对目录结构。
- `03_sample_data/clothes_samples/`：少量工服样本图片和对应 YOLO 标注。
- `04_alarm_demo/`：离线工服报警演示脚本和本项目当前 person / workwear 权重。

## 使用说明

这份资料包主要用于文档撰写、代码理解和简单离线报警测试。包内已包含报警演示脚本需要的 `person_detect_yolov8.pt` 和 `workwear_detect_yolov8.pt`，但不包含完整训练数据和大体积训练 runs 产物。如需真正复现实验，需要回到完整仓库和完整 `frame_label` 数据目录中运行。

## 样本标注格式

工服样本采用 YOLO 检测格式：`class_id x_center y_center width height`，当前工服类别为 `0 -> clothes`。

## 报警脚本快速测试

进入 `04_alarm_demo/` 后可运行：

```powershell
python workwear_alarm_demo.py ..\03_sample_data\clothes_samples\images --output alarm_output --device cpu
```

该脚本采用 `person -> ROI -> workwear -> track_id -> temporal` 链路。样本数量较少或没有连续同一人员时，可能不会触发报警，这是正常现象。

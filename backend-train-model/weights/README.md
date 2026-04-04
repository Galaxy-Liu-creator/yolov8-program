# 本地权重目录说明

这个目录用于放置 **不建议直接提交到仓库的大文件权重**。

当前默认约定如下：

- 默认微调权重：`backend-train-model/weights/yolov8n.pt`

推荐做法：

1. 先把官方或你自己的 `yolov8n.pt` 放到这个目录。
2. 再执行默认训练命令：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train
```

如果你暂时没有本地 `yolov8n.pt`，但明确允许 Ultralytics 自动下载，也可以显式加：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --allow-remote-model-download
```

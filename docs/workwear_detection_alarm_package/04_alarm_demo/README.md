# 工服未穿戴报警脚本说明

本目录用于离线演示本项目当前工服报警链路。脚本严格贴合项目现有检测规范：

```text
person 整帧检测
-> ROI 区域过滤
-> 人员裁剪图 workwear/clothes 检测
-> SimpleIoUTracker 分配 track_id
-> 按 track_id 做时间窗口违规比例判断
-> 保存触发 track 的证据图和 JSON 报告
```

## 目录结构

```text
04_alarm_demo/
+-- workwear_alarm_demo.py
+-- weights/
|   +-- person_detect_yolov8.pt
|   +-- person_detect_yolov8.metadata.json
|   +-- workwear_detect_yolov8.pt
+-- README.md
```

## 权重来源

- `weights/person_detect_yolov8.pt`
  - 来源：`backend-train-model/person-train-model/train-result/export/person_detect_yolov8_with_new_labels_and_hard_examples_v1.pt`
  - 说明：该权重对应“双上游 personcrop”方案中的上游 B，即 `person_fullframe_with_new_labels_and_hard_examples_v1_from_baseline` 的 `person` 命名 alias。选择它是因为报警链路中漏人会直接导致后续没有 person crop，方案文档也说明该权重在 hard holdout 上更强、Recall 更高，更适合离线报警演示。
- `weights/workwear_detect_yolov8.pt`
  - 来源：`backend-train-model/new_clothes_train/train-result/artifacts/runs/clothes_merged_with_new_labels_v1_baseline/weights/best.pt`
  - 说明：按当前要求使用扩样后的 clothes baseline，并生成 `{0: "clothes"}` 的 alias，保证报警脚本按 `clothes` 标签过滤时口径正确。

## 默认阈值

```text
PERSON_CONF = 0.55
WORKWEAR_CONF = 0.45
ROI_MIN_OVERLAP_RATIO = 0.5
TEMPORAL_WINDOW_SIZE = 5
TEMPORAL_TRIGGER_RATIO = 0.6
MIN_TRACK_APPEAR_FRAMES = 2
TRACKER_MAX_AGE = 2
TRACKER_IOU_THRESHOLD = 0.3
```

## 运行方式

在 `04_alarm_demo/` 目录下运行：

```powershell
python workwear_alarm_demo.py ..\03_sample_data\clothes_samples\images --output alarm_output --device cpu
```

如果当前环境对相对输出目录有限制，也可以把 `--output` 改成绝对路径，例如：

```powershell
python workwear_alarm_demo.py ..\03_sample_data\clothes_samples\images --output D:\temp\workwear_alarm_output --device cpu
```

如果测试视频或图片时需要指定 ROI：

```powershell
python workwear_alarm_demo.py path\to\video.mp4 --roi 100,80,900,700 --output alarm_output --device cpu --frame-step 5
```

## 输出结果

```text
alarm_output/
+-- alarm_report.json
+-- evidence/
    +-- alarm_frame_000xxx.jpg
```

- `alarm_report.json`：逐帧检测结果、track_id、疑似违规统计和触发事件。
- `evidence/`：只保存触发 track 的证据图。

## 注意事项

- 该脚本是离线演示入口，不依赖 Flask、数据库和摄像头线程。
- 真正线上系统仍以 `inspection-flask` 中的线程、规则和证据保存逻辑为准。
- 资料包中的样本主要用于理解格式；若样本不足 5 帧或没有连续同一人员，可能不会触发时序报警，这是正常情况。

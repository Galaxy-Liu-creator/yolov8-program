# Baseline FP/FN Summary

- 生成时间：`2026-04-13T21:49:33`
- baseline：`clothes_merged_v2_balanced_from_first_holdout_v1`
- 权重：`D:\University-Competition\Innovation_Entrepreneurship\MyProgram\yolov8-program\backend-train-model\All-train-model\artifacts\runs\clothes_merged_v2_balanced_from_first_holdout_v1\weights\best.pt`
- 数据集：`D:\University-Competition\Innovation_Entrepreneurship\MyProgram\yolov8-program\backend-train-model\All-train-model\datasets\unified_holdout_v1\dataset.yaml`
- split：`test`
- 预测保留阈值：`0.45`
- GT 匹配 IoU：`0.5`

## 总体统计

- 图片数：`75`
- GT 框数：`150`
- 预测框数：`147`
- TP：`144`
- FP：`3`
- FN：`6`
- Precision：`0.979592`
- Recall：`0.960000`
- 有误报图片数：`3`
- 有漏报图片数：`5`

## 按序列统计

| sequence | images | gt_boxes | tp | fp | fn | fp_images | fn_images |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| D02_20260123070624 | 13 | 12 | 10 | 2 | 2 | 2 | 2 |
| D05_20260123074841 | 4 | 18 | 16 | 0 | 2 | 0 | 1 |
| D15_20260119061405 | 17 | 26 | 25 | 0 | 1 | 0 | 1 |
| D15_20260123074848 | 6 | 22 | 22 | 1 | 0 | 1 | 0 |
| D02_20260123074836 | 3 | 6 | 5 | 0 | 1 | 0 | 1 |
| D15_20260119203927 | 28 | 56 | 56 | 0 | 0 | 0 | 0 |
| D04_20260123074846 | 4 | 10 | 10 | 0 | 0 | 0 | 0 |

## 误报图片

- `images/test/g31__D15_20260123074848_frame_0009.jpg` | sequence `D15_20260123074848` | fp `1` | pred `4` | gt `3`
- `images/test/g33__D02_20260123070624_frame_0004.jpg` | sequence `D02_20260123070624` | fp `1` | pred `2` | gt `2`
- `images/test/g33__D02_20260123070624_frame_0032.jpg` | sequence `D02_20260123070624` | fp `1` | pred `1` | gt `1`

## 漏报图片

- `images/test/g31__D05_20260123074841_frame_0010.jpg` | sequence `D05_20260123074841` | fn `2` | pred `3` | gt `5`
- `images/test/g32__D15_20260119061405_frame_0289.jpg` | sequence `D15_20260119061405` | fn `1` | pred `1` | gt `2`
- `images/test/g33__D02_20260123070624_frame_0004.jpg` | sequence `D02_20260123070624` | fn `1` | pred `2` | gt `2`
- `images/test/g33__D02_20260123070624_frame_0032.jpg` | sequence `D02_20260123070624` | fn `1` | pred `1` | gt `1`
- `images/test/g33__D02_20260123074836_frame_0021.jpg` | sequence `D02_20260123074836` | fn `1` | pred `1` | gt `2`

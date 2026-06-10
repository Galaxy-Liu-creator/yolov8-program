# 行人单帧误检 / 漏检复盘摘要

- 生成时间: `2026-05-25T19:07:05`
- 运行名: `person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_from_fullframe`
- 权重路径: `D:\University-Competition\Innovation_Entrepreneurship\MyProgram\yolov8-program\backend-train-model\person-train-model\train-result\artifacts\runs\person_roi_aware_with_new_labels_v1_mask_then_crop_margin64_from_fullframe\weights\best.pt`
- 数据集 YAML: `D:\University-Competition\Innovation_Entrepreneurship\MyProgram\yolov8-program\backend-train-model\person-train-model\train-result\prepared\person_roi_aware_with_new_labels_v1_mask_then_crop_margin64\sequence_contiguous\dataset.yaml`
- 数据划分: `测试集`
- 置信度阈值: `0.25`
- NMS IoU: `0.7`
- 匹配 IoU: `0.5`

## 总体统计

- 图片数: `450`
- GT 框数: `844`
- 预测框数: `813`
- 真阳性（TP）: `768`
- 误检（FP）: `45`
- 漏检（FN）: `76`
- Precision（精确率）: `0.944649`
- Recall（召回率）: `0.909953`
- 含 FP 图片数: `43`
- 含 FN 图片数: `69`

## 按序列统计

| 序列 | 图片数 | GT 框数 | 真阳性 | 误检 | 漏检 | 含误检图片数 | 含漏检图片数 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| group_0006 | 103 | 202 | 193 | 21 | 9 | 21 | 9 |
| group_0005 | 87 | 289 | 277 | 9 | 12 | 7 | 11 |
| group_0004 | 58 | 87 | 73 | 5 | 14 | 5 | 12 |
| D15_20260119061405 | 17 | 34 | 22 | 2 | 12 | 2 | 11 |
| D15_20260119203927 | 28 | 18 | 7 | 0 | 11 | 0 | 11 |
| D02_20260123070624 | 12 | 19 | 12 | 1 | 7 | 1 | 7 |
| D02_20260123074836 | 4 | 13 | 7 | 1 | 6 | 1 | 3 |
| D05_20260123074841 | 5 | 18 | 15 | 1 | 3 | 1 | 3 |
| group_0002 | 67 | 74 | 74 | 3 | 0 | 3 | 0 |
| group_0001 | 41 | 59 | 57 | 1 | 2 | 1 | 2 |
| group_0003 | 19 | 18 | 18 | 1 | 0 | 1 | 0 |
| D15_20260123074848 | 5 | 7 | 7 | 0 | 0 | 0 | 0 |
| D04_20260123074846 | 4 | 6 | 6 | 0 | 0 | 0 | 0 |

## 误检图片

- `images/test/01473.jpg` | 序列 `group_0005` | 误检数 `2` | 预测框 `6` | GT 框 `4`
- `images/test/01474.jpg` | 序列 `group_0005` | 误检数 `2` | 预测框 `6` | GT 框 `4`
- `images/test/00389.jpg` | 序列 `group_0002` | 误检数 `1` | 预测框 `2` | GT 框 `1`
- `images/test/00390.jpg` | 序列 `group_0002` | 误检数 `1` | 预测框 `2` | GT 框 `1`
- `images/test/00391.jpg` | 序列 `group_0002` | 误检数 `1` | 预测框 `2` | GT 框 `1`
- `images/test/00559.jpg` | 序列 `group_0003` | 误检数 `1` | 预测框 `1` | GT 框 `0`
- `images/test/00925.jpg` | 序列 `group_0004` | 误检数 `1` | 预测框 `2` | GT 框 `2`
- `images/test/00929.jpg` | 序列 `group_0004` | 误检数 `1` | 预测框 `3` | GT 框 `2`
- `images/test/00934.jpg` | 序列 `group_0004` | 误检数 `1` | 预测框 `2` | GT 框 `2`
- `images/test/00954.jpg` | 序列 `group_0004` | 误检数 `1` | 预测框 `2` | GT 框 `2`
- `images/test/00955.jpg` | 序列 `group_0004` | 误检数 `1` | 预测框 `3` | GT 框 `3`
- `images/test/01468.jpg` | 序列 `group_0005` | 误检数 `1` | 预测框 `3` | GT 框 `3`
- `images/test/01470.jpg` | 序列 `group_0005` | 误检数 `1` | 预测框 `3` | GT 框 `3`
- `images/test/01471.jpg` | 序列 `group_0005` | 误检数 `1` | 预测框 `3` | GT 框 `3`
- `images/test/01521.jpg` | 序列 `group_0005` | 误检数 `1` | 预测框 `4` | GT 框 `4`
- `images/test/01526.jpg` | 序列 `group_0005` | 误检数 `1` | 预测框 `4` | GT 框 `4`
- `images/test/02136.jpg` | 序列 `group_0006` | 误检数 `1` | 预测框 `2` | GT 框 `1`
- `images/test/02159.jpg` | 序列 `group_0006` | 误检数 `1` | 预测框 `3` | GT 框 `2`
- `images/test/02169.jpg` | 序列 `group_0006` | 误检数 `1` | 预测框 `3` | GT 框 `2`
- `images/test/02170.jpg` | 序列 `group_0006` | 误检数 `1` | 预测框 `3` | GT 框 `2`
- `images/test/02172.jpg` | 序列 `group_0006` | 误检数 `1` | 预测框 `3` | GT 框 `3`
- `images/test/02173.jpg` | 序列 `group_0006` | 误检数 `1` | 预测框 `3` | GT 框 `3`
- `images/test/02174.jpg` | 序列 `group_0006` | 误检数 `1` | 预测框 `3` | GT 框 `3`
- `images/test/02190.jpg` | 序列 `group_0006` | 误检数 `1` | 预测框 `3` | GT 框 `2`
- `images/test/02192.jpg` | 序列 `group_0006` | 误检数 `1` | 预测框 `2` | GT 框 `1`
- `images/test/02193.jpg` | 序列 `group_0006` | 误检数 `1` | 预测框 `2` | GT 框 `1`
- `images/test/02198.jpg` | 序列 `group_0006` | 误检数 `1` | 预测框 `2` | GT 框 `1`
- `images/test/02199.jpg` | 序列 `group_0006` | 误检数 `1` | 预测框 `2` | GT 框 `1`
- `images/test/02204.jpg` | 序列 `group_0006` | 误检数 `1` | 预测框 `3` | GT 框 `2`
- `images/test/02205.jpg` | 序列 `group_0006` | 误检数 `1` | 预测框 `3` | GT 框 `2`
- `images/test/02206.jpg` | 序列 `group_0006` | 误检数 `1` | 预测框 `4` | GT 框 `3`
- `images/test/02207.jpg` | 序列 `group_0006` | 误检数 `1` | 预测框 `3` | GT 框 `3`
- `images/test/02210.jpg` | 序列 `group_0006` | 误检数 `1` | 预测框 `5` | GT 框 `4`
- `images/test/02212.jpg` | 序列 `group_0006` | 误检数 `1` | 预测框 `4` | GT 框 `4`
- `images/test/02213.jpg` | 序列 `group_0006` | 误检数 `1` | 预测框 `4` | GT 框 `3`
- `images/test/02230.jpg` | 序列 `group_0006` | 误检数 `1` | 预测框 `3` | GT 框 `2`
- `images/test/02231.jpg` | 序列 `group_0006` | 误检数 `1` | 预测框 `3` | GT 框 `2`
- `images/test/02480.jpg` | 序列 `group_0001` | 误检数 `1` | 预测框 `3` | GT 框 `2`
- `images/test/D02_20260123070624_frame_0076.jpg` | 序列 `D02_20260123070624` | 误检数 `1` | 预测框 `2` | GT 框 `2`
- `images/test/D02_20260123074836_frame_0023.jpg` | 序列 `D02_20260123074836` | 误检数 `1` | 预测框 `2` | GT 框 `4`
- `images/test/D05_20260123074841_frame_0028.jpg` | 序列 `D05_20260123074841` | 误检数 `1` | 预测框 `4` | GT 框 `4`
- `images/test/D15_20260119061405_frame_0340.jpg` | 序列 `D15_20260119061405` | 误检数 `1` | 预测框 `3` | GT 框 `3`
- `images/test/D15_20260119061405_frame_0352.jpg` | 序列 `D15_20260119061405` | 误检数 `1` | 预测框 `2` | GT 框 `1`

## 漏检图片

- `images/test/D02_20260123074836_frame_0023.jpg` | 序列 `D02_20260123074836` | 漏检数 `3` | 预测框 `2` | GT 框 `4`
- `images/test/00946.jpg` | 序列 `group_0004` | 漏检数 `2` | 预测框 `1` | GT 框 `3`
- `images/test/00947.jpg` | 序列 `group_0004` | 漏检数 `2` | 预测框 `1` | GT 框 `3`
- `images/test/01542.jpg` | 序列 `group_0005` | 漏检数 `2` | 预测框 `2` | GT 框 `4`
- `images/test/D02_20260123074836_frame_0024.jpg` | 序列 `D02_20260123074836` | 漏检数 `2` | 预测框 `2` | GT 框 `4`
- `images/test/D15_20260119061405_frame_0348.jpg` | 序列 `D15_20260119061405` | 漏检数 `2` | 预测框 `0` | GT 框 `2`
- `images/test/00919.jpg` | 序列 `group_0004` | 漏检数 `1` | 预测框 `1` | GT 框 `2`
- `images/test/00925.jpg` | 序列 `group_0004` | 漏检数 `1` | 预测框 `2` | GT 框 `2`
- `images/test/00926.jpg` | 序列 `group_0004` | 漏检数 `1` | 预测框 `1` | GT 框 `2`
- `images/test/00930.jpg` | 序列 `group_0004` | 漏检数 `1` | 预测框 `1` | GT 框 `2`
- `images/test/00933.jpg` | 序列 `group_0004` | 漏检数 `1` | 预测框 `1` | GT 框 `2`
- `images/test/00934.jpg` | 序列 `group_0004` | 漏检数 `1` | 预测框 `2` | GT 框 `2`
- `images/test/00952.jpg` | 序列 `group_0004` | 漏检数 `1` | 预测框 `1` | GT 框 `2`
- `images/test/00953.jpg` | 序列 `group_0004` | 漏检数 `1` | 预测框 `1` | GT 框 `2`
- `images/test/00954.jpg` | 序列 `group_0004` | 漏检数 `1` | 预测框 `2` | GT 框 `2`
- `images/test/00955.jpg` | 序列 `group_0004` | 漏检数 `1` | 预测框 `3` | GT 框 `3`
- `images/test/01468.jpg` | 序列 `group_0005` | 漏检数 `1` | 预测框 `3` | GT 框 `3`
- `images/test/01470.jpg` | 序列 `group_0005` | 漏检数 `1` | 预测框 `3` | GT 框 `3`
- `images/test/01471.jpg` | 序列 `group_0005` | 漏检数 `1` | 预测框 `3` | GT 框 `3`
- `images/test/01483.jpg` | 序列 `group_0005` | 漏检数 `1` | 预测框 `2` | GT 框 `3`
- `images/test/01521.jpg` | 序列 `group_0005` | 漏检数 `1` | 预测框 `4` | GT 框 `4`
- `images/test/01526.jpg` | 序列 `group_0005` | 漏检数 `1` | 预测框 `4` | GT 框 `4`
- `images/test/01533.jpg` | 序列 `group_0005` | 漏检数 `1` | 预测框 `3` | GT 框 `4`
- `images/test/01543.jpg` | 序列 `group_0005` | 漏检数 `1` | 预测框 `3` | GT 框 `4`
- `images/test/01544.jpg` | 序列 `group_0005` | 漏检数 `1` | 预测框 `2` | GT 框 `3`
- `images/test/01545.jpg` | 序列 `group_0005` | 漏检数 `1` | 预测框 `1` | GT 框 `2`
- `images/test/02172.jpg` | 序列 `group_0006` | 漏检数 `1` | 预测框 `3` | GT 框 `3`
- `images/test/02173.jpg` | 序列 `group_0006` | 漏检数 `1` | 预测框 `3` | GT 框 `3`
- `images/test/02174.jpg` | 序列 `group_0006` | 漏检数 `1` | 预测框 `3` | GT 框 `3`
- `images/test/02175.jpg` | 序列 `group_0006` | 漏检数 `1` | 预测框 `2` | GT 框 `3`
- `images/test/02176.jpg` | 序列 `group_0006` | 漏检数 `1` | 预测框 `2` | GT 框 `3`
- `images/test/02207.jpg` | 序列 `group_0006` | 漏检数 `1` | 预测框 `3` | GT 框 `3`
- `images/test/02208.jpg` | 序列 `group_0006` | 漏检数 `1` | 预测框 `2` | GT 框 `3`
- `images/test/02211.jpg` | 序列 `group_0006` | 漏检数 `1` | 预测框 `2` | GT 框 `3`
- `images/test/02212.jpg` | 序列 `group_0006` | 漏检数 `1` | 预测框 `4` | GT 框 `4`
- `images/test/02499.jpg` | 序列 `group_0001` | 漏检数 `1` | 预测框 `1` | GT 框 `2`
- `images/test/02500.jpg` | 序列 `group_0001` | 漏检数 `1` | 预测框 `1` | GT 框 `2`
- `images/test/D02_20260123070624_frame_0071.jpg` | 序列 `D02_20260123070624` | 漏检数 `1` | 预测框 `1` | GT 框 `2`
- `images/test/D02_20260123070624_frame_0072.jpg` | 序列 `D02_20260123070624` | 漏检数 `1` | 预测框 `1` | GT 框 `2`
- `images/test/D02_20260123070624_frame_0073.jpg` | 序列 `D02_20260123070624` | 漏检数 `1` | 预测框 `1` | GT 框 `2`
- `images/test/D02_20260123070624_frame_0074.jpg` | 序列 `D02_20260123070624` | 漏检数 `1` | 预测框 `1` | GT 框 `2`
- `images/test/D02_20260123070624_frame_0075.jpg` | 序列 `D02_20260123070624` | 漏检数 `1` | 预测框 `1` | GT 框 `2`
- `images/test/D02_20260123070624_frame_0076.jpg` | 序列 `D02_20260123070624` | 漏检数 `1` | 预测框 `2` | GT 框 `2`
- `images/test/D02_20260123070624_frame_0077.jpg` | 序列 `D02_20260123070624` | 漏检数 `1` | 预测框 `1` | GT 框 `2`
- `images/test/D02_20260123074836_frame_0021.jpg` | 序列 `D02_20260123074836` | 漏检数 `1` | 预测框 `1` | GT 框 `2`
- `images/test/D05_20260123074841_frame_0028.jpg` | 序列 `D05_20260123074841` | 漏检数 `1` | 预测框 `4` | GT 框 `4`
- `images/test/D05_20260123074841_frame_0029.jpg` | 序列 `D05_20260123074841` | 漏检数 `1` | 预测框 `3` | GT 框 `4`
- `images/test/D05_20260123074841_frame_0030.jpg` | 序列 `D05_20260123074841` | 漏检数 `1` | 预测框 `3` | GT 框 `4`
- `images/test/D15_20260119061405_frame_0340.jpg` | 序列 `D15_20260119061405` | 漏检数 `1` | 预测框 `3` | GT 框 `3`
- `images/test/D15_20260119061405_frame_0341.jpg` | 序列 `D15_20260119061405` | 漏检数 `1` | 预测框 `2` | GT 框 `3`
- `images/test/D15_20260119061405_frame_0342.jpg` | 序列 `D15_20260119061405` | 漏检数 `1` | 预测框 `2` | GT 框 `3`
- `images/test/D15_20260119061405_frame_0343.jpg` | 序列 `D15_20260119061405` | 漏检数 `1` | 预测框 `2` | GT 框 `3`
- `images/test/D15_20260119061405_frame_0344.jpg` | 序列 `D15_20260119061405` | 漏检数 `1` | 预测框 `2` | GT 框 `3`
- `images/test/D15_20260119061405_frame_0345.jpg` | 序列 `D15_20260119061405` | 漏检数 `1` | 预测框 `2` | GT 框 `3`
- `images/test/D15_20260119061405_frame_0346.jpg` | 序列 `D15_20260119061405` | 漏检数 `1` | 预测框 `1` | GT 框 `2`
- `images/test/D15_20260119061405_frame_0347.jpg` | 序列 `D15_20260119061405` | 漏检数 `1` | 预测框 `1` | GT 框 `2`
- `images/test/D15_20260119061405_frame_0349.jpg` | 序列 `D15_20260119061405` | 漏检数 `1` | 预测框 `1` | GT 框 `2`
- `images/test/D15_20260119061405_frame_0350.jpg` | 序列 `D15_20260119061405` | 漏检数 `1` | 预测框 `1` | GT 框 `2`
- `images/test/D15_20260119203927_frame_0162.jpg` | 序列 `D15_20260119203927` | 漏检数 `1` | 预测框 `0` | GT 框 `1`
- `images/test/D15_20260119203927_frame_0164.jpg` | 序列 `D15_20260119203927` | 漏检数 `1` | 预测框 `0` | GT 框 `1`
- `images/test/D15_20260119203927_frame_0165.jpg` | 序列 `D15_20260119203927` | 漏检数 `1` | 预测框 `0` | GT 框 `1`
- `images/test/D15_20260119203927_frame_0166.jpg` | 序列 `D15_20260119203927` | 漏检数 `1` | 预测框 `0` | GT 框 `1`
- `images/test/D15_20260119203927_frame_0167.jpg` | 序列 `D15_20260119203927` | 漏检数 `1` | 预测框 `0` | GT 框 `1`
- `images/test/D15_20260119203927_frame_0168.jpg` | 序列 `D15_20260119203927` | 漏检数 `1` | 预测框 `0` | GT 框 `1`
- `images/test/D15_20260119203927_frame_0169.jpg` | 序列 `D15_20260119203927` | 漏检数 `1` | 预测框 `0` | GT 框 `1`
- `images/test/D15_20260119203927_frame_0170.jpg` | 序列 `D15_20260119203927` | 漏检数 `1` | 预测框 `0` | GT 框 `1`
- `images/test/D15_20260119203927_frame_0171.jpg` | 序列 `D15_20260119203927` | 漏检数 `1` | 预测框 `0` | GT 框 `1`
- `images/test/D15_20260119203927_frame_0173.jpg` | 序列 `D15_20260119203927` | 漏检数 `1` | 预测框 `0` | GT 框 `1`
- `images/test/D15_20260119203927_frame_0176.jpg` | 序列 `D15_20260119203927` | 漏检数 `1` | 预测框 `1` | GT 框 `2`

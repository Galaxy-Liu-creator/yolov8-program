# 阶段 PPT 汇报素材

## 本阶段进展
- 本阶段重点完成 person 检测与 ROI 标注配套整理：共 7 段序列、502 张图片、1651 个 person 框，并同步生成 502 份逐图 ROI JSON。
- person fullframe baseline 训练 180 轮，best epoch 为 151，P=0.9677、R=0.8216、mAP50=0.9133、mAP50-95=0.5684。
- ROI-aware person baseline 训练 123 轮，best epoch 为 83，P=0.9854、R=0.7809、mAP50=0.8721、mAP50-95=0.5509。

推荐图片：
![person fullframe 训练曲线](../person-train-model/train-result/artifacts/runs/person_fullframe_baseline/results.png)
![person fullframe 预测示例](../person-train-model/train-result/artifacts/runs/person_fullframe_baseline/val_batch0_pred.jpg)
![ROI-aware person 预测示例](../person-train-model/train-result/artifacts/runs/person_roi_aware_baseline/val_batch0_pred.jpg)

## 问题与缺陷
- 两个 person 方案的 mAP50-95 都只在 0.55 左右，说明对遮挡、小目标和复杂边界场景的稳定性还不够。
- ROI-aware person 虽然 precision 更高，但 recall 只有 0.7809，低于 fullframe 的 0.8216，说明 ROI 裁切后存在漏检。
- 4 张 ROI 边界复查帧均为 boxes=1、kept=0、dropped=1，说明当前 center_inside 规则对“人框压线”样本过硬。

推荐图片：
![ROI 边界问题 0181](../person-train-model/train-result/review/roi_filter_overlays/D15_20260119203927_frame_0181_roi_filter_overlay.jpg)
![ROI 边界问题 0184](../person-train-model/train-result/review/roi_filter_overlays/D15_20260119203927_frame_0184_roi_filter_overlay.jpg)
![ROI-aware person 曲线](../person-train-model/train-result/artifacts/runs/person_roi_aware_baseline/results.png)

## 改进方案
- 短期先以 fullframe person 作为主召回入口，再结合 ROI、停留时间和规则层筛选候选作业人员，先保证少漏检。
- 下一步优化 ROI-aware person：把过滤规则从 center_inside 调整为 bottom-center 或 box_ioA>=0.25，并补充 ROI 边界样本。
- 后续统一对比 fullframe 与 ROI-aware 的 P、R、mAP50、mAP50-95，持续观察规则修改前后的真实提升。

推荐图片：
![person fullframe PR 曲线](../person-train-model/train-result/artifacts/runs/person_fullframe_baseline/BoxPR_curve.png)
![ROI-aware person PR 曲线](../person-train-model/train-result/artifacts/runs/person_roi_aware_baseline/BoxPR_curve.png)

# Person 召回瓶颈分析报告

## 配置

- Source dataset: backend-train-model/new_clothes_train/train-result/datasets/clothes_merged_with_new_labels_v1/dataset.yaml
- Split: test
- Person conf: 0.2
- Assignment min IoA: 0.35

## Person 模型 A

- Weights: backend-train-model/person-train-model/train-result/export/person_detect_yolov8_with_new_labels.pt
- Total clothes GT: 800
- Unassigned clothes (因 person 不足): 10
- **Bottleneck ratio: 1.25%**

## Person 模型 B

- Weights: backend-train-model/person-train-model/train-result/export/person_detect_yolov8_with_new_labels_and_hard_examples_v1.pt
- Total clothes GT: 800
- Unassigned clothes (因 person 不足): 10
- **Bottleneck ratio: 1.25%**

## 结论

**Person 不是主要瓶颈** (<5%)，应优化 clothes 模型或裁剪策略。

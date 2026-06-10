#!/usr/bin/env python3
"""
Person 召回瓶颈量化分析脚本

目标：量化有多少 clothes GT 因为 person 漏检而无法进入下游
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple
import yaml
import numpy as np
from ultralytics import YOLO
import cv2

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        return iterable


def parse_args():
    parser = argparse.ArgumentParser(description='分析 person 召回对 clothes 检测的瓶颈影响')
    parser.add_argument('--source-dataset', type=str, required=True,
                        help='Source clothes dataset.yaml 路径')
    parser.add_argument('--person-weights-a', type=str, required=True,
                        help='Person 模型 A 权重路径')
    parser.add_argument('--person-weights-b', type=str, required=True,
                        help='Person 模型 B 权重路径')
    parser.add_argument('--split', type=str, default='test',
                        help='评估的 split (train/val/test)')
    parser.add_argument('--person-conf', type=float, default=0.20,
                        help='Person 检测置信度阈值')
    parser.add_argument('--assignment-min-ioa', type=float, default=0.35,
                        help='Clothes 框分配到 person 框的最小 IoA 阈值')
    parser.add_argument('--match-iou', type=float, default=0.5,
                        help='GT person 匹配的 IoU 阈值')
    parser.add_argument('--output', type=str, required=True,
                        help='输出目录')
    return parser.parse_args()


def load_dataset_yaml(yaml_path: Path) -> Dict:
    """加载 dataset.yaml"""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def resolve_split_dir(dataset_yaml_path: Path, payload: Dict, split: str) -> Path:
    """解析 split 目录"""
    split_rel = payload.get(split)
    if not split_rel:
        raise ValueError(f"Split '{split}' not found in dataset.yaml")
    
    # 尝试用 path 字段解析
    if 'path' in payload and payload['path']:
        base_dir = Path(payload['path'])
        split_dir = base_dir / split_rel
        if split_dir.exists():
            return split_dir
    
    # Fallback: 相对于 dataset.yaml 所在目录
    split_dir = dataset_yaml_path.parent / split_rel
    if not split_dir.exists():
        raise FileNotFoundError(f"Split dir not found: {split_dir}")
    return split_dir


def yolo_to_xyxy(box: List[float], img_w: int, img_h: int) -> List[float]:
    """YOLO 格式转 xyxy"""
    cx, cy, w, h = box
    x1 = (cx - w / 2) * img_w
    y1 = (cy - h / 2) * img_h
    x2 = (cx + w / 2) * img_w
    y2 = (cy + h / 2) * img_h
    return [x1, y1, x2, y2]


def box_iou(box1: List[float], box2: List[float]) -> float:
    """计算两个框的 IoU"""
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2
    
    inter_xmin = max(x1_min, x2_min)
    inter_ymin = max(y1_min, y2_min)
    inter_xmax = min(x1_max, x2_max)
    inter_ymax = min(y1_max, y2_max)
    
    inter_w = max(0, inter_xmax - inter_xmin)
    inter_h = max(0, inter_ymax - inter_ymin)
    inter_area = inter_w * inter_h
    
    area1 = (x1_max - x1_min) * (y1_max - y1_min)
    area2 = (x2_max - x2_min) * (y2_max - y2_min)
    union = area1 + area2 - inter_area
    
    return inter_area / union if union > 0 else 0.0


def box_ioa(box1: List[float], box2: List[float]) -> float:
    """计算 box1 相对于 box2 的 IoA (intersection over area of box1)"""
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2
    
    inter_xmin = max(x1_min, x2_min)
    inter_ymin = max(y1_min, y2_min)
    inter_xmax = min(x1_max, x2_max)
    inter_ymax = min(y1_max, y2_max)
    
    inter_w = max(0, inter_xmax - inter_xmin)
    inter_h = max(0, inter_ymax - inter_ymin)
    inter_area = inter_w * inter_h
    
    area1 = (x1_max - x1_min) * (y1_max - y1_min)
    return inter_area / area1 if area1 > 0 else 0.0


def analyze_bottleneck(args):
    """执行瓶颈分析"""
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载 dataset
    dataset_yaml_path = Path(args.source_dataset)
    dataset_payload = load_dataset_yaml(dataset_yaml_path)
    
    # 解析图片和标注目录
    image_dir = resolve_split_dir(dataset_yaml_path, dataset_payload, args.split)
    label_dir = image_dir.parent.parent / 'labels' / args.split
    
    # 加载 person 模型
    print(f"加载 person 模型 A: {args.person_weights_a}")
    person_model_a = YOLO(args.person_weights_a)
    print(f"加载 person 模型 B: {args.person_weights_b}")
    person_model_b = YOLO(args.person_weights_b)
    
    # 收集所有图片
    image_files = sorted(image_dir.glob('*.jpg'))
    print(f"找到 {len(image_files)} 张图片")
    
    # 统计结果
    results_a = []
    results_b = []
    
    for img_path in tqdm(image_files, desc='分析瓶颈'):
        img = cv2.imread(str(img_path))
        img_h, img_w = img.shape[:2]
        
        # 加载 GT
        label_path = label_dir / f"{img_path.stem}.txt"
        gt_person_boxes = []
        gt_clothes_boxes = []
        
        if label_path.exists():
            with open(label_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        cls_id = int(parts[0])
                        box_yolo = [float(x) for x in parts[1:5]]
                        box_xyxy = yolo_to_xyxy(box_yolo, img_w, img_h)
                        
                        # 假设 person GT 存在（需要根据实际情况调整）
                        # 这里简化处理：只分析 clothes GT
                        gt_clothes_boxes.append(box_xyxy)
        
        # 用 person 模型 A 检测
        det_a = person_model_a(img, conf=args.person_conf, verbose=False)[0]
        detected_person_a = []
        if det_a.boxes is not None and len(det_a.boxes) > 0:
            for box in det_a.boxes:
                detected_person_a.append(box.xyxy[0].cpu().numpy().tolist())
        
        # 用 person 模型 B 检测
        det_b = person_model_b(img, conf=args.person_conf, verbose=False)[0]
        detected_person_b = []
        if det_b.boxes is not None and len(det_b.boxes) > 0:
            for box in det_b.boxes:
                detected_person_b.append(box.xyxy[0].cpu().numpy().tolist())
        
        # 分配 clothes GT 到检测到的 person 框
        unassigned_clothes_a = 0
        for clothes_box in gt_clothes_boxes:
            best_ioa = 0.0
            for person_box in detected_person_a:
                ioa = box_ioa(clothes_box, person_box)
                best_ioa = max(best_ioa, ioa)
            
            if best_ioa < args.assignment_min_ioa:
                unassigned_clothes_a += 1
        
        unassigned_clothes_b = 0
        for clothes_box in gt_clothes_boxes:
            best_ioa = 0.0
            for person_box in detected_person_b:
                ioa = box_ioa(clothes_box, person_box)
                best_ioa = max(best_ioa, ioa)
            
            if best_ioa < args.assignment_min_ioa:
                unassigned_clothes_b += 1
        
        results_a.append({
            'image': img_path.name,
            'detected_person': len(detected_person_a),
            'gt_clothes': len(gt_clothes_boxes),
            'unassigned_clothes': unassigned_clothes_a
        })
        
        results_b.append({
            'image': img_path.name,
            'detected_person': len(detected_person_b),
            'gt_clothes': len(gt_clothes_boxes),
            'unassigned_clothes': unassigned_clothes_b
        })
    
    # 计算瓶颈比例
    total_clothes_a = sum(r['gt_clothes'] for r in results_a)
    total_unassigned_a = sum(r['unassigned_clothes'] for r in results_a)
    bottleneck_ratio_a = total_unassigned_a / total_clothes_a if total_clothes_a > 0 else 0.0
    
    total_clothes_b = sum(r['gt_clothes'] for r in results_b)
    total_unassigned_b = sum(r['unassigned_clothes'] for r in results_b)
    bottleneck_ratio_b = total_unassigned_b / total_clothes_b if total_clothes_b > 0 else 0.0
    
    # 生成报告
    report = {
        'config': {
            'source_dataset': str(args.source_dataset),
            'split': args.split,
            'person_conf': args.person_conf,
            'assignment_min_ioa': args.assignment_min_ioa
        },
        'person_model_a': {
            'weights': str(args.person_weights_a),
            'total_clothes_gt': total_clothes_a,
            'unassigned_clothes': total_unassigned_a,
            'bottleneck_ratio': bottleneck_ratio_a,
            'per_image': results_a
        },
        'person_model_b': {
            'weights': str(args.person_weights_b),
            'total_clothes_gt': total_clothes_b,
            'unassigned_clothes': total_unassigned_b,
            'bottleneck_ratio': bottleneck_ratio_b,
            'per_image': results_b
        }
    }
    
    # 保存报告
    report_path = output_dir / 'person_bottleneck_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 生成可读性总结
    summary_lines = [
        '# Person 召回瓶颈分析报告\n',
        f'## 配置\n',
        f'- Source dataset: {args.source_dataset}',
        f'- Split: {args.split}',
        f'- Person conf: {args.person_conf}',
        f'- Assignment min IoA: {args.assignment_min_ioa}\n',
        f'## Person 模型 A\n',
        f'- Weights: {args.person_weights_a}',
        f'- Total clothes GT: {total_clothes_a}',
        f'- Unassigned clothes (因 person 不足): {total_unassigned_a}',
        f'- **Bottleneck ratio: {bottleneck_ratio_a:.2%}**\n',
        f'## Person 模型 B\n',
        f'- Weights: {args.person_weights_b}',
        f'- Total clothes GT: {total_clothes_b}',
        f'- Unassigned clothes (因 person 不足): {total_unassigned_b}',
        f'- **Bottleneck ratio: {bottleneck_ratio_b:.2%}**\n',
        f'## 结论\n'
    ]
    
    if bottleneck_ratio_b > 0.15:
        summary_lines.append('**Person 是主要瓶颈** (>15%)，应优先优化 person 召回。\n')
    elif bottleneck_ratio_b > 0.05:
        summary_lines.append('Person 是次要瓶颈 (5-15%)，可考虑调整 person_conf 阈值。\n')
    else:
        summary_lines.append('**Person 不是主要瓶颈** (<5%)，应优化 clothes 模型或裁剪策略。\n')
    
    summary_path = output_dir / 'bottleneck_summary.md'
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(summary_lines))
    
    print(f"\n报告已保存到: {output_dir}")
    print(f"Person A bottleneck ratio: {bottleneck_ratio_a:.2%}")
    print(f"Person B bottleneck ratio: {bottleneck_ratio_b:.2%}")


if __name__ == '__main__':
    args = parse_args()
    analyze_bottleneck(args)

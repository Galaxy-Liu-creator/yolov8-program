#!/usr/bin/env python3
"""
实验1：原图级 Personcrop vs Fullframe 对比脚本

将 personcrop 检测结果映射回原图空间，与 fullframe baseline 在统一评估空间对比
"""

import argparse
import json
from pathlib import Path
import yaml
from ultralytics import YOLO
import cv2
from tqdm import tqdm


def parse_args():
    parser = argparse.ArgumentParser(description='原图级 Personcrop vs Fullframe 对比')
    parser.add_argument('--personcrop-data-a', type=str, required=True)
    parser.add_argument('--personcrop-weights-a', type=str, required=True)
    parser.add_argument('--personcrop-data-b', type=str, required=True)
    parser.add_argument('--personcrop-weights-b', type=str, required=True)
    parser.add_argument('--source-dataset', type=str, required=True)
    parser.add_argument('--split', type=str, default='test')
    parser.add_argument('--conf', type=float, default=0.45)
    parser.add_argument('--output', type=str, required=True)
    return parser.parse_args()


def load_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def resolve_split_dir(yaml_path, payload, split):
    split_rel = payload.get(split)
    if not split_rel:
        raise ValueError(f"Split '{split}' not found")
    
    if 'path' in payload and payload['path']:
        split_dir = Path(payload['path']) / split_rel
        if split_dir.exists():
            return split_dir
    
    split_dir = yaml_path.parent / split_rel
    if not split_dir.exists():
        raise FileNotFoundError(f"Split dir not found: {split_dir}")
    return split_dir


def yolo_to_xyxy(box, img_w, img_h):
    cx, cy, w, h = box
    x1 = (cx - w / 2) * img_w
    y1 = (cy - h / 2) * img_h
    x2 = (cx + w / 2) * img_w
    y2 = (cy + h / 2) * img_h
    return [x1, y1, x2, y2]


def main(args):
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载数据集
    source_yaml = Path(args.source_dataset)
    source_payload = load_yaml(source_yaml)
    image_dir = resolve_split_dir(source_yaml, source_payload, args.split)
    label_dir = image_dir.parent.parent / 'labels' / args.split
    
    # 加载模型
    print("加载 Personcrop 模型 A...")
    model_a = YOLO(args.personcrop_weights_a)
    print("加载 Personcrop 模型 B...")
    model_b = YOLO(args.personcrop_weights_b)
    
    # 加载 personcrop 数据集的映射信息
    # 简化实现：直接在原图上评估（假设personcrop已经是crop后的图）
    # 完整实现需要读取 personcrop prepare 时生成的映射信息
    
    image_files = sorted(image_dir.glob('*.jpg'))
    print(f"找到 {len(image_files)} 张图片")
    
    results_summary = {
        'config': {
            'source_dataset': str(args.source_dataset),
            'split': args.split,
            'conf': args.conf
        },
        'personcrop_a': {'model': str(args.personcrop_weights_a)},
        'personcrop_b': {'model': str(args.personcrop_weights_b)},
        'per_image': []
    }
    
    print("\n当前为简化实现版本：")
    print("完整的原图级评估需要读取 personcrop prepare 时的映射信息")
    print("建议：先执行实验2 person瓶颈分析，明确优化方向后再补充完整实现\n")
    
    # 保存配置
    report_path = output_dir / 'original_level_comparison_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results_summary, f, indent=2, ensure_ascii=False)
    
    # 生成总结
    summary_lines = [
        '# 原图级 Personcrop vs Fullframe 对比报告\n',
        '## 注意\n',
        '当前为简化实现版本。完整的原图级评估需要：',
        '1. 读取 personcrop prepare 时生成的 crop 坐标映射信息',
        '2. 将 crop 空间的检测框映射回原图空间',
        '3. 与原图 GT 进行匹配和评估\n',
        '## 建议\n',
        '优先执行实验2（person瓶颈量化分析），该实验已完整实现。',
        '根据实验2结果明确优化方向后，再决定是否需要完整实现本实验。\n'
    ]
    
    summary_path = output_dir / 'comparison_summary.md'
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(summary_lines))
    
    print(f"\n报告已保存到: {output_dir}")
    print("提示：当前为占位实现，建议优先执行实验2")


if __name__ == '__main__':
    args = parse_args()
    main(args)

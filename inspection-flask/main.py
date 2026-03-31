"""YOLOv8 加油站工服检测管线 -- 独立诊断与验证工具。

不依赖 Flask 应用上下文，可直接通过命令行运行，支持以下模式：

  python main.py check                          验证模型加载与推理设备
  python main.py image <path> [-o <dir>]         对单张图片或目录执行检测
  python main.py validate <dir> [-o <dir>]       批量推理统计
  python main.py validate <dir> --labels <dir>   带真值对比的准确率验证

使用场景：
  - 部署前快速验证权重文件与推理环境是否就绪
  - 对离线图片批量跑检测，评估模型准确率
  - 无需启动 Flask 服务即可调试检测链路

离线模式局限性：
  - 不包含时序约束 (MIN_TRACK_APPEAR_FRAMES / TEMPORAL_TRIGGER_RATIO)
  - 统计结果为单帧逐人判定，与在线告警口径存在差异
  - 可通过 --roi 参数模拟 ROI 过滤，但不含 track 跟踪
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import settings
from utils.models import (
    PersonDetector,
    WorkwearDetector,
    load_detection_models,
    select_runtime_device,
)
from utils.workwear_policy import evaluate_workwear_compliance, get_person_crop

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

_OFFLINE_NOTE = (
    "[注意] 离线模式不包含时序约束 (MIN_TRACK_APPEAR_FRAMES / TEMPORAL_TRIGGER_RATIO)，\n"
    "       统计结果为单帧逐人判定，与在线告警口径存在差异。"
)


def _parse_roi_arg(roi_str: str | None) -> list | None:
    """解析命令行 --roi 参数为 [x1, y1, x2, y2] 列表。"""
    if not roi_str:
        return None
    parts = [int(v.strip()) for v in roi_str.split(",")]
    if len(parts) != 4:
        raise ValueError(f"ROI 格式错误，需要 x1,y1,x2,y2，实际: {roi_str}")
    return parts


def _check_in_roi(bbox: list, roi: list | None) -> bool:
    """使用与在线 _in_roi() 相同的重叠比例策略判断目标是否在 ROI 内。"""
    if not roi:
        return True
    x1, y1, x2, y2 = bbox
    rx1, ry1, rx2, ry2 = roi
    ix1 = max(x1, rx1)
    iy1 = max(y1, ry1)
    ix2 = min(x2, rx2)
    iy2 = min(y2, ry2)
    if ix2 <= ix1 or iy2 <= iy1:
        return False
    inter_area = (ix2 - ix1) * (iy2 - iy1)
    person_area = max(1, (x2 - x1) * (y2 - y1))
    overlap_ratio = inter_area / person_area
    min_ratio = getattr(settings, "ROI_MIN_OVERLAP_RATIO", 0.5)
    return overlap_ratio >= min_ratio


def _load_models() -> tuple[PersonDetector, WorkwearDetector, str]:
    device = select_runtime_device()
    print(f"[INFO] 推理设备: {device}")
    t0 = time.perf_counter()
    person_model, workwear_model = load_detection_models(device)
    elapsed = time.perf_counter() - t0
    print(f"[INFO] 模型加载完成，耗时 {elapsed:.2f}s")
    return person_model, workwear_model, device


def _draw_results(
    frame: np.ndarray,
    person_contexts: list[dict],
) -> np.ndarray:
    """在帧上绘制人员框与工服检测结果，返回标注后的图像副本。"""
    canvas = frame.copy()
    for ctx in person_contexts:
        x1, y1, x2, y2 = ctx["bbox"]
        has_ww = ctx.get("has_workwear", False)
        color = (0, 180, 0) if has_ww else (0, 0, 220)
        label_text = "OK" if has_ww else "NO_WORKWEAR"
        conf = ctx.get("confidence", 0.0)
        tag = f"{label_text} {conf:.2f}"

        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 2)
        (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(canvas, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
        cv2.putText(canvas, tag, (x1 + 2, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        for item in ctx.get("workwear_items", []):
            bx1, by1, bx2, by2 = item["bbox"]
            bx1 += x1
            by1 += y1
            bx2 += x1
            by2 += y1
            wlabel = f"{item['label']} {item['confidence']:.2f}"
            cv2.rectangle(canvas, (bx1, by1), (bx2, by2), (0, 160, 0), 1)
            cv2.putText(canvas, wlabel, (bx1, by1 - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 160, 0), 1)
    return canvas


def _build_person_contexts(
    frame: np.ndarray,
    persons: list[dict],
    workwear_model: WorkwearDetector,
    roi: list | None = None,
) -> list[dict]:
    """复用与 HKCustomThread.build_person_contexts 相同的逻辑构建人员上下文。

    裁剪策略和合规判定均由 utils.workwear_policy 统一提供。
    ROI 判定使用与在线相同的重叠比例策略。
    """
    min_area = getattr(settings, "MIN_PERSON_BOX_AREA", 3000)
    area_mode = getattr(settings, "MIN_PERSON_AREA_MODE", "absolute")
    area_ratio_threshold = getattr(settings, "MIN_PERSON_AREA_RATIO", 0.005)
    workwear_conf = getattr(settings, "WORKWEAR_CONF", 0.45)
    frame_area = frame.shape[0] * frame.shape[1] if area_mode == "relative" else 0

    contexts: list[dict] = []
    for person in persons:
        bbox = person.get("bbox", [])
        if len(bbox) != 4:
            continue
        x1, y1, x2, y2 = bbox
        area = max(0, x2 - x1) * max(0, y2 - y1)
        if area_mode == "relative":
            if frame_area > 0 and area / frame_area < area_ratio_threshold:
                continue
        else:
            if area < min_area:
                continue

        in_roi = _check_in_roi(bbox, roi)

        crop = get_person_crop(frame, bbox)

        workwear_items: list[dict] = []
        if crop is not None and crop.size > 0:
            workwear_items = workwear_model.infer(crop, conf_threshold=workwear_conf)

        has_workwear = evaluate_workwear_compliance(workwear_items)

        contexts.append(
            {
                "bbox": bbox,
                "confidence": float(person.get("confidence", 0.0)),
                "label": person.get("label", "person"),
                "area": area,
                "in_roi": in_roi,
                "workwear_items": workwear_items,
                "has_workwear": has_workwear,
            }
        )
    return contexts


def _process_single_image(
    image_path: Path,
    person_model: PersonDetector,
    workwear_model: WorkwearDetector,
    output_dir: Path | None,
    roi: list | None = None,
) -> dict:
    """对单张图片执行完整检测管线并打印结果。

    返回值中包含 label_counts 字段，供 cmd_validate 直接使用，避免二次推理。
    """
    frame = cv2.imread(str(image_path))
    if frame is None:
        print(f"[WARN] 无法读取图片: {image_path}")
        return {"path": str(image_path), "error": "unreadable"}

    t0 = time.perf_counter()
    persons = person_model.infer(frame, conf_threshold=getattr(settings, "PERSON_CONF", 0.55))
    t_person = time.perf_counter() - t0

    t1 = time.perf_counter()
    contexts = _build_person_contexts(frame, persons, workwear_model, roi=roi)
    t_workwear = time.perf_counter() - t1

    total_persons = len(persons)
    filtered_contexts = contexts
    if roi is not None:
        filtered_contexts = [c for c in contexts if c.get("in_roi", False)]
    valid_persons = len(filtered_contexts)
    violation_count = sum(1 for c in filtered_contexts if not c.get("has_workwear", False))
    compliant_count = valid_persons - violation_count

    label_counts: dict[str, int] = {}
    for ctx in filtered_contexts:
        for item in ctx.get("workwear_items", []):
            lbl = item.get("label", "unknown")
            label_counts[lbl] = label_counts.get(lbl, 0) + 1

    print(f"\n  {image_path.name}")
    print(f"    人员检测: {total_persons} 人 ({t_person * 1000:.1f}ms)")
    if roi is not None:
        print(f"    ROI内有效目标: {valid_persons} 人 (共 {len(contexts)} 人通过面积过滤)")
    else:
        print(f"    有效目标: {valid_persons} 人 (面积 >= {getattr(settings, 'MIN_PERSON_BOX_AREA', 3000)})")
    print(f"    穿戴合规: {compliant_count}    未穿工服: {violation_count}")
    print(f"    工服检测耗时: {t_workwear * 1000:.1f}ms (共 {len(contexts)} 次裁剪推理)")

    for i, ctx in enumerate(contexts):
        status = "合规" if ctx["has_workwear"] else "违规"
        roi_tag = " ROI外" if not ctx.get("in_roi", True) else ""
        items_str = ", ".join(
            f"{it['label']}({it['confidence']:.2f})" for it in ctx.get("workwear_items", [])
        ) or "无"
        print(f"      [{i}] {status}{roi_tag} conf={ctx['confidence']:.2f} area={ctx['area']} 工服={items_str}")

    if output_dir is not None:
        canvas = _draw_results(frame, contexts)
        out_path = output_dir / f"det_{image_path.stem}.jpg"
        cv2.imwrite(str(out_path), canvas)
        print(f"    可视化已保存: {out_path}")

    return {
        "path": str(image_path),
        "total_persons": total_persons,
        "valid_persons": valid_persons,
        "compliant": compliant_count,
        "violations": violation_count,
        "label_counts": label_counts,
    }


def cmd_check(_args: argparse.Namespace) -> None:
    """验证模型加载与推理设备是否就绪。"""
    yolo_family = getattr(settings, "YOLO_FAMILY", "yolov8")
    print("=" * 60)
    print(f"{yolo_family.upper()} 工服检测管线 -- 环境检查")
    print("=" * 60)

    print(f"\n[配置]")
    print(f"  YOLO_FAMILY            : {yolo_family}")
    print(f"  PERSON_WEIGHT          : {settings.PERSON_WEIGHT}")
    print(f"  WORKWEAR_WEIGHT        : {settings.WORKWEAR_WEIGHT}")
    print(f"  IMGSZ                  : {getattr(settings, 'IMGSZ', 640)}")
    print(f"  PERSON_CONF            : {getattr(settings, 'PERSON_CONF', 0.55)}")
    print(f"  WORKWEAR_CONF          : {getattr(settings, 'WORKWEAR_CONF', 0.45)}")
    print(f"  PREDICT_IOU            : {getattr(settings, 'PREDICT_IOU', 0.45)}")
    print(f"  PREDICT_MAX_DET        : {getattr(settings, 'PREDICT_MAX_DET', 100)}")
    print(f"  MONITORED_PERSON_LABELS: {getattr(settings, 'MONITORED_PERSON_LABELS', ['person'])}")
    print(f"  WORKWEAR_LABELS        : {getattr(settings, 'WORKWEAR_LABELS', [])}")
    print(f"  COMPLIANCE_MODE        : {getattr(settings, 'WORKWEAR_COMPLIANCE_MODE', 'any')}")
    print(f"  USE_WHITE_BG_MASK      : {getattr(settings, 'USE_WHITE_BG_MASK', False)}")
    print(f"  MIN_PERSON_AREA_MODE   : {getattr(settings, 'MIN_PERSON_AREA_MODE', 'absolute')}")
    print(f"  MIN_PERSON_BOX_AREA    : {getattr(settings, 'MIN_PERSON_BOX_AREA', 3000)}")
    print(f"  TEMPORAL_WINDOW        : {getattr(settings, 'TEMPORAL_WINDOW_SIZE', 5)}")
    print(f"  TRIGGER_RATIO          : {getattr(settings, 'TEMPORAL_TRIGGER_RATIO', 0.6)}")

    person_ok = Path(settings.PERSON_WEIGHT).exists()
    workwear_ok = Path(settings.WORKWEAR_WEIGHT).exists()
    print(f"\n[权重文件]")
    print(f"  人员检测: {'存在' if person_ok else '缺失'}")
    print(f"  工服检测: {'存在' if workwear_ok else '缺失'}")

    if not (person_ok and workwear_ok):
        print("\n[结果] 权重文件不完整，请先将 .pt 文件放入 weights/ 目录")
        sys.exit(1)

    person_model, workwear_model, device = _load_models()

    print(f"\n[模型类别名]")
    print(f"  人员模型类别: {person_model.get_class_names()}")
    print(f"  工服模型类别: {workwear_model.get_class_names()}")

    dummy = np.zeros((640, 640, 3), dtype=np.uint8)
    t0 = time.perf_counter()
    person_model.infer(dummy)
    t_warmup_person = time.perf_counter() - t0

    crop = np.zeros((128, 64, 3), dtype=np.uint8)
    t1 = time.perf_counter()
    workwear_model.infer(crop)
    t_warmup_workwear = time.perf_counter() - t1

    print(f"\n[预热推理]")
    print(f"  人员检测 warmup: {t_warmup_person * 1000:.1f}ms")
    print(f"  工服检测 warmup: {t_warmup_workwear * 1000:.1f}ms")

    print(f"\n[结果] 环境检查通过，检测管线就绪 (device={device})")


def cmd_image(args: argparse.Namespace) -> None:
    """对单张图片或目录执行工服检测。"""
    target = Path(args.path)
    if not target.exists():
        print(f"[ERROR] 路径不存在: {target}")
        sys.exit(1)

    output_dir: Path | None = None
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

    roi = _parse_roi_arg(getattr(args, "roi", None))

    person_model, workwear_model, device = _load_models()

    if target.is_file():
        image_paths = [target]
    else:
        image_paths = sorted(
            p for p in target.iterdir()
            if p.is_file() and p.suffix.lower() in _IMAGE_EXTS
        )
        if not image_paths:
            print(f"[WARN] 目录中未找到图片文件: {target}")
            sys.exit(1)

    print(f"\n{_OFFLINE_NOTE}")
    if roi:
        print(f"[ROI] 已启用离线 ROI 过滤: {roi}")
    print(f"\n待处理图片: {len(image_paths)} 张")
    print("-" * 60)

    results = []
    t_total = time.perf_counter()
    for img_path in image_paths:
        results.append(_process_single_image(img_path, person_model, workwear_model, output_dir, roi=roi))
    elapsed_total = time.perf_counter() - t_total

    valid_results = [r for r in results if "error" not in r]
    total_persons = sum(r["total_persons"] for r in valid_results)
    total_valid = sum(r["valid_persons"] for r in valid_results)
    total_violations = sum(r["violations"] for r in valid_results)
    total_compliant = sum(r["compliant"] for r in valid_results)

    print("\n" + "=" * 60)
    print("汇总")
    print(f"  图片数量: {len(image_paths)} (成功 {len(valid_results)})")
    print(f"  检测人数: {total_persons} (有效 {total_valid})")
    print(f"  穿戴合规: {total_compliant}    未穿工服: {total_violations}")
    print(f"  总耗时: {elapsed_total:.2f}s  平均: {elapsed_total / max(len(valid_results), 1) * 1000:.1f}ms/张")
    print("=" * 60)


def _load_ground_truth(label_path: Path, img_w: int, img_h: int,
                       person_cls: int = 0, clothes_cls: int = 0) -> dict:
    """读取 YOLO 格式标注文件，返回该图片的真值统计。

    标注约定：
    - person 标注行的 class_id == person_cls
    - clothes 标注行的 class_id == clothes_cls
    - 有 clothes 标注框与某 person 框 IoU > 0 即视为该 person 真值合规

    返回:
        {"gt_total": int, "gt_compliant": int, "gt_violation": int}
    """
    if person_cls == clothes_cls:
        print(f"[WARN] person_cls 与 clothes_cls 相同 ({person_cls})，GT 统计将不准确，请检查 --person-cls / --clothes-cls 参数")
        return {"gt_total": 0, "gt_compliant": 0, "gt_violation": 0}

    if not label_path.exists():
        return {"gt_total": 0, "gt_compliant": 0, "gt_violation": 0}

    persons_xyxy: list[list[float]] = []
    clothes_xyxy: list[list[float]] = []

    for line in label_path.read_text().strip().splitlines():
        parts = line.strip().split()
        if len(parts) < 5:
            continue
        cls_id = int(parts[0])
        cx, cy, w, h = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
        x1 = (cx - w / 2) * img_w
        y1 = (cy - h / 2) * img_h
        x2 = (cx + w / 2) * img_w
        y2 = (cy + h / 2) * img_h
        if cls_id == person_cls:
            persons_xyxy.append([x1, y1, x2, y2])
        elif cls_id == clothes_cls:
            clothes_xyxy.append([x1, y1, x2, y2])

    gt_compliant = 0
    for pb in persons_xyxy:
        has_clothes = False
        for cb in clothes_xyxy:
            ix1 = max(pb[0], cb[0])
            iy1 = max(pb[1], cb[1])
            ix2 = min(pb[2], cb[2])
            iy2 = min(pb[3], cb[3])
            if ix2 > ix1 and iy2 > iy1:
                has_clothes = True
                break
        if has_clothes:
            gt_compliant += 1

    gt_total = len(persons_xyxy)
    return {
        "gt_total": gt_total,
        "gt_compliant": gt_compliant,
        "gt_violation": gt_total - gt_compliant,
    }


def cmd_validate(args: argparse.Namespace) -> None:
    """批量评估数据集，输出推理统计与可选的真值对比。"""
    dataset_dir = Path(args.path)
    if not dataset_dir.is_dir():
        print(f"[ERROR] 数据集目录不存在: {dataset_dir}")
        sys.exit(1)

    output_dir: Path | None = None
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

    roi = _parse_roi_arg(getattr(args, "roi", None))
    labels_dir: Path | None = None
    if getattr(args, "labels", None):
        labels_dir = Path(args.labels)
        if not labels_dir.is_dir():
            print(f"[ERROR] 标注目录不存在: {labels_dir}")
            sys.exit(1)

    person_cls = int(getattr(args, "person_cls", 0))
    clothes_cls = int(getattr(args, "clothes_cls", 0))

    person_model, workwear_model, device = _load_models()

    image_paths = sorted(
        p for p in dataset_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in _IMAGE_EXTS
    )
    if not image_paths:
        print(f"[WARN] 数据集目录中未找到图片: {dataset_dir}")
        sys.exit(1)

    print(f"\n{_OFFLINE_NOTE}")
    if roi:
        print(f"[ROI] 已启用离线 ROI 过滤: {roi}")
    if labels_dir:
        print(f"[真值] 标注目录: {labels_dir} (person_cls={person_cls}, clothes_cls={clothes_cls})")
    else:
        print("[模式] 推理统计（无真值对比）")

    print(f"\n数据集: {dataset_dir}")
    print(f"图片数量: {len(image_paths)}")
    print("-" * 60)

    results = []
    label_counter: dict[str, int] = {}
    gt_results: list[dict] = []
    t_total = time.perf_counter()

    for img_path in image_paths:
        result = _process_single_image(
            img_path, person_model, workwear_model, output_dir, roi=roi,
        )
        results.append(result)

        if "error" not in result:
            for lbl, cnt in result.get("label_counts", {}).items():
                label_counter[lbl] = label_counter.get(lbl, 0) + cnt

        if labels_dir and "error" not in result:
            label_path = labels_dir / f"{img_path.stem}.txt"
            frame = cv2.imread(str(img_path))
            if frame is not None:
                h, w = frame.shape[:2]
                gt = _load_ground_truth(label_path, w, h, person_cls, clothes_cls)
                gt["pred_violations"] = result["violations"]
                gt["pred_compliant"] = result["compliant"]
                gt_results.append(gt)

    elapsed_total = time.perf_counter() - t_total

    valid_results = [r for r in results if "error" not in r]
    error_results = [r for r in results if "error" in r]
    total_persons = sum(r["total_persons"] for r in valid_results)
    total_valid = sum(r["valid_persons"] for r in valid_results)
    total_violations = sum(r["violations"] for r in valid_results)
    total_compliant = sum(r["compliant"] for r in valid_results)

    compliant_images = sum(1 for r in valid_results if r["violations"] == 0)
    violation_images = sum(1 for r in valid_results if r["violations"] > 0)

    print("\n" + "=" * 60)
    report_title = "数据集评估报告（真值对比）" if labels_dir else "数据集评估报告（推理统计）"
    print(report_title)
    print("=" * 60)
    print(f"  数据集路径    : {dataset_dir}")
    print(f"  图片总数      : {len(image_paths)}")
    print(f"  成功处理      : {len(valid_results)}")
    print(f"  读取失败      : {len(error_results)}")
    print(f"  检测人数(总)  : {total_persons}")
    print(f"  有效人数(面积): {total_valid}")
    print(f"  穿戴合规人数  : {total_compliant}")
    print(f"  未穿工服人数  : {total_violations}")
    print(f"  全合规图片    : {compliant_images}")
    print(f"  含违规图片    : {violation_images}")
    if total_valid > 0:
        print(f"  合规率        : {total_compliant / total_valid * 100:.1f}%")
    print(f"  总耗时        : {elapsed_total:.2f}s")
    print(f"  平均耗时      : {elapsed_total / max(len(valid_results), 1) * 1000:.1f}ms/张")

    if label_counter:
        print(f"\n  工服标签分布:")
        for lbl, cnt in sorted(label_counter.items(), key=lambda x: -x[1]):
            print(f"    {lbl:20s}: {cnt}")

    if labels_dir and gt_results:
        tp = sum(min(g["pred_violations"], g["gt_violation"]) for g in gt_results)
        fp = sum(max(0, g["pred_violations"] - g["gt_violation"]) for g in gt_results)
        fn = sum(max(0, g["gt_violation"] - g["pred_violations"]) for g in gt_results)
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-9)
        gt_total = sum(g["gt_total"] for g in gt_results)
        gt_vio = sum(g["gt_violation"] for g in gt_results)
        gt_comp = sum(g["gt_compliant"] for g in gt_results)

        print(f"\n  真值对比:")
        print(f"    真值人数(总)  : {gt_total}")
        print(f"    真值合规      : {gt_comp}")
        print(f"    真值违规      : {gt_vio}")
        print(f"    TP (正确检出) : {tp}")
        print(f"    FP (误报)     : {fp}")
        print(f"    FN (漏报)     : {fn}")
        print(f"    Precision     : {precision:.4f}")
        print(f"    Recall        : {recall:.4f}")
        print(f"    F1            : {f1:.4f}")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="YOLOv8 加油站工服检测管线 -- 独立诊断与验证工具",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用子命令")

    subparsers.add_parser("check", help="验证模型加载与推理设备")

    image_parser = subparsers.add_parser("image", help="对图片执行工服检测")
    image_parser.add_argument("path", help="图片路径或包含图片的目录")
    image_parser.add_argument("-o", "--output", help="可视化结果输出目录（可选）")
    image_parser.add_argument(
        "--roi", help="可选 ROI 区域 x1,y1,x2,y2（与在线重叠比例判定一致）",
    )

    validate_parser = subparsers.add_parser("validate", help="批量数据集评估与统计")
    validate_parser.add_argument("path", help="数据集目录路径")
    validate_parser.add_argument("-o", "--output", help="可视化结果输出目录（可选）")
    validate_parser.add_argument(
        "--roi", help="可选 ROI 区域 x1,y1,x2,y2（与在线重叠比例判定一致）",
    )
    validate_parser.add_argument(
        "--labels", help="YOLO 格式标注目录，提供后进入真值对比模式",
    )
    validate_parser.add_argument(
        "--person-cls", dest="person_cls", type=int, default=0,
        help="标注文件中 person 类别 ID（默认 0）",
    )
    validate_parser.add_argument(
        "--clothes-cls", dest="clothes_cls", type=int, default=1,
        help="标注文件中 clothes 类别 ID（默认 1）",
    )

    args = parser.parse_args()

    if args.command == "check":
        cmd_check(args)
    elif args.command == "image":
        cmd_image(args)
    elif args.command == "validate":
        cmd_validate(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

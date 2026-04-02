"""YOLOv8 加油站工服检测管线 -- 独立诊断与验证工具。

不依赖 Flask 应用上下文，可直接通过命令行运行，支持以下模式：

  python main.py check
  python main.py image <path> [-o <dir>] [--roi x1,y1,x2,y2]
  python main.py validate <dir> [-o <dir>] [--labels <dir>]

使用场景：
  - 部署前快速验证权重文件与推理环境是否就绪
  - 对离线图片批量跑检测，复核“作业区人员工服检出”效果
  - 无需启动 Flask 服务即可调试检测链路

离线模式局限性：
  - 不包含时序约束 (MIN_TRACK_APPEAR_FRAMES / TEMPORAL_TRIGGER_RATIO)
  - 不包含跨帧 track 跟踪，不能直接等价为在线告警结果
  - validate 会尽量做实例级真值匹配，但仍需结合真实 ROI / 视频流做在线验证
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
_DEFAULT_EVAL_MATCH_IOU = 0.5
_LABEL_SCAN_LIMIT = 200

_OFFLINE_NOTE = (
    "[注意] 离线模式不包含时序约束 (MIN_TRACK_APPEAR_FRAMES / TEMPORAL_TRIGGER_RATIO)，\n"
    "       也不包含跨帧 track 跟踪；统计结果仅代表单帧实例匹配，不直接等价于在线告警效果。"
)

_DATASET_DEFAULT_NOTE = (
    "[提示] 当前仓库 `docs/dataset.md` 记录的数据口径是单类 `clothes` 标注，\n"
    "       因此 validate 默认采用 `--gt-mode clothes-only --clothes-cls 0`。\n"
    "       若你使用的是 `person + clothes` 配对标注，请显式指定 `--gt-mode paired`。"
)


def _parse_roi_arg(roi_str: str | None) -> list[int] | None:
    """解析命令行 --roi 参数为 [x1, y1, x2, y2] 列表。"""
    if not roi_str:
        return None
    parts = [int(v.strip()) for v in roi_str.split(",")]
    if len(parts) != 4:
        raise ValueError(f"ROI 格式错误，需要 x1,y1,x2,y2，实际: {roi_str}")
    return parts


def _check_in_roi(bbox: list[float], roi: list[int] | None) -> bool:
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
    person_area = max(1.0, (x2 - x1) * (y2 - y1))
    overlap_ratio = inter_area / person_area
    min_ratio = getattr(settings, "ROI_MIN_OVERLAP_RATIO", 0.5)
    return overlap_ratio >= min_ratio


def _bbox_iou(box_a: list[float], box_b: list[float]) -> float:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    inter_area = (ix2 - ix1) * (iy2 - iy1)
    area_a = max(1.0, (ax2 - ax1) * (ay2 - ay1))
    area_b = max(1.0, (bx2 - bx1) * (by2 - by1))
    union_area = area_a + area_b - inter_area
    if union_area <= 0:
        return 0.0
    return inter_area / union_area


def _boxes_overlap(box_a: list[float], box_b: list[float]) -> bool:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    return ix2 > ix1 and iy2 > iy1


def _greedy_match(
    pred_boxes: list[list[float]],
    gt_boxes: list[list[float]],
    iou_threshold: float = _DEFAULT_EVAL_MATCH_IOU,
) -> tuple[list[tuple[int, int, float]], list[int], list[int]]:
    """基于 IoU 的贪心一对一匹配。"""
    candidates: list[tuple[float, int, int]] = []
    for pred_idx, pred_box in enumerate(pred_boxes):
        for gt_idx, gt_box in enumerate(gt_boxes):
            iou = _bbox_iou(pred_box, gt_box)
            if iou >= iou_threshold:
                candidates.append((iou, pred_idx, gt_idx))

    candidates.sort(key=lambda item: item[0], reverse=True)
    matched_pred: set[int] = set()
    matched_gt: set[int] = set()
    matches: list[tuple[int, int, float]] = []

    for iou, pred_idx, gt_idx in candidates:
        if pred_idx in matched_pred or gt_idx in matched_gt:
            continue
        matched_pred.add(pred_idx)
        matched_gt.add(gt_idx)
        matches.append((pred_idx, gt_idx, iou))

    unmatched_pred = [idx for idx in range(len(pred_boxes)) if idx not in matched_pred]
    unmatched_gt = [idx for idx in range(len(gt_boxes)) if idx not in matched_gt]
    return matches, unmatched_pred, unmatched_gt


def _safe_read_label_lines(label_path: Path) -> list[str]:
    if not label_path.exists():
        return []
    try:
        return label_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return label_path.read_text(encoding="utf-8", errors="ignore").splitlines()


def _xywhn_to_xyxy(
    cx: float,
    cy: float,
    w: float,
    h: float,
    img_w: int,
    img_h: int,
) -> list[float]:
    x1 = (cx - w / 2) * img_w
    y1 = (cy - h / 2) * img_h
    x2 = (cx + w / 2) * img_w
    y2 = (cy + h / 2) * img_h
    return [x1, y1, x2, y2]


def _load_label_entries(label_path: Path, img_w: int, img_h: int) -> list[dict]:
    entries: list[dict] = []
    for line in _safe_read_label_lines(label_path):
        parts = line.strip().split()
        if len(parts) < 5:
            continue
        try:
            cls_id = int(parts[0])
            cx, cy, w, h = map(float, parts[1:5])
        except ValueError:
            continue
        entries.append(
            {
                "class_id": cls_id,
                "bbox": _xywhn_to_xyxy(cx, cy, w, h, img_w, img_h),
            }
        )
    return entries


def _collect_label_class_ids(label_path: Path) -> set[int]:
    class_ids: set[int] = set()
    for line in _safe_read_label_lines(label_path):
        parts = line.strip().split()
        if not parts:
            continue
        try:
            class_ids.add(int(parts[0]))
        except ValueError:
            continue
    return class_ids


def _scan_label_classes(labels_dir: Path, max_files: int = _LABEL_SCAN_LIMIT) -> tuple[set[int], int]:
    class_ids: set[int] = set()
    scanned = 0
    for label_path in sorted(labels_dir.rglob("*.txt")):
        class_ids |= _collect_label_class_ids(label_path)
        scanned += 1
        if scanned >= max_files:
            break
    return class_ids, scanned


def _emit_label_scan_warnings(
    labels_dir: Path,
    gt_mode: str,
    person_cls: int,
    clothes_cls: int,
) -> None:
    class_ids, scanned = _scan_label_classes(labels_dir)
    if scanned == 0:
        print(f"[WARN] 标注目录下未找到任何 .txt 文件: {labels_dir}")
        return

    print(f"[INFO] 标注类扫描: 已扫描 {scanned} 个文件，观测到 class_id={sorted(class_ids)}")

    if gt_mode == "clothes-only":
        if clothes_cls not in class_ids:
            print(
                "[WARN] 当前 `clothes-only` 配置可能不匹配："
                f"`--clothes-cls {clothes_cls}` 未出现在扫描到的标注中。"
            )
        if len(class_ids) > 1:
            print(
                "[WARN] 扫描到多个 class_id，但当前使用的是 `clothes-only` 模式；"
                "请确认数据集是否真的只有 `clothes` 单类标注。"
            )
    else:
        missing: list[str] = []
        if person_cls not in class_ids:
            missing.append(f"person_cls={person_cls}")
        if clothes_cls not in class_ids:
            missing.append(f"clothes_cls={clothes_cls}")
        if missing:
            print(
                "[WARN] 当前 `paired` 配置可能不匹配：以下 class_id 未出现在扫描到的标注中 -> "
                + ", ".join(missing)
            )
        if class_ids == {clothes_cls} and person_cls != clothes_cls:
            print(
                "[WARN] 扫描结果看起来像单类 `clothes` 数据；"
                "若当前数据确为仓库文档中的数据集，请改用 "
                f"`--gt-mode clothes-only --clothes-cls {clothes_cls}`。"
            )


def _resolve_label_path(
    image_path: Path,
    dataset_dir: Path,
    labels_dir: Path,
) -> tuple[Path | None, list[str]]:
    """同时兼容 mirrored labels 与统一平铺 labels 根目录。"""
    warnings: list[str] = []
    rel = image_path.relative_to(dataset_dir)
    mirrored = labels_dir / rel.with_suffix(".txt")
    flat = labels_dir / f"{image_path.stem}.txt"

    mirrored_exists = mirrored.exists()
    flat_exists = flat.exists()

    if mirrored == flat:
        return (mirrored if mirrored_exists else None), warnings

    if mirrored_exists and flat_exists:
        try:
            if mirrored.read_bytes() != flat.read_bytes():
                warnings.append(
                    f"{image_path.name} 同时匹配到 mirrored 与 flat 标注，且内容不同；"
                    f"默认优先使用 mirrored: {mirrored}"
                )
            else:
                warnings.append(
                    f"{image_path.name} 同时匹配到 mirrored 与 flat 标注；"
                    f"默认优先使用 mirrored: {mirrored}"
                )
        except OSError:
            warnings.append(
                f"{image_path.name} 同时匹配到 mirrored 与 flat 标注；"
                f"默认优先使用 mirrored: {mirrored}"
            )
        return mirrored, warnings

    if mirrored_exists:
        return mirrored, warnings
    if flat_exists:
        return flat, warnings
    return None, warnings


def _load_models() -> tuple[PersonDetector, WorkwearDetector, str]:
    device = select_runtime_device()
    print(f"[INFO] 推理设备: {device}")
    t0 = time.perf_counter()
    person_model, workwear_model = load_detection_models(device)
    elapsed = time.perf_counter() - t0
    print(f"[INFO] 模型加载完成，耗时 {elapsed:.2f}s")
    return person_model, workwear_model, device


def _globalize_workwear_items(
    person_contexts: list[dict],
    workwear_labels: set[str] | None = None,
) -> list[dict]:
    """将 crop 局部坐标的工服框映射回整图坐标，供离线 GT 对比使用。"""
    if workwear_labels is None:
        workwear_labels = {
            str(label).strip()
            for label in getattr(settings, "WORKWEAR_LABELS", [])
            if str(label).strip()
        }

    global_items: list[dict] = []
    for ctx in person_contexts:
        person_bbox = ctx.get("bbox", [])
        if len(person_bbox) != 4:
            continue
        px1, py1, _, _ = person_bbox
        for item in ctx.get("workwear_items", []):
            item_bbox = item.get("bbox", [])
            if len(item_bbox) != 4:
                continue
            label = str(item.get("label", "")).strip()
            if workwear_labels and label not in workwear_labels:
                continue
            bx1, by1, bx2, by2 = item_bbox
            global_items.append(
                {
                    "bbox": [px1 + bx1, py1 + by1, px1 + bx2, py1 + by2],
                    "confidence": float(item.get("confidence", 0.0)),
                    "label": label,
                }
            )
    return global_items


def _draw_results(
    frame: np.ndarray,
    person_contexts: list[dict],
) -> np.ndarray:
    """在帧上绘制人员框与工服检测结果，返回标注后的图像副本。"""
    canvas = frame.copy()
    for ctx in person_contexts:
        x1, y1, x2, y2 = [int(v) for v in ctx["bbox"]]
        has_ww = ctx.get("has_workwear", False)
        color = (0, 180, 0) if has_ww else (0, 0, 220)
        label_text = "OK" if has_ww else "SUSPECT"
        conf = ctx.get("confidence", 0.0)
        tag = f"{label_text} {conf:.2f}"

        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 2)
        (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(canvas, (x1, max(0, y1 - th - 6)), (x1 + tw + 4, y1), color, -1)
        cv2.putText(canvas, tag, (x1 + 2, max(12, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        for item in ctx.get("workwear_items", []):
            item_bbox = item.get("bbox", [])
            if len(item_bbox) != 4:
                continue
            bx1, by1, bx2, by2 = [int(v) for v in item_bbox]
            gx1, gy1, gx2, gy2 = x1 + bx1, y1 + by1, x1 + bx2, y1 + by2
            wlabel = f"{item.get('label', 'unknown')} {float(item.get('confidence', 0.0)):.2f}"
            cv2.rectangle(canvas, (gx1, gy1), (gx2, gy2), (0, 160, 0), 1)
            cv2.putText(canvas, wlabel, (gx1, max(12, gy1 - 3)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 160, 0), 1)
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
    roi: list[int] | None = None,
    base_dir: Path | None = None,
) -> dict:
    """对单张图片执行完整检测管线并打印结果。"""
    frame = cv2.imread(str(image_path))
    if frame is None:
        print(f"[WARN] 无法读取图片: {image_path}")
        return {"path": str(image_path), "error": "unreadable"}

    img_h, img_w = frame.shape[:2]

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
        print(f"    有效目标: {valid_persons} 人 (面积过滤后)")
    print(f"    判定合规人员: {compliant_count}    疑似未穿工服: {violation_count}")
    print(f"    工服检测耗时: {t_workwear * 1000:.1f}ms (共 {len(contexts)} 次裁剪推理)")

    for i, ctx in enumerate(contexts):
        status = "合规" if ctx["has_workwear"] else "疑似未穿工服"
        roi_tag = " ROI外" if not ctx.get("in_roi", True) else ""
        items_str = ", ".join(
            f"{it['label']}({it['confidence']:.2f})" for it in ctx.get("workwear_items", [])
        ) or "无"
        print(f"      [{i}] {status}{roi_tag} conf={ctx['confidence']:.2f} area={ctx['area']} 工服={items_str}")

    if output_dir is not None:
        canvas = _draw_results(frame, contexts)
        if base_dir is not None:
            rel = image_path.relative_to(base_dir)
            out_path = output_dir / rel.parent / f"det_{image_path.stem}.jpg"
            out_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            out_path = output_dir / f"det_{image_path.stem}.jpg"
        cv2.imwrite(str(out_path), canvas)
        print(f"    可视化已保存: {out_path}")

    return {
        "path": str(image_path),
        "img_w": img_w,
        "img_h": img_h,
        "total_persons": total_persons,
        "valid_persons": valid_persons,
        "compliant": compliant_count,
        "violations": violation_count,
        "label_counts": label_counts,
        "effective_contexts": filtered_contexts,
        "pred_workwear_boxes": _globalize_workwear_items(filtered_contexts),
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
    print(f"  判定合规: {total_compliant}    疑似未穿工服: {total_violations}")
    print(f"  总耗时: {elapsed_total:.2f}s  平均: {elapsed_total / max(len(valid_results), 1) * 1000:.1f}ms/张")
    print("=" * 60)


def _load_ground_truth(
    label_path: Path | None,
    img_w: int,
    img_h: int,
    person_cls: int = 0,
    clothes_cls: int = 0,
    roi: list[int] | None = None,
    gt_mode: str = "clothes-only",
) -> dict:
    """读取 YOLO 标注并转换为离线评估所需的真值结构。"""
    empty = {
        "gt_mode": gt_mode,
        "gt_total": 0,
        "gt_compliant": 0,
        "gt_violation": 0,
        "persons": [],
        "clothes": [],
    }

    if label_path is None or not label_path.exists():
        return empty

    if gt_mode == "paired" and person_cls == clothes_cls:
        print(
            f"[WARN] paired 模式下 person_cls 与 clothes_cls 不能相同，当前均为 {person_cls}；"
            "该图片的 GT 对比将跳过。"
        )
        return empty

    entries = _load_label_entries(label_path, img_w, img_h)
    if not entries:
        return empty

    clothes_boxes = [entry["bbox"] for entry in entries if entry["class_id"] == clothes_cls]
    if gt_mode == "clothes-only":
        if roi is not None:
            clothes_boxes = [bbox for bbox in clothes_boxes if _check_in_roi(bbox, roi)]
        gt_total = len(clothes_boxes)
        return {
            "gt_mode": gt_mode,
            "gt_total": gt_total,
            "gt_compliant": gt_total,
            "gt_violation": 0,
            "persons": [],
            "clothes": clothes_boxes,
        }

    person_boxes = [entry["bbox"] for entry in entries if entry["class_id"] == person_cls]
    if roi is not None:
        person_boxes = [bbox for bbox in person_boxes if _check_in_roi(bbox, roi)]

    gt_persons: list[dict] = []
    for person_box in person_boxes:
        has_workwear = any(_boxes_overlap(person_box, clothes_box) for clothes_box in clothes_boxes)
        gt_persons.append(
            {
                "bbox": person_box,
                "has_workwear": has_workwear,
            }
        )

    gt_total = len(gt_persons)
    gt_compliant = sum(1 for person in gt_persons if person["has_workwear"])
    return {
        "gt_mode": gt_mode,
        "gt_total": gt_total,
        "gt_compliant": gt_compliant,
        "gt_violation": gt_total - gt_compliant,
        "persons": gt_persons,
        "clothes": clothes_boxes,
    }


def _compute_prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-9)
    return precision, recall, f1


def _evaluate_clothes_only(
    pred_workwear_boxes: list[dict],
    gt_clothes_boxes: list[list[float]],
    iou_threshold: float = _DEFAULT_EVAL_MATCH_IOU,
) -> dict:
    pred_boxes = [item["bbox"] for item in pred_workwear_boxes]
    matches, unmatched_pred, unmatched_gt = _greedy_match(pred_boxes, gt_clothes_boxes, iou_threshold)
    return {
        "pred_total": len(pred_boxes),
        "gt_total": len(gt_clothes_boxes),
        "matched": len(matches),
        "tp": len(matches),
        "fp": len(unmatched_pred),
        "fn": len(unmatched_gt),
    }


def _evaluate_paired(
    pred_contexts: list[dict],
    gt_persons: list[dict],
    iou_threshold: float = _DEFAULT_EVAL_MATCH_IOU,
) -> dict:
    pred_boxes = [ctx["bbox"] for ctx in pred_contexts]
    gt_boxes = [person["bbox"] for person in gt_persons]
    matches, unmatched_pred, unmatched_gt = _greedy_match(pred_boxes, gt_boxes, iou_threshold)

    status_correct = 0
    status_mismatch = 0

    violation_tp = violation_fp = violation_fn = 0
    compliant_tp = compliant_fp = compliant_fn = 0

    for pred_idx, gt_idx, _iou in matches:
        pred_has_workwear = bool(pred_contexts[pred_idx].get("has_workwear", False))
        gt_has_workwear = bool(gt_persons[gt_idx].get("has_workwear", False))

        if pred_has_workwear == gt_has_workwear:
            status_correct += 1
        else:
            status_mismatch += 1

        pred_violation = not pred_has_workwear
        gt_violation = not gt_has_workwear
        if pred_violation and gt_violation:
            violation_tp += 1
        elif pred_violation and not gt_violation:
            violation_fp += 1
        elif not pred_violation and gt_violation:
            violation_fn += 1

        pred_compliant = pred_has_workwear
        gt_compliant = gt_has_workwear
        if pred_compliant and gt_compliant:
            compliant_tp += 1
        elif pred_compliant and not gt_compliant:
            compliant_fp += 1
        elif not pred_compliant and gt_compliant:
            compliant_fn += 1

    for pred_idx in unmatched_pred:
        if pred_contexts[pred_idx].get("has_workwear", False):
            compliant_fp += 1
        else:
            violation_fp += 1

    for gt_idx in unmatched_gt:
        if gt_persons[gt_idx].get("has_workwear", False):
            compliant_fn += 1
        else:
            violation_fn += 1

    return {
        "pred_total": len(pred_contexts),
        "gt_total": len(gt_persons),
        "matched": len(matches),
        "status_correct": status_correct,
        "status_mismatch": status_mismatch,
        "unmatched_pred": len(unmatched_pred),
        "unmatched_gt": len(unmatched_gt),
        "violation_tp": violation_tp,
        "violation_fp": violation_fp,
        "violation_fn": violation_fn,
        "compliant_tp": compliant_tp,
        "compliant_fp": compliant_fp,
        "compliant_fn": compliant_fn,
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
    gt_mode = getattr(args, "gt_mode", "clothes-only")

    if gt_mode == "paired" and person_cls == clothes_cls:
        print(
            "[ERROR] paired 模式下 `--person-cls` 与 `--clothes-cls` 不能相同；"
            "请显式指定两种不同的 class_id。"
        )
        sys.exit(1)

    person_model, workwear_model, _device = _load_models()

    image_paths = sorted(
        p for p in dataset_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in _IMAGE_EXTS
    )
    if not image_paths:
        print(f"[WARN] 数据集目录中未找到图片: {dataset_dir}")
        sys.exit(1)

    print(f"\n{_OFFLINE_NOTE}")
    if labels_dir:
        print(_DATASET_DEFAULT_NOTE)
    if roi:
        print(f"[ROI] 已启用离线 ROI 过滤: {roi}")
    if labels_dir:
        print(f"[真值] 标注目录: {labels_dir} (gt_mode={gt_mode}, person_cls={person_cls}, clothes_cls={clothes_cls})")
        _emit_label_scan_warnings(labels_dir, gt_mode, person_cls, clothes_cls)
    else:
        print("[模式] 推理统计（无真值对比）")

    print(f"\n数据集: {dataset_dir}")
    print(f"图片数量: {len(image_paths)}")
    print("-" * 60)

    results = []
    label_counter: dict[str, int] = {}
    gt_results: list[dict] = []
    label_path_warning_cache: set[str] = set()
    missing_label_count = 0
    t_total = time.perf_counter()

    for img_path in image_paths:
        result = _process_single_image(
            img_path, person_model, workwear_model, output_dir, roi=roi,
            base_dir=dataset_dir,
        )

        if "error" in result:
            results.append(result)
            continue

        effective_contexts = result.pop("effective_contexts", [])
        pred_workwear_boxes = result.pop("pred_workwear_boxes", [])
        img_w = int(result.pop("img_w"))
        img_h = int(result.pop("img_h"))

        for lbl, cnt in result.get("label_counts", {}).items():
            label_counter[lbl] = label_counter.get(lbl, 0) + cnt

        if labels_dir:
            label_path, resolve_warnings = _resolve_label_path(img_path, dataset_dir, labels_dir)
            for warning in resolve_warnings:
                if warning not in label_path_warning_cache:
                    print(f"[WARN] {warning}")
                    label_path_warning_cache.add(warning)

            if label_path is None:
                missing_label_count += 1
            else:
                gt = _load_ground_truth(
                    label_path=label_path,
                    img_w=img_w,
                    img_h=img_h,
                    person_cls=person_cls,
                    clothes_cls=clothes_cls,
                    roi=roi,
                    gt_mode=gt_mode,
                )
                if gt_mode == "clothes-only":
                    eval_result = _evaluate_clothes_only(pred_workwear_boxes, gt["clothes"])
                else:
                    eval_result = _evaluate_paired(effective_contexts, gt["persons"])
                gt_results.append(
                    {
                        "path": str(img_path),
                        "label_path": str(label_path),
                        **gt,
                        **eval_result,
                    }
                )

        results.append(result)

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
    if labels_dir:
        print(f"  缺失标注      : {missing_label_count}")
    print(f"  检测人数(总)  : {total_persons}")
    print(f"  有效人数(面积/ROI): {total_valid}")
    print(f"  判定合规人员数    : {total_compliant}")
    print(f"  疑似未穿工服人数  : {total_violations}")
    print(f"  全合规图片    : {compliant_images}")
    print(f"  含疑似违规图片: {violation_images}")
    if total_valid > 0:
        print(f"  合规率        : {total_compliant / total_valid * 100:.1f}%")
    print(f"  总耗时        : {elapsed_total:.2f}s")
    print(f"  平均耗时      : {elapsed_total / max(len(valid_results), 1) * 1000:.1f}ms/张")

    if label_counter:
        print(f"\n  工服标签分布:")
        for lbl, cnt in sorted(label_counter.items(), key=lambda x: -x[1]):
            print(f"    {lbl:20s}: {cnt}")

    if labels_dir and gt_results:
        if gt_mode == "clothes-only":
            tp = sum(item["tp"] for item in gt_results)
            fp = sum(item["fp"] for item in gt_results)
            fn = sum(item["fn"] for item in gt_results)
            pred_total = sum(item["pred_total"] for item in gt_results)
            gt_total = sum(item["gt_total"] for item in gt_results)
            matched = sum(item["matched"] for item in gt_results)
            precision, recall, f1 = _compute_prf(tp, fp, fn)

            print("\n  真值对比 [clothes-only 模式: 评估的是 `clothes` 正类实例检出，不直接代表“疑似未穿工服”告警准确率]:")
            print(f"    GT clothes 标注数 : {gt_total}")
            print(f"    预测 clothes 框数 : {pred_total}")
            print(f"    实例匹配成功数   : {matched}")
            print(f"    TP               : {tp}")
            print(f"    FP               : {fp}")
            print(f"    FN               : {fn}")
            print(f"    Precision     : {precision:.4f}")
            print(f"    Recall        : {recall:.4f}")
            print(f"    F1            : {f1:.4f}")
        else:
            matched = sum(item["matched"] for item in gt_results)
            status_correct = sum(item["status_correct"] for item in gt_results)
            status_mismatch = sum(item["status_mismatch"] for item in gt_results)
            unmatched_pred = sum(item["unmatched_pred"] for item in gt_results)
            unmatched_gt = sum(item["unmatched_gt"] for item in gt_results)
            pred_total = sum(item["pred_total"] for item in gt_results)
            gt_total = sum(item["gt_total"] for item in gt_results)

            violation_tp = sum(item["violation_tp"] for item in gt_results)
            violation_fp = sum(item["violation_fp"] for item in gt_results)
            violation_fn = sum(item["violation_fn"] for item in gt_results)
            compliant_tp = sum(item["compliant_tp"] for item in gt_results)
            compliant_fp = sum(item["compliant_fp"] for item in gt_results)
            compliant_fn = sum(item["compliant_fn"] for item in gt_results)

            vio_precision, vio_recall, vio_f1 = _compute_prf(violation_tp, violation_fp, violation_fn)
            com_precision, com_recall, com_f1 = _compute_prf(compliant_tp, compliant_fp, compliant_fn)

            print("\n  真值对比 [paired 模式: 先做 person 实例 IoU 匹配，再比较每个实例的工服状态]:")
            print(f"    GT person 数        : {gt_total}")
            print(f"    预测有效 person 数  : {pred_total}")
            print(f"    实例匹配成功数      : {matched}")
            print(f"    状态判断正确        : {status_correct}")
            print(f"    状态判断冲突        : {status_mismatch}")
            print(f"    未匹配预测实例      : {unmatched_pred}")
            print(f"    未匹配 GT 实例      : {unmatched_gt}")
            print("    疑似未穿工服(正类):")
            print(f"      TP               : {violation_tp}")
            print(f"      FP               : {violation_fp}")
            print(f"      FN               : {violation_fn}")
            print(f"      Precision        : {vio_precision:.4f}")
            print(f"      Recall           : {vio_recall:.4f}")
            print(f"      F1               : {vio_f1:.4f}")
            print("    合规人员(正类):")
            print(f"      TP               : {compliant_tp}")
            print(f"      FP               : {compliant_fp}")
            print(f"      FN               : {compliant_fn}")
            print(f"      Precision        : {com_precision:.4f}")
            print(f"      Recall           : {com_recall:.4f}")
            print(f"      F1               : {com_f1:.4f}")

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

    validate_parser = subparsers.add_parser(
        "validate",
        help="批量数据集评估与统计（默认按 clothes-only 单类标注解释）",
    )
    validate_parser.add_argument("path", help="数据集目录路径")
    validate_parser.add_argument("-o", "--output", help="可视化结果输出目录（可选）")
    validate_parser.add_argument(
        "--roi", help="可选 ROI 区域 x1,y1,x2,y2（与在线重叠比例判定一致）",
    )
    validate_parser.add_argument(
        "--labels", help="YOLO 格式标注目录（支持 mirrored / flat 配对），提供后进入真值对比模式",
    )
    validate_parser.add_argument(
        "--person-cls", dest="person_cls", type=int, default=0,
        help="标注文件中 person 类别 ID（仅 paired 模式使用，默认 0）",
    )
    validate_parser.add_argument(
        "--clothes-cls", dest="clothes_cls", type=int, default=0,
        help="标注文件中 clothes 类别 ID（默认 0，适配当前 clothes-only 数据集）",
    )
    validate_parser.add_argument(
        "--gt-mode", dest="gt_mode", choices=["paired", "clothes-only"],
        default="clothes-only",
        help="真值模式: paired=标注含person+clothes两类; clothes-only=仅clothes正类标注（默认 clothes-only）",
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

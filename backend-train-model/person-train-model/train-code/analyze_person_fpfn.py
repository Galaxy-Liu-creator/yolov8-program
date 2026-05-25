from __future__ import annotations

import argparse
import json
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import yaml
from ultralytics import YOLO

from prepare_person_dataset import (
    DEFAULT_PROJECT_CONFIG,
    PERSON_ROOT,
    assert_directory_within_root,
    iter_image_paths,
    load_person_project_context,
)


DEFAULT_EVAL_REPORT = (
    PERSON_ROOT
    / "train-result"
    / "artifacts"
    / "reports"
    / "person_roi_aware_v3_mask_then_crop_margin64_from_fullframe"
    / "person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_eval.json"
)
DEFAULT_OUTPUT_PARENT = PERSON_ROOT / "train-result" / "review"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze per-image FP/FN for a person detection run."
    )
    parser.add_argument(
        "--project-config",
        default=str(DEFAULT_PROJECT_CONFIG),
        help="Path to person_project_config.json.",
    )
    parser.add_argument(
        "--eval-report",
        default=str(DEFAULT_EVAL_REPORT),
        help="Path to an existing *_eval.json report. Used to infer weights and dataset when not passed explicitly.",
    )
    parser.add_argument("--dataset-yaml", help="Path to dataset.yaml.")
    parser.add_argument("--weights", help="Path to best.pt.")
    parser.add_argument("--output-root", help="Directory for fp/fn review outputs.")
    parser.add_argument(
        "--split",
        default="test",
        choices=["train", "val", "test"],
        help="Dataset split to analyze.",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        help="Inference image size. Defaults to the imgsz recorded in eval report, else 640.",
    )
    parser.add_argument(
        "--conf-threshold",
        type=float,
        default=0.25,
        help="Prediction confidence threshold kept for review.",
    )
    parser.add_argument(
        "--nms-iou",
        type=float,
        default=0.7,
        help="Prediction NMS IoU threshold.",
    )
    parser.add_argument(
        "--match-iou",
        type=float,
        default=0.5,
        help="GT matching IoU threshold.",
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting an existing non-empty output directory.",
    )
    return parser.parse_args()


def load_json(path: Path) -> Dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError("Failed to read JSON: {0}".format(path)) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("Invalid JSON: {0}".format(path)) from exc
    if not isinstance(payload, dict):
        raise RuntimeError("JSON top level must be an object: {0}".format(path))
    return payload


def resolve_path(raw_value: object, base_dir: Path) -> Path:
    candidate = Path(str(raw_value)).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (base_dir / candidate).resolve()


def resolve_dataset_source(
    *,
    eval_report_path: Path,
    explicit_dataset_yaml: Optional[str],
    explicit_weights: Optional[str],
) -> Tuple[Path, Path, Dict[str, object]]:
    report_payload = load_json(eval_report_path)
    base_dir = eval_report_path.parent
    raw_dataset_yaml = explicit_dataset_yaml or report_payload.get("dataset_yaml")
    raw_weights = explicit_weights or report_payload.get("weights")
    if raw_dataset_yaml in (None, ""):
        raise RuntimeError("Unable to resolve dataset.yaml from arguments or eval report.")
    if raw_weights in (None, ""):
        raise RuntimeError("Unable to resolve weights from arguments or eval report.")
    dataset_yaml = resolve_path(raw_dataset_yaml, base_dir)
    weights = resolve_path(raw_weights, base_dir)
    return dataset_yaml, weights, report_payload


def parse_imgsz_from_eval_report(report_payload: Dict[str, object]) -> int:
    runtime = report_payload.get("runtime")
    if not isinstance(runtime, dict):
        return 640
    argv = runtime.get("argv")
    if not isinstance(argv, list):
        return 640
    for index, token in enumerate(argv[:-1]):
        if str(token) == "--imgsz":
            try:
                return int(argv[index + 1])
            except (TypeError, ValueError):
                return 640
    return 640


def sanitize_name(raw_value: str) -> str:
    safe = []
    for char in raw_value:
        if char.isalnum() or char in ("-", "_"):
            safe.append(char)
        else:
            safe.append("_")
    return "".join(safe).strip("_") or "unknown"


def run_name_from_weights(weights: Path) -> str:
    if weights.parent.name == "weights" and weights.parent.parent.name:
        return weights.parent.parent.name
    return weights.stem


def derive_default_output_root(
    *,
    weights: Path,
    split_name: str,
    conf_threshold: float,
) -> Path:
    run_name = sanitize_name(run_name_from_weights(weights))
    conf_token = str(int(round(conf_threshold * 1000.0))).zfill(4)
    return DEFAULT_OUTPUT_PARENT / "{0}_fpfn_{1}_conf{2}".format(
        run_name,
        split_name,
        conf_token,
    )


def ensure_output_root(output_root: Path, *, overwrite: bool) -> None:
    if output_root.exists():
        if not output_root.is_dir():
            raise RuntimeError("Output path exists and is not a directory: {0}".format(output_root))
        if any(output_root.iterdir()):
            if not overwrite:
                raise RuntimeError(
                    "Output directory already exists and is not empty: {0}. Pass --overwrite to replace it.".format(
                        output_root
                    )
                )
            assert_directory_within_root(output_root, PERSON_ROOT / "train-result")
            shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)


def load_dataset(
    dataset_yaml: Path,
    split_name: str,
) -> Tuple[Dict[str, object], Path, Path, Path]:
    payload = yaml.safe_load(dataset_yaml.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise RuntimeError("dataset.yaml top level must be an object: {0}".format(dataset_yaml))
    dataset_root = resolve_path(payload.get("path", "."), dataset_yaml.parent)
    raw_split = payload.get(split_name)
    if raw_split in (None, ""):
        raise RuntimeError("dataset.yaml is missing split `{0}`".format(split_name))
    image_dir = resolve_path(raw_split, dataset_root)
    label_dir = dataset_root / "labels" / split_name
    return payload, dataset_root, image_dir, label_dir


def read_image_size(image_path: Path) -> Tuple[int, int]:
    import cv2

    image = cv2.imread(str(image_path))
    if image is None:
        raise RuntimeError("Failed to read image: {0}".format(image_path))
    image_height, image_width = image.shape[:2]
    return image_width, image_height


def read_gt(label_path: Path, image_width: int, image_height: int) -> List[Dict[str, object]]:
    if not label_path.exists():
        return []
    entries: List[Dict[str, object]] = []
    for raw_line in label_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 5:
            raise RuntimeError("Invalid label line: {0} -> `{1}`".format(label_path, raw_line))
        class_id = int(parts[0])
        x_center, y_center, width, height = [float(value) for value in parts[1:]]
        x1 = (x_center - width / 2.0) * image_width
        y1 = (y_center - height / 2.0) * image_height
        x2 = (x_center + width / 2.0) * image_width
        y2 = (y_center + height / 2.0) * image_height
        entries.append(
            {
                "index": len(entries),
                "class_id": class_id,
                "xyxy": [x1, y1, x2, y2],
                "line": line,
            }
        )
    return entries


def predict(
    model: YOLO,
    image_path: Path,
    *,
    imgsz: int,
    conf_threshold: float,
    nms_iou: float,
    device: str,
) -> List[Dict[str, object]]:
    results = model.predict(
        source=str(image_path),
        imgsz=imgsz,
        conf=conf_threshold,
        iou=nms_iou,
        device=device,
        verbose=False,
        max_det=300,
    )
    if not results or results[0].boxes is None or len(results[0].boxes) == 0:
        return []
    boxes = results[0].boxes
    xyxy = boxes.xyxy.cpu()
    conf = boxes.conf.cpu()
    cls = boxes.cls.cpu()
    return [
        {
            "index": index,
            "class_id": int(cls[index].item()),
            "conf": float(conf[index].item()),
            "xyxy": [float(value) for value in xyxy[index].tolist()],
        }
        for index in range(len(boxes))
    ]


def box_iou(box_a: Sequence[float], box_b: Sequence[float]) -> float:
    inter_x1 = max(box_a[0], box_b[0])
    inter_y1 = max(box_a[1], box_b[1])
    inter_x2 = min(box_a[2], box_b[2])
    inter_y2 = min(box_a[3], box_b[3])
    inter_area = max(0.0, inter_x2 - inter_x1) * max(0.0, inter_y2 - inter_y1)
    if inter_area <= 0.0:
        return 0.0
    area_a = max(0.0, box_a[2] - box_a[0]) * max(0.0, box_a[3] - box_a[1])
    area_b = max(0.0, box_b[2] - box_b[0]) * max(0.0, box_b[3] - box_b[1])
    union = area_a + area_b - inter_area
    return inter_area / union if union > 0.0 else 0.0


def match_boxes(
    gt_entries: Sequence[Dict[str, object]],
    pred_entries: Sequence[Dict[str, object]],
    iou_threshold: float,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], List[Dict[str, object]]]:
    candidates = []
    for pred_index, pred_entry in enumerate(pred_entries):
        for gt_index, gt_entry in enumerate(gt_entries):
            if int(pred_entry["class_id"]) != int(gt_entry["class_id"]):
                continue
            iou_value = box_iou(pred_entry["xyxy"], gt_entry["xyxy"])
            if iou_value >= iou_threshold:
                candidates.append((iou_value, float(pred_entry["conf"]), pred_index, gt_index))
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)

    matched_preds = set()
    matched_gts = set()
    matches: List[Dict[str, object]] = []
    for iou_value, _, pred_index, gt_index in candidates:
        if pred_index in matched_preds or gt_index in matched_gts:
            continue
        matched_preds.add(pred_index)
        matched_gts.add(gt_index)
        matches.append(
            {
                "pred_index": pred_index,
                "gt_index": gt_index,
                "class_id": int(pred_entries[pred_index]["class_id"]),
                "iou": float(iou_value),
                "pred_conf": float(pred_entries[pred_index]["conf"]),
                "pred_xyxy": pred_entries[pred_index]["xyxy"],
                "gt_xyxy": gt_entries[gt_index]["xyxy"],
            }
        )

    unmatched_preds = [
        {
            "pred_index": int(entry["index"]),
            "class_id": int(entry["class_id"]),
            "conf": float(entry["conf"]),
            "xyxy": entry["xyxy"],
        }
        for entry in pred_entries
        if int(entry["index"]) not in matched_preds
    ]
    unmatched_gts = [
        {
            "gt_index": int(entry["index"]),
            "class_id": int(entry["class_id"]),
            "xyxy": entry["xyxy"],
            "line": str(entry["line"]),
        }
        for entry in gt_entries
        if int(entry["index"]) not in matched_gts
    ]
    return matches, unmatched_preds, unmatched_gts


def rel(path: Path, base_dir: Path) -> str:
    try:
        return str(path.resolve().relative_to(base_dir.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve())


def precision_recall(tp: int, fp: int, fn: int) -> Tuple[float, float]:
    return tp / float(max(tp + fp, 1)), tp / float(max(tp + fn, 1))


def sequence_name_from_stem(stem: str) -> str:
    marker = "_frame_"
    if marker in stem:
        return stem.split(marker, 1)[0]
    return stem


def build_original_lookup(project_config_path: Path) -> Dict[str, Dict[str, str]]:
    context = load_person_project_context(project_config_path)
    lookup: Dict[str, Dict[str, str]] = {}
    for sequence in context.sequences:
        label_lookup = {path.stem: path for path in sequence.label_root.glob("*.txt") if path.name.lower() != "classes.txt"}
        for image_path in iter_image_paths(sequence.image_root, context.image_extensions):
            if image_path.stem in lookup:
                raise RuntimeError("Duplicate image stem found in source dataset: {0}".format(image_path.stem))
            lookup[image_path.stem] = {
                "sequence_name": sequence.sequence_name,
                "source_id": sequence.source_id,
                "group": sequence.group,
                "original_image_path": str(image_path),
                "original_label_path": str(label_lookup.get(image_path.stem, "")),
            }
    return lookup


def markdown_summary(payload: Dict[str, object]) -> str:
    totals = payload["totals"]
    split_labels = {
        "train": "训练集",
        "val": "验证集",
        "test": "测试集",
    }

    def format_split_name(split_name: object) -> str:
        raw_name = str(split_name)
        return split_labels.get(raw_name, raw_name)

    lines = [
        "# 行人单帧误检 / 漏检复盘摘要",
        "",
        "- 生成时间: `{0}`".format(payload["generated_at"]),
        "- 运行名: `{0}`".format(payload["run_name"]),
        "- 权重路径: `{0}`".format(payload["weights"]),
        "- 数据集 YAML: `{0}`".format(payload["dataset_yaml"]),
        "- 数据划分: `{0}`".format(format_split_name(payload["split"])),
        "- 置信度阈值: `{0}`".format(payload["prediction"]["conf_threshold"]),
        "- NMS IoU: `{0}`".format(payload["prediction"]["nms_iou"]),
        "- 匹配 IoU: `{0}`".format(payload["matching"]["iou_threshold"]),
        "",
        "## 总体统计",
        "",
        "- 图片数: `{0}`".format(totals["images"]),
        "- GT 框数: `{0}`".format(totals["gt_boxes"]),
        "- 预测框数: `{0}`".format(totals["pred_boxes"]),
        "- 真阳性（TP）: `{0}`".format(totals["tp"]),
        "- 误检（FP）: `{0}`".format(totals["fp"]),
        "- 漏检（FN）: `{0}`".format(totals["fn"]),
        "- Precision（精确率）: `{0:.6f}`".format(float(totals["precision"])),
        "- Recall（召回率）: `{0:.6f}`".format(float(totals["recall"])),
        "- 含 FP 图片数: `{0}`".format(totals["fp_images"]),
        "- 含 FN 图片数: `{0}`".format(totals["fn_images"]),
        "",
        "## 按序列统计",
        "",
        "| 序列 | 图片数 | GT 框数 | 真阳性 | 误检 | 漏检 | 含误检图片数 | 含漏检图片数 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["per_sequence"]:
        lines.append(
            "| {sequence_name} | {images} | {gt_boxes} | {tp} | {fp} | {fn} | {fp_images} | {fn_images} |".format(
                **row
            )
        )

    lines.extend(["", "## 误检图片", ""])
    if not payload["false_positive_images"]:
        lines.append("- 无")
    else:
        for entry in payload["false_positive_images"]:
            lines.append(
                "- `{0}` | 序列 `{1}` | 误检数 `{2}` | 预测框 `{3}` | GT 框 `{4}`".format(
                    entry["prepared_image_relpath"],
                    entry.get("sequence_name") or "未知",
                    entry["fp_count"],
                    entry["pred_count"],
                    entry["gt_count"],
                )
            )

    lines.extend(["", "## 漏检图片", ""])
    if not payload["false_negative_images"]:
        lines.append("- 无")
    else:
        for entry in payload["false_negative_images"]:
            lines.append(
                "- `{0}` | 序列 `{1}` | 漏检数 `{2}` | 预测框 `{3}` | GT 框 `{4}`".format(
                    entry["prepared_image_relpath"],
                    entry.get("sequence_name") or "未知",
                    entry["fn_count"],
                    entry["pred_count"],
                    entry["gt_count"],
                )
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    project_config_path = Path(args.project_config).expanduser().resolve()
    eval_report_path = Path(args.eval_report).expanduser().resolve()
    dataset_yaml, weights, report_payload = resolve_dataset_source(
        eval_report_path=eval_report_path,
        explicit_dataset_yaml=args.dataset_yaml,
        explicit_weights=args.weights,
    )
    imgsz = args.imgsz if args.imgsz is not None else parse_imgsz_from_eval_report(report_payload)
    output_root = (
        Path(args.output_root).expanduser().resolve()
        if args.output_root
        else derive_default_output_root(
            weights=weights,
            split_name=args.split,
            conf_threshold=args.conf_threshold,
        ).resolve()
    )
    ensure_output_root(output_root, overwrite=args.overwrite)

    _, dataset_root, image_dir, label_dir = load_dataset(dataset_yaml, args.split)
    image_paths = sorted(
        path
        for path in image_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )
    if not image_paths:
        raise RuntimeError("No images found for split `{0}` in {1}".format(args.split, image_dir))

    model = YOLO(str(weights))
    original_lookup = build_original_lookup(project_config_path)

    all_images: List[Dict[str, object]] = []
    false_positive_images: List[Dict[str, object]] = []
    false_negative_images: List[Dict[str, object]] = []
    per_sequence = defaultdict(
        lambda: {
            "sequence_name": "",
            "images": 0,
            "gt_boxes": 0,
            "pred_boxes": 0,
            "tp": 0,
            "fp": 0,
            "fn": 0,
            "fp_images": 0,
            "fn_images": 0,
        }
    )
    total_gt = 0
    total_pred = 0
    total_tp = 0
    total_fp = 0
    total_fn = 0

    for image_path in image_paths:
        image_width, image_height = read_image_size(image_path)
        label_path = label_dir / "{0}.txt".format(image_path.stem)
        gt_entries = read_gt(label_path, image_width, image_height)
        pred_entries = predict(
            model,
            image_path,
            imgsz=imgsz,
            conf_threshold=args.conf_threshold,
            nms_iou=args.nms_iou,
            device=args.device,
        )
        matches, unmatched_preds, unmatched_gts = match_boxes(
            gt_entries,
            pred_entries,
            args.match_iou,
        )

        original_info = original_lookup.get(image_path.stem, {})
        sequence_name = str(original_info.get("sequence_name") or sequence_name_from_stem(image_path.stem))
        entry = {
            "prepared_image_path": str(image_path),
            "prepared_image_relpath": rel(image_path, dataset_root),
            "prepared_label_path": str(label_path),
            "prepared_label_relpath": rel(label_path, dataset_root),
            "original_image_path": str(original_info.get("original_image_path") or ""),
            "original_label_path": str(original_info.get("original_label_path") or ""),
            "source_id": str(original_info.get("source_id") or ""),
            "group": str(original_info.get("group") or ""),
            "sequence_name": sequence_name,
            "stem": image_path.stem,
            "image_width": image_width,
            "image_height": image_height,
            "gt_count": len(gt_entries),
            "pred_count": len(pred_entries),
            "tp_count": len(matches),
            "fp_count": len(unmatched_preds),
            "fn_count": len(unmatched_gts),
            "matched_pairs": matches,
            "unmatched_predictions": unmatched_preds,
            "unmatched_gt": unmatched_gts,
        }
        all_images.append(entry)

        total_gt += len(gt_entries)
        total_pred += len(pred_entries)
        total_tp += len(matches)
        total_fp += len(unmatched_preds)
        total_fn += len(unmatched_gts)

        bucket = per_sequence[sequence_name]
        bucket["sequence_name"] = sequence_name
        bucket["images"] += 1
        bucket["gt_boxes"] += len(gt_entries)
        bucket["pred_boxes"] += len(pred_entries)
        bucket["tp"] += len(matches)
        bucket["fp"] += len(unmatched_preds)
        bucket["fn"] += len(unmatched_gts)
        if unmatched_preds:
            bucket["fp_images"] += 1
            false_positive_images.append(entry)
        if unmatched_gts:
            bucket["fn_images"] += 1
            false_negative_images.append(entry)

    precision, recall = precision_recall(total_tp, total_fp, total_fn)
    false_positive_images.sort(key=lambda item: (-int(item["fp_count"]), item["prepared_image_relpath"]))
    false_negative_images.sort(key=lambda item: (-int(item["fn_count"]), item["prepared_image_relpath"]))
    per_sequence_rows = sorted(
        per_sequence.values(),
        key=lambda item: (
            -int(item["fp"] + item["fn"]),
            -int(item["images"]),
            str(item["sequence_name"]),
        ),
    )

    run_name = run_name_from_weights(weights)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_config": str(project_config_path),
        "eval_report": str(eval_report_path),
        "run_name": run_name,
        "weights": str(weights),
        "dataset_yaml": str(dataset_yaml),
        "dataset_root": str(dataset_root),
        "split": args.split,
        "prediction": {
            "imgsz": imgsz,
            "conf_threshold": args.conf_threshold,
            "nms_iou": args.nms_iou,
            "device": args.device,
        },
        "matching": {"iou_threshold": args.match_iou},
        "totals": {
            "images": len(all_images),
            "gt_boxes": total_gt,
            "pred_boxes": total_pred,
            "tp": total_tp,
            "fp": total_fp,
            "fn": total_fn,
            "precision": precision,
            "recall": recall,
            "fp_images": len(false_positive_images),
            "fn_images": len(false_negative_images),
        },
        "per_sequence": per_sequence_rows,
        "false_positive_images": false_positive_images,
        "false_negative_images": false_negative_images,
        "all_images": all_images,
    }

    output_json = output_root / "fpfn_per_image.json"
    output_md = output_root / "fpfn_summary.md"
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(markdown_summary(payload), encoding="utf-8")

    print("output_root  : {0}".format(output_root))
    print("output_json  : {0}".format(output_json))
    print("output_md    : {0}".format(output_md))
    print(
        "images={0}, gt={1}, pred={2}, tp={3}, fp={4}, fn={5}, precision={6:.6f}, recall={7:.6f}".format(
            len(all_images),
            total_gt,
            total_pred,
            total_tp,
            total_fp,
            total_fn,
            precision,
            recall,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

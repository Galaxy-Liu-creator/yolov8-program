from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import yaml
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parent
BASELINE_JSON = ROOT / "00_CURRENT_BASELINE" / "current_clothes_fullframe_baseline.json"
OUTPUT_JSON = ROOT / "00_CURRENT_BASELINE" / "baseline_fpfn_per_image.json"
OUTPUT_MD = ROOT / "00_CURRENT_BASELINE" / "baseline_fpfn_summary.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成 baseline 单帧 GT 对照误报 / 漏报清单。")
    parser.add_argument("--baseline-json", default=str(BASELINE_JSON))
    parser.add_argument("--output-json", default=str(OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(OUTPUT_MD))
    parser.add_argument("--split", default="test")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--conf-threshold", type=float, default=0.45)
    parser.add_argument("--nms-iou", type=float, default=0.7)
    parser.add_argument("--match-iou", type=float, default=0.5)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError("读取 JSON 失败: {0}".format(path)) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("JSON 格式无效: {0}".format(path)) from exc
    if not isinstance(payload, dict):
        raise RuntimeError("JSON 顶层必须是对象: {0}".format(path))
    return payload


def resolve_path(raw_value: object, base_dir: Path) -> Path:
    candidate = Path(str(raw_value)).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (base_dir / candidate).resolve()


def load_dataset(dataset_yaml: Path, split_name: str) -> tuple[dict, Path, Path, Path]:
    payload = yaml.safe_load(dataset_yaml.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise RuntimeError("dataset.yaml 顶层必须是对象: {0}".format(dataset_yaml))
    dataset_root = resolve_path(payload.get("path", "."), dataset_yaml.parent)
    raw_split = payload.get(split_name)
    if raw_split in (None, ""):
        raise RuntimeError("dataset.yaml 缺少 split: {0}".format(split_name))
    image_dir = resolve_path(raw_split, dataset_root)
    label_dir = dataset_root / "labels" / split_name
    return payload, dataset_root, image_dir, label_dir


def load_manifest(manifest_path: Path) -> dict[str, dict[str, str]]:
    if not manifest_path.exists():
        return {}
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return {
            str(row.get("merged_stem")): dict(row)
            for row in reader
            if str(row.get("merged_stem") or "").strip()
        }


def read_image_size(image_path: Path, manifest_row: dict[str, str]) -> tuple[int, int]:
    width = int(manifest_row.get("image_width") or 0)
    height = int(manifest_row.get("image_height") or 0)
    if width > 0 and height > 0:
        return width, height
    import cv2

    image = cv2.imread(str(image_path))
    if image is None:
        raise RuntimeError("读取图片失败: {0}".format(image_path))
    height, width = image.shape[:2]
    return width, height


def read_gt(label_path: Path, image_width: int, image_height: int) -> list[dict]:
    if not label_path.exists():
        return []
    entries = []
    for raw_line in label_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 5:
            raise RuntimeError("标签行格式无效: {0} -> `{1}`".format(label_path, raw_line))
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


def predict(model: YOLO, image_path: Path, args: argparse.Namespace) -> list[dict]:
    results = model.predict(
        source=str(image_path),
        imgsz=args.imgsz,
        conf=args.conf_threshold,
        iou=args.nms_iou,
        device=args.device,
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


def box_iou(box_a: list[float], box_b: list[float]) -> float:
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


def match_boxes(gt_entries: list[dict], pred_entries: list[dict], iou_threshold: float) -> tuple[list, list, list]:
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
    matches = []
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


def precision_recall(tp: int, fp: int, fn: int) -> tuple[float, float]:
    return tp / float(max(tp + fp, 1)), tp / float(max(tp + fn, 1))


def markdown_summary(payload: dict) -> str:
    totals = payload["totals"]
    lines = [
        "# Baseline FP/FN Summary",
        "",
        "- 生成时间：`{0}`".format(payload["generated_at"]),
        "- baseline：`{0}`".format(payload["baseline_name"]),
        "- 权重：`{0}`".format(payload["weights"]),
        "- 数据集：`{0}`".format(payload["dataset_yaml"]),
        "- split：`{0}`".format(payload["split"]),
        "- 预测保留阈值：`{0}`".format(payload["prediction"]["conf_threshold"]),
        "- GT 匹配 IoU：`{0}`".format(payload["matching"]["iou_threshold"]),
        "",
        "## 总体统计",
        "",
        "- 图片数：`{0}`".format(totals["images"]),
        "- GT 框数：`{0}`".format(totals["gt_boxes"]),
        "- 预测框数：`{0}`".format(totals["pred_boxes"]),
        "- TP：`{0}`".format(totals["tp"]),
        "- FP：`{0}`".format(totals["fp"]),
        "- FN：`{0}`".format(totals["fn"]),
        "- Precision：`{0:.6f}`".format(float(totals["precision"])),
        "- Recall：`{0:.6f}`".format(float(totals["recall"])),
        "- 有误报图片数：`{0}`".format(totals["fp_images"]),
        "- 有漏报图片数：`{0}`".format(totals["fn_images"]),
        "",
        "## 按序列统计",
        "",
        "| sequence | images | gt_boxes | tp | fp | fn | fp_images | fn_images |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["per_sequence"]:
        lines.append(
            "| {sequence_name} | {images} | {gt_boxes} | {tp} | {fp} | {fn} | {fp_images} | {fn_images} |".format(
                **row
            )
        )

    lines.extend(["", "## 误报图片", ""])
    if not payload["false_positive_images"]:
        lines.append("- 无逐图误报。")
    else:
        for entry in payload["false_positive_images"]:
            lines.append(
                "- `{0}` | sequence `{1}` | fp `{2}` | pred `{3}` | gt `{4}`".format(
                    entry["image_relpath"],
                    entry.get("sequence_name") or "unknown",
                    entry["fp_count"],
                    entry["pred_count"],
                    entry["gt_count"],
                )
            )

    lines.extend(["", "## 漏报图片", ""])
    if not payload["false_negative_images"]:
        lines.append("- 无逐图漏报。")
    else:
        for entry in payload["false_negative_images"]:
            lines.append(
                "- `{0}` | sequence `{1}` | fn `{2}` | pred `{3}` | gt `{4}`".format(
                    entry["image_relpath"],
                    entry.get("sequence_name") or "unknown",
                    entry["fn_count"],
                    entry["pred_count"],
                    entry["gt_count"],
                )
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    baseline_json = Path(args.baseline_json).expanduser().resolve()
    output_json = Path(args.output_json).expanduser().resolve()
    output_md = Path(args.output_md).expanduser().resolve()

    baseline_payload = load_json(baseline_json)
    selected_run = baseline_payload.get("selected_run")
    comparison_dataset = baseline_payload.get("comparison_dataset")
    if not isinstance(selected_run, dict) or not isinstance(comparison_dataset, dict):
        raise RuntimeError("baseline JSON 缺少 selected_run 或 comparison_dataset。")

    base_dir = ROOT.parent.parent
    weight_path = resolve_path(selected_run.get("weight"), base_dir)
    dataset_yaml = resolve_path(comparison_dataset.get("dataset_yaml"), base_dir)
    _, dataset_root, image_dir, label_dir = load_dataset(dataset_yaml, args.split)
    manifest = load_manifest(dataset_yaml.parent / "manifest.csv")
    image_paths = sorted(
        path
        for path in image_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )
    if not image_paths:
        raise RuntimeError("未找到待分析图片: {0}".format(image_dir))

    model = YOLO(str(weight_path))
    all_images = []
    false_positive_images = []
    false_negative_images = []
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
    total_gt = total_pred = total_tp = total_fp = total_fn = 0

    for image_path in image_paths:
        manifest_row = manifest.get(image_path.stem, {})
        image_width, image_height = read_image_size(image_path, manifest_row)
        label_path = label_dir / "{0}.txt".format(image_path.stem)
        gt_entries = read_gt(label_path, image_width, image_height)
        pred_entries = predict(model, image_path, args)
        matches, unmatched_preds, unmatched_gts = match_boxes(
            gt_entries,
            pred_entries,
            args.match_iou,
        )

        sequence_name = str(manifest_row.get("sequence_name") or image_path.stem)
        entry = {
            "image_path": str(image_path),
            "image_relpath": rel(image_path, dataset_yaml.parent),
            "label_path": str(label_path),
            "label_relpath": rel(label_path, dataset_yaml.parent),
            "source_id": str(manifest_row.get("source_id") or ""),
            "sequence_name": sequence_name,
            "merged_stem": image_path.stem,
            "original_stem": str(manifest_row.get("original_stem") or image_path.stem),
            "original_image_path": str(manifest_row.get("original_image_path") or image_path),
            "original_label_path": str(manifest_row.get("label_source_path") or label_path),
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
    false_positive_images.sort(key=lambda item: (-int(item["fp_count"]), item["image_relpath"]))
    false_negative_images.sort(key=lambda item: (-int(item["fn_count"]), item["image_relpath"]))
    per_sequence_rows = sorted(
        per_sequence.values(),
        key=lambda item: (
            -int(item["fp"] + item["fn"]),
            -int(item["images"]),
            str(item["sequence_name"]),
        ),
    )
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "baseline_json": str(baseline_json),
        "baseline_name": str(selected_run.get("name") or "unknown"),
        "weights": str(weight_path),
        "dataset_yaml": str(dataset_yaml),
        "dataset_root": str(dataset_root),
        "split": args.split,
        "prediction": {
            "imgsz": args.imgsz,
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

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(markdown_summary(payload), encoding="utf-8")
    print("输出 JSON : {0}".format(output_json))
    print("输出 Markdown : {0}".format(output_md))
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

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import cv2
import yaml
from ultralytics import YOLO


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


@dataclass
class LabelEntry:
    class_id: int
    x_center: float
    y_center: float
    width: float
    height: float


@dataclass
class SourceSample:
    split_name: str
    image_path: Path
    label_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a personcrop clothes dataset from an existing YOLO dataset.yaml.",
        allow_abbrev=False,
    )
    parser.add_argument("--source-dataset-yaml", required=True, help="Source YOLO dataset.yaml path.")
    parser.add_argument("--person-model", required=True, help="Person detector weights path.")
    parser.add_argument("--output-root", required=True, help="Prepared dataset output root.")
    parser.add_argument("--person-conf", type=float, default=0.20)
    parser.add_argument("--person-imgsz", type=int, default=640)
    parser.add_argument("--assignment-min-ioa", type=float, default=0.35)
    parser.add_argument(
        "--monitored-person-labels",
        nargs="+",
        default=["person"],
        help="Person labels kept from the upstream person detector.",
    )
    parser.add_argument("--include-empty-person-crops", action="store_true")
    parser.add_argument(
        "--no-fallback-to-fullframe",
        action="store_true",
        help="Disable fallback fullframe sample when clothes boxes cannot be assigned.",
    )
    parser.add_argument("--device", default=None, help="Optional device passed to Ultralytics, e.g. 0 or cpu.")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def ensure_output_root(output_root: Path, overwrite: bool) -> None:
    if output_root.exists():
        if not overwrite:
            raise RuntimeError(f"Output root already exists: {output_root}")
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)


def load_dataset_yaml(dataset_yaml_path: Path) -> Dict[str, object]:
    payload = yaml.safe_load(dataset_yaml_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise RuntimeError(f"Invalid dataset yaml payload: {dataset_yaml_path}")
    return payload


def resolve_dataset_base_dir(dataset_yaml_path: Path, payload: Dict[str, object]) -> Path:
    base_dir = dataset_yaml_path.parent.resolve()
    raw_path = str(payload.get("path", "")).strip()
    if not raw_path:
        return base_dir
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate.resolve()
    return (base_dir / candidate).resolve()


def resolve_split_image_dir(dataset_yaml_path: Path, payload: Dict[str, object], split_name: str) -> Path:
    raw_value = str(payload.get(split_name, "")).strip()
    if not raw_value:
        raise RuntimeError(f"Missing '{split_name}' in dataset yaml: {dataset_yaml_path}")
    base_dir = resolve_dataset_base_dir(dataset_yaml_path, payload)
    candidate = Path(raw_value)
    if candidate.is_absolute():
        return candidate.resolve()

    primary = (base_dir / candidate).resolve()
    if primary.exists():
        return primary

    # Some historical dataset.yaml files keep an outdated absolute `path:` field.
    # Fall back to resolving split dirs from the yaml's own location when needed.
    fallback = (dataset_yaml_path.parent.resolve() / candidate).resolve()
    if fallback.exists():
        return fallback

    return primary


def normalize_class_names(raw_value: object) -> Dict[int, str]:
    if isinstance(raw_value, dict):
        items = raw_value.items()
    elif isinstance(raw_value, list):
        items = enumerate(raw_value)
    else:
        raise RuntimeError("dataset yaml names must be a dict or list")

    normalized: Dict[int, str] = {}
    for raw_key, raw_name in items:
        normalized[int(raw_key)] = str(raw_name)
    return dict(sorted(normalized.items()))


def split_label_dir_from_image_dir(image_dir: Path) -> Path:
    split_name = image_dir.name
    parent = image_dir.parent
    if parent.name != "images":
        raise RuntimeError(f"Expected image dir under images/<split>, got: {image_dir}")
    return parent.parent / "labels" / split_name


def iter_source_samples(image_dir: Path, label_dir: Path, split_name: str) -> List[SourceSample]:
    samples: List[SourceSample] = []
    for image_path in sorted(path for path in image_dir.rglob("*") if path.suffix.lower() in IMAGE_EXTENSIONS):
        relative_path = image_path.relative_to(image_dir)
        label_path = label_dir / relative_path.with_suffix(".txt")
        if not label_path.exists():
            raise RuntimeError(f"Missing label for image: {image_path}")
        samples.append(SourceSample(split_name=split_name, image_path=image_path, label_path=label_path))
    return samples


def read_label_entries(label_path: Path) -> List[LabelEntry]:
    text = label_path.read_text(encoding="utf-8").strip()
    if not text:
        return []

    entries: List[LabelEntry] = []
    for line in text.splitlines():
        parts = line.strip().split()
        if len(parts) != 5:
            raise RuntimeError(f"Invalid label line in {label_path}: {line}")
        entries.append(
            LabelEntry(
                class_id=int(parts[0]),
                x_center=float(parts[1]),
                y_center=float(parts[2]),
                width=float(parts[3]),
                height=float(parts[4]),
            )
        )
    return entries


def write_label_entries(label_path: Path, entries: Sequence[LabelEntry]) -> None:
    label_path.parent.mkdir(parents=True, exist_ok=True)
    if not entries:
        label_path.write_text("", encoding="utf-8")
        return
    lines = [
        f"{entry.class_id} {entry.x_center:.6f} {entry.y_center:.6f} {entry.width:.6f} {entry.height:.6f}"
        for entry in entries
    ]
    label_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def clip_xyxy(box: Tuple[float, float, float, float], width: int, height: int) -> Tuple[float, float, float, float]:
    x1, y1, x2, y2 = box
    x1 = max(0.0, min(float(width), x1))
    y1 = max(0.0, min(float(height), y1))
    x2 = max(0.0, min(float(width), x2))
    y2 = max(0.0, min(float(height), y2))
    return x1, y1, x2, y2


def yolo_to_xyxy(entry: LabelEntry, image_width: int, image_height: int) -> Tuple[float, float, float, float]:
    box_width = entry.width * image_width
    box_height = entry.height * image_height
    center_x = entry.x_center * image_width
    center_y = entry.y_center * image_height
    x1 = center_x - box_width / 2.0
    y1 = center_y - box_height / 2.0
    x2 = center_x + box_width / 2.0
    y2 = center_y + box_height / 2.0
    return clip_xyxy((x1, y1, x2, y2), image_width, image_height)


def xyxy_to_yolo(box: Tuple[float, float, float, float], crop_width: int, crop_height: int, class_id: int) -> LabelEntry:
    x1, y1, x2, y2 = box
    box_width = x2 - x1
    box_height = y2 - y1
    center_x = x1 + box_width / 2.0
    center_y = y1 + box_height / 2.0
    return LabelEntry(
        class_id=class_id,
        x_center=center_x / crop_width,
        y_center=center_y / crop_height,
        width=box_width / crop_width,
        height=box_height / crop_height,
    )


def intersection_area(a: Tuple[float, float, float, float], b: Tuple[float, float, float, float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    return inter_w * inter_h


def box_area(box: Tuple[float, float, float, float]) -> float:
    x1, y1, x2, y2 = box
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def ioa(source_box: Tuple[float, float, float, float], target_box: Tuple[float, float, float, float]) -> float:
    denom = box_area(source_box)
    if denom <= 0.0:
        return 0.0
    return intersection_area(source_box, target_box) / denom


def detect_person_boxes(
    person_model: YOLO,
    image,
    confidence_threshold: float,
    imgsz: int,
    monitored_labels: Sequence[str],
    device: Optional[str],
) -> List[Tuple[float, float, float, float]]:
    predict_kwargs = {
        "source": image,
        "conf": confidence_threshold,
        "imgsz": imgsz,
        "verbose": False,
    }
    if device not in (None, ""):
        predict_kwargs["device"] = device

    results = person_model.predict(**predict_kwargs)
    if not results:
        return []

    result = results[0]
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return []

    name_map = result.names if hasattr(result, "names") else getattr(person_model, "names", {})
    monitored = {label.strip() for label in monitored_labels if label.strip()}

    detected: List[Tuple[float, float, float, float]] = []
    image_height, image_width = image.shape[:2]
    for box in boxes:
        class_id = int(box.cls.item())
        class_name = str(name_map.get(class_id, class_id))
        if monitored and class_name not in monitored:
            continue
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        clipped = clip_xyxy((x1, y1, x2, y2), image_width, image_height)
        if box_area(clipped) <= 1.0:
            continue
        detected.append(clipped)
    return detected


def assign_boxes_to_persons(
    person_detections: Sequence[Tuple[float, float, float, float]],
    gt_items: Sequence[Tuple[LabelEntry, Tuple[float, float, float, float]]],
    assignment_min_ioa: float,
) -> Tuple[Dict[int, List[Tuple[LabelEntry, Tuple[float, float, float, float]]]], List[Tuple[LabelEntry, Tuple[float, float, float, float]]]]:
    assignments: Dict[int, List[Tuple[LabelEntry, Tuple[float, float, float, float]]]] = {
        index: [] for index in range(len(person_detections))
    }
    unmatched: List[Tuple[LabelEntry, Tuple[float, float, float, float]]] = []

    for gt_item in gt_items:
        _, gt_box = gt_item
        best_index: Optional[int] = None
        best_score = 0.0
        for index, person_box in enumerate(person_detections):
            score = ioa(gt_box, person_box)
            if score > best_score:
                best_score = score
                best_index = index
        if best_index is None or best_score < assignment_min_ioa:
            unmatched.append(gt_item)
            continue
        assignments[best_index].append(gt_item)

    return assignments, unmatched


def crop_person_sample(
    image,
    person_box: Tuple[float, float, float, float],
    assigned_boxes: Sequence[Tuple[LabelEntry, Tuple[float, float, float, float]]],
) -> Tuple[object, List[LabelEntry]]:
    x1, y1, x2, y2 = person_box
    crop_x1 = int(max(0, round(x1)))
    crop_y1 = int(max(0, round(y1)))
    crop_x2 = int(max(crop_x1 + 1, round(x2)))
    crop_y2 = int(max(crop_y1 + 1, round(y2)))
    crop_image = image[crop_y1:crop_y2, crop_x1:crop_x2].copy()
    crop_height, crop_width = crop_image.shape[:2]

    local_entries: List[LabelEntry] = []
    for entry, gt_box in assigned_boxes:
        gt_x1, gt_y1, gt_x2, gt_y2 = gt_box
        local_box = (
            max(0.0, gt_x1 - crop_x1),
            max(0.0, gt_y1 - crop_y1),
            min(float(crop_width), gt_x2 - crop_x1),
            min(float(crop_height), gt_y2 - crop_y1),
        )
        if box_area(local_box) <= 1.0:
            continue
        local_entries.append(xyxy_to_yolo(local_box, crop_width, crop_height, entry.class_id))

    return crop_image, local_entries


def build_output_stem(stem: str, suffix: str) -> str:
    return f"{stem}__{suffix}"


def copy_fallback_sample(
    sample: SourceSample,
    split_image_dir: Path,
    split_label_dir: Path,
    gt_entries: Sequence[LabelEntry],
) -> Tuple[Path, Path]:
    output_image_path = split_image_dir / f"{build_output_stem(sample.image_path.stem, 'fb')}{sample.image_path.suffix.lower()}"
    output_label_path = split_label_dir / f"{build_output_stem(sample.label_path.stem, 'fb')}.txt"
    shutil.copy2(sample.image_path, output_image_path)
    write_label_entries(output_label_path, gt_entries)
    return output_image_path, output_label_path


def write_dataset_yaml(output_root: Path, class_names: Dict[int, str]) -> Path:
    payload = {
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": class_names,
    }
    dataset_yaml_path = output_root / "dataset.yaml"
    dataset_yaml_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=False), encoding="utf-8")
    return dataset_yaml_path


def collect_source_samples(dataset_yaml_path: Path) -> Tuple[Dict[int, str], Dict[str, List[SourceSample]], Dict[str, Dict[str, int]]]:
    payload = load_dataset_yaml(dataset_yaml_path)
    class_names = normalize_class_names(payload.get("names", {0: "clothes"}))

    split_map: Dict[str, List[SourceSample]] = {}
    source_counts = {
        "image_counts": {"train": 0, "val": 0, "test": 0},
        "label_counts": {"train": 0, "val": 0, "test": 0},
        "box_counts": {"train": 0, "val": 0, "test": 0},
    }

    for split_name in ("train", "val", "test"):
        image_dir = resolve_split_image_dir(dataset_yaml_path, payload, split_name)
        label_dir = split_label_dir_from_image_dir(image_dir)
        samples = iter_source_samples(image_dir, label_dir, split_name)
        split_map[split_name] = samples
        source_counts["image_counts"][split_name] = len(samples)
        source_counts["label_counts"][split_name] = len(samples)
        source_counts["box_counts"][split_name] = sum(len(read_label_entries(sample.label_path)) for sample in samples)

    return class_names, split_map, source_counts


def build_prepare_report(
    args: argparse.Namespace,
    source_dataset_yaml: Path,
    source_counts: Dict[str, Dict[str, int]],
    output_root: Path,
    dataset_yaml_path: Path,
    split_image_counts: Dict[str, int],
    split_label_counts: Dict[str, int],
    split_box_counts: Dict[str, int],
    positive_crops: int,
    negative_crops: int,
    fallback_fullframes: int,
    unmatched_boxes: int,
    images_without_person_detection: int,
) -> Dict[str, object]:
    return {
        "runtime": {
            "command": "prepare_personcrop_from_dataset_yaml",
            "argv": list(__import__("sys").argv[1:]),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        },
        "source_dataset": {
            "dataset_yaml": str(source_dataset_yaml.resolve()),
            "split_image_counts": source_counts["image_counts"],
            "split_label_counts": source_counts["label_counts"],
            "split_box_counts": source_counts["box_counts"],
            "total_images": sum(source_counts["image_counts"].values()),
            "total_labels": sum(source_counts["label_counts"].values()),
            "total_boxes": sum(source_counts["box_counts"].values()),
        },
        "prepare_request": {
            "output_root": str(output_root.resolve()),
            "person_model": str(Path(args.person_model).resolve()),
            "person_conf": args.person_conf,
            "person_imgsz": args.person_imgsz,
            "assignment_min_ioa": args.assignment_min_ioa,
            "monitored_person_labels": list(args.monitored_person_labels),
            "include_empty_person_crops": bool(args.include_empty_person_crops),
            "fallback_to_fullframe": not bool(args.no_fallback_to_fullframe),
            "device": args.device,
        },
        "prepare": {
            "mode": "personcrop",
            "source_split_strategy": "preserve_existing_split",
            "dataset_root": str(output_root.resolve()),
            "dataset_yaml": str(dataset_yaml_path.resolve()),
            "split_image_counts": split_image_counts,
            "split_label_counts": split_label_counts,
            "split_box_counts": split_box_counts,
            "positive_crops": positive_crops,
            "negative_crops": negative_crops,
            "fallback_fullframes": fallback_fullframes,
            "unmatched_boxes": unmatched_boxes,
            "images_without_person_detection": images_without_person_detection,
            "report_path": str((output_root / 'prepare_report.json').resolve()),
        },
    }


def main() -> None:
    args = parse_args()
    source_dataset_yaml = Path(args.source_dataset_yaml).resolve()
    output_root = Path(args.output_root).resolve()
    ensure_output_root(output_root, overwrite=bool(args.overwrite))

    class_names, split_map, source_counts = collect_source_samples(source_dataset_yaml)

    person_model = YOLO(str(Path(args.person_model).resolve()))
    monitored_person_labels = [label.strip() for label in args.monitored_person_labels if label.strip()]
    fallback_to_fullframe = not bool(args.no_fallback_to_fullframe)

    split_image_counts = {"train": 0, "val": 0, "test": 0}
    split_label_counts = {"train": 0, "val": 0, "test": 0}
    split_box_counts = {"train": 0, "val": 0, "test": 0}
    positive_crops = 0
    negative_crops = 0
    fallback_fullframes = 0
    unmatched_boxes = 0
    images_without_person_detection = 0

    for split_name, samples in split_map.items():
        split_image_dir = output_root / "images" / split_name
        split_label_dir = output_root / "labels" / split_name
        split_image_dir.mkdir(parents=True, exist_ok=True)
        split_label_dir.mkdir(parents=True, exist_ok=True)

        for sample in samples:
            image = cv2.imread(str(sample.image_path))
            if image is None:
                raise RuntimeError(f"Failed to read image: {sample.image_path}")

            image_height, image_width = image.shape[:2]
            gt_entries = read_label_entries(sample.label_path)
            gt_items = [(entry, yolo_to_xyxy(entry, image_width, image_height)) for entry in gt_entries]

            person_detections = detect_person_boxes(
                person_model=person_model,
                image=image,
                confidence_threshold=args.person_conf,
                imgsz=args.person_imgsz,
                monitored_labels=monitored_person_labels,
                device=args.device,
            )
            if not person_detections:
                images_without_person_detection += 1

            assignments, unmatched = assign_boxes_to_persons(
                person_detections=person_detections,
                gt_items=gt_items,
                assignment_min_ioa=args.assignment_min_ioa,
            )

            for person_index, person_box in enumerate(person_detections):
                assigned_boxes = assignments.get(person_index, [])
                if not assigned_boxes and not args.include_empty_person_crops:
                    continue

                crop_image, local_entries = crop_person_sample(
                    image=image,
                    person_box=person_box,
                    assigned_boxes=assigned_boxes,
                )
                if not local_entries and not args.include_empty_person_crops:
                    continue

                output_stem = build_output_stem(sample.image_path.stem, f"pc_{person_index:02d}")
                output_image_path = split_image_dir / f"{output_stem}{sample.image_path.suffix.lower()}"
                output_label_path = split_label_dir / f"{output_stem}.txt"
                cv2.imwrite(str(output_image_path), crop_image)
                write_label_entries(output_label_path, local_entries)

                split_image_counts[split_name] += 1
                split_label_counts[split_name] += 1
                split_box_counts[split_name] += len(local_entries)
                if local_entries:
                    positive_crops += 1
                else:
                    negative_crops += 1

            unmatched_boxes += len(unmatched)
            if unmatched and fallback_to_fullframe:
                copy_fallback_sample(sample, split_image_dir, split_label_dir, gt_entries)
                split_image_counts[split_name] += 1
                split_label_counts[split_name] += 1
                split_box_counts[split_name] += len(gt_entries)
                fallback_fullframes += 1

    dataset_yaml_path = write_dataset_yaml(output_root, class_names)
    report = build_prepare_report(
        args=args,
        source_dataset_yaml=source_dataset_yaml,
        source_counts=source_counts,
        output_root=output_root,
        dataset_yaml_path=dataset_yaml_path,
        split_image_counts=split_image_counts,
        split_label_counts=split_label_counts,
        split_box_counts=split_box_counts,
        positive_crops=positive_crops,
        negative_crops=negative_crops,
        fallback_fullframes=fallback_fullframes,
        unmatched_boxes=unmatched_boxes,
        images_without_person_detection=images_without_person_detection,
    )
    report_path = output_root / "prepare_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["prepare"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

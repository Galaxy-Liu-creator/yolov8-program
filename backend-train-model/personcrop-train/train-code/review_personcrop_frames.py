from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import cv2
import yaml
from ultralytics import YOLO


BOX_COLOR_FULLFRAME = (0, 200, 0)
BOX_COLOR_PERSON = (0, 215, 255)
BOX_COLOR_CLOTHES = (0, 0, 255)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Review representative personcrop frames with fullframe/A/B pipelines.",
        allow_abbrev=False,
    )
    parser.add_argument("--source-dataset-yaml", required=True)
    parser.add_argument("--fullframe-weights", required=True)
    parser.add_argument("--person-model-a", required=True)
    parser.add_argument("--person-model-b", required=True)
    parser.add_argument("--clothes-model-a", required=True)
    parser.add_argument("--clothes-model-b", required=True)
    parser.add_argument("--prepared-a", required=True)
    parser.add_argument("--prepared-b", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--frame-stems", nargs="+", required=True)
    parser.add_argument("--person-conf", type=float, default=0.20)
    parser.add_argument("--person-imgsz", type=int, default=640)
    parser.add_argument("--clothes-conf", type=float, default=0.25)
    parser.add_argument("--clothes-imgsz", type=int, default=640)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


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

    fallback = (dataset_yaml_path.parent.resolve() / candidate).resolve()
    if fallback.exists():
        return fallback
    return primary


def index_source_images(dataset_yaml_path: Path) -> Dict[str, Tuple[str, Path]]:
    payload = load_dataset_yaml(dataset_yaml_path)
    mapping: Dict[str, Tuple[str, Path]] = {}
    for split_name in ("train", "val", "test"):
        image_dir = resolve_split_image_dir(dataset_yaml_path, payload, split_name)
        for image_path in sorted(image_dir.glob("*.jpg")):
            mapping[image_path.stem] = (split_name, image_path)
    return mapping


def collect_prepared_counts(prepared_root: Path) -> Dict[str, Dict[str, int]]:
    counts: Dict[str, Dict[str, int]] = {}
    for split_name in ("train", "val", "test"):
        image_dir = prepared_root / "images" / split_name
        if not image_dir.exists():
            continue
        for image_path in sorted(image_dir.glob("*.jpg")):
            stem = image_path.stem
            if stem.endswith("__fb"):
                original_stem = stem[:-4]
                bucket = counts.setdefault(original_stem, {"crop": 0, "fallback": 0})
                bucket["fallback"] += 1
            elif "__pc_" in stem:
                original_stem = stem.split("__pc_", 1)[0]
                bucket = counts.setdefault(original_stem, {"crop": 0, "fallback": 0})
                bucket["crop"] += 1
    return counts


def clip_box(box: Sequence[float], width: int, height: int) -> Tuple[int, int, int, int]:
    x1, y1, x2, y2 = box
    left = max(0, min(width - 1, int(round(x1))))
    top = max(0, min(height - 1, int(round(y1))))
    right = max(left + 1, min(width, int(round(x2))))
    bottom = max(top + 1, min(height, int(round(y2))))
    return left, top, right, bottom


def run_model_boxes(
    model: YOLO,
    image,
    imgsz: int,
    conf: float,
    device: Optional[str],
    allowed_names: Optional[Sequence[str]] = None,
) -> List[Tuple[Tuple[int, int, int, int], float, str]]:
    predict_kwargs = {
        "source": image,
        "imgsz": imgsz,
        "conf": conf,
        "verbose": False,
    }
    if device not in (None, ""):
        predict_kwargs["device"] = device

    results = model.predict(**predict_kwargs)
    if not results:
        return []

    result = results[0]
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return []

    names_map = result.names if hasattr(result, "names") else getattr(model, "names", {})
    allowed = {name.strip() for name in allowed_names or [] if str(name).strip()}
    image_height, image_width = image.shape[:2]
    output: List[Tuple[Tuple[int, int, int, int], float, str]] = []
    for box in boxes:
        cls_id = int(box.cls.item())
        cls_name = str(names_map.get(cls_id, cls_id))
        if allowed and cls_name not in allowed:
            continue
        xyxy = clip_box(box.xyxy[0].tolist(), image_width, image_height)
        conf_value = float(box.conf.item()) if getattr(box, "conf", None) is not None else 0.0
        output.append((xyxy, conf_value, cls_name))
    return output


def run_personcrop_pipeline(
    person_model: YOLO,
    clothes_model: YOLO,
    image,
    person_conf: float,
    person_imgsz: int,
    clothes_conf: float,
    clothes_imgsz: int,
    device: Optional[str],
) -> Tuple[List[Tuple[Tuple[int, int, int, int], float, str]], List[Tuple[Tuple[int, int, int, int], float, str]]]:
    person_boxes = run_model_boxes(
        model=person_model,
        image=image,
        imgsz=person_imgsz,
        conf=person_conf,
        device=device,
        allowed_names=["person"],
    )
    clothes_boxes: List[Tuple[Tuple[int, int, int, int], float, str]] = []
    for person_xyxy, _, _ in person_boxes:
        x1, y1, x2, y2 = person_xyxy
        crop = image[y1:y2, x1:x2]
        if crop.size == 0:
            continue
        crop_boxes = run_model_boxes(
            model=clothes_model,
            image=crop,
            imgsz=clothes_imgsz,
            conf=clothes_conf,
            device=device,
        )
        for crop_xyxy, conf_value, cls_name in crop_boxes:
            cx1, cy1, cx2, cy2 = crop_xyxy
            mapped = (x1 + cx1, y1 + cy1, x1 + cx2, y1 + cy2)
            clothes_boxes.append((mapped, conf_value, cls_name))
    return person_boxes, clothes_boxes


def draw_boxes(
    image,
    boxes: Sequence[Tuple[Tuple[int, int, int, int], float, str]],
    color: Tuple[int, int, int],
    label_prefix: str,
):
    canvas = image.copy()
    for index, (xyxy, conf_value, cls_name) in enumerate(boxes, start=1):
        x1, y1, x2, y2 = xyxy
        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 2)
        label = f"{label_prefix}{index}:{conf_value:.2f}"
        cv2.putText(canvas, label, (x1, max(16, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
    return canvas


def annotate_header(image, title: str, lines: Sequence[str]):
    canvas = image.copy()
    cv2.rectangle(canvas, (0, 0), (canvas.shape[1], 70), (255, 255, 255), -1)
    cv2.putText(canvas, title, (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2, cv2.LINE_AA)
    for index, line in enumerate(lines, start=1):
        cv2.putText(canvas, line, (10, 22 + index * 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (30, 30, 30), 1, cv2.LINE_AA)
    return canvas


def resize_to_width(image, width: int):
    scale = width / image.shape[1]
    height = int(round(image.shape[0] * scale))
    return cv2.resize(image, (width, height))


def pad_to_height(image, height: int):
    if image.shape[0] >= height:
        return image
    pad = height - image.shape[0]
    return cv2.copyMakeBorder(image, 0, pad, 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))


def build_montage(
    title: str,
    original,
    fullframe_boxes,
    person_boxes_a,
    clothes_boxes_a,
    person_boxes_b,
    clothes_boxes_b,
):
    panel_width = 900
    original_panel = annotate_header(
        resize_to_width(original, panel_width),
        f"{title} | 原图",
        ["左上：原图", "左下：fullframe clothes", "右上：A pipeline", "右下：B pipeline"],
    )
    fullframe_panel = annotate_header(
        resize_to_width(draw_boxes(original, fullframe_boxes, BOX_COLOR_FULLFRAME, "F"), panel_width),
        f"{title} | fullframe",
        [f"clothes det={len(fullframe_boxes)}"],
    )
    panel_a = draw_boxes(original, clothes_boxes_a, BOX_COLOR_CLOTHES, "C")
    panel_a = draw_boxes(panel_a, person_boxes_a, BOX_COLOR_PERSON, "P")
    panel_a = annotate_header(
        resize_to_width(panel_a, panel_width),
        f"{title} | A pipeline",
        [f"person det={len(person_boxes_a)}", f"clothes det={len(clothes_boxes_a)}"],
    )
    panel_b = draw_boxes(original, clothes_boxes_b, BOX_COLOR_CLOTHES, "C")
    panel_b = draw_boxes(panel_b, person_boxes_b, BOX_COLOR_PERSON, "P")
    panel_b = annotate_header(
        resize_to_width(panel_b, panel_width),
        f"{title} | B pipeline",
        [f"person det={len(person_boxes_b)}", f"clothes det={len(clothes_boxes_b)}"],
    )

    top_height = max(original_panel.shape[0], fullframe_panel.shape[0])
    bottom_height = max(panel_a.shape[0], panel_b.shape[0])
    top_row = cv2.hconcat([pad_to_height(original_panel, top_height), pad_to_height(fullframe_panel, top_height)])
    bottom_row = cv2.hconcat([pad_to_height(panel_a, bottom_height), pad_to_height(panel_b, bottom_height)])
    return cv2.vconcat([top_row, bottom_row])


def main() -> None:
    args = parse_args()
    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    source_index = index_source_images(Path(args.source_dataset_yaml).resolve())
    prepared_a = collect_prepared_counts(Path(args.prepared_a).resolve())
    prepared_b = collect_prepared_counts(Path(args.prepared_b).resolve())

    fullframe_model = YOLO(str(Path(args.fullframe_weights).resolve()))
    person_model_a = YOLO(str(Path(args.person_model_a).resolve()))
    person_model_b = YOLO(str(Path(args.person_model_b).resolve()))
    clothes_model_a = YOLO(str(Path(args.clothes_model_a).resolve()))
    clothes_model_b = YOLO(str(Path(args.clothes_model_b).resolve()))

    summary: Dict[str, object] = {"frames": []}
    for frame_stem in args.frame_stems:
        if frame_stem not in source_index:
            raise RuntimeError(f"Frame stem not found in source dataset: {frame_stem}")
        split_name, image_path = source_index[frame_stem]
        image = cv2.imread(str(image_path))
        if image is None:
            raise RuntimeError(f"Failed to read image: {image_path}")

        fullframe_boxes = run_model_boxes(
            model=fullframe_model,
            image=image,
            imgsz=args.clothes_imgsz,
            conf=args.clothes_conf,
            device=args.device,
        )
        person_boxes_a, clothes_boxes_a = run_personcrop_pipeline(
            person_model=person_model_a,
            clothes_model=clothes_model_a,
            image=image,
            person_conf=args.person_conf,
            person_imgsz=args.person_imgsz,
            clothes_conf=args.clothes_conf,
            clothes_imgsz=args.clothes_imgsz,
            device=args.device,
        )
        person_boxes_b, clothes_boxes_b = run_personcrop_pipeline(
            person_model=person_model_b,
            clothes_model=clothes_model_b,
            image=image,
            person_conf=args.person_conf,
            person_imgsz=args.person_imgsz,
            clothes_conf=args.clothes_conf,
            clothes_imgsz=args.clothes_imgsz,
            device=args.device,
        )

        montage = build_montage(
            title=frame_stem,
            original=image,
            fullframe_boxes=fullframe_boxes,
            person_boxes_a=person_boxes_a,
            clothes_boxes_a=clothes_boxes_a,
            person_boxes_b=person_boxes_b,
            clothes_boxes_b=clothes_boxes_b,
        )
        output_image_path = output_root / f"{frame_stem}.jpg"
        cv2.imwrite(str(output_image_path), montage)

        summary["frames"].append(
            {
                "frame_stem": frame_stem,
                "split": split_name,
                "source_image": str(image_path),
                "prepared_a": prepared_a.get(frame_stem, {"crop": 0, "fallback": 0}),
                "prepared_b": prepared_b.get(frame_stem, {"crop": 0, "fallback": 0}),
                "fullframe_clothes_det": len(fullframe_boxes),
                "person_det_a": len(person_boxes_a),
                "person_det_b": len(person_boxes_b),
                "pipeline_clothes_det_a": len(clothes_boxes_a),
                "pipeline_clothes_det_b": len(clothes_boxes_b),
                "review_image": str(output_image_path),
            }
        )

    summary_path = output_root / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(summary_path))


if __name__ == "__main__":
    main()

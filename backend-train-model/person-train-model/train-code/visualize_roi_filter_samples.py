from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import cv2
import numpy as np

from prepare_person_dataset import (
    DEFAULT_PROJECT_CONFIG,
    PERSON_ROOT,
    PersonProjectContext,
    PersonSequence,
    load_person_project_context,
)
from prepare_roi_aware_person_dataset import (
    LabelEntry,
    point_inside_polygon,
    polygon_from_config,
    read_label_entries,
    yolo_entry_to_xyxy,
)


DEFAULT_OUTPUT_ROOT = PERSON_ROOT / "train-result" / "review" / "roi_filter_overlays"
DEFAULT_PROBLEM_STEMS = [
    "D15_20260119203927_frame_0181",
    "D15_20260119203927_frame_0182",
    "D15_20260119203927_frame_0183",
    "D15_20260119203927_frame_0184",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="可视化 ROI-aware 过滤结果：ROI polygon、原 person 框、保留/丢弃状态。"
    )
    parser.add_argument(
        "--project-config",
        default=str(DEFAULT_PROJECT_CONFIG),
        help="person 项目配置 JSON 路径。",
    )
    parser.add_argument(
        "--roi-config",
        help="统一 ROI 配置 JSON；默认读取 person_project_config.json 中的 roi.config_path。",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="overlay 输出目录。",
    )
    parser.add_argument(
        "--stem",
        action="append",
        dest="stems",
        help="要可视化的图片 stem，可重复传入。不传则使用本轮发现的 4 张问题帧。",
    )
    return parser.parse_args()


def load_json(path: Path) -> Dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError("读取 JSON 失败: {0}".format(path)) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("JSON 格式无效: {0}".format(path)) from exc
    if not isinstance(payload, dict):
        raise RuntimeError("JSON 顶层必须是对象: {0}".format(path))
    return payload


def collect_image_lookup(context: PersonProjectContext) -> Dict[str, Tuple[PersonSequence, Path]]:
    lookup: Dict[str, Tuple[PersonSequence, Path]] = {}
    allowed_suffixes = {suffix.lower() for suffix in context.image_extensions}
    for sequence in context.sequences:
        for image_path in sequence.image_root.iterdir():
            if not image_path.is_file() or image_path.suffix.lower() not in allowed_suffixes:
                continue
            if image_path.stem in lookup:
                raise RuntimeError("图片 stem 重复，无法安全可视化: {0}".format(image_path.stem))
            lookup[image_path.stem] = (sequence, image_path)
    return lookup


def draw_label(
    image: np.ndarray,
    text: str,
    origin: Tuple[int, int],
    color: Tuple[int, int, int],
) -> None:
    x_coord, y_coord = origin
    cv2.putText(
        image,
        text,
        (x_coord, y_coord),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 0, 0),
        4,
        cv2.LINE_AA,
    )
    cv2.putText(
        image,
        text,
        (x_coord, y_coord),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        color,
        2,
        cv2.LINE_AA,
    )


def entry_to_int_box(
    entry: LabelEntry,
    image_width: int,
    image_height: int,
) -> Tuple[int, int, int, int]:
    x1, y1, x2, y2 = yolo_entry_to_xyxy(entry, image_width, image_height)
    return (
        int(round(max(0.0, min(float(image_width), x1)))),
        int(round(max(0.0, min(float(image_height), y1)))),
        int(round(max(0.0, min(float(image_width), x2)))),
        int(round(max(0.0, min(float(image_height), y2)))),
    )


def make_overlay(
    image: np.ndarray,
    *,
    polygon: Sequence[Sequence[float]],
    entries: Sequence[LabelEntry],
) -> Tuple[np.ndarray, Dict[str, int]]:
    image_height, image_width = image.shape[:2]
    overlay = image.copy()
    polygon_array = np.array(
        [
            [
                min(max(int(round(float(point[0]))), 0), image_width),
                min(max(int(round(float(point[1]))), 0), image_height),
            ]
            for point in polygon
        ],
        dtype=np.int32,
    )
    if polygon_array.ndim != 2 or polygon_array.shape[0] < 3:
        raise RuntimeError("ROI polygon 至少需要 3 个点。")

    shaded = image.copy()
    cv2.fillPoly(shaded, [polygon_array], (0, 180, 255))
    overlay = cv2.addWeighted(shaded, 0.25, overlay, 0.75, 0.0)
    cv2.polylines(overlay, [polygon_array], True, (0, 180, 255), 4, cv2.LINE_AA)

    x_min = int(np.min(polygon_array[:, 0]))
    y_min = int(np.min(polygon_array[:, 1]))
    x_max = int(np.max(polygon_array[:, 0]))
    y_max = int(np.max(polygon_array[:, 1]))
    cv2.rectangle(overlay, (x_min, y_min), (x_max, y_max), (255, 255, 0), 2)

    kept_count = 0
    dropped_count = 0
    for index, entry in enumerate(entries, start=1):
        x1, y1, x2, y2 = entry_to_int_box(entry, image_width, image_height)
        center_x = (x1 + x2) / 2.0
        center_y = (y1 + y2) / 2.0
        center_inside = point_inside_polygon(center_x, center_y, polygon_array)
        if center_inside:
            kept_count += 1
            color = (0, 255, 0)
            status = "keep"
        else:
            dropped_count += 1
            color = (0, 0, 255)
            status = "drop:center_out"
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 3)
        cv2.circle(overlay, (int(round(center_x)), int(round(center_y))), 5, color, -1)
        draw_label(overlay, "{0}:{1}".format(index, status), (x1, max(25, y1 - 8)), color)

    draw_label(overlay, "ROI polygon: orange", (20, 40), (0, 180, 255))
    draw_label(overlay, "crop bbox: cyan", (20, 75), (255, 255, 0))
    draw_label(overlay, "green=kept red=dropped", (20, 110), (255, 255, 255))
    draw_label(
        overlay,
        "boxes={0} kept={1} dropped={2}".format(len(entries), kept_count, dropped_count),
        (20, 145),
        (255, 255, 255),
    )
    return overlay, {
        "boxes": len(entries),
        "kept": kept_count,
        "dropped": dropped_count,
    }


def visualize_samples(
    context: PersonProjectContext,
    *,
    roi_config_path: Path,
    output_root: Path,
    stems: Iterable[str],
) -> Dict[str, object]:
    roi_payload = load_json(roi_config_path)
    output_root.mkdir(parents=True, exist_ok=True)
    image_lookup = collect_image_lookup(context)
    reports: List[Dict[str, object]] = []

    for stem in stems:
        if stem not in image_lookup:
            raise RuntimeError("未找到图片 stem: {0}".format(stem))
        sequence, image_path = image_lookup[stem]
        image = cv2.imread(str(image_path))
        if image is None:
            raise RuntimeError("无法读取图片: {0}".format(image_path))
        label_path = context.aggregated_label_root / "{0}.txt".format(stem)
        if not label_path.exists():
            raise RuntimeError("未找到汇总 person 标签: {0}".format(label_path))
        entries = read_label_entries(label_path, context.class_names)
        polygon = polygon_from_config(
            roi_payload,
            sequence_name=sequence.sequence_name,
            image_stem=stem,
        )
        overlay, stats = make_overlay(
            image,
            polygon=polygon,
            entries=entries,
        )
        output_path = output_root / "{0}_roi_filter_overlay.jpg".format(stem)
        cv2.imwrite(str(output_path), overlay)
        report = {
            "stem": stem,
            "sequence_name": sequence.sequence_name,
            "image_path": str(image_path),
            "label_path": str(label_path),
            "output_path": str(output_path),
            **stats,
        }
        reports.append(report)

    manifest = {
        "roi_config_path": str(roi_config_path),
        "output_root": str(output_root),
        "samples": reports,
    }
    manifest_path = output_root / "roi_filter_overlay_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def main() -> int:
    args = parse_args()
    context = load_person_project_context(Path(args.project_config))
    roi_config_path = Path(args.roi_config).expanduser().resolve() if args.roi_config else context.roi.config_path
    stems = args.stems if args.stems else DEFAULT_PROBLEM_STEMS
    manifest = visualize_samples(
        context,
        roi_config_path=roi_config_path,
        output_root=Path(args.output_root).expanduser().resolve(),
        stems=stems,
    )
    print("overlay 输出目录 : {0}".format(manifest["output_root"]))
    print("样本数          : {0}".format(len(manifest["samples"])))
    print("manifest        : {0}".format(manifest["manifest_path"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

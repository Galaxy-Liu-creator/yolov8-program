from __future__ import annotations

import argparse
import json
import math
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import cv2
import numpy as np

from prepare_person_dataset import (
    DEFAULT_PROJECT_CONFIG,
    PERSON_ROOT,
    PersonProjectContext,
    PersonSequence,
    RoiSettings,
    apply_roi_setting_overrides,
    assert_directory_within_root,
    load_person_project_context,
    prepare_person_labels,
)


FRAME_INDEX_RE = re.compile(r"_frame_(\d+)$", re.IGNORECASE)


@dataclass(frozen=True)
class LabelEntry:
    class_id: int
    x_center: float
    y_center: float
    width: float
    height: float

    def to_yolo_line(self) -> str:
        return (
            f"{self.class_id} "
            f"{self.x_center:.6f} "
            f"{self.y_center:.6f} "
            f"{self.width:.6f} "
            f"{self.height:.6f}"
        )


@dataclass(frozen=True)
class ImageSample:
    sequence_name: str
    image_path: Path
    label_path: Path
    stem: str


@dataclass(frozen=True)
class RoiKeepDecision:
    keep: bool
    triggered_rule: str
    center_inside: bool
    bottom_center_inside: bool
    box_ioa: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="基于 ROI polygon 生成人员 ROI-aware 训练数据集。"
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
        help="ROI-aware 数据集输出目录；默认读取 person_dataset.roi_aware_prepared_output_root。",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="允许覆盖既有 ROI-aware 输出目录。",
    )
    parser.add_argument(
        "--limit-per-sequence",
        type=int,
        help="仅用于快速烟雾验证；对每个序列只取前 N 张图片。",
    )
    parser.add_argument(
        "--roi-mode",
        choices=["mask_then_crop", "crop_only"],
        help="覆盖 project_config 中的 roi.mode。",
    )
    parser.add_argument(
        "--crop-margin-px",
        type=int,
        help="覆盖 project_config 中的 roi.crop_margin_px。",
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


def ensure_person_labels_available(context: PersonProjectContext, *, overwrite: bool) -> None:
    if context.aggregated_label_root.exists() and not overwrite:
        return
    prepare_person_labels(context, overwrite=overwrite)


def ensure_output_root(output_root: Path, *, overwrite: bool) -> None:
    if output_root.exists():
        if not output_root.is_dir():
            raise RuntimeError("输出路径不是目录: {0}".format(output_root))
        if any(output_root.iterdir()):
            if not overwrite:
                raise RuntimeError(
                    "输出目录已存在且非空: {0}。如需覆盖，请显式传 `--overwrite`。".format(
                        output_root
                    )
                )
            assert_directory_within_root(output_root, PERSON_ROOT / "train-result")
            shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)


def read_label_entries(label_path: Path, class_names: Mapping[int, str]) -> List[LabelEntry]:
    try:
        lines = label_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = label_path.read_text(encoding="utf-8", errors="ignore").splitlines()

    entries: List[LabelEntry] = []
    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        if len(parts) != 5:
            raise RuntimeError(
                "{0}:{1} 不是合法 YOLO 检测标注，字段数应为 5，实际为 {2}。".format(
                    label_path,
                    line_number,
                    len(parts),
                )
            )
        try:
            class_id = int(parts[0])
            x_center = float(parts[1])
            y_center = float(parts[2])
            width = float(parts[3])
            height = float(parts[4])
        except ValueError as exc:
            raise RuntimeError("{0}:{1} 含有非数字字段。".format(label_path, line_number)) from exc
        if class_id not in class_names:
            raise RuntimeError(
                "{0}:{1} 类别 ID 非法，当前仅支持 {2}。".format(
                    label_path,
                    line_number,
                    sorted(class_names),
                )
            )
        if width <= 0.0 or height <= 0.0:
            raise RuntimeError("{0}:{1} width/height 必须大于 0。".format(label_path, line_number))
        entries.append(
            LabelEntry(
                class_id=class_id,
                x_center=min(max(x_center, 0.0), 1.0),
                y_center=min(max(y_center, 0.0), 1.0),
                width=min(max(width, 1e-6), 1.0),
                height=min(max(height, 1e-6), 1.0),
            )
        )
    return entries


def write_label_file(label_path: Path, entries: Iterable[LabelEntry]) -> None:
    label_path.write_text(
        "\n".join(entry.to_yolo_line() for entry in entries),
        encoding="utf-8",
    )


def yolo_entry_to_xyxy(
    entry: LabelEntry,
    image_width: int,
    image_height: int,
) -> Tuple[float, float, float, float]:
    x_center = entry.x_center * image_width
    y_center = entry.y_center * image_height
    box_width = entry.width * image_width
    box_height = entry.height * image_height
    return (
        x_center - box_width / 2.0,
        y_center - box_height / 2.0,
        x_center + box_width / 2.0,
        y_center + box_height / 2.0,
    )


def xyxy_to_yolo_entry(
    box: Tuple[float, float, float, float],
    image_width: int,
    image_height: int,
    class_id: int,
) -> LabelEntry:
    width = max(1.0, box[2] - box[0])
    height = max(1.0, box[3] - box[1])
    x_center = box[0] + width / 2.0
    y_center = box[1] + height / 2.0
    return LabelEntry(
        class_id=class_id,
        x_center=min(max(x_center / float(image_width), 0.0), 1.0),
        y_center=min(max(y_center / float(image_height), 0.0), 1.0),
        width=min(max(width / float(image_width), 1e-6), 1.0),
        height=min(max(height / float(image_height), 1e-6), 1.0),
    )


def image_sort_key(image_path: Path) -> Tuple[int, str]:
    match = FRAME_INDEX_RE.search(image_path.stem)
    if match:
        return (int(match.group(1)), image_path.name)
    return (10**9, image_path.name)


def collect_sequence_samples(
    context: PersonProjectContext,
    *,
    limit_per_sequence: Optional[int],
) -> Dict[str, List[ImageSample]]:
    samples_by_sequence: Dict[str, List[ImageSample]] = {}
    for sequence in context.sequences:
        image_paths = sorted(
            [
                path
                for path in sequence.image_root.iterdir()
                if path.is_file() and path.suffix.lower() in {suffix.lower() for suffix in context.image_extensions}
            ],
            key=image_sort_key,
        )
        if limit_per_sequence is not None:
            if limit_per_sequence <= 0:
                raise RuntimeError("--limit-per-sequence 必须大于 0。")
            image_paths = image_paths[:limit_per_sequence]
        sequence_samples: List[ImageSample] = []
        for image_path in image_paths:
            label_path = context.aggregated_label_root / "{0}.txt".format(image_path.stem)
            if not label_path.exists():
                raise RuntimeError("未找到聚合标签文件: {0}".format(label_path))
            sequence_samples.append(
                ImageSample(
                    sequence_name=sequence.sequence_name,
                    image_path=image_path,
                    label_path=label_path,
                    stem=image_path.stem,
                )
            )
        samples_by_sequence[sequence.sequence_name] = sequence_samples
    return samples_by_sequence


def contiguous_split_counts(total: int, split_ratios: Dict[str, float]) -> Dict[str, int]:
    ordered = ("train", "val", "test")
    if total <= 0:
        return {"train": 0, "val": 0, "test": 0}
    if total == 1:
        return {"train": 1, "val": 0, "test": 0}

    positive_splits = [name for name in ordered if split_ratios.get(name, 0.0) > 0]
    if total < len(positive_splits):
        counts = {name: 0 for name in ordered}
        for split_name in ordered[:total]:
            counts[split_name] = 1
        return counts

    raw_counts = {
        split_name: total * float(split_ratios.get(split_name, 0.0))
        for split_name in ordered
    }
    counts = {
        split_name: int(math.floor(raw_counts[split_name]))
        for split_name in ordered
    }
    for split_name in positive_splits:
        if counts[split_name] == 0:
            counts[split_name] = 1

    while sum(counts.values()) > total:
        reducible = max(
            ordered,
            key=lambda name: (counts[name], raw_counts[name]),
        )
        if counts[reducible] > 1:
            counts[reducible] -= 1
        else:
            break

    while sum(counts.values()) < total:
        target = max(
            ordered,
            key=lambda name: (
                raw_counts[name] - counts[name],
                split_ratios.get(name, 0.0),
                1 if name == "train" else 0,
            ),
        )
        counts[target] += 1
    return counts


def build_split_map(
    samples_by_sequence: Dict[str, List[ImageSample]],
    *,
    split_ratios: Dict[str, float],
    split_strategy: str,
) -> Dict[str, List[ImageSample]]:
    split_map: Dict[str, List[ImageSample]] = {"train": [], "val": [], "test": []}
    if split_strategy == "sequence_contiguous":
        for samples in samples_by_sequence.values():
            counts = contiguous_split_counts(len(samples), split_ratios)
            cursor = 0
            for split_name in ("train", "val", "test"):
                count = counts[split_name]
                split_map[split_name].extend(samples[cursor:cursor + count])
                cursor += count
        return split_map
    if split_strategy == "sequence_holdout":
        ordered_sequences = list(samples_by_sequence.items())
        counts = contiguous_split_counts(len(ordered_sequences), split_ratios)
        cursor = 0
        for split_name in ("train", "val", "test"):
            count = counts[split_name]
            for _, samples in ordered_sequences[cursor:cursor + count]:
                split_map[split_name].extend(samples)
            cursor += count
        return split_map
    raise RuntimeError("未知 split strategy: {0}".format(split_strategy))


def write_dataset_yaml(dataset_root: Path, class_names: Mapping[int, str]) -> Path:
    dataset_yaml = dataset_root / "dataset.yaml"
    names_yaml = "".join(
        "  {0}: {1}\n".format(class_id, class_name)
        for class_id, class_name in sorted(class_names.items())
    )
    dataset_yaml.write_text(
        (
            "path: {0}\n"
            "train: images/train\n"
            "val: images/val\n"
            "test: images/test\n"
            "names:\n"
            "{1}"
        ).format(dataset_root.as_posix(), names_yaml),
        encoding="utf-8",
    )
    return dataset_yaml


def load_roi_config(roi_config_path: Path) -> Dict[str, object]:
    payload = load_json(roi_config_path)
    per_sequence = payload.get("per_sequence", {})
    per_image = payload.get("per_image", {})
    if not isinstance(per_sequence, Mapping):
        raise RuntimeError("ROI 配置中的 per_sequence 必须是对象: {0}".format(roi_config_path))
    if not isinstance(per_image, Mapping):
        raise RuntimeError("ROI 配置中的 per_image 必须是对象: {0}".format(roi_config_path))
    if not per_sequence and not per_image:
        raise RuntimeError("ROI 配置至少需要 per_sequence 或 per_image: {0}".format(roi_config_path))
    payload["per_sequence"] = dict(per_sequence)
    payload["per_image"] = dict(per_image)
    return payload


def normalize_polygon_entry(entry: object, *, entry_name: str) -> List[List[float]]:
    if not isinstance(entry, Mapping):
        raise RuntimeError("ROI 配置中的 {0} 必须是对象。".format(entry_name))
    polygon = entry.get("polygon")
    if not isinstance(polygon, Sequence) or isinstance(polygon, (str, bytes)):
        raise RuntimeError("ROI 配置中的 {0}.polygon 必须是数组。".format(entry_name))
    if len(polygon) < 3:
        raise RuntimeError("ROI 配置中的 {0}.polygon 至少需要 3 个点。".format(entry_name))
    normalized: List[List[float]] = []
    for index, raw_point in enumerate(polygon):
        if not isinstance(raw_point, Sequence) or isinstance(raw_point, (str, bytes)) or len(raw_point) != 2:
            raise RuntimeError(
                "ROI 配置中的 {0}.polygon[{1}] 必须是 [x, y]。".format(entry_name, index)
            )
        normalized.append([float(raw_point[0]), float(raw_point[1])])
    return normalized


def polygon_from_config(
    roi_payload: Mapping[str, object],
    *,
    sequence_name: str,
    image_stem: str,
) -> List[List[float]]:
    per_image = roi_payload.get("per_image", {})
    if isinstance(per_image, Mapping):
        sequence_images = per_image.get(sequence_name)
        if isinstance(sequence_images, Mapping) and image_stem in sequence_images:
            return normalize_polygon_entry(
                sequence_images[image_stem],
                entry_name="{0}.{1}".format(sequence_name, image_stem),
            )

    per_sequence = roi_payload["per_sequence"]
    if sequence_name not in per_sequence:
        raise RuntimeError(
            "ROI 配置缺少图片 {0}/{1} 的 per_image polygon，且没有该序列的 per_sequence fallback。".format(
                sequence_name,
                image_stem,
            )
        )
    return normalize_polygon_entry(
        per_sequence[sequence_name],
        entry_name=sequence_name,
    )


def build_mask_and_crop_bounds(
    image_width: int,
    image_height: int,
    polygon: Sequence[Sequence[float]],
    *,
    margin_px: int = 0,
) -> Tuple[np.ndarray, np.ndarray, Tuple[int, int, int, int]]:
    coord_eps = 1e-6
    for index, point in enumerate(polygon):
        x_coord = float(point[0])
        y_coord = float(point[1])
        if (
            x_coord < -coord_eps
            or x_coord > image_width + coord_eps
            or y_coord < -coord_eps
            or y_coord > image_height + coord_eps
        ):
            raise RuntimeError(
                "ROI polygon 第 {0} 个点超出图片范围: ({1}, {2}), image=({3}, {4})".format(
                    index,
                    x_coord,
                    y_coord,
                    image_width,
                    image_height,
                )
            )
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
        raise RuntimeError("ROI polygon 至少需要 3 个合法点。")
    if np.any(polygon_array[:, 0] < 0) or np.any(polygon_array[:, 0] > image_width):
        raise RuntimeError("ROI polygon 的 x 坐标超出图片范围。")
    if np.any(polygon_array[:, 1] < 0) or np.any(polygon_array[:, 1] > image_height):
        raise RuntimeError("ROI polygon 的 y 坐标超出图片范围。")

    x_min = max(0, int(math.floor(float(np.min(polygon_array[:, 0])))))
    y_min = max(0, int(math.floor(float(np.min(polygon_array[:, 1])))))
    x_max = min(image_width, int(math.ceil(float(np.max(polygon_array[:, 0])))))
    y_max = min(image_height, int(math.ceil(float(np.max(polygon_array[:, 1])))))
    if margin_px < 0:
        raise RuntimeError("crop_margin_px 不能为负数。")
    if margin_px > 0:
        x_min = max(0, x_min - margin_px)
        y_min = max(0, y_min - margin_px)
        x_max = min(image_width, x_max + margin_px)
        y_max = min(image_height, y_max + margin_px)
    if x_max <= x_min or y_max <= y_min:
        raise RuntimeError("ROI polygon 的最小外接矩形无效。")

    mask = np.zeros((image_height, image_width), dtype=np.uint8)
    cv2.fillPoly(mask, [polygon_array], 255)
    return polygon_array, mask, (x_min, y_min, x_max, y_max)


def point_inside_polygon(
    x_coord: float,
    y_coord: float,
    polygon: np.ndarray,
) -> bool:
    return cv2.pointPolygonTest(
        polygon.astype(np.float32),
        (float(x_coord), float(y_coord)),
        False,
    ) >= 0


def box_ioa_with_roi(
    box: Tuple[float, float, float, float],
    roi_mask: np.ndarray,
) -> float:
    x1, y1, x2, y2 = box
    box_width = max(0.0, float(x2) - float(x1))
    box_height = max(0.0, float(y2) - float(y1))
    if box_width <= 0.0 or box_height <= 0.0:
        return 0.0

    mask_height, mask_width = roi_mask.shape[:2]
    left = max(0, int(math.floor(float(x1))))
    top = max(0, int(math.floor(float(y1))))
    right = min(mask_width, int(math.ceil(float(x2))))
    bottom = min(mask_height, int(math.ceil(float(y2))))
    if right <= left or bottom <= top:
        return 0.0

    intersection_area = float(np.count_nonzero(roi_mask[top:bottom, left:right]))
    box_area = max(box_width * box_height, 1.0)
    return min(intersection_area / box_area, 1.0)


def evaluate_roi_keep_rule(
    entry: LabelEntry,
    *,
    image_width: int,
    image_height: int,
    polygon: np.ndarray,
    roi_mask: np.ndarray,
    roi_settings: RoiSettings,
) -> Tuple[Tuple[float, float, float, float], RoiKeepDecision]:
    box = yolo_entry_to_xyxy(entry, image_width, image_height)
    x1, y1, x2, y2 = box
    center_x = (x1 + x2) / 2.0
    center_y = (y1 + y2) / 2.0
    bottom_center_x = center_x
    bottom_center_y = y2
    center_inside = point_inside_polygon(center_x, center_y, polygon)
    bottom_center_inside = point_inside_polygon(bottom_center_x, bottom_center_y, polygon)
    box_ioa = box_ioa_with_roi(box, roi_mask)

    if roi_settings.center_inside and center_inside:
        return box, RoiKeepDecision(
            keep=True,
            triggered_rule="center_inside",
            center_inside=center_inside,
            bottom_center_inside=bottom_center_inside,
            box_ioa=box_ioa,
        )
    if roi_settings.bottom_center_inside and bottom_center_inside:
        return box, RoiKeepDecision(
            keep=True,
            triggered_rule="bottom_center_inside",
            center_inside=center_inside,
            bottom_center_inside=bottom_center_inside,
            box_ioa=box_ioa,
        )
    if roi_settings.min_box_ioa > 0.0 and box_ioa >= roi_settings.min_box_ioa:
        return box, RoiKeepDecision(
            keep=True,
            triggered_rule="min_box_ioa",
            center_inside=center_inside,
            bottom_center_inside=bottom_center_inside,
            box_ioa=box_ioa,
        )
    return box, RoiKeepDecision(
        keep=False,
        triggered_rule="none",
        center_inside=center_inside,
        bottom_center_inside=bottom_center_inside,
        box_ioa=box_ioa,
    )


def prepare_roi_aware_dataset(
    context: PersonProjectContext,
    *,
    roi_config_path: Path,
    output_root: Path,
    overwrite: bool,
    limit_per_sequence: Optional[int],
) -> Dict[str, object]:
    if not context.roi.enabled:
        raise RuntimeError("当前配置中 roi.enabled=false，请先启用 ROI-aware 配置。")
    if context.roi.mode not in ("mask_then_crop", "crop_only"):
        raise RuntimeError("roi.mode 仅支持 `mask_then_crop` 或 `crop_only`。")

    ensure_person_labels_available(context, overwrite=overwrite)
    ensure_output_root(output_root, overwrite=overwrite)
    roi_payload = load_roi_config(roi_config_path)
    samples_by_sequence = collect_sequence_samples(
        context,
        limit_per_sequence=limit_per_sequence,
    )
    split_map = build_split_map(
        samples_by_sequence,
        split_ratios=context.split_ratios,
        split_strategy=context.default_split_strategy,
    )

    split_image_counts = {"train": 0, "val": 0, "test": 0}
    split_label_counts = {"train": 0, "val": 0, "test": 0}
    split_box_counts = {"train": 0, "val": 0, "test": 0}
    kept_boxes = 0
    dropped_boxes = 0
    cropped_boxes = 0
    empty_roi_negative_images = 0
    sequence_stats: Dict[str, Dict[str, int]] = {
        sequence.sequence_name: {
            "input_images": 0,
            "output_images": 0,
            "kept_boxes": 0,
            "dropped_boxes": 0,
            "cropped_boxes": 0,
            "empty_negative_images": 0,
        }
        for sequence in context.sequences
    }

    for split_name, samples in split_map.items():
        image_dir = output_root / "images" / split_name
        label_dir = output_root / "labels" / split_name
        image_dir.mkdir(parents=True, exist_ok=True)
        label_dir.mkdir(parents=True, exist_ok=True)

        for sample in samples:
            sequence_stats[sample.sequence_name]["input_images"] += 1
            image = cv2.imread(str(sample.image_path))
            if image is None:
                raise RuntimeError("无法读取图片: {0}".format(sample.image_path))
            image_height, image_width = image.shape[:2]
            polygon = polygon_from_config(
                roi_payload,
                sequence_name=sample.sequence_name,
                image_stem=sample.stem,
            )
            polygon_array, mask, (x_min, y_min, x_max, y_max) = build_mask_and_crop_bounds(
                image_width,
                image_height,
                polygon,
                margin_px=context.roi.crop_margin_px,
            )

            if context.roi.mode == "mask_then_crop":
                masked_image = np.zeros_like(image)
                masked_image[mask == 255] = image[mask == 255]
                crop_source = masked_image
            else:
                crop_source = image
            crop_image = crop_source[y_min:y_max, x_min:x_max]
            crop_height, crop_width = crop_image.shape[:2]
            if crop_height <= 0 or crop_width <= 0:
                raise RuntimeError("ROI 裁剪结果为空: {0}".format(sample.image_path))

            label_entries = read_label_entries(sample.label_path, context.class_names)
            local_entries: List[LabelEntry] = []
            for entry in label_entries:
                (x1, y1, x2, y2), keep_decision = evaluate_roi_keep_rule(
                    entry,
                    image_width=image_width,
                    image_height=image_height,
                    polygon=polygon_array,
                    roi_mask=mask,
                    roi_settings=context.roi,
                )
                if not keep_decision.keep:
                    dropped_boxes += 1
                    sequence_stats[sample.sequence_name]["dropped_boxes"] += 1
                    continue

                clipped = (
                    max(float(x1), float(x_min)),
                    max(float(y1), float(y_min)),
                    min(float(x2), float(x_max)),
                    min(float(y2), float(y_max)),
                )
                if clipped[2] <= clipped[0] or clipped[3] <= clipped[1]:
                    dropped_boxes += 1
                    sequence_stats[sample.sequence_name]["dropped_boxes"] += 1
                    continue
                if (
                    abs(clipped[0] - x1) > 1e-6
                    or abs(clipped[1] - y1) > 1e-6
                    or abs(clipped[2] - x2) > 1e-6
                    or abs(clipped[3] - y2) > 1e-6
                ):
                    cropped_boxes += 1
                    sequence_stats[sample.sequence_name]["cropped_boxes"] += 1

                local_entries.append(
                    xyxy_to_yolo_entry(
                        box=(
                            clipped[0] - x_min,
                            clipped[1] - y_min,
                            clipped[2] - x_min,
                            clipped[3] - y_min,
                        ),
                        image_width=crop_width,
                        image_height=crop_height,
                        class_id=entry.class_id,
                    )
                )
                kept_boxes += 1
                sequence_stats[sample.sequence_name]["kept_boxes"] += 1

            output_image_path = image_dir / sample.image_path.name
            output_label_path = label_dir / "{0}.txt".format(sample.stem)
            cv2.imwrite(str(output_image_path), crop_image)
            write_label_file(output_label_path, local_entries)

            split_image_counts[split_name] += 1
            split_label_counts[split_name] += 1
            split_box_counts[split_name] += len(local_entries)
            sequence_stats[sample.sequence_name]["output_images"] += 1
            if not local_entries:
                empty_roi_negative_images += 1
                sequence_stats[sample.sequence_name]["empty_negative_images"] += 1

    dataset_yaml = write_dataset_yaml(output_root, context.class_names)
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_config": str(context.config_path),
        "roi_config_path": str(roi_config_path),
        "roi_scope": str(roi_payload.get("scope", "mixed")),
        "mode": context.roi.mode,
        "crop_margin_px": context.roi.crop_margin_px,
        "keep_rule": {
            "center_inside": context.roi.center_inside,
            "bottom_center_inside": context.roi.bottom_center_inside,
            "min_box_ioa": context.roi.min_box_ioa,
        },
        "dataset_root": str(output_root),
        "dataset_yaml": str(dataset_yaml),
        "split_strategy": context.default_split_strategy,
        "split_ratios": context.split_ratios,
        "split_image_counts": split_image_counts,
        "split_label_counts": split_label_counts,
        "split_box_counts": split_box_counts,
        "input_image_count": sum(len(samples) for samples in split_map.values()),
        "output_image_count": sum(split_image_counts.values()),
        "kept_boxes": kept_boxes,
        "dropped_boxes": dropped_boxes,
        "cropped_boxes": cropped_boxes,
        "empty_roi_negative_images": empty_roi_negative_images,
        "limit_per_sequence": limit_per_sequence,
        "sequences": sequence_stats,
    }
    report_path = output_root / "prepare_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["report_path"] = str(report_path)
    return report


def main() -> int:
    args = parse_args()
    context = apply_roi_setting_overrides(
        load_person_project_context(Path(args.project_config)),
        mode=args.roi_mode,
        crop_margin_px=args.crop_margin_px,
    )
    roi_config_path = Path(args.roi_config).expanduser().resolve() if args.roi_config else context.roi.config_path
    output_root = (
        Path(args.output_root).expanduser().resolve()
        if args.output_root
        else context.roi_aware_prepared_output_root
    )
    report = prepare_roi_aware_dataset(
        context,
        roi_config_path=roi_config_path,
        output_root=output_root,
        overwrite=args.overwrite,
        limit_per_sequence=args.limit_per_sequence,
    )
    print("ROI-aware 数据集 : {0}".format(report["dataset_root"]))
    print("dataset.yaml    : {0}".format(report["dataset_yaml"]))
    print(
        "输入图片={0}, 输出图片={1}, 保留框={2}, 丢弃框={3}, 空负样本={4}".format(
            report["input_image_count"],
            report["output_image_count"],
            report["kept_boxes"],
            report["dropped_boxes"],
            report["empty_roi_negative_images"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

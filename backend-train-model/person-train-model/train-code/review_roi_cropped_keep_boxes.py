from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

import cv2
import numpy as np

from prepare_person_dataset import (
    DEFAULT_PROJECT_CONFIG,
    PERSON_ROOT,
    assert_directory_within_root,
    load_person_project_context,
)
from prepare_roi_aware_person_dataset import (
    ImageSample,
    build_mask_and_crop_bounds,
    build_split_map,
    collect_sequence_samples,
    evaluate_roi_keep_rule,
    load_json,
    polygon_from_config,
    read_label_entries,
    yolo_entry_to_xyxy,
)


DEFAULT_OUTPUT_ROOT = PERSON_ROOT / "train-result" / "review" / "roi_cropped_keep_positive_v2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="筛查 ROI-aware v2 中 keep-positive 且被当前 crop bbox 裁剪的样本，并输出清单与可视化。"
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
        help="review 产物输出目录。",
    )
    parser.add_argument(
        "--margin-px",
        type=int,
        default=64,
        help="用于模拟 margin crop 的扩边像素，默认 64。",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="允许覆盖已有 review 输出目录。",
    )
    return parser.parse_args()


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


def clip_box_to_crop(
    box: Tuple[float, float, float, float],
    crop_bounds: Tuple[int, int, int, int],
) -> Tuple[float, float, float, float]:
    x1, y1, x2, y2 = box
    crop_x1, crop_y1, crop_x2, crop_y2 = crop_bounds
    return (
        max(float(x1), float(crop_x1)),
        max(float(y1), float(crop_y1)),
        min(float(x2), float(crop_x2)),
        min(float(y2), float(crop_y2)),
    )


def boxes_differ(
    box_a: Tuple[float, float, float, float],
    box_b: Tuple[float, float, float, float],
    *,
    eps: float = 1e-6,
) -> bool:
    return any(abs(box_a[index] - box_b[index]) > eps for index in range(4))


def clipped_sides(
    original_box: Tuple[float, float, float, float],
    clipped_box: Tuple[float, float, float, float],
    *,
    eps: float = 1e-6,
) -> List[str]:
    sides: List[str] = []
    if clipped_box[0] - original_box[0] > eps:
        sides.append("left")
    if clipped_box[1] - original_box[1] > eps:
        sides.append("top")
    if original_box[2] - clipped_box[2] > eps:
        sides.append("right")
    if original_box[3] - clipped_box[3] > eps:
        sides.append("bottom")
    return sides


def box_to_int(
    box: Tuple[float, float, float, float],
    *,
    image_width: int,
    image_height: int,
) -> Tuple[int, int, int, int]:
    return (
        int(round(max(0.0, min(float(image_width), box[0])))),
        int(round(max(0.0, min(float(image_height), box[1])))),
        int(round(max(0.0, min(float(image_width), box[2])))),
        int(round(max(0.0, min(float(image_height), box[3])))),
    )


def expand_crop_bounds(
    crop_bounds: Tuple[int, int, int, int],
    *,
    image_width: int,
    image_height: int,
    margin_px: int,
) -> Tuple[int, int, int, int]:
    x_min, y_min, x_max, y_max = crop_bounds
    return (
        max(0, x_min - margin_px),
        max(0, y_min - margin_px),
        min(image_width, x_max + margin_px),
        min(image_height, y_max + margin_px),
    )


def draw_crop_preview(
    crop_image: np.ndarray,
    *,
    crop_bounds: Tuple[int, int, int, int],
    boxes: Sequence[Mapping[str, object]],
    title: str,
    color: Tuple[int, int, int],
) -> np.ndarray:
    preview = crop_image.copy()
    crop_x1, crop_y1, _, _ = crop_bounds
    crop_height, crop_width = preview.shape[:2]
    for box_index, box_report in enumerate(boxes, start=1):
        local_box = (
            float(box_report["box"][0]) - crop_x1,
            float(box_report["box"][1]) - crop_y1,
            float(box_report["box"][2]) - crop_x1,
            float(box_report["box"][3]) - crop_y1,
        )
        x1, y1, x2, y2 = box_to_int(local_box, image_width=crop_width, image_height=crop_height)
        cv2.rectangle(preview, (x1, y1), (x2, y2), color, 2)
        draw_label(
            preview,
            "#{0} {1}".format(box_index, box_report["rule"]),
            (x1, max(25, y1 - 8)),
            color,
        )
    draw_label(preview, title, (20, 35), (255, 255, 255))
    return preview


def build_sample_overlay(
    image: np.ndarray,
    *,
    polygon_array: np.ndarray,
    current_crop: Tuple[int, int, int, int],
    margin_crop: Tuple[int, int, int, int],
    box_reports: Sequence[Mapping[str, object]],
) -> np.ndarray:
    image_height, image_width = image.shape[:2]
    overlay = image.copy()
    shaded = image.copy()
    cv2.fillPoly(shaded, [polygon_array], (0, 180, 255))
    overlay = cv2.addWeighted(shaded, 0.2, overlay, 0.8, 0.0)
    cv2.polylines(overlay, [polygon_array], True, (0, 180, 255), 4, cv2.LINE_AA)

    current_x1, current_y1, current_x2, current_y2 = current_crop
    margin_x1, margin_y1, margin_x2, margin_y2 = margin_crop
    cv2.rectangle(overlay, (current_x1, current_y1), (current_x2, current_y2), (255, 255, 0), 2)
    cv2.rectangle(overlay, (margin_x1, margin_y1), (margin_x2, margin_y2), (255, 0, 255), 2)

    for box_index, box_report in enumerate(box_reports, start=1):
        original_box = tuple(float(value) for value in box_report["original_box"])
        clipped_current_box = tuple(float(value) for value in box_report["clipped_current_box"])
        clipped_margin_box = tuple(float(value) for value in box_report["clipped_margin_box"])
        original_x1, original_y1, original_x2, original_y2 = box_to_int(
            original_box,
            image_width=image_width,
            image_height=image_height,
        )
        current_x1_box, current_y1_box, current_x2_box, current_y2_box = box_to_int(
            clipped_current_box,
            image_width=image_width,
            image_height=image_height,
        )
        margin_x1_box, margin_y1_box, margin_x2_box, margin_y2_box = box_to_int(
            clipped_margin_box,
            image_width=image_width,
            image_height=image_height,
        )
        cv2.rectangle(overlay, (original_x1, original_y1), (original_x2, original_y2), (0, 255, 0), 2)
        cv2.rectangle(
            overlay,
            (current_x1_box, current_y1_box),
            (current_x2_box, current_y2_box),
            (0, 0, 255),
            2,
        )
        cv2.rectangle(
            overlay,
            (margin_x1_box, margin_y1_box),
            (margin_x2_box, margin_y2_box),
            (255, 0, 255),
            2,
        )
        center_x = (original_box[0] + original_box[2]) / 2.0
        center_y = (original_box[1] + original_box[3]) / 2.0
        bottom_center_x = center_x
        bottom_center_y = original_box[3]
        cv2.circle(overlay, (int(round(center_x)), int(round(center_y))), 5, (0, 255, 255), -1)
        cv2.circle(
            overlay,
            (int(round(bottom_center_x)), int(round(bottom_center_y))),
            5,
            (255, 255, 0),
            -1,
        )
        draw_label(
            overlay,
            "#{0} {1} now:{2} margin:{3}".format(
                box_index,
                box_report["rule"],
                ",".join(box_report["current_cut_sides"]) if box_report["current_cut_sides"] else "none",
                ",".join(box_report["margin_cut_sides"]) if box_report["margin_cut_sides"] else "none",
            ),
            (original_x1, max(25, original_y1 - 8)),
            (255, 255, 255),
        )

    draw_label(overlay, "ROI polygon: orange", (20, 40), (0, 180, 255))
    draw_label(overlay, "current crop: cyan", (20, 75), (255, 255, 0))
    draw_label(overlay, "margin64 crop: magenta", (20, 110), (255, 0, 255))
    draw_label(overlay, "original box: green", (20, 145), (0, 255, 0))
    draw_label(overlay, "current clipped box: red", (20, 180), (0, 0, 255))
    return overlay


def write_summary_markdown(
    output_path: Path,
    *,
    generated_at: str,
    total_scanned_images: int,
    affected_images: int,
    affected_boxes: int,
    trigger_rule_counts: Mapping[str, int],
    current_cut_side_counts: Mapping[str, int],
    margin_recovered_boxes: int,
    margin_still_cropped_boxes: int,
    sample_reports: Sequence[Mapping[str, object]],
) -> None:
    lines: List[str] = [
        "# ROI-aware v2 keep-positive cropped boxes review",
        "",
        "- generated_at: `{0}`".format(generated_at),
        "- total_scanned_images: `{0}`".format(total_scanned_images),
        "- affected_images: `{0}`".format(affected_images),
        "- affected_boxes: `{0}`".format(affected_boxes),
        "- margin64_recovers_fully: `{0}`".format(margin_recovered_boxes),
        "- margin64_still_cropped: `{0}`".format(margin_still_cropped_boxes),
        "",
        "## Trigger Rule Counts",
        "",
    ]
    for rule_name, count in sorted(trigger_rule_counts.items()):
        lines.append("- `{0}`: `{1}`".format(rule_name, count))
    lines.extend(["", "## Current Cut Side Counts", ""])
    for side_name, count in sorted(current_cut_side_counts.items()):
        lines.append("- `{0}`: `{1}`".format(side_name, count))
    lines.extend(["", "## Affected Samples", ""])
    for sample_report in sample_reports:
        lines.append(
            "- `{0}` (`{1}` / `{2}`): boxes=`{3}` current_overlay=`{4}`".format(
                sample_report["stem"],
                sample_report["split"],
                sample_report["sequence_name"],
                len(sample_report["boxes"]),
                sample_report["overlay_path"],
            )
        )
        for box_report in sample_report["boxes"]:
            lines.append(
                "  - rule=`{0}` current_cut=`{1}` margin_cut=`{2}` current_preview=`{3}` margin_preview=`{4}`".format(
                    box_report["rule"],
                    ",".join(box_report["current_cut_sides"]) if box_report["current_cut_sides"] else "none",
                    ",".join(box_report["margin_cut_sides"]) if box_report["margin_cut_sides"] else "none",
                    sample_report["current_crop_preview_path"],
                    sample_report["margin_crop_preview_path"],
                )
            )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def review_cropped_keep_boxes(
    *,
    project_config_path: Path,
    roi_config_path: Path,
    output_root: Path,
    margin_px: int,
    overwrite: bool,
) -> Dict[str, object]:
    context = load_person_project_context(project_config_path)
    ensure_output_root(output_root, overwrite=overwrite)

    roi_payload = load_json(roi_config_path)
    samples_by_sequence = collect_sequence_samples(context, limit_per_sequence=None)
    split_map = build_split_map(
        samples_by_sequence,
        split_ratios=context.split_ratios,
        split_strategy=context.default_split_strategy,
    )

    sample_reports: List[Dict[str, object]] = []
    trigger_rule_counts: Counter[str] = Counter()
    current_cut_side_counts: Counter[str] = Counter()
    affected_boxes = 0
    total_scanned_images = 0
    margin_recovered_boxes = 0
    margin_still_cropped_boxes = 0

    overlays_dir = output_root / "overlays"
    current_previews_dir = output_root / "current_mask_crops"
    margin_previews_dir = output_root / "margin64_mask_crops"
    overlays_dir.mkdir(parents=True, exist_ok=True)
    current_previews_dir.mkdir(parents=True, exist_ok=True)
    margin_previews_dir.mkdir(parents=True, exist_ok=True)

    for split_name, samples in split_map.items():
        for sample in samples:
            total_scanned_images += 1
            image = cv2.imread(str(sample.image_path))
            if image is None:
                raise RuntimeError("无法读取图片: {0}".format(sample.image_path))
            image_height, image_width = image.shape[:2]
            polygon = polygon_from_config(
                roi_payload,
                sequence_name=sample.sequence_name,
                image_stem=sample.stem,
            )
            polygon_array, mask, current_crop = build_mask_and_crop_bounds(
                image_width,
                image_height,
                polygon,
            )
            margin_crop = expand_crop_bounds(
                current_crop,
                image_width=image_width,
                image_height=image_height,
                margin_px=margin_px,
            )
            label_entries = read_label_entries(sample.label_path, context.class_names)
            box_reports: List[Dict[str, object]] = []
            for entry in label_entries:
                original_box, keep_decision = evaluate_roi_keep_rule(
                    entry,
                    image_width=image_width,
                    image_height=image_height,
                    polygon=polygon_array,
                    roi_mask=mask,
                    roi_settings=context.roi,
                )
                if not keep_decision.keep:
                    continue
                clipped_current_box = clip_box_to_crop(original_box, current_crop)
                if (
                    clipped_current_box[2] <= clipped_current_box[0]
                    or clipped_current_box[3] <= clipped_current_box[1]
                ):
                    continue
                if not boxes_differ(original_box, clipped_current_box):
                    continue

                clipped_margin_box = clip_box_to_crop(original_box, margin_crop)
                current_cut_sides = clipped_sides(original_box, clipped_current_box)
                margin_cut_sides = clipped_sides(original_box, clipped_margin_box)
                trigger_rule_counts[keep_decision.triggered_rule] += 1
                for side_name in current_cut_sides:
                    current_cut_side_counts[side_name] += 1
                affected_boxes += 1
                if margin_cut_sides:
                    margin_still_cropped_boxes += 1
                else:
                    margin_recovered_boxes += 1
                box_reports.append(
                    {
                        "rule": keep_decision.triggered_rule,
                        "center_inside": keep_decision.center_inside,
                        "bottom_center_inside": keep_decision.bottom_center_inside,
                        "box_ioa": round(float(keep_decision.box_ioa), 6),
                        "original_box": [round(float(value), 3) for value in original_box],
                        "clipped_current_box": [round(float(value), 3) for value in clipped_current_box],
                        "clipped_margin_box": [round(float(value), 3) for value in clipped_margin_box],
                        "current_cut_sides": current_cut_sides,
                        "margin_cut_sides": margin_cut_sides,
                    }
                )

            if not box_reports:
                continue

            masked_image = np.zeros_like(image)
            masked_image[mask == 255] = image[mask == 255]
            current_crop_image = masked_image[
                current_crop[1] : current_crop[3],
                current_crop[0] : current_crop[2],
            ]
            margin_crop_image = masked_image[
                margin_crop[1] : margin_crop[3],
                margin_crop[0] : margin_crop[2],
            ]

            overlay = build_sample_overlay(
                image,
                polygon_array=polygon_array,
                current_crop=current_crop,
                margin_crop=margin_crop,
                box_reports=box_reports,
            )
            current_preview = draw_crop_preview(
                current_crop_image,
                crop_bounds=current_crop,
                boxes=[
                    {
                        "box": box_report["clipped_current_box"],
                        "rule": box_report["rule"],
                    }
                    for box_report in box_reports
                ],
                title="current mask_then_crop",
                color=(0, 0, 255),
            )
            margin_preview = draw_crop_preview(
                margin_crop_image,
                crop_bounds=margin_crop,
                boxes=[
                    {
                        "box": box_report["clipped_margin_box"],
                        "rule": box_report["rule"],
                    }
                    for box_report in box_reports
                ],
                title="margin64 simulated mask_then_crop",
                color=(255, 0, 255),
            )

            overlay_path = overlays_dir / "{0}_cropped_keep_overlay.jpg".format(sample.stem)
            current_preview_path = current_previews_dir / "{0}_current_mask_crop.jpg".format(sample.stem)
            margin_preview_path = margin_previews_dir / "{0}_margin64_mask_crop.jpg".format(sample.stem)
            cv2.imwrite(str(overlay_path), overlay)
            cv2.imwrite(str(current_preview_path), current_preview)
            cv2.imwrite(str(margin_preview_path), margin_preview)

            sample_reports.append(
                {
                    "stem": sample.stem,
                    "sequence_name": sample.sequence_name,
                    "split": split_name,
                    "image_path": str(sample.image_path),
                    "label_path": str(sample.label_path),
                    "overlay_path": str(overlay_path),
                    "current_crop_preview_path": str(current_preview_path),
                    "margin_crop_preview_path": str(margin_preview_path),
                    "current_crop": list(current_crop),
                    "margin_crop": list(margin_crop),
                    "boxes": box_reports,
                }
            )

    generated_at = datetime.now().isoformat(timespec="seconds")
    summary = {
        "generated_at": generated_at,
        "project_config": str(project_config_path),
        "roi_config_path": str(roi_config_path),
        "output_root": str(output_root),
        "margin_px": margin_px,
        "total_scanned_images": total_scanned_images,
        "affected_images": len(sample_reports),
        "affected_boxes": affected_boxes,
        "trigger_rule_counts": dict(trigger_rule_counts),
        "current_cut_side_counts": dict(current_cut_side_counts),
        "margin_recovered_boxes": margin_recovered_boxes,
        "margin_still_cropped_boxes": margin_still_cropped_boxes,
        "samples": sample_reports,
    }
    summary_json_path = output_root / "cropped_keep_positive_summary.json"
    summary_json_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    summary_markdown_path = output_root / "cropped_keep_positive_summary.md"
    write_summary_markdown(
        summary_markdown_path,
        generated_at=generated_at,
        total_scanned_images=total_scanned_images,
        affected_images=len(sample_reports),
        affected_boxes=affected_boxes,
        trigger_rule_counts=summary["trigger_rule_counts"],
        current_cut_side_counts=summary["current_cut_side_counts"],
        margin_recovered_boxes=margin_recovered_boxes,
        margin_still_cropped_boxes=margin_still_cropped_boxes,
        sample_reports=sample_reports,
    )
    summary["summary_json_path"] = str(summary_json_path)
    summary["summary_markdown_path"] = str(summary_markdown_path)
    return summary


def main() -> int:
    args = parse_args()
    project_config_path = Path(args.project_config).expanduser().resolve()
    context = load_person_project_context(project_config_path)
    roi_config_path = (
        Path(args.roi_config).expanduser().resolve()
        if args.roi_config
        else context.roi.config_path
    )
    summary = review_cropped_keep_boxes(
        project_config_path=project_config_path,
        roi_config_path=roi_config_path,
        output_root=Path(args.output_root).expanduser().resolve(),
        margin_px=args.margin_px,
        overwrite=args.overwrite,
    )
    print("output_root            : {0}".format(summary["output_root"]))
    print("affected_images        : {0}".format(summary["affected_images"]))
    print("affected_boxes         : {0}".format(summary["affected_boxes"]))
    print("margin_recovered_boxes : {0}".format(summary["margin_recovered_boxes"]))
    print("margin_still_cropped   : {0}".format(summary["margin_still_cropped_boxes"]))
    print("summary_json           : {0}".format(summary["summary_json_path"]))
    print("summary_markdown       : {0}".format(summary["summary_markdown_path"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

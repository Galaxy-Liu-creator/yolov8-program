from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import cv2
import numpy as np

from prepare_person_dataset import (
    DEFAULT_PROJECT_CONFIG,
    PERSON_ROOT,
    PersonProjectContext,
    apply_roi_setting_overrides,
    assert_directory_within_root,
    load_person_project_context,
)
from prepare_roi_aware_person_dataset import (
    LabelEntry,
    build_mask_and_crop_bounds,
    evaluate_roi_keep_rule,
    load_json,
    polygon_from_config,
    read_label_entries,
    yolo_entry_to_xyxy,
)


DEFAULT_FPFN_JSON = (
    PERSON_ROOT
    / "train-result"
    / "review"
    / "person_roi_aware_v3_mask_then_crop_margin64_from_fullframe_fpfn_test_conf025"
    / "fpfn_per_image.json"
)
DEFAULT_OUTPUT_ROOT = PERSON_ROOT / "train-result" / "review" / "person_roi_failure_review"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="把原图 ROI keep/drop、prepared ROI 图与单帧 TP/FP/FN 结果拼到同一张复盘图里。"
    )
    parser.add_argument(
        "--project-config",
        default=str(DEFAULT_PROJECT_CONFIG),
        help="person 项目配置 JSON 路径。",
    )
    parser.add_argument(
        "--roi-config",
        help="统一 ROI 配置 JSON；默认读取 fpfn 对应 prepared 数据集所用的 ROI 配置。",
    )
    parser.add_argument(
        "--fpfn-json",
        default=str(DEFAULT_FPFN_JSON),
        help="analyze_person_fpfn.py 生成的 fpfn_per_image.json。",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="复盘图输出目录。",
    )
    parser.add_argument(
        "--stem",
        action="append",
        dest="stems",
        help="指定要复盘的图片 stem，可重复传入；不传则默认取 false_negative_images 前 N 张。",
    )
    parser.add_argument(
        "--top-fn",
        type=int,
        default=12,
        help="未显式指定 --stem 时，默认取 false_negative_images 前 N 张。",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="允许覆盖既有输出目录。",
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


def box_iou(box_a: Sequence[float], box_b: Sequence[float]) -> float:
    inter_x1 = max(float(box_a[0]), float(box_b[0]))
    inter_y1 = max(float(box_a[1]), float(box_b[1]))
    inter_x2 = min(float(box_a[2]), float(box_b[2]))
    inter_y2 = min(float(box_a[3]), float(box_b[3]))
    inter_area = max(0.0, inter_x2 - inter_x1) * max(0.0, inter_y2 - inter_y1)
    if inter_area <= 0.0:
        return 0.0
    area_a = max(0.0, float(box_a[2]) - float(box_a[0])) * max(
        0.0, float(box_a[3]) - float(box_a[1])
    )
    area_b = max(0.0, float(box_b[2]) - float(box_b[0])) * max(
        0.0, float(box_b[3]) - float(box_b[1])
    )
    union = area_a + area_b - inter_area
    return inter_area / union if union > 0.0 else 0.0


def load_fpfn_payload(fpfn_json_path: Path) -> Dict[str, object]:
    payload = load_json(fpfn_json_path)
    all_images = payload.get("all_images")
    false_negative_images = payload.get("false_negative_images")
    if not isinstance(all_images, list) or not isinstance(false_negative_images, list):
        raise RuntimeError("fpfn JSON 缺少 all_images / false_negative_images 列表。")
    return payload


def select_sample_entries(
    fpfn_payload: Mapping[str, object],
    *,
    stems: Optional[Sequence[str]],
    top_fn: int,
) -> List[Dict[str, object]]:
    all_images = fpfn_payload["all_images"]
    lookup: Dict[str, Dict[str, object]] = {}
    for entry in all_images:
        if not isinstance(entry, Mapping):
            continue
        stem = str(entry.get("stem") or "").strip()
        if stem:
            lookup[stem] = dict(entry)

    selected: List[Dict[str, object]] = []
    if stems:
        for stem in stems:
            if stem not in lookup:
                raise RuntimeError("fpfn JSON 中未找到指定 stem: {0}".format(stem))
            selected.append(lookup[stem])
        return selected

    false_negative_images = fpfn_payload["false_negative_images"]
    for entry in false_negative_images[: max(top_fn, 0)]:
        if not isinstance(entry, Mapping):
            continue
        selected.append(dict(entry))
    return selected


def draw_text(
    image: np.ndarray,
    text: str,
    origin: Tuple[int, int],
    color: Tuple[int, int, int],
    *,
    font_scale: float = 0.62,
    thickness: int = 2,
) -> None:
    cv2.putText(
        image,
        text,
        origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        (0, 0, 0),
        thickness + 2,
        cv2.LINE_AA,
    )
    cv2.putText(
        image,
        text,
        origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        color,
        thickness,
        cv2.LINE_AA,
    )


def fit_to_height(image: np.ndarray, target_height: int) -> np.ndarray:
    if image.shape[0] == target_height:
        return image
    scale = float(target_height) / float(image.shape[0])
    target_width = max(1, int(round(float(image.shape[1]) * scale)))
    interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
    return cv2.resize(image, (target_width, target_height), interpolation=interpolation)


def render_header(lines: Sequence[str], width: int) -> np.ndarray:
    line_height = 34
    padding_top = 26
    padding_bottom = 18
    canvas = np.full(
        (padding_top + padding_bottom + line_height * len(lines), width, 3),
        250,
        dtype=np.uint8,
    )
    for index, line in enumerate(lines):
        y_coord = padding_top + line_height * (index + 1) - 10
        draw_text(canvas, line, (24, y_coord), (20, 20, 20), font_scale=0.72)
    return canvas


def relative_height(box: Sequence[float], image_height: int) -> float:
    return max(0.0, float(box[3]) - float(box[1])) / float(max(image_height, 1))


def relative_area(box: Sequence[float], image_width: int, image_height: int) -> float:
    box_area = max(0.0, float(box[2]) - float(box[0])) * max(0.0, float(box[3]) - float(box[1]))
    return box_area / float(max(image_width * image_height, 1))


def min_edge_distance(box: Sequence[float], image_width: int, image_height: int) -> float:
    return min(
        float(box[0]),
        float(box[1]),
        float(image_width) - float(box[2]),
        float(image_height) - float(box[3]),
    )


def to_int_box(box: Sequence[float], image_width: int, image_height: int) -> Tuple[int, int, int, int]:
    return (
        int(round(max(0.0, min(float(image_width), float(box[0]))))),
        int(round(max(0.0, min(float(image_height), float(box[1]))))),
        int(round(max(0.0, min(float(image_width), float(box[2]))))),
        int(round(max(0.0, min(float(image_height), float(box[3]))))),
    )


def build_prepared_gt_entries(sample_entry: Mapping[str, object]) -> List[Dict[str, object]]:
    entries: List[Dict[str, object]] = []
    for index, match in enumerate(sample_entry.get("matched_pairs", []), start=1):
        if not isinstance(match, Mapping):
            continue
        entries.append(
            {
                "state": "tp",
                "gt_index": int(match.get("gt_index", index - 1)),
                "pred_index": int(match.get("pred_index", -1)),
                "label": "TP",
                "xyxy": [float(value) for value in match.get("gt_xyxy", [])],
                "pred_xyxy": [float(value) for value in match.get("pred_xyxy", [])],
                "pred_conf": float(match.get("pred_conf", 0.0)),
            }
        )
    for index, unmatched_gt in enumerate(sample_entry.get("unmatched_gt", []), start=1):
        if not isinstance(unmatched_gt, Mapping):
            continue
        entries.append(
            {
                "state": "fn",
                "gt_index": int(unmatched_gt.get("gt_index", index - 1)),
                "pred_index": -1,
                "label": "FN",
                "xyxy": [float(value) for value in unmatched_gt.get("xyxy", [])],
                "pred_xyxy": [],
                "pred_conf": 0.0,
            }
        )
    return entries


def map_original_kept_boxes_to_prepared(
    prepared_gt_entries: Sequence[Mapping[str, object]],
    local_box: Sequence[float],
) -> Tuple[str, float]:
    best_state = "kept_untracked"
    best_iou = 0.0
    for entry in prepared_gt_entries:
        score = box_iou(local_box, entry["xyxy"])
        if score > best_iou:
            best_iou = score
            best_state = str(entry["state"])
    if best_iou < 0.90:
        return "kept_untracked", best_iou
    return best_state, best_iou


def build_original_records(
    context: PersonProjectContext,
    *,
    roi_payload: Mapping[str, object],
    sample_entry: Mapping[str, object],
) -> Tuple[List[Dict[str, object]], np.ndarray, Tuple[int, int, int, int]]:
    original_image_path = Path(str(sample_entry["original_image_path"]))
    original_label_path = Path(str(sample_entry.get("original_label_path") or ""))
    if not original_label_path.exists():
        fallback_label_path = context.aggregated_label_root / "{0}.txt".format(sample_entry["stem"])
        if fallback_label_path.exists():
            original_label_path = fallback_label_path
        else:
            raise RuntimeError("未找到原图标签: {0}".format(original_label_path))

    image = cv2.imread(str(original_image_path))
    if image is None:
        raise RuntimeError("无法读取原图: {0}".format(original_image_path))
    image_height, image_width = image.shape[:2]
    polygon = polygon_from_config(
        roi_payload,
        sequence_name=str(sample_entry["sequence_name"]),
        image_stem=str(sample_entry["stem"]),
    )
    polygon_array, mask, crop_bounds = build_mask_and_crop_bounds(
        image_width,
        image_height,
        polygon,
        margin_px=context.roi.crop_margin_px,
    )
    x_min, y_min, x_max, y_max = crop_bounds
    crop_width = x_max - x_min
    crop_height = y_max - y_min
    prepared_gt_entries = build_prepared_gt_entries(sample_entry)
    label_entries = read_label_entries(original_label_path, context.class_names)

    records: List[Dict[str, object]] = []
    for index, entry in enumerate(label_entries, start=1):
        box, keep_decision = evaluate_roi_keep_rule(
            entry,
            image_width=image_width,
            image_height=image_height,
            polygon=polygon_array,
            roi_mask=mask,
            roi_settings=context.roi,
        )
        clipped_box = (
            max(float(box[0]), float(x_min)),
            max(float(box[1]), float(y_min)),
            min(float(box[2]), float(x_max)),
            min(float(box[3]), float(y_max)),
        )
        is_clipped = any(abs(float(clipped_box[i]) - float(box[i])) > 1e-6 for i in range(4))
        local_box = (
            clipped_box[0] - x_min,
            clipped_box[1] - y_min,
            clipped_box[2] - x_min,
            clipped_box[3] - y_min,
        )
        prepared_state = "dropped"
        prepared_iou = 0.0
        edge_distance_px = None
        if keep_decision.keep:
            prepared_state, prepared_iou = map_original_kept_boxes_to_prepared(
                prepared_gt_entries,
                local_box,
            )
            edge_distance_px = min_edge_distance(local_box, crop_width, crop_height)

        records.append(
            {
                "index": index,
                "original_xyxy": box,
                "clipped_xyxy": clipped_box,
                "local_xyxy": local_box,
                "keep": keep_decision.keep,
                "triggered_rule": keep_decision.triggered_rule,
                "center_inside": keep_decision.center_inside,
                "bottom_center_inside": keep_decision.bottom_center_inside,
                "box_ioa": keep_decision.box_ioa,
                "is_clipped": is_clipped,
                "prepared_state": prepared_state,
                "prepared_iou": prepared_iou,
                "edge_distance_px": edge_distance_px,
            }
        )
    return records, polygon_array, crop_bounds


def original_box_label(record: Mapping[str, object]) -> str:
    index = int(record["index"])
    if not bool(record["keep"]):
        return "#{0} DROP ioa={1:.2f}".format(index, float(record["box_ioa"]))
    state = str(record["prepared_state"])
    if state == "fn":
        return "#{0} FN keep={1}".format(index, str(record["triggered_rule"]).replace("_inside", ""))
    if state == "tp":
        return "#{0} TP keep={1}".format(index, str(record["triggered_rule"]).replace("_inside", ""))
    return "#{0} KEEP keep={1}".format(index, str(record["triggered_rule"]).replace("_inside", ""))


def original_box_color(record: Mapping[str, object]) -> Tuple[int, int, int]:
    if not bool(record["keep"]):
        return (0, 0, 255)
    state = str(record["prepared_state"])
    if state == "fn":
        return (0, 165, 255)
    if state == "tp":
        return (0, 200, 0)
    return (255, 255, 255)


def make_original_overlay(
    image: np.ndarray,
    *,
    original_records: Sequence[Mapping[str, object]],
    polygon_array: np.ndarray,
    crop_bounds: Tuple[int, int, int, int],
) -> np.ndarray:
    overlay = image.copy()
    shaded = image.copy()
    cv2.fillPoly(shaded, [polygon_array], (0, 180, 255))
    overlay = cv2.addWeighted(shaded, 0.23, overlay, 0.77, 0.0)
    cv2.polylines(overlay, [polygon_array], True, (0, 180, 255), 4, cv2.LINE_AA)

    x_min, y_min, x_max, y_max = crop_bounds
    cv2.rectangle(overlay, (x_min, y_min), (x_max, y_max), (255, 255, 0), 3, cv2.LINE_AA)

    draw_order = {"dropped": 0, "tp": 1, "kept_untracked": 2, "fn": 3}
    sorted_records = sorted(
        original_records,
        key=lambda item: draw_order.get(str(item["prepared_state"]), 2),
    )
    image_height, image_width = image.shape[:2]
    for record in sorted_records:
        x1, y1, x2, y2 = to_int_box(record["original_xyxy"], image_width, image_height)
        color = original_box_color(record)
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 3, cv2.LINE_AA)
        label_y = max(26, y1 - 8)
        draw_text(overlay, original_box_label(record), (x1, label_y), color, font_scale=0.55)

    draw_text(overlay, "Original image + ROI keep/drop", (20, 40), (20, 20, 20), font_scale=0.85)
    draw_text(overlay, "orange=ROI  cyan=crop bbox", (20, 78), (20, 20, 20), font_scale=0.65)
    draw_text(
        overlay,
        "green=kept TP  orange=kept FN  red=dropped",
        (20, 112),
        (20, 20, 20),
        font_scale=0.65,
    )
    return overlay


def draw_prepared_gt_box(
    canvas: np.ndarray,
    *,
    label: str,
    box: Sequence[float],
    color: Tuple[int, int, int],
) -> None:
    image_height, image_width = canvas.shape[:2]
    x1, y1, x2, y2 = to_int_box(box, image_width, image_height)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 3, cv2.LINE_AA)
    draw_text(canvas, label, (x1, max(26, y1 - 8)), color, font_scale=0.56)


def draw_prepared_pred_box(
    canvas: np.ndarray,
    *,
    label: str,
    box: Sequence[float],
    color: Tuple[int, int, int],
) -> None:
    image_height, image_width = canvas.shape[:2]
    x1, y1, x2, y2 = to_int_box(box, image_width, image_height)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)
    draw_text(canvas, label, (x1, min(image_height - 8, y2 + 20)), color, font_scale=0.52)


def make_prepared_overlay(
    image: np.ndarray,
    *,
    sample_entry: Mapping[str, object],
) -> np.ndarray:
    overlay = image.copy()
    for match in sample_entry.get("matched_pairs", []):
        if not isinstance(match, Mapping):
            continue
        draw_prepared_gt_box(
            overlay,
            label="GT TP",
            box=match["gt_xyxy"],
            color=(0, 200, 0),
        )
        draw_prepared_pred_box(
            overlay,
            label="Pred {0:.2f}".format(float(match.get("pred_conf", 0.0))),
            box=match["pred_xyxy"],
            color=(255, 0, 0),
        )
    for unmatched_gt in sample_entry.get("unmatched_gt", []):
        if not isinstance(unmatched_gt, Mapping):
            continue
        draw_prepared_gt_box(
            overlay,
            label="GT FN",
            box=unmatched_gt["xyxy"],
            color=(0, 165, 255),
        )
    for unmatched_pred in sample_entry.get("unmatched_predictions", []):
        if not isinstance(unmatched_pred, Mapping):
            continue
        draw_prepared_pred_box(
            overlay,
            label="FP {0:.2f}".format(float(unmatched_pred.get("conf", 0.0))),
            box=unmatched_pred["xyxy"],
            color=(255, 0, 255),
        )

    draw_text(overlay, "Prepared ROI image + TP/FP/FN", (20, 40), (20, 20, 20), font_scale=0.85)
    draw_text(overlay, "green=GT TP  orange=GT FN", (20, 78), (20, 20, 20), font_scale=0.65)
    draw_text(overlay, "blue=matched pred  magenta=FP", (20, 112), (20, 20, 20), font_scale=0.65)
    return overlay


def compose_review_image(
    *,
    run_name: str,
    sample_entry: Mapping[str, object],
    original_overlay: np.ndarray,
    prepared_overlay: np.ndarray,
    original_records: Sequence[Mapping[str, object]],
    roi_mode: str,
    crop_margin_px: int,
) -> np.ndarray:
    kept_boxes = sum(1 for item in original_records if bool(item["keep"]))
    dropped_boxes = sum(1 for item in original_records if not bool(item["keep"]))
    cropped_kept_boxes = sum(1 for item in original_records if bool(item["keep"]) and bool(item["is_clipped"]))
    fn_records = [item for item in original_records if str(item["prepared_state"]) == "fn"]
    fn_heights = [
        relative_height(item["local_xyxy"], int(sample_entry["image_height"])) for item in fn_records
    ]
    fn_edges = [float(item["edge_distance_px"]) for item in fn_records if item["edge_distance_px"] is not None]

    target_panel_height = max(original_overlay.shape[0], prepared_overlay.shape[0], 900)
    left_panel = fit_to_height(original_overlay, target_panel_height)
    right_panel = fit_to_height(prepared_overlay, target_panel_height)

    gap = 24
    width = left_panel.shape[1] + right_panel.shape[1] + gap * 3
    lines = [
        "run={0} | stem={1} | seq={2}".format(
            run_name,
            sample_entry["stem"],
            sample_entry["sequence_name"],
        ),
        "orig boxes={0} kept={1} dropped={2} kept_clipped={3}".format(
            len(original_records),
            kept_boxes,
            dropped_boxes,
            cropped_kept_boxes,
        ),
        "prepared gt: tp={0} fn={1} | pred={2} fp={3} | roi={4} margin={5}".format(
            int(sample_entry["tp_count"]),
            int(sample_entry["fn_count"]),
            int(sample_entry["pred_count"]),
            int(sample_entry["fp_count"]),
            roi_mode,
            crop_margin_px,
        ),
    ]
    if fn_records:
        lines.append(
            "fn height ratios={0} | fn edge px={1}".format(
                ",".join("{0:.3f}".format(value) for value in fn_heights),
                ",".join("{0:.1f}".format(value) for value in fn_edges),
            )
        )

    header = render_header(lines, width)
    canvas = np.full(
        (header.shape[0] + target_panel_height + gap * 2, width, 3),
        255,
        dtype=np.uint8,
    )
    canvas[: header.shape[0], :, :] = header
    top = header.shape[0] + gap
    canvas[top : top + target_panel_height, gap : gap + left_panel.shape[1], :] = left_panel
    right_x = gap * 2 + left_panel.shape[1]
    canvas[top : top + target_panel_height, right_x : right_x + right_panel.shape[1], :] = right_panel
    return canvas


def make_sample_summary(
    *,
    sample_entry: Mapping[str, object],
    original_records: Sequence[Mapping[str, object]],
    output_path: Path,
) -> Dict[str, object]:
    prepared_width = int(sample_entry["image_width"])
    prepared_height = int(sample_entry["image_height"])
    fn_boxes = sample_entry.get("unmatched_gt", [])
    fn_relative_heights = [
        relative_height(item["xyxy"], prepared_height) for item in fn_boxes if isinstance(item, Mapping)
    ]
    fn_area_ratios = [
        relative_area(item["xyxy"], prepared_width, prepared_height)
        for item in fn_boxes
        if isinstance(item, Mapping)
    ]
    fn_edge_distances = [
        min_edge_distance(item["xyxy"], prepared_width, prepared_height)
        for item in fn_boxes
        if isinstance(item, Mapping)
    ]
    return {
        "stem": sample_entry["stem"],
        "sequence_name": sample_entry["sequence_name"],
        "original_image_path": sample_entry["original_image_path"],
        "prepared_image_path": sample_entry["prepared_image_path"],
        "output_path": str(output_path),
        "original_box_count": len(original_records),
        "kept_boxes": sum(1 for item in original_records if bool(item["keep"])),
        "dropped_boxes": sum(1 for item in original_records if not bool(item["keep"])),
        "cropped_kept_boxes": sum(1 for item in original_records if bool(item["keep"]) and bool(item["is_clipped"])),
        "prepared_tp_count": int(sample_entry["tp_count"]),
        "prepared_fn_count": int(sample_entry["fn_count"]),
        "prepared_pred_count": int(sample_entry["pred_count"]),
        "prepared_fp_count": int(sample_entry["fp_count"]),
        "fn_relative_heights": fn_relative_heights,
        "fn_area_ratios": fn_area_ratios,
        "fn_min_edge_distances_px": fn_edge_distances,
        "fn_triggered_rules": [
            str(item["triggered_rule"])
            for item in original_records
            if str(item["prepared_state"]) == "fn"
        ],
    }


def write_summary_markdown(
    *,
    output_path: Path,
    fpfn_json_path: Path,
    roi_config_path: Path,
    manifest: Mapping[str, object],
) -> None:
    lines = [
        "# ROI-aware person hard FN 复盘摘要",
        "",
        "- 生成时间: `{0}`".format(manifest["generated_at"]),
        "- 运行名: `{0}`".format(manifest["run_name"]),
        "- fpfn JSON: `{0}`".format(fpfn_json_path),
        "- ROI 配置: `{0}`".format(roi_config_path),
        "- 输出目录: `{0}`".format(manifest["output_root"]),
        "- 样本数: `{0}`".format(len(manifest["samples"])),
        "",
        "## 样本列表",
        "",
    ]
    for sample in manifest["samples"]:
        lines.append(
            "- `{stem}` | 序列 `{sequence_name}` | 原框 `{original_box_count}` | kept `{kept_boxes}` | dropped `{dropped_boxes}` | prepared `tp={prepared_tp_count} fn={prepared_fn_count} pred={prepared_pred_count} fp={prepared_fp_count}` | FN 高度 `{fn_relative_heights}` | FN 离边界像素 `{fn_min_edge_distances_px}` | 输出 `{output_path}`".format(
                **sample
            )
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def review_person_roi_failures(
    context: PersonProjectContext,
    *,
    roi_config_path: Path,
    fpfn_json_path: Path,
    output_root: Path,
    stems: Optional[Sequence[str]],
    top_fn: int,
    overwrite: bool,
) -> Dict[str, object]:
    roi_payload = load_json(roi_config_path)
    context = apply_roi_setting_overrides(
        context,
        mode=str(roi_payload.get("mode") or context.roi.mode),
        crop_margin_px=int(roi_payload.get("crop_margin_px", context.roi.crop_margin_px)),
    )
    fpfn_payload = load_fpfn_payload(fpfn_json_path)
    sample_entries = select_sample_entries(fpfn_payload, stems=stems, top_fn=top_fn)
    ensure_output_root(output_root, overwrite=overwrite)

    run_name = str(fpfn_payload.get("run_name") or "unknown_run")
    sample_summaries: List[Dict[str, object]] = []

    for sample_entry in sample_entries:
        original_image_path = Path(str(sample_entry["original_image_path"]))
        prepared_image_path = Path(str(sample_entry["prepared_image_path"]))
        original_image = cv2.imread(str(original_image_path))
        prepared_image = cv2.imread(str(prepared_image_path))
        if original_image is None:
            raise RuntimeError("无法读取原图: {0}".format(original_image_path))
        if prepared_image is None:
            raise RuntimeError("无法读取 prepared ROI 图: {0}".format(prepared_image_path))

        original_records, polygon_array, crop_bounds = build_original_records(
            context,
            roi_payload=roi_payload,
            sample_entry=sample_entry,
        )
        original_overlay = make_original_overlay(
            original_image,
            original_records=original_records,
            polygon_array=polygon_array,
            crop_bounds=crop_bounds,
        )
        prepared_overlay = make_prepared_overlay(
            prepared_image,
            sample_entry=sample_entry,
        )
        review_image = compose_review_image(
            run_name=run_name,
            sample_entry=sample_entry,
            original_overlay=original_overlay,
            prepared_overlay=prepared_overlay,
            original_records=original_records,
            roi_mode=context.roi.mode,
            crop_margin_px=context.roi.crop_margin_px,
        )
        output_path = output_root / "{0}_roi_failure_review.jpg".format(sample_entry["stem"])
        cv2.imwrite(str(output_path), review_image)
        sample_summaries.append(
            make_sample_summary(
                sample_entry=sample_entry,
                original_records=original_records,
                output_path=output_path,
            )
        )

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "run_name": run_name,
        "fpfn_json": str(fpfn_json_path),
        "roi_config_path": str(roi_config_path),
        "output_root": str(output_root),
        "samples": sample_summaries,
    }
    manifest_path = output_root / "roi_failure_review_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    summary_md_path = output_root / "roi_failure_review_summary.md"
    write_summary_markdown(
        output_path=summary_md_path,
        fpfn_json_path=fpfn_json_path,
        roi_config_path=roi_config_path,
        manifest=manifest,
    )
    manifest["manifest_path"] = str(manifest_path)
    manifest["summary_markdown_path"] = str(summary_md_path)
    return manifest


def main() -> int:
    args = parse_args()
    project_config_path = Path(args.project_config).expanduser().resolve()
    fpfn_json_path = Path(args.fpfn_json).expanduser().resolve()
    context = load_person_project_context(project_config_path)
    roi_config_path = (
        Path(args.roi_config).expanduser().resolve()
        if args.roi_config
        else (
            PERSON_ROOT
            / "train-result"
            / "working"
            / "roi"
            / "roi_config.v3.mask_then_crop_margin64.generated.json"
        ).resolve()
    )
    manifest = review_person_roi_failures(
        context,
        roi_config_path=roi_config_path,
        fpfn_json_path=fpfn_json_path,
        output_root=Path(args.output_root).expanduser().resolve(),
        stems=args.stems,
        top_fn=args.top_fn,
        overwrite=args.overwrite,
    )
    print("output_root : {0}".format(manifest["output_root"]))
    print("sample_count: {0}".format(len(manifest["samples"])))
    print("manifest    : {0}".format(manifest["manifest_path"]))
    print("summary_md  : {0}".format(manifest["summary_markdown_path"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

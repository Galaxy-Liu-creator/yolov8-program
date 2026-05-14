from __future__ import annotations

import json
import shutil
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from PIL import Image, ImageDraw, ImageFont


SCRIPT_PATH = Path(__file__).resolve()
PERSON_ROOT = SCRIPT_PATH.parents[1]
REVIEW_ROOT = PERSON_ROOT / "train-result" / "review"
HARD_REVIEW_ROOT = REVIEW_ROOT / "person_fullframe_with_new_labels_hard_sample_review"
BY_SOURCE_ROOT = HARD_REVIEW_ROOT / "by_source"
SEND_PACKAGES_ROOT = BY_SOURCE_ROOT / "send_packages"
SUMMARY_JSON = REVIEW_ROOT / "person_fullframe_with_new_labels_prescreen_summary.json"
PREPARE_REPORT = (
    PERSON_ROOT
    / "train-result"
    / "prepared"
    / "person_fullframe_with_new_labels"
    / "sequence_contiguous"
    / "prepare_report.json"
)
RUNS = {
    "baseline_val": REVIEW_ROOT / "person_fullframe_with_new_labels_baseline_fpfn_val_conf025" / "fpfn_per_image.json",
    "baseline_test": REVIEW_ROOT / "person_fullframe_with_new_labels_baseline_fpfn_test_conf025" / "fpfn_per_image.json",
    "img768_val": REVIEW_ROOT / "person_fullframe_with_new_labels_img768_fpfn_val_conf025" / "fpfn_per_image.json",
    "img768_test": REVIEW_ROOT / "person_fullframe_with_new_labels_img768_fpfn_test_conf025" / "fpfn_per_image.json",
}
FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/msyh.ttc"),
    Path("C:/Windows/Fonts/msyhbd.ttc"),
    Path("C:/Windows/Fonts/simhei.ttf"),
    Path("C:/Windows/Fonts/simsun.ttc"),
]
LEGEND_TITLE = "框颜色说明（GT=人工标注，Pred=模型检测）"
LEGEND_ITEMS: Tuple[Tuple[Tuple[int, int, int], str], ...] = (
    ((0, 128, 255), "蓝色框：Pred 预测框（与 GT 成功匹配）"),
    ((0, 200, 0), "绿色框：GT 真值框（已匹配 / TP 对应 GT）"),
    ((255, 0, 0), "红色框：GT 真值框（人工标注有，但模型漏检 / FN）"),
    ((255, 165, 0), "橙色框：Pred 预测框（模型多检 / FP，若出现）"),
)


def iou(box_a: List[float], box_b: List[float]) -> float:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter = inter_w * inter_h
    if inter <= 0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    denom = area_a + area_b - inter
    return inter / denom if denom > 0 else 0.0


def classify(best_iou: float, rel_height: float, min_edge_px: float) -> str:
    if best_iou >= 0.5:
        return "crowded_or_localization"
    if rel_height < 0.10:
        return "small_boundary_person" if min_edge_px <= 10 else "small_interior_person"
    return "medium_large_pose_or_appearance"


def safe_name(name: str) -> str:
    return name.replace("/", "_").replace("\\", "_")


def load_font(size: int) -> ImageFont.ImageFont:
    for font_path in FONT_CANDIDATES:
        if not font_path.exists():
            continue
        try:
            return ImageFont.truetype(str(font_path), size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def choose_legend_fonts(draw: ImageDraw.ImageDraw, image_width: int) -> Tuple[ImageFont.ImageFont, ImageFont.ImageFont]:
    for title_size, body_size in ((28, 24), (24, 20), (22, 18), (20, 16)):
        title_font = load_font(title_size)
        body_font = load_font(body_size)
        title_width, _ = text_size(draw, LEGEND_TITLE, title_font)
        max_line_width = max(text_size(draw, line, body_font)[0] for _, line in LEGEND_ITEMS)
        content_width = max(title_width, 34 + max_line_width)
        if content_width + 40 <= image_width - 16:
            return title_font, body_font
    return load_font(18), load_font(16)


def draw_overlay_legend(draw: ImageDraw.ImageDraw, image_width: int) -> None:
    title_font, body_font = choose_legend_fonts(draw, image_width)
    margin_x = 14
    margin_y = 34
    padding = 12
    row_gap = 10
    swatch_size = 22
    swatch_gap = 12

    title_width, title_height = text_size(draw, LEGEND_TITLE, title_font)
    line_sizes = [text_size(draw, line, body_font) for _, line in LEGEND_ITEMS]
    max_line_width = max(width for width, _ in line_sizes)
    line_height = max(height for _, height in line_sizes)

    legend_width = max(title_width, swatch_size + swatch_gap + max_line_width) + padding * 2
    legend_height = (
        padding * 2
        + title_height
        + 10
        + len(LEGEND_ITEMS) * line_height
        + (len(LEGEND_ITEMS) - 1) * row_gap
    )

    x1 = margin_x
    y1 = margin_y
    x2 = min(image_width - margin_x, x1 + legend_width)
    y2 = y1 + legend_height

    shadow_offset = 4
    draw.rectangle((x1 + shadow_offset, y1 + shadow_offset, x2 + shadow_offset, y2 + shadow_offset), fill=(0, 0, 0))
    draw.rectangle((x1, y1, x2, y2), fill=(255, 255, 255), outline=(0, 0, 0), width=2)

    current_y = y1 + padding
    draw.text((x1 + padding, current_y), LEGEND_TITLE, fill=(0, 0, 0), font=title_font)
    current_y += title_height + 10

    for color, line in LEGEND_ITEMS:
        swatch_y = current_y + max(0, (line_height - swatch_size) // 2)
        draw.rectangle(
            (x1 + padding, swatch_y, x1 + padding + swatch_size, swatch_y + swatch_size),
            outline=color,
            width=5,
        )
        draw.text(
            (x1 + padding + swatch_size + swatch_gap, current_y),
            line,
            fill=(0, 0, 0),
            font=body_font,
        )
        current_y += line_height + row_gap


def draw_box(
    draw: ImageDraw.ImageDraw,
    box: List[float],
    color: Tuple[int, int, int],
    width: int,
    label: str = "",
) -> None:
    xyxy = [box[0], box[1], box[2], box[3]]
    draw.rectangle(xyxy, outline=color, width=width)
    if label:
        text_x = max(0, int(box[0]))
        text_y = max(0, int(box[1]) - 16)
        draw.text((text_x, text_y), label, fill=color)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def choose_source_root(image_path: str, roots: List[str]) -> str:
    image_lower = image_path.lower()
    matches = [root for root in roots if image_lower.startswith(root.lower())]
    if not matches:
        return "unmatched_source"
    return max(matches, key=len)


def load_frame_registry() -> Dict[str, dict]:
    registry: Dict[str, dict] = {}
    for run_name, json_path in RUNS.items():
        data = load_json(json_path)
        for item in data["false_negative_images"]:
            stem = item["stem"]
            record = registry.setdefault(
                stem,
                {
                    "stem": stem,
                    "sequence_name": item["sequence_name"],
                    "source_id": item.get("source_id", ""),
                    "group": item.get("group", ""),
                    "original_image_path": item["original_image_path"],
                    "original_label_path": item["original_label_path"],
                    "prepared_image_path": item["prepared_image_path"],
                    "prepared_label_path": item["prepared_label_path"],
                    "runs": {},
                },
            )
            record["runs"][run_name] = item
    return registry


def collect_selected_stems(summary: dict, registry: Dict[str, dict]) -> Tuple[List[dict], Dict[str, str]]:
    selected: Dict[str, str] = {}

    for item in summary["combined"]["suggested_manual_review_frames"][:12]:
        selected[item["stem"]] = "auto_top12"

    extra_from_notes = [
        "D02_20260123074836_frame_0022",
        "D02_20260123074836_frame_0023",
        "D02_20260123074836_frame_0024",
        "D05_20260123074841_frame_0029",
        "D05_20260123074841_frame_0030",
    ]
    for stem in extra_from_notes:
        selected[stem] = "note_extra"

    d15_seq_counter: Counter[str] = Counter()
    for stem, frame in registry.items():
        if frame["sequence_name"] != "D15_20260119203927":
            continue
        total_fn = sum(run_item["fn_count"] for run_item in frame["runs"].values())
        d15_seq_counter[stem] = total_fn
    for stem, _ in d15_seq_counter.most_common(3):
        selected.setdefault(stem, "d15_19203927_fill")

    ordered: List[dict] = []
    for stem, reason in selected.items():
        if stem not in registry:
            continue
        ordered.append(
            {
                "stem": stem,
                "reason": reason,
                "sequence_name": registry[stem]["sequence_name"],
            }
        )
    ordered.sort(key=lambda item: (item["sequence_name"], item["stem"]))
    return ordered, selected


def create_overlay(frame: dict, run_name: str, sequence_dir: Path) -> str:
    item = frame["runs"][run_name]
    image = Image.open(frame["original_image_path"]).convert("RGB")
    draw = ImageDraw.Draw(image)
    header_font = load_font(16)

    for pair in item["matched_pairs"]:
        draw_box(draw, pair["gt_xyxy"], (0, 200, 0), 2, f"GT{pair['gt_index']}")
        draw_box(draw, pair["pred_xyxy"], (0, 128, 255), 2, f"P{pair['pred_index']}")

    preds = [p["pred_xyxy"] for p in item["matched_pairs"]] + [p["xyxy"] for p in item["unmatched_predictions"]]
    for pred in item["unmatched_predictions"]:
        draw_box(draw, pred["xyxy"], (255, 165, 0), 2, f"FP {pred['conf']:.2f}")

    for gt in item["unmatched_gt"]:
        x1, y1, x2, y2 = gt["xyxy"]
        rel_h = (y2 - y1) / item["image_height"]
        min_edge = min(x1, y1, item["image_width"] - x2, item["image_height"] - y2)
        best = max((iou(gt["xyxy"], pred_box) for pred_box in preds), default=0.0)
        bucket = classify(best, rel_h, min_edge)
        draw_box(draw, gt["xyxy"], (255, 0, 0), 4, f"FN{gt['gt_index']} {bucket}")

    split_name = item["prepared_image_relpath"].split("/")[1]
    header = f"{run_name} | split={split_name} | fn={item['fn_count']} fp={item['fp_count']}"
    draw.rectangle((0, 0, min(image.width, 1000), 24), fill=(0, 0, 0))
    draw.text((6, 4), header, fill=(255, 255, 255), font=header_font)
    draw_overlay_legend(draw, image.width)

    overlay_name = f"{run_name}__{frame['stem']}.jpg"
    overlay_path = sequence_dir / "overlays" / overlay_name
    image.save(overlay_path, quality=95)
    return overlay_name


def copy_label_or_empty(src: Path, dst: Path) -> None:
    if src.exists():
        shutil.copy2(src, dst)
    else:
        dst.write_text("", encoding="utf-8")


def create_zip_from_paths(paths: Iterable[Path], zip_path: Path, root_parent: Path) -> None:
    ensure_dir(zip_path.parent)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root in paths:
            for path in sorted(root.rglob("*")):
                if path.is_dir():
                    continue
                arcname = path.relative_to(root_parent)
                zf.write(path, arcname.as_posix())


def main() -> None:
    prepare_report = load_json(PREPARE_REPORT)
    source_roots: List[str] = prepare_report["runtime"]["config"]["image_roots"]
    source_name_map = {root: Path(root).name for root in source_roots}
    summary = load_json(SUMMARY_JSON)
    registry = load_frame_registry()
    selected_items, selected_reason_map = collect_selected_stems(summary, registry)

    ensure_dir(BY_SOURCE_ROOT)
    ensure_dir(SEND_PACKAGES_ROOT)
    for stale_zip in SEND_PACKAGES_ROOT.glob("*.zip"):
        stale_zip.unlink()

    manifest = {
        "description": "按 prepare_report.json 的 8 个来源整理人工复核图片、标签和 overlay。",
        "selection_policy": {
            "auto_top12": "自动预筛 suggested_manual_review_frames 前 12 张",
            "note_extra": "当前各序列 notes.md 中额外强调的边界 / 拥挤代表帧",
            "d15_19203927_fill": "为第二优先级主序列 D15_20260119203927 补齐的 top 帧",
        },
        "all_sources_zip": str((SEND_PACKAGES_ROOT / "all_sources__review_bundle.zip").relative_to(HARD_REVIEW_ROOT)),
        "sources": [],
    }

    source_frame_map: Dict[str, List[dict]] = defaultdict(list)
    for item in selected_items:
        frame = registry[item["stem"]]
        source_root = choose_source_root(frame["original_image_path"], source_roots)
        source_frame_map[source_root].append(item)

    by_source_readme_lines = [
        "# 按 8 个来源整理的人工复核素材",
        "",
        "## 1. 本目录作用",
        "",
        "这个目录专门存放已经筛出来、需要人工复核的图片素材，按 `prepare_report.json` 中的 8 个来源进行整理。",
        "",
        "每个来源目录下再按具体 `sequence_name` 拆分，方便本地查看和后续继续扩展。",
        "",
        "## 2. 目录约定",
        "",
        "每个 `source_*` 目录内，通常包含：",
        "",
        "- `README.md`：说明这个来源对应什么、当前放了哪些待复核样本",
        "- `sequence_*/images/`：原图 jpg",
        "- `sequence_*/labels/`：对应 YOLO txt",
        "- `sequence_*/overlays/`：按 run 生成的 overlay 图",
        "",
        "## 3. 发送建议",
        "",
        "如果只需要发给 1 个组员，优先发送 `send_packages/all_sources__review_bundle.zip`。",
        "不要再按单条序列分别发 zip 包。",
        "",
        "## 4. 当前说明",
        "",
        "如果某个来源目录下当前没有图片，表示这轮优先人工复核名单里暂时没有从该来源挑出来的样本，不代表该来源永远不需要复核。",
        "",
    ]

    exported_source_dirs: List[Path] = []

    for source_root in source_roots:
        source_name = source_name_map[source_root]
        source_dir = BY_SOURCE_ROOT / f"source_{safe_name(source_name)}"
        ensure_dir(source_dir)
        frame_items = source_frame_map.get(source_root, [])
        source_readme_lines = [
            f"# 来源 {source_name} 人工复核素材",
            "",
            "## 1. 本来源对应什么",
            "",
            f"- 原始来源根目录：`{source_root}`",
            f"- 当前进入人工复核清单的图片数量：`{len(frame_items)}`",
            "",
            "## 2. 子目录说明",
            "",
            "- `sequence_*/images/`：待人工复核的原图",
            "- `sequence_*/labels/`：对应的 YOLO 标签 txt",
            "- `sequence_*/overlays/`：按不同 run 生成的 overlay 图",
            "",
        ]

        manifest_entry = {
            "source_name": source_name,
            "source_root": source_root,
            "selected_frame_count": len(frame_items),
            "sequences": [],
        }

        if not frame_items:
            source_readme_lines.extend(
                [
                    "## 3. 当前状态",
                    "",
                    "当前这轮优先人工复核名单中，暂时没有从这个来源挑出的样本。",
                    "如果后续要扩展复核范围，可根据 `person_fullframe_with_new_labels_prescreen_summary.json` 再补充。",
                ]
            )
            write_text(source_dir / "README.md", "\n".join(source_readme_lines).strip() + "\n")
            manifest["sources"].append(manifest_entry)
            exported_source_dirs.append(source_dir)
            continue

        sequence_group: Dict[str, List[dict]] = defaultdict(list)
        for item in frame_items:
            sequence_group[registry[item["stem"]]["sequence_name"]].append(item)

        for sequence_name, items in sorted(sequence_group.items()):
            seq_dir = source_dir / f"sequence_{safe_name(sequence_name)}"
            ensure_dir(seq_dir / "images")
            ensure_dir(seq_dir / "labels")
            ensure_dir(seq_dir / "overlays")

            manifest_sequence = {
                "sequence_name": sequence_name,
                "frames": [],
            }

            for item in sorted(items, key=lambda x: x["stem"]):
                frame = registry[item["stem"]]
                image_src = Path(frame["original_image_path"])
                label_src = Path(frame["original_label_path"])
                image_dst = seq_dir / "images" / image_src.name
                label_dst = seq_dir / "labels" / label_src.name
                shutil.copy2(image_src, image_dst)
                copy_label_or_empty(label_src, label_dst)

                overlay_files = []
                for run_name in sorted(frame["runs"].keys()):
                    overlay_files.append(create_overlay(frame, run_name, seq_dir))

                manifest_sequence["frames"].append(
                    {
                        "stem": frame["stem"],
                        "selection_reason": selected_reason_map[item["stem"]],
                        "image_file": f"images/{image_src.name}",
                        "label_file": f"labels/{label_src.name}",
                        "runs": sorted(frame["runs"].keys()),
                        "overlay_files": [f"overlays/{name}" for name in overlay_files],
                    }
                )

            manifest_entry["sequences"].append(manifest_sequence)
            source_readme_lines.extend(
                [
                    f"## 序列 `{sequence_name}`",
                    "",
                    f"- 当前放入待复核图片：`{len(manifest_sequence['frames'])}` 张",
                    "- 优先看 `images/` 中原图，再对照 `overlays/` 中不同 run 的 overlay。",
                    "- 如果怀疑标签有问题，优先在当前目录做临时副本再进入 LabelImg 修框。",
                    "",
                ]
            )

        write_text(source_dir / "README.md", "\n".join(source_readme_lines).strip() + "\n")
        manifest["sources"].append(manifest_entry)
        exported_source_dirs.append(source_dir)

    all_sources_zip = SEND_PACKAGES_ROOT / "all_sources__review_bundle.zip"
    create_zip_from_paths(exported_source_dirs, all_sources_zip, BY_SOURCE_ROOT)

    write_text(BY_SOURCE_ROOT / "README.md", "\n".join(by_source_readme_lines).strip() + "\n")
    write_text(BY_SOURCE_ROOT / "review_asset_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    send_readme_lines = [
        "# 发给组员的压缩包",
        "",
        "如果只需要发给 1 个组员，直接发送下面这个总压缩包：",
        "",
        "- `all_sources__review_bundle.zip`",
        "",
        "这个 zip 已经包含全部 `source_*` 顶层目录，以及每个来源下的图片、标签和 overlay。",
        "为了避免接收端解析失败，不再额外按单条序列生成 zip 包。",
        "",
        "组员解压后，直接在解压目录内查看 `source_* / sequence_* / images|labels|overlays` 即可。",
        "",
    ]
    write_text(SEND_PACKAGES_ROOT / "README.md", "\n".join(send_readme_lines))

    print(f"selected_frames={len(selected_items)}")
    print(f"output_root={BY_SOURCE_ROOT}")
    print(f"all_sources_zip={all_sources_zip}")


if __name__ == "__main__":
    main()

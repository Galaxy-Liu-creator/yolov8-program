from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Dict, List

import cv2


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "backend-train-model"
NEW_CLOTHES_ROOT = BACKEND_ROOT / "new_clothes_train"
FRAME_LABEL_ROOT_ENV = "YOLO_FRAME_LABEL_ROOT"


def resolve_frame_label_root() -> Path:
    """解析仓库外 frame_label 根目录。"""

    raw_value = os.environ.get(FRAME_LABEL_ROOT_ENV, "").strip()
    if not raw_value:
        return (REPO_ROOT.parent / "frame_label").resolve()

    candidate = Path(raw_value).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (REPO_ROOT / candidate).resolve()


FRAME_LABEL_ROOT = resolve_frame_label_root()
IMAGE_ROOT = FRAME_LABEL_ROOT / "new_clothes_labels" / "images"
RAW_LABEL_ROOT = FRAME_LABEL_ROOT / "new_clothes_labels" / "clothes_labels"
COMPLETED_LABEL_ROOT = NEW_CLOTHES_ROOT / "train-result" / "working" / "new_source_completed_labels"
REPORT_JSON_PATH = NEW_CLOTHES_ROOT / "train-result" / "working" / "new_source_validation_report.json"
REPORT_MD_PATH = NEW_CLOTHES_ROOT / "train-result" / "working" / "new_source_validation_report.md"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
IGNORED_LABEL_FILENAMES = {"classes.txt", "classed.txt"}
COORD_TOLERANCE = 1e-6
BOX_EDGE_TOLERANCE = 1e-6


def list_image_paths() -> List[Path]:
    return sorted(
        [path for path in IMAGE_ROOT.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS],
        key=lambda path: path.name,
    )


def list_label_paths(label_root: Path) -> List[Path]:
    return sorted(
        [
            path
            for path in label_root.iterdir()
            if path.is_file() and path.suffix.lower() == ".txt" and path.name.lower() not in IGNORED_LABEL_FILENAMES
        ],
        key=lambda path: path.name,
    )


def validate_image(path: Path) -> Dict[str, object]:
    image = cv2.imread(str(path))
    if image is None or image.size == 0:
        return {"ok": False, "reason": "opencv_imread_failed"}
    height, width = image.shape[:2]
    if width <= 0 or height <= 0:
        return {"ok": False, "reason": "invalid_image_size"}
    return {"ok": True, "width": int(width), "height": int(height)}


def validate_label(path: Path) -> Dict[str, object]:
    raw_text = path.read_text(encoding="utf-8", errors="ignore")
    stripped_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not stripped_lines:
        return {"ok": True, "is_empty": True, "box_count": 0, "invalid_lines": []}

    invalid_lines: List[Dict[str, object]] = []
    for line_idx, line in enumerate(stripped_lines, start=1):
        parts = line.split()
        if len(parts) != 5:
            invalid_lines.append({"line_index": line_idx, "reason": "field_count_not_5", "content": line})
            continue
        try:
            class_id = int(parts[0])
            coords = [float(value) for value in parts[1:]]
        except ValueError:
            invalid_lines.append({"line_index": line_idx, "reason": "non_numeric_field", "content": line})
            continue

        if class_id != 0:
            invalid_lines.append({"line_index": line_idx, "reason": "class_id_not_0", "content": line})
            continue

        if any(value < -COORD_TOLERANCE or value > 1.0 + COORD_TOLERANCE for value in coords):
            invalid_lines.append({"line_index": line_idx, "reason": "coord_out_of_range", "content": line})
            continue

        x_center, y_center, width, height = coords
        x_center = min(max(x_center, 0.0), 1.0)
        y_center = min(max(y_center, 0.0), 1.0)
        width = min(max(width, 0.0), 1.0)
        height = min(max(height, 0.0), 1.0)
        if width <= 0.0 or height <= 0.0:
            invalid_lines.append({"line_index": line_idx, "reason": "non_positive_wh", "content": line})
            continue

        x1 = x_center - width / 2.0
        y1 = y_center - height / 2.0
        x2 = x_center + width / 2.0
        y2 = y_center + height / 2.0
        edge_overshoot = max(0.0, -x1, -y1, x2 - 1.0, y2 - 1.0)
        if edge_overshoot > BOX_EDGE_TOLERANCE:
            invalid_lines.append({"line_index": line_idx, "reason": "box_out_of_bounds", "content": line})

    return {
        "ok": len(invalid_lines) == 0,
        "is_empty": False,
        "box_count": len(stripped_lines),
        "invalid_lines": invalid_lines,
    }


def write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: Dict[str, object]) -> None:
    summary = payload["summary"]
    invalid_examples = payload["invalid_label_examples"]
    bad_image_examples = payload["bad_image_examples"]

    lines = [
        "# new_clothes 数据源检查报告",
        "",
        "## 1. 检查范围",
        "",
        f"- 图片根目录：`{payload['image_root']}`",
        f"- 原始标注目录：`{payload['raw_label_root']}`",
        f"- 补齐后标注目录：`{payload['completed_label_root']}`",
        "",
        "## 2. 汇总结果",
        "",
        f"- 图片总数：`{summary['image_count']}`",
        f"- 原始标注文件数：`{summary['raw_label_count']}`",
        f"- 补齐后标注文件数：`{summary['completed_label_count']}`",
        f"- 可正常读取图片数：`{summary['readable_image_count']}`",
        f"- 损坏/不可读图片数：`{summary['bad_image_count']}`",
        f"- 空标注文件数：`{summary['empty_label_count']}`",
        f"- 非空标注文件数：`{summary['positive_label_count']}`",
        f"- 非法标注文件数：`{summary['invalid_label_file_count']}`",
        f"- 非法标注行数：`{summary['invalid_label_line_count']}`",
        f"- 孤立原始标注文件数：`{summary['orphan_raw_label_count']}`",
        "",
        "## 3. 结论",
        "",
    ]

    if summary["bad_image_count"] == 0 and summary["invalid_label_file_count"] == 0:
        lines.append("- 本轮检查未发现损坏图片，也未发现非法 YOLO 标注行。")
    else:
        lines.append("- 本轮检查发现需要人工处理的问题，请优先查看下方异常样例。")

    lines.extend([
        f"- `classes.txt` 等说明性文件已从标注样本检查中排除。",
        f"- 空标注文件已被视为合法负样本，不单独判错。",
        "",
        "## 4. 异常样例",
        "",
        "### 4.1 不可读图片",
        "",
    ])

    if bad_image_examples:
        for item in bad_image_examples[:20]:
            lines.append(f"- `{item['image_name']}`: {item['reason']}")
    else:
        lines.append("- 无")

    lines.extend([
        "",
        "### 4.2 非法标注样例",
        "",
    ])

    if invalid_examples:
        for item in invalid_examples[:20]:
            lines.append(
                f"- `{item['label_name']}` 第 `{item['line_index']}` 行：`{item['reason']}` -> `{item['content']}`"
            )
    else:
        lines.append("- 无")

    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    image_paths = list_image_paths()
    raw_label_paths = list_label_paths(RAW_LABEL_ROOT)
    completed_label_paths = list_label_paths(COMPLETED_LABEL_ROOT)

    image_stems = {path.stem for path in image_paths}
    raw_label_stems = {path.stem for path in raw_label_paths}

    bad_image_examples: List[Dict[str, object]] = []
    readable_image_count = 0
    for image_path in image_paths:
        result = validate_image(image_path)
        if result["ok"]:
            readable_image_count += 1
        else:
            bad_image_examples.append({"image_name": image_path.name, "reason": result["reason"]})

    empty_label_count = 0
    positive_label_count = 0
    invalid_label_file_count = 0
    invalid_label_line_count = 0
    invalid_label_examples: List[Dict[str, object]] = []
    total_box_count = 0

    for label_path in completed_label_paths:
        result = validate_label(label_path)
        if result["is_empty"]:
            empty_label_count += 1
            continue

        positive_label_count += 1
        total_box_count += int(result["box_count"])
        if not result["ok"]:
            invalid_label_file_count += 1
            invalid_label_line_count += len(result["invalid_lines"])
            for item in result["invalid_lines"]:
                invalid_label_examples.append(
                    {
                        "label_name": label_path.name,
                        "line_index": item["line_index"],
                        "reason": item["reason"],
                        "content": item["content"],
                    }
                )

    orphan_raw_labels = sorted(raw_label_stems - image_stems)
    missing_raw_labels = sorted(image_stems - raw_label_stems)

    payload: Dict[str, object] = {
        "image_root": str(IMAGE_ROOT),
        "raw_label_root": str(RAW_LABEL_ROOT),
        "completed_label_root": str(COMPLETED_LABEL_ROOT),
        "summary": {
            "image_count": len(image_paths),
            "raw_label_count": len(raw_label_paths),
            "completed_label_count": len(completed_label_paths),
            "readable_image_count": readable_image_count,
            "bad_image_count": len(bad_image_examples),
            "empty_label_count": empty_label_count,
            "positive_label_count": positive_label_count,
            "invalid_label_file_count": invalid_label_file_count,
            "invalid_label_line_count": invalid_label_line_count,
            "orphan_raw_label_count": len(orphan_raw_labels),
            "missing_raw_label_count": len(missing_raw_labels),
            "total_box_count": total_box_count,
        },
        "bad_image_examples": bad_image_examples[:50],
        "invalid_label_examples": invalid_label_examples[:50],
        "orphan_raw_label_stems": orphan_raw_labels[:50],
        "missing_raw_label_stems": missing_raw_labels[:50],
        "report_files": {
            "json": str(REPORT_JSON_PATH),
            "markdown": str(REPORT_MD_PATH),
        },
    }

    write_json(REPORT_JSON_PATH, payload)
    write_markdown(REPORT_MD_PATH, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

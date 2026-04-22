from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Set, Tuple

from prepare_person_dataset import (
    DEFAULT_PROJECT_CONFIG,
    PersonProjectContext,
    load_person_project_context,
)


DEFAULT_ROI_LABEL = "roi"
COORD_EPS = 1e-6


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="从 Labelme ROI JSON 中提取 polygon，生成 person ROI 配置。"
    )
    parser.add_argument(
        "--project-config",
        default=str(DEFAULT_PROJECT_CONFIG),
        help="person 项目配置 JSON 路径。",
    )
    parser.add_argument(
        "--roi-json-root",
        help="Labelme ROI JSON 根目录；默认读取 project_config.json 中的 roi.json_root。",
    )
    parser.add_argument(
        "--output",
        help="输出 ROI 配置 JSON；默认使用 project_config.json 中的 roi.config_path。",
    )
    parser.add_argument(
        "--label",
        default=DEFAULT_ROI_LABEL,
        help="Labelme 中用于 ROI polygon 的标签名。",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="允许覆盖既有 ROI 配置文件。",
    )
    return parser.parse_args()


def load_json(path: Path) -> Dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError("读取 Labelme JSON 失败: {0}".format(path)) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("Labelme JSON 格式无效: {0}".format(path)) from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Labelme JSON 顶层必须是对象: {0}".format(path))
    return payload


def find_sequence_for_json(
    json_path: Path,
    roi_json_root: Path,
    sequence_aliases: Mapping[str, str],
) -> Optional[str]:
    try:
        relative_parts = json_path.relative_to(roi_json_root).parts
    except ValueError:
        relative_parts = json_path.parts
    for part in relative_parts:
        if part in sequence_aliases:
            return sequence_aliases[part]
    return None


def build_sequence_aliases(context: PersonProjectContext) -> Tuple[Dict[str, str], Set[str]]:
    alias_candidates: Dict[str, Set[str]] = {}
    for sequence in context.sequences:
        for alias in (sequence.sequence_name, sequence.image_root.name):
            normalized = str(alias).strip()
            if not normalized:
                continue
            alias_candidates.setdefault(normalized, set()).add(sequence.sequence_name)

    aliases: Dict[str, str] = {}
    ambiguous_aliases: Set[str] = set()
    for alias, sequence_names in alias_candidates.items():
        if len(sequence_names) == 1:
            aliases[alias] = next(iter(sequence_names))
        else:
            ambiguous_aliases.add(alias)
    return aliases, ambiguous_aliases


def coerce_positive_int(raw_value: object, field_name: str, json_path: Path) -> int:
    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("{0} 缺少合法的 {1}。".format(json_path, field_name)) from exc
    if value <= 0:
        raise RuntimeError("{0} 的 {1} 必须大于 0。".format(json_path, field_name))
    return value


def coerce_polygon_points(
    raw_points: object,
    *,
    image_width: int,
    image_height: int,
    json_path: Path,
) -> List[List[float]]:
    if not isinstance(raw_points, Sequence) or isinstance(raw_points, (str, bytes)):
        raise RuntimeError("{0} 的 ROI points 必须是数组。".format(json_path))
    if len(raw_points) < 3:
        raise RuntimeError("{0} 的 ROI polygon 至少需要 3 个点。".format(json_path))

    polygon: List[List[float]] = []
    for index, raw_point in enumerate(raw_points):
        if not isinstance(raw_point, Sequence) or isinstance(raw_point, (str, bytes)):
            raise RuntimeError("{0} 的 ROI 第 {1} 个点不是坐标对。".format(json_path, index))
        if len(raw_point) != 2:
            raise RuntimeError("{0} 的 ROI 第 {1} 个点必须包含 x,y。".format(json_path, index))
        try:
            x_coord = float(raw_point[0])
            y_coord = float(raw_point[1])
        except (TypeError, ValueError) as exc:
            raise RuntimeError("{0} 的 ROI 第 {1} 个点含有非数字坐标。".format(json_path, index)) from exc
        if (
            x_coord < -COORD_EPS
            or x_coord > image_width + COORD_EPS
            or y_coord < -COORD_EPS
            or y_coord > image_height + COORD_EPS
        ):
            raise RuntimeError(
                "{0} 的 ROI 第 {1} 个点越界: ({2}, {3}), image=({4}, {5})".format(
                    json_path,
                    index,
                    x_coord,
                    y_coord,
                    image_width,
                    image_height,
                )
            )
        x_coord = min(max(x_coord, 0.0), float(image_width))
        y_coord = min(max(y_coord, 0.0), float(image_height))
        polygon.append([normalize_number(x_coord), normalize_number(y_coord)])
    return polygon


def normalize_number(value: float) -> float:
    rounded = round(value)
    if abs(value - rounded) < 1e-6:
        return float(rounded)
    return round(value, 6)


def canonical_polygon(polygon: Sequence[Sequence[float]]) -> Tuple[Tuple[float, float], ...]:
    return tuple((round(float(point[0]), 3), round(float(point[1]), 3)) for point in polygon)


def extract_labelme_roi_polygon(
    json_path: Path,
    *,
    label_name: str,
) -> Tuple[List[List[float]], int, int]:
    payload = load_json(json_path)
    image_width = coerce_positive_int(payload.get("imageWidth"), "imageWidth", json_path)
    image_height = coerce_positive_int(payload.get("imageHeight"), "imageHeight", json_path)
    shapes = payload.get("shapes")
    if not isinstance(shapes, Sequence) or isinstance(shapes, (str, bytes)):
        raise RuntimeError("{0} 缺少合法的 shapes 数组。".format(json_path))

    roi_shapes = []
    for raw_shape in shapes:
        if not isinstance(raw_shape, Mapping):
            continue
        if str(raw_shape.get("label", "")).strip() == label_name:
            roi_shapes.append(raw_shape)
    if not roi_shapes:
        raise RuntimeError("{0} 未找到 label == {1} 的 ROI polygon。".format(json_path, label_name))
    if len(roi_shapes) > 1:
        raise RuntimeError("{0} 中存在多个 label == {1} 的 ROI polygon。".format(json_path, label_name))

    roi_shape = roi_shapes[0]
    shape_type = str(roi_shape.get("shape_type", "polygon")).strip()
    if shape_type != "polygon":
        raise RuntimeError("{0} 的 ROI shape_type 必须是 polygon，实际为 {1}。".format(json_path, shape_type))
    polygon = coerce_polygon_points(
        roi_shape.get("points"),
        image_width=image_width,
        image_height=image_height,
        json_path=json_path,
    )
    return polygon, image_width, image_height


def extract_roi_config(
    context: PersonProjectContext,
    *,
    roi_json_root: Path,
    output_path: Path,
    label_name: str,
    overwrite: bool,
) -> Dict[str, object]:
    root = roi_json_root.expanduser().resolve()
    if not root.exists():
        raise RuntimeError("ROI JSON 根目录不存在: {0}".format(root))
    if not root.is_dir():
        raise RuntimeError("ROI JSON 根路径不是目录: {0}".format(root))
    target = output_path.expanduser().resolve()
    if target.exists() and not overwrite:
        raise RuntimeError("ROI 配置已存在，请显式传 `--overwrite`: {0}".format(target))

    sequence_names = [sequence.sequence_name for sequence in context.sequences]
    sequence_aliases, ambiguous_aliases = build_sequence_aliases(context)
    per_image: Dict[str, Dict[str, Dict[str, object]]] = {}
    first_by_sequence: Dict[str, Dict[str, object]] = {}
    canonical_by_sequence: Dict[str, set] = {}
    canonical_by_image: Dict[Tuple[str, str], Tuple[Tuple[float, float], ...]] = {}
    json_paths = sorted(path for path in root.rglob("*.json") if path.is_file())
    if not json_paths:
        raise RuntimeError("ROI JSON 根目录下没有 .json 文件: {0}".format(root))

    for json_path in json_paths:
        sequence_name = find_sequence_for_json(json_path, root, sequence_aliases)
        if sequence_name is None:
            ambiguous_text = (
                "\n已忽略的歧义别名: {0}".format(", ".join(sorted(ambiguous_aliases)))
                if ambiguous_aliases
                else ""
            )
            raise RuntimeError(
                "无法从 ROI JSON 路径识别序列名: {0}\n已知序列: {1}\n可用路径别名: {2}{3}".format(
                    json_path,
                    ", ".join(sequence_names),
                    ", ".join(sorted(sequence_aliases)),
                    ambiguous_text,
                )
            )
        polygon, image_width, image_height = extract_labelme_roi_polygon(
            json_path,
            label_name=label_name,
        )
        canonical = canonical_polygon(polygon)
        image_stem = json_path.stem
        image_key = (sequence_name, image_stem)
        if image_key in canonical_by_image:
            if canonical_by_image[image_key] != canonical:
                raise RuntimeError(
                    "同一图片存在不一致 ROI polygon: {0}/{1}\n冲突文件: {2}".format(
                        sequence_name,
                        image_stem,
                        json_path,
                    )
                )
            continue
        canonical_by_image[image_key] = canonical
        canonical_by_sequence.setdefault(sequence_name, set()).add(canonical)
        image_entry = {
            "polygon": polygon,
            "source_json": str(json_path),
            "image_width": image_width,
            "image_height": image_height,
        }
        per_image.setdefault(sequence_name, {})[image_stem] = image_entry
        first_by_sequence.setdefault(sequence_name, image_entry)

    per_sequence = {
        sequence_name: first_by_sequence[sequence_name]
        for sequence_name, canonical_set in sorted(canonical_by_sequence.items())
        if len(canonical_set) == 1
    }
    unique_counts = {
        sequence_name: len(canonical_set)
        for sequence_name, canonical_set in sorted(canonical_by_sequence.items())
    }
    image_counts = {
        sequence_name: len(images)
        for sequence_name, images in sorted(per_image.items())
    }

    result = {
        "version": 1,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": "labelme",
        "roi_json_root": str(root),
        "label": label_name,
        "scope": "per_image",
        "mode": context.roi.mode,
        "keep_rule": {
            "center_inside": context.roi.center_inside,
        },
        "per_sequence": dict(sorted(per_sequence.items())),
        "per_image": {
            sequence_name: dict(sorted(images.items()))
            for sequence_name, images in sorted(per_image.items())
        },
        "summary": {
            "json_count": len(json_paths),
            "sequence_image_counts": image_counts,
            "sequence_unique_polygon_counts": unique_counts,
            "sequence_level_fallback_count": len(per_sequence),
        },
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    args = parse_args()
    context = load_person_project_context(Path(args.project_config))
    output_path = Path(args.output).expanduser().resolve() if args.output else context.roi.config_path
    result = extract_roi_config(
        context,
        roi_json_root=(
            Path(args.roi_json_root).expanduser().resolve()
            if args.roi_json_root
            else context.roi.json_root
        ),
        output_path=output_path,
        label_name=args.label,
        overwrite=args.overwrite,
    )
    print("ROI 配置文件 : {0}".format(output_path))
    per_image_total = sum(len(images) for images in result.get("per_image", {}).values())
    print("序列级 ROI 数 : {0}".format(len(result["per_sequence"])))
    print("逐图 ROI 数   : {0}".format(per_image_total))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

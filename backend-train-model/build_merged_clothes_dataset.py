from __future__ import annotations

import argparse
import csv
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

import cv2

COORD_TOLERANCE = 1e-6
BOX_EDGE_TOLERANCE = 1e-6
SUPPORTED_SPLITS = ("train", "val", "test")
SUPPORTED_ASSIGNMENT_SPLITS = SUPPORTED_SPLITS + ("skip",)
SUPPORTED_POLICIES = {"skip", "use_review_labels"}
IGNORED_LABEL_FILENAMES = {"classes.txt", "classed.txt"}


class BuildConfigError(RuntimeError):
    """合并数据集配置无效时抛出的异常。"""


class DatasetBuildError(RuntimeError):
    """构建 merged 数据集失败时抛出的异常。"""


@dataclass(frozen=True)
class SequenceConfig:
    source_id: str
    sequence_name: str
    image_root: Path
    label_root: Path
    split: str


@dataclass(frozen=True)
class SplitAssignment:
    split: str
    note: str
    holdout_group: Optional[str]
    merged_stem: Optional[str]


@dataclass
class IncludedSample:
    source_id: str
    sequence_name: str
    split: str
    assignment_source: str
    assignment_note: str
    holdout_group: Optional[str]
    original_stem: str
    merged_stem: str
    image_path: Path
    label_source_path: Path
    label_origin: str
    sample_role: str
    label_lines: List[str]
    box_count: int
    image_width: int
    image_height: int


@dataclass
class MissingReviewItem:
    source_id: str
    sequence_name: str
    split: str
    original_stem: str
    merged_stem: str
    original_image_path: Path
    expected_review_label_path: Optional[Path]
    review_status: str
    review_box_count: int
    note: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="构建三套 clothes 数据的 merged YOLO 数据集。"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="构建配置 JSON 路径。",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="允许覆盖已存在的输出目录。",
    )
    return parser.parse_args()


def resolve_config_path(raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    return candidate.resolve()


def load_json(path: Path) -> Dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise BuildConfigError("读取配置失败: {0}".format(path)) from exc
    except json.JSONDecodeError as exc:
        raise BuildConfigError("配置 JSON 格式无效: {0}".format(path)) from exc
    if not isinstance(payload, dict):
        raise BuildConfigError("配置顶层必须是对象: {0}".format(path))
    return payload


def resolve_value_path(raw_value: object, base_dir: Path, field_name: str) -> Path:
    text = str(raw_value).strip()
    if not text:
        raise BuildConfigError("{0} 不能为空。".format(field_name))
    candidate = Path(text).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (base_dir / candidate).resolve()


def coerce_string(raw_value: object, field_name: str) -> str:
    text = str(raw_value).strip()
    if not text:
        raise BuildConfigError("{0} 不能为空。".format(field_name))
    return text


def coerce_class_names(raw_value: object) -> Dict[int, str]:
    if isinstance(raw_value, Mapping):
        items = raw_value.items()
    elif isinstance(raw_value, Sequence) and not isinstance(raw_value, (str, bytes)):
        items = enumerate(raw_value)
    else:
        raise BuildConfigError("class_names 必须是对象或字符串列表。")

    normalized: Dict[int, str] = {}
    for raw_key, raw_name in items:
        try:
            class_id = int(raw_key)
        except (TypeError, ValueError) as exc:
            raise BuildConfigError("class_names 中存在非法 class_id: {0}".format(raw_key)) from exc
        class_name = str(raw_name).strip()
        if not class_name:
            raise BuildConfigError("class_names 中存在空类别名。")
        normalized[class_id] = class_name
    if not normalized:
        raise BuildConfigError("class_names 不能为空。")
    return dict(sorted(normalized.items()))


def coerce_extensions(raw_value: object) -> List[str]:
    if raw_value is None:
        return [".jpg", ".jpeg", ".png"]
    if not isinstance(raw_value, Sequence) or isinstance(raw_value, (str, bytes)):
        raise BuildConfigError("image_extensions 必须是字符串列表。")
    normalized: List[str] = []
    for item in raw_value:
        suffix = str(item).strip().lower()
        if not suffix:
            continue
        if not suffix.startswith("."):
            suffix = ".{0}".format(suffix)
        normalized.append(suffix)
    if not normalized:
        raise BuildConfigError("image_extensions 不能为空。")
    return normalized


def determine_sample_role(*, label_origin: str, box_count: int) -> str:
    if box_count > 0:
        return "positive"
    if label_origin == "review":
        return "review_empty"
    return "source_empty"


def load_split_assignments(split_manifest_path: Path) -> Dict[Tuple[str, str, str], SplitAssignment]:
    try:
        with split_manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = set(reader.fieldnames or [])
            required_fields = {"source_id", "sequence_name", "original_stem", "split"}
            missing_fields = sorted(required_fields - fieldnames)
            if missing_fields:
                raise BuildConfigError(
                    "split_manifest_csv 缺少字段 {0}: {1}".format(
                        missing_fields,
                        split_manifest_path,
                    )
                )

            assignments: Dict[Tuple[str, str, str], SplitAssignment] = {}
            for row_index, row in enumerate(reader, start=2):
                source_id = coerce_string(row.get("source_id"), "split_manifest_csv[{0}].source_id".format(row_index))
                sequence_name = coerce_string(
                    row.get("sequence_name"),
                    "split_manifest_csv[{0}].sequence_name".format(row_index),
                )
                original_stem = coerce_string(
                    row.get("original_stem"),
                    "split_manifest_csv[{0}].original_stem".format(row_index),
                )
                split = coerce_string(row.get("split"), "split_manifest_csv[{0}].split".format(row_index))
                if split not in SUPPORTED_ASSIGNMENT_SPLITS:
                    raise BuildConfigError(
                        "split_manifest_csv[{0}].split 仅支持 {1}。".format(
                            row_index,
                            list(SUPPORTED_ASSIGNMENT_SPLITS),
                        )
                    )
                assignment_key = (source_id, sequence_name, original_stem)
                if assignment_key in assignments:
                    raise BuildConfigError(
                        "split_manifest_csv 中存在重复样本: {0}/{1}/{2}".format(
                            source_id,
                            sequence_name,
                            original_stem,
                        )
                    )
                merged_stem = str(row.get("merged_stem", "") or "").strip() or None
                holdout_group = str(row.get("holdout_group", "") or "").strip() or None
                note = str(row.get("note", "") or "").strip()
                assignments[assignment_key] = SplitAssignment(
                    split=split,
                    note=note,
                    holdout_group=holdout_group,
                    merged_stem=merged_stem,
                )
    except OSError as exc:
        raise BuildConfigError("读取 split_manifest_csv 失败: {0}".format(split_manifest_path)) from exc

    if not assignments:
        raise BuildConfigError("split_manifest_csv 不能为空: {0}".format(split_manifest_path))
    return assignments


def load_build_config(config_path: Path) -> Dict[str, object]:
    payload = load_json(config_path)
    base_dir = config_path.parent

    dataset_name = coerce_string(payload.get("dataset_name"), "dataset_name")
    output_root = resolve_value_path(payload.get("output_root"), base_dir, "output_root")
    review_root = resolve_value_path(payload.get("review_root"), base_dir, "review_root")

    train_project_config = None
    if payload.get("train_project_config") not in (None, ""):
        train_project_config = resolve_value_path(
            payload.get("train_project_config"),
            base_dir,
            "train_project_config",
        )

    recommended_run_name = coerce_string(
        payload.get("recommended_run_name", dataset_name),
        "recommended_run_name",
    )
    class_names = coerce_class_names(payload.get("class_names", {0: "clothes"}))
    image_extensions = coerce_extensions(payload.get("image_extensions"))
    missing_label_policy = str(payload.get("missing_label_policy", "skip")).strip()
    if missing_label_policy not in SUPPORTED_POLICIES:
        raise BuildConfigError(
            "missing_label_policy 仅支持 {0}。".format(sorted(SUPPORTED_POLICIES))
        )
    require_review_completion = bool(payload.get("require_review_completion", False))

    review_labels_root = None
    if payload.get("review_labels_root") not in (None, ""):
        review_labels_root = resolve_value_path(
            payload.get("review_labels_root"),
            base_dir,
            "review_labels_root",
        )
    if missing_label_policy == "use_review_labels" and review_labels_root is None:
        raise BuildConfigError("missing_label_policy=use_review_labels 时必须提供 review_labels_root。")

    split_manifest_csv = None
    if payload.get("split_manifest_csv") not in (None, ""):
        split_manifest_csv = resolve_value_path(
            payload.get("split_manifest_csv"),
            base_dir,
            "split_manifest_csv",
        )
    strict_split_manifest = bool(payload.get("strict_split_manifest", False))

    raw_sequences = payload.get("sequences")
    if not isinstance(raw_sequences, Sequence) or isinstance(raw_sequences, (str, bytes)):
        raise BuildConfigError("sequences 必须是数组。")

    sequences: List[SequenceConfig] = []
    seen_sequence_keys = set()
    for index, raw_item in enumerate(raw_sequences):
        if not isinstance(raw_item, Mapping):
            raise BuildConfigError("sequences[{0}] 必须是对象。".format(index))
        source_id = coerce_string(raw_item.get("source_id"), "sequences[{0}].source_id".format(index))
        sequence_name = coerce_string(
            raw_item.get("sequence_name"),
            "sequences[{0}].sequence_name".format(index),
        )
        split = coerce_string(raw_item.get("split"), "sequences[{0}].split".format(index))
        if split not in SUPPORTED_SPLITS:
            raise BuildConfigError(
                "sequences[{0}].split 仅支持 {1}。".format(index, list(SUPPORTED_SPLITS))
            )
        sequence_key = (source_id, sequence_name)
        if sequence_key in seen_sequence_keys:
            raise BuildConfigError("存在重复 sequence: {0}/{1}".format(source_id, sequence_name))
        seen_sequence_keys.add(sequence_key)
        image_root = resolve_value_path(
            raw_item.get("image_root"),
            base_dir,
            "sequences[{0}].image_root".format(index),
        )
        label_root = resolve_value_path(
            raw_item.get("label_root"),
            base_dir,
            "sequences[{0}].label_root".format(index),
        )
        sequences.append(
            SequenceConfig(
                source_id=source_id,
                sequence_name=sequence_name,
                image_root=image_root,
                label_root=label_root,
                split=split,
            )
        )

    return {
        "config_path": config_path,
        "dataset_name": dataset_name,
        "output_root": output_root,
        "review_root": review_root,
        "review_labels_root": review_labels_root,
        "split_manifest_csv": split_manifest_csv,
        "strict_split_manifest": strict_split_manifest,
        "train_project_config": train_project_config,
        "recommended_run_name": recommended_run_name,
        "class_names": class_names,
        "allowed_class_ids": set(class_names),
        "image_extensions": set(image_extensions),
        "missing_label_policy": missing_label_policy,
        "require_review_completion": require_review_completion,
        "sequences": sequences,
    }


def load_label_lookup(label_root: Path) -> Dict[str, Path]:
    if not label_root.exists():
        raise DatasetBuildError("标注目录不存在: {0}".format(label_root))
    if not label_root.is_dir():
        raise DatasetBuildError("标注路径不是目录: {0}".format(label_root))

    lookup: Dict[str, Path] = {}
    for label_path in sorted(label_root.glob("*.txt")):
        if label_path.name.lower() in IGNORED_LABEL_FILENAMES:
            continue
        if label_path.stem in lookup:
            raise DatasetBuildError(
                "标注目录存在重名 stem，无法安全配对: {0} <-> {1}".format(
                    lookup[label_path.stem],
                    label_path,
                )
            )
        lookup[label_path.stem] = label_path
    return lookup


def iter_image_paths(image_root: Path, allowed_extensions: Iterable[str]) -> List[Path]:
    if not image_root.exists():
        raise DatasetBuildError("图片目录不存在: {0}".format(image_root))
    if not image_root.is_dir():
        raise DatasetBuildError("图片路径不是目录: {0}".format(image_root))
    suffixes = {item.lower() for item in allowed_extensions}
    image_paths = [
        path
        for path in sorted(image_root.iterdir())
        if path.is_file() and path.suffix.lower() in suffixes
    ]
    if not image_paths:
        raise DatasetBuildError("图片目录为空或没有支持的图片: {0}".format(image_root))
    return image_paths


def normalize_label_lines(label_path: Path, allowed_class_ids: Sequence[int]) -> List[str]:
    try:
        raw_text = label_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw_text = label_path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        raise DatasetBuildError("读取标注失败: {0}".format(label_path)) from exc

    normalized_lines: List[str] = []
    for line_number, line in enumerate(raw_text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        if len(parts) != 5:
            raise DatasetBuildError(
                "{0}:{1} 不是合法 YOLO 标注，字段数应为 5，实际为 {2}。".format(
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
            raise DatasetBuildError(
                "{0}:{1} 含有非数字字段。".format(label_path, line_number)
            ) from exc

        if class_id not in allowed_class_ids:
            raise DatasetBuildError(
                "{0}:{1} class_id 非法，当前仅允许 {2}。".format(
                    label_path,
                    line_number,
                    sorted(allowed_class_ids),
                )
            )

        numeric_fields = [x_center, y_center, width, height]
        if any(
            value < -COORD_TOLERANCE or value > 1.0 + COORD_TOLERANCE
            for value in numeric_fields
        ):
            raise DatasetBuildError(
                "{0}:{1} 坐标必须归一化到 [0,1]。".format(label_path, line_number)
            )

        x_center = min(max(x_center, 0.0), 1.0)
        y_center = min(max(y_center, 0.0), 1.0)
        width = min(max(width, 0.0), 1.0)
        height = min(max(height, 0.0), 1.0)
        if width <= 0.0 or height <= 0.0:
            raise DatasetBuildError(
                "{0}:{1} width/height 必须大于 0。".format(label_path, line_number)
            )

        x1 = x_center - width / 2.0
        y1 = y_center - height / 2.0
        x2 = x_center + width / 2.0
        y2 = y_center + height / 2.0
        edge_overshoot = max(0.0, -x1, -y1, x2 - 1.0, y2 - 1.0)
        if edge_overshoot > BOX_EDGE_TOLERANCE:
            raise DatasetBuildError(
                "{0}:{1} 标注框超出图像边界。".format(label_path, line_number)
            )
        if edge_overshoot > 0.0:
            clipped_x1 = min(max(x1, 0.0), 1.0)
            clipped_y1 = min(max(y1, 0.0), 1.0)
            clipped_x2 = min(max(x2, 0.0), 1.0)
            clipped_y2 = min(max(y2, 0.0), 1.0)
            if clipped_x2 <= clipped_x1 or clipped_y2 <= clipped_y1:
                raise DatasetBuildError(
                    "{0}:{1} 裁剪边界后标注框面积为 0。".format(label_path, line_number)
                )
            x_center = (clipped_x1 + clipped_x2) / 2.0
            y_center = (clipped_y1 + clipped_y2) / 2.0
            width = clipped_x2 - clipped_x1
            height = clipped_y2 - clipped_y1

        normalized_lines.append(
            "{0} {1:.6f} {2:.6f} {3:.6f} {4:.6f}".format(
                class_id,
                x_center,
                y_center,
                width,
                height,
            )
        )

    return normalized_lines


def load_image_size(image_path: Path) -> tuple[int, int]:
    image = cv2.imread(str(image_path))
    if image is None:
        raise DatasetBuildError("无法读取图片: {0}".format(image_path))
    height, width = image.shape[:2]
    if width <= 0 or height <= 0:
        raise DatasetBuildError("图片尺寸非法: {0}".format(image_path))
    return width, height


def ensure_output_root(output_root: Path, overwrite: bool) -> None:
    if output_root.exists():
        if not overwrite:
            raise DatasetBuildError(
                "输出目录已存在，若确认覆盖请追加 --overwrite: {0}".format(output_root)
            )
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)


def write_dataset_yaml(output_root: Path, class_names: Mapping[int, str]) -> Path:
    dataset_yaml = output_root / "dataset.yaml"
    lines = [
        "path: {0}".format(output_root.as_posix()),
        "train: images/train",
        "val: images/val",
        "test: images/test",
        "names:",
    ]
    for class_id, class_name in sorted(class_names.items()):
        lines.append("  {0}: {1}".format(class_id, class_name))
    dataset_yaml.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dataset_yaml


def write_manifest(output_root: Path, samples: Sequence[IncludedSample]) -> Path:
    manifest_path = output_root / "manifest.csv"
    fieldnames = [
        "source_id",
        "sequence_name",
        "split",
        "assignment_source",
        "assignment_note",
        "holdout_group",
        "original_stem",
        "merged_stem",
        "original_image_path",
        "label_source_path",
        "label_origin",
        "sample_role",
        "merged_image_relpath",
        "merged_label_relpath",
        "box_count",
        "image_width",
        "image_height",
    ]
    with manifest_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for sample in samples:
            writer.writerow(
                {
                    "source_id": sample.source_id,
                    "sequence_name": sample.sequence_name,
                    "split": sample.split,
                    "assignment_source": sample.assignment_source,
                    "assignment_note": sample.assignment_note,
                    "holdout_group": sample.holdout_group or "",
                    "original_stem": sample.original_stem,
                    "merged_stem": sample.merged_stem,
                    "original_image_path": str(sample.image_path),
                    "label_source_path": str(sample.label_source_path),
                    "label_origin": sample.label_origin,
                    "sample_role": sample.sample_role,
                    "merged_image_relpath": "images/{0}/{1}.jpg".format(
                        sample.split,
                        sample.merged_stem,
                    ),
                    "merged_label_relpath": "labels/{0}/{1}.txt".format(
                        sample.split,
                        sample.merged_stem,
                    ),
                    "box_count": sample.box_count,
                    "image_width": sample.image_width,
                    "image_height": sample.image_height,
                }
            )
    return manifest_path


def write_missing_review_csv(review_root: Path, items: Sequence[MissingReviewItem]) -> Path:
    review_root.mkdir(parents=True, exist_ok=True)
    review_csv = review_root / "missing_review.csv"
    fieldnames = [
        "source_id",
        "sequence_name",
        "split",
        "original_stem",
        "merged_stem",
        "original_image_path",
        "expected_review_label_path",
        "review_status",
        "review_box_count",
        "note",
    ]
    with review_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "source_id": item.source_id,
                    "sequence_name": item.sequence_name,
                    "split": item.split,
                    "original_stem": item.original_stem,
                    "merged_stem": item.merged_stem,
                    "original_image_path": str(item.original_image_path),
                    "expected_review_label_path": (
                        str(item.expected_review_label_path)
                        if item.expected_review_label_path is not None
                        else ""
                    ),
                    "review_status": item.review_status,
                    "review_box_count": item.review_box_count,
                    "note": item.note,
                }
            )
    return review_csv


def build_training_commands(
    *,
    project_config: Optional[Path],
    dataset_yaml: Path,
    recommended_run_name: str,
    output_root: Path,
) -> Dict[str, str]:
    python_exe = r"D:\Miniconda3_python\envs\yolo_code\python.exe"
    script_path = Path("backend-train-model") / "train_workwear.py"
    project_config_flag = ""
    if project_config is not None:
        project_config_flag = " --project-config {0}".format(project_config)

    train_cmd = (
        f"{python_exe} {script_path}"
        f" train{project_config_flag}"
        f" --dataset-yaml {dataset_yaml}"
        f" --name {recommended_run_name}"
    )
    weights_path = (
        output_root.parent.parent / "artifacts" / "runs" / recommended_run_name / "weights" / "best.pt"
    )
    evaluate_cmd = (
        f"{python_exe} {script_path}"
        f" evaluate{project_config_flag}"
        f" --dataset-yaml {dataset_yaml}"
        f" --weights {weights_path}"
    )
    export_cmd = (
        f"{python_exe} {script_path}"
        f" export{project_config_flag}"
        f" --weights {weights_path}"
        f" --overwrite"
    )
    return {
        "train": train_cmd,
        "evaluate": evaluate_cmd,
        "export": export_cmd,
    }


def build_dataset(config_payload: Dict[str, object], overwrite: bool) -> Dict[str, object]:
    config_path = config_payload["config_path"]
    dataset_name = config_payload["dataset_name"]
    output_root = config_payload["output_root"]
    review_root = config_payload["review_root"]
    review_labels_root = config_payload["review_labels_root"]
    split_manifest_csv = config_payload["split_manifest_csv"]
    strict_split_manifest = config_payload["strict_split_manifest"]
    train_project_config = config_payload["train_project_config"]
    recommended_run_name = config_payload["recommended_run_name"]
    class_names = config_payload["class_names"]
    allowed_class_ids = config_payload["allowed_class_ids"]
    image_extensions = config_payload["image_extensions"]
    missing_label_policy = config_payload["missing_label_policy"]
    require_review_completion = config_payload["require_review_completion"]
    sequences: List[SequenceConfig] = config_payload["sequences"]
    split_assignments = (
        load_split_assignments(split_manifest_csv) if split_manifest_csv is not None else {}
    )
    used_split_assignment_keys: Set[Tuple[str, str, str]] = set()

    label_lookup_cache: Dict[Path, Dict[str, Path]] = {}
    included_samples: List[IncludedSample] = []
    missing_review_items: List[MissingReviewItem] = []
    sequence_summaries: List[Dict[str, object]] = []
    total_source_images = 0
    skipped_by_split_manifest = 0
    split_image_counts = {split: 0 for split in SUPPORTED_SPLITS}
    split_box_counts = {split: 0 for split in SUPPORTED_SPLITS}
    split_source_counts = {split: {} for split in SUPPORTED_SPLITS}
    split_role_counts = {split: {} for split in SUPPORTED_SPLITS}
    split_source_role_counts = {split: {} for split in SUPPORTED_SPLITS}
    assignment_source_counts = {"sequence_default": 0, "split_manifest": 0}

    for sequence in sequences:
        label_lookup = label_lookup_cache.get(sequence.label_root)
        if label_lookup is None:
            label_lookup = load_label_lookup(sequence.label_root)
            label_lookup_cache[sequence.label_root] = label_lookup

        image_paths = iter_image_paths(sequence.image_root, image_extensions)
        total_source_images += len(image_paths)
        matched_count = 0
        included_count = 0
        missing_count = 0
        sequence_box_count = 0
        sequence_split_counts = {split: 0 for split in SUPPORTED_SPLITS}
        sequence_assignment_source_counts = {"sequence_default": 0, "split_manifest": 0}
        sequence_skipped_by_split_manifest = 0

        for image_path in image_paths:
            original_stem = image_path.stem
            merged_stem = "{0}__{1}".format(sequence.source_id, original_stem)
            sample_key = (sequence.source_id, sequence.sequence_name, original_stem)
            split_assignment = split_assignments.get(sample_key)
            resolved_split = sequence.split
            assignment_source = "sequence_default"
            assignment_note = ""
            holdout_group = None
            if split_assignment is not None:
                if split_assignment.merged_stem is not None and split_assignment.merged_stem != merged_stem:
                    raise DatasetBuildError(
                        "split_manifest_csv 中的 merged_stem 与实际样本不一致: {0}/{1}/{2}".format(
                            sequence.source_id,
                            sequence.sequence_name,
                            original_stem,
                        )
                    )
                resolved_split = split_assignment.split
                assignment_source = "split_manifest"
                assignment_note = split_assignment.note
                holdout_group = split_assignment.holdout_group
                used_split_assignment_keys.add(sample_key)
            label_path = label_lookup.get(original_stem)
            label_origin = "source"

            if label_path is not None:
                normalized_lines = normalize_label_lines(label_path, allowed_class_ids)
                matched_count += 1
            else:
                missing_count += 1
                review_label_path = None
                review_status = "pending"
                review_box_count = 0
                note = "source label missing"
                normalized_lines = []
                if review_labels_root is not None:
                    review_label_path = review_labels_root / "{0}.txt".format(merged_stem)
                    if review_label_path.exists():
                        normalized_lines = normalize_label_lines(review_label_path, allowed_class_ids)
                        label_path = review_label_path
                        label_origin = "review"
                        matched_count += 1
                        review_box_count = len(normalized_lines)
                        review_status = (
                            "resolved_positive" if normalized_lines else "resolved_negative"
                        )
                        note = "resolved from review_labels_root"
                missing_review_items.append(
                    MissingReviewItem(
                        source_id=sequence.source_id,
                        sequence_name=sequence.sequence_name,
                        split=resolved_split,
                        original_stem=original_stem,
                        merged_stem=merged_stem,
                        original_image_path=image_path,
                        expected_review_label_path=review_label_path,
                        review_status=review_status,
                        review_box_count=review_box_count,
                        note=note,
                    )
                )
                if label_path is None:
                    if missing_label_policy in SUPPORTED_POLICIES:
                        continue
                    raise DatasetBuildError(
                        "不支持的 missing_label_policy: {0}".format(missing_label_policy)
                    )

            if split_assignments and split_assignment is None and strict_split_manifest:
                raise DatasetBuildError(
                    "split_manifest_csv 未覆盖样本: {0}/{1}/{2}".format(
                        sequence.source_id,
                        sequence.sequence_name,
                        original_stem,
                    )
                )
            if resolved_split == "skip":
                skipped_by_split_manifest += 1
                sequence_skipped_by_split_manifest += 1
                continue

            width, height = load_image_size(image_path)
            box_count = len(normalized_lines)
            sample_role = determine_sample_role(label_origin=label_origin, box_count=box_count)
            sequence_box_count += box_count
            included_count += 1
            split_image_counts[resolved_split] += 1
            split_box_counts[resolved_split] += box_count
            split_source_counts[resolved_split][sequence.source_id] = (
                split_source_counts[resolved_split].get(sequence.source_id, 0) + 1
            )
            split_role_counts[resolved_split][sample_role] = (
                split_role_counts[resolved_split].get(sample_role, 0) + 1
            )
            source_role_counts = split_source_role_counts[resolved_split].setdefault(sequence.source_id, {})
            source_role_counts[sample_role] = source_role_counts.get(sample_role, 0) + 1
            assignment_source_counts[assignment_source] = assignment_source_counts.get(assignment_source, 0) + 1
            sequence_split_counts[resolved_split] += 1
            sequence_assignment_source_counts[assignment_source] = (
                sequence_assignment_source_counts.get(assignment_source, 0) + 1
            )
            included_samples.append(
                IncludedSample(
                    source_id=sequence.source_id,
                    sequence_name=sequence.sequence_name,
                    split=resolved_split,
                    assignment_source=assignment_source,
                    assignment_note=assignment_note,
                    holdout_group=holdout_group,
                    original_stem=original_stem,
                    merged_stem=merged_stem,
                    image_path=image_path,
                    label_source_path=label_path,
                    label_origin=label_origin,
                    sample_role=sample_role,
                    label_lines=normalized_lines,
                    box_count=box_count,
                    image_width=width,
                    image_height=height,
                )
            )

        sequence_summaries.append(
            {
                "source_id": sequence.source_id,
                "sequence_name": sequence.sequence_name,
                "configured_split": sequence.split,
                "image_root": str(sequence.image_root),
                "label_root": str(sequence.label_root),
                "source_images": len(image_paths),
                "included_images": included_count,
                "matched_images": matched_count,
                "missing_source_labels": missing_count,
                "included_boxes": sequence_box_count,
                "actual_split_counts": sequence_split_counts,
                "assignment_source_counts": sequence_assignment_source_counts,
                "skipped_by_split_manifest": sequence_skipped_by_split_manifest,
            }
        )

    review_csv = write_missing_review_csv(review_root, missing_review_items)
    pending_review_items = [
        item for item in missing_review_items if item.review_status == "pending"
    ]
    if require_review_completion and pending_review_items:
        raise DatasetBuildError(
            "仍有 {0} 张缺标图片未完成 review，已输出清单: {1}".format(
                len(pending_review_items),
                review_csv,
            )
        )

    ensure_output_root(output_root, overwrite)
    for split_name in SUPPORTED_SPLITS:
        (output_root / "images" / split_name).mkdir(parents=True, exist_ok=True)
        (output_root / "labels" / split_name).mkdir(parents=True, exist_ok=True)

    for sample in included_samples:
        target_image = output_root / "images" / sample.split / "{0}.jpg".format(sample.merged_stem)
        target_label = output_root / "labels" / sample.split / "{0}.txt".format(sample.merged_stem)
        shutil.copy2(sample.image_path, target_image)
        target_label.write_text(
            "\n".join(sample.label_lines) + ("\n" if sample.label_lines else ""),
            encoding="utf-8",
        )

    dataset_yaml = write_dataset_yaml(output_root, class_names)
    manifest_csv = write_manifest(output_root, included_samples)
    commands = build_training_commands(
        project_config=train_project_config,
        dataset_yaml=dataset_yaml,
        recommended_run_name=recommended_run_name,
        output_root=output_root,
    )
    build_report = {
        "dataset_name": dataset_name,
        "config_path": str(config_path),
        "output_root": str(output_root),
        "review_root": str(review_root),
        "review_labels_root": str(review_labels_root) if review_labels_root is not None else None,
        "train_project_config": str(train_project_config) if train_project_config is not None else None,
        "recommended_run_name": recommended_run_name,
        "class_names": {str(class_id): name for class_id, name in sorted(class_names.items())},
        "image_extensions": sorted(image_extensions),
        "missing_label_policy": missing_label_policy,
        "require_review_completion": require_review_completion,
        "counts": {
            "source_images": total_source_images,
            "included_images": len(included_samples),
            "included_boxes": sum(sample.box_count for sample in included_samples),
            "missing_source_labels": len(missing_review_items),
            "pending_review_items": len(pending_review_items),
            "resolved_review_items": len(
                [item for item in missing_review_items if item.review_status != "pending"]
            ),
            "skipped_by_split_manifest": skipped_by_split_manifest,
            "split_image_counts": split_image_counts,
            "split_box_counts": split_box_counts,
            "split_source_counts": split_source_counts,
            "split_role_counts": split_role_counts,
            "split_source_role_counts": split_source_role_counts,
            "assignment_source_counts": assignment_source_counts,
        },
        "files": {
            "dataset_yaml": str(dataset_yaml),
            "manifest_csv": str(manifest_csv),
            "missing_review_csv": str(review_csv),
        },
        "split_manifest": {
            "path": str(split_manifest_csv) if split_manifest_csv is not None else None,
            "strict": strict_split_manifest,
            "loaded_rows": len(split_assignments),
            "used_rows": len(used_split_assignment_keys),
            "unused_rows": len(split_assignments) - len(used_split_assignment_keys),
        },
        "sequences": sequence_summaries,
        "commands": commands,
    }
    build_report_path = output_root / "build_report.json"
    build_report_path.write_text(
        json.dumps(build_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return build_report


def main() -> int:
    args = parse_args()
    config_path = resolve_config_path(args.config)
    try:
        config_payload = load_build_config(config_path)
        report = build_dataset(config_payload, overwrite=bool(args.overwrite))
    except (BuildConfigError, DatasetBuildError) as exc:
        print("构建失败: {0}".format(exc))
        return 1

    counts = report["counts"]
    print("构建完成")
    print("dataset_name      : {0}".format(report["dataset_name"]))
    print("output_root       : {0}".format(report["output_root"]))
    print("dataset_yaml      : {0}".format(report["files"]["dataset_yaml"]))
    print("manifest_csv      : {0}".format(report["files"]["manifest_csv"]))
    print("missing_review_csv: {0}".format(report["files"]["missing_review_csv"]))
    print("source_images     : {0}".format(counts["source_images"]))
    print("included_images   : {0}".format(counts["included_images"]))
    print("included_boxes    : {0}".format(counts["included_boxes"]))
    print("missing_labels    : {0}".format(counts["missing_source_labels"]))
    print("skipped_by_split  : {0}".format(counts["skipped_by_split_manifest"]))
    print("split_images      : {0}".format(counts["split_image_counts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

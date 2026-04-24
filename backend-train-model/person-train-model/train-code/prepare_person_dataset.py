from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Set


SCRIPT_ROOT = Path(__file__).resolve().parent
PERSON_ROOT = SCRIPT_ROOT.parent
DEFAULT_PROJECT_CONFIG = PERSON_ROOT / "person_project_config.json"


@dataclass(frozen=True)
class PersonSequence:
    source_id: str
    group: str
    sequence_name: str
    image_root: Path
    label_root: Path


@dataclass(frozen=True)
class RoiSettings:
    enabled: bool
    mode: str
    json_root: Path
    work_root: Path
    center_inside: bool
    bottom_center_inside: bool
    min_box_ioa: float
    config_path: Path


@dataclass(frozen=True)
class PersonProjectContext:
    config_path: Path
    config_dir: Path
    artifacts_root: Path
    image_roots: List[Path]
    image_extensions: List[str]
    class_names: Dict[int, str]
    split_ratios: Dict[str, float]
    default_split_strategy: str
    sequences: List[PersonSequence]
    aggregated_label_root: Path
    summary_path: Path
    prepared_output_root: Path
    roi_aware_prepared_output_root: Path
    export_alias_path: Path
    export_alias_metadata_path: Path
    recommended_run_name: str
    roi_aware_recommended_run_name: str
    roi: RoiSettings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="汇总 person 标签并为缺标图片补空白负样本。"
    )
    parser.add_argument(
        "--project-config",
        default=str(DEFAULT_PROJECT_CONFIG),
        help="person 项目配置 JSON 路径。",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="允许覆盖既有汇总标签目录。",
    )
    return parser.parse_args()


def load_json(path: Path) -> Dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError("读取配置失败: {0}".format(path)) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("配置 JSON 格式无效: {0}".format(path)) from exc
    if not isinstance(payload, dict):
        raise RuntimeError("配置顶层必须是对象: {0}".format(path))
    return payload


def resolve_path(raw_value: object, base_dir: Path, field_name: str) -> Path:
    text = str(raw_value).strip()
    if not text:
        raise RuntimeError("{0} 不能为空。".format(field_name))
    candidate = Path(text).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (base_dir / candidate).resolve()


def coerce_string(raw_value: object, field_name: str) -> str:
    text = str(raw_value).strip()
    if not text:
        raise RuntimeError("{0} 不能为空。".format(field_name))
    return text


def coerce_bool(raw_value: object, field_name: str) -> bool:
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, str):
        normalized = raw_value.strip().lower()
        if normalized in ("1", "true", "yes", "y", "on"):
            return True
        if normalized in ("0", "false", "no", "n", "off"):
            return False
    raise RuntimeError("{0} 必须是布尔值。".format(field_name))


def coerce_ratio(raw_value: object, field_name: str) -> float:
    try:
        value = float(raw_value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("{0} 必须是数字。".format(field_name)) from exc
    if value < 0.0 or value > 1.0:
        raise RuntimeError("{0} 必须位于 [0, 1]。".format(field_name))
    return value


def coerce_class_names(raw_value: object) -> Dict[int, str]:
    if not isinstance(raw_value, Mapping):
        raise RuntimeError("data.class_names 必须是对象。")
    normalized: Dict[int, str] = {}
    for raw_key, raw_name in raw_value.items():
        class_id = int(raw_key)
        class_name = str(raw_name).strip()
        if not class_name:
            raise RuntimeError("data.class_names 中存在空类别名。")
        normalized[class_id] = class_name
    if not normalized:
        raise RuntimeError("data.class_names 不能为空。")
    return dict(sorted(normalized.items()))


def coerce_image_extensions(raw_value: object) -> List[str]:
    if not isinstance(raw_value, Sequence) or isinstance(raw_value, (str, bytes)):
        raise RuntimeError("data.image_extensions 必须是字符串列表。")
    normalized: List[str] = []
    for item in raw_value:
        suffix = str(item).strip().lower()
        if not suffix:
            continue
        if not suffix.startswith("."):
            suffix = ".{0}".format(suffix)
        normalized.append(suffix)
    if not normalized:
        raise RuntimeError("data.image_extensions 不能为空。")
    return normalized


def coerce_split_ratios(raw_value: object) -> Dict[str, float]:
    if not isinstance(raw_value, Mapping):
        raise RuntimeError("data.split_ratios 必须是对象。")
    normalized: Dict[str, float] = {}
    for split_name in ("train", "val", "test"):
        try:
            ratio = float(raw_value.get(split_name, 0.0))
        except (TypeError, ValueError) as exc:
            raise RuntimeError("data.split_ratios.{0} 必须是数字。".format(split_name)) from exc
        if ratio < 0:
            raise RuntimeError("data.split_ratios.{0} 不能为负数。".format(split_name))
        normalized[split_name] = ratio
    if sum(normalized.values()) <= 0:
        raise RuntimeError("data.split_ratios 至少需要一个正数比例。")
    return normalized


def load_person_project_context(config_path: Path) -> PersonProjectContext:
    resolved_path = Path(config_path).expanduser().resolve()
    payload = load_json(resolved_path)
    config_dir = resolved_path.parent

    artifacts_section = payload.get("artifacts")
    if not isinstance(artifacts_section, Mapping):
        raise RuntimeError("配置缺少 `artifacts` 段。")
    artifacts_root = resolve_path(artifacts_section.get("root"), config_dir, "artifacts.root")

    data_section = payload.get("data")
    if not isinstance(data_section, Mapping):
        raise RuntimeError("配置缺少 `data` 段。")
    image_roots = [
        resolve_path(item, config_dir, "data.image_roots")
        for item in data_section.get("image_roots", [])
    ]
    image_extensions = coerce_image_extensions(data_section.get("image_extensions", [".jpg"]))
    class_names = coerce_class_names(data_section.get("class_names", {0: "person"}))
    split_ratios = coerce_split_ratios(
        data_section.get("split_ratios", {"train": 0.7, "val": 0.15, "test": 0.15})
    )
    default_split_strategy = coerce_string(
        data_section.get("default_split_strategy", "sequence_contiguous"),
        "data.default_split_strategy",
    )
    if default_split_strategy not in ("sequence_contiguous", "sequence_holdout"):
        raise RuntimeError(
            "data.default_split_strategy 仅支持 sequence_contiguous 或 sequence_holdout。"
        )

    person_dataset_section = payload.get("person_dataset")
    if not isinstance(person_dataset_section, Mapping):
        raise RuntimeError("配置缺少 `person_dataset` 段。")
    raw_sequences = person_dataset_section.get("sequences")
    if not isinstance(raw_sequences, Sequence) or isinstance(raw_sequences, (str, bytes)):
        raise RuntimeError("person_dataset.sequences 必须是数组。")

    sequences: List[PersonSequence] = []
    for index, raw_item in enumerate(raw_sequences):
        if not isinstance(raw_item, Mapping):
            raise RuntimeError("person_dataset.sequences[{0}] 必须是对象。".format(index))
        sequences.append(
            PersonSequence(
                source_id=coerce_string(
                    raw_item.get("source_id"),
                    "person_dataset.sequences[{0}].source_id".format(index),
                ),
                group=coerce_string(
                    raw_item.get("group"),
                    "person_dataset.sequences[{0}].group".format(index),
                ),
                sequence_name=coerce_string(
                    raw_item.get("sequence_name"),
                    "person_dataset.sequences[{0}].sequence_name".format(index),
                ),
                image_root=resolve_path(
                    raw_item.get("image_root"),
                    config_dir,
                    "person_dataset.sequences[{0}].image_root".format(index),
                ),
                label_root=resolve_path(
                    raw_item.get("label_root"),
                    config_dir,
                    "person_dataset.sequences[{0}].label_root".format(index),
                ),
            )
        )

    sequence_image_roots = [sequence.image_root for sequence in sequences]
    if image_roots and image_roots != sequence_image_roots:
        raise RuntimeError(
            "`data.image_roots` 与 `person_dataset.sequences[*].image_root` 不一致，请统一配置。"
        )

    roi_section = payload.get("roi", {})
    if roi_section is None:
        roi_section = {}
    if not isinstance(roi_section, Mapping):
        raise RuntimeError("配置中的 `roi` 段必须是对象。")
    keep_rule_section = roi_section.get("keep_rule", {})
    if keep_rule_section is None:
        keep_rule_section = {}
    if not isinstance(keep_rule_section, Mapping):
        raise RuntimeError("配置中的 `roi.keep_rule` 段必须是对象。")

    roi_mode = coerce_string(roi_section.get("mode", "mask_then_crop"), "roi.mode")
    if roi_mode != "mask_then_crop":
        raise RuntimeError("当前 ROI-aware 仅支持 roi.mode=mask_then_crop。")

    roi_center_inside = coerce_bool(
        keep_rule_section.get("center_inside", True),
        "roi.keep_rule.center_inside",
    )
    roi_bottom_center_inside = coerce_bool(
        keep_rule_section.get("bottom_center_inside", False),
        "roi.keep_rule.bottom_center_inside",
    )
    roi_min_box_ioa = coerce_ratio(
        keep_rule_section.get("min_box_ioa", 0.0),
        "roi.keep_rule.min_box_ioa",
    )
    if (
        not roi_center_inside
        and not roi_bottom_center_inside
        and roi_min_box_ioa <= 0.0
    ):
        raise RuntimeError(
            "roi.keep_rule 至少需要启用一种保留条件：center_inside、bottom_center_inside 或 min_box_ioa。"
        )

    return PersonProjectContext(
        config_path=resolved_path,
        config_dir=config_dir,
        artifacts_root=artifacts_root,
        image_roots=sequence_image_roots,
        image_extensions=image_extensions,
        class_names=class_names,
        split_ratios=split_ratios,
        default_split_strategy=default_split_strategy,
        sequences=sequences,
        aggregated_label_root=resolve_path(
            person_dataset_section.get("aggregated_label_root"),
            config_dir,
            "person_dataset.aggregated_label_root",
        ),
        summary_path=resolve_path(
            person_dataset_section.get("summary_path"),
            config_dir,
            "person_dataset.summary_path",
        ),
        prepared_output_root=resolve_path(
            person_dataset_section.get("prepared_output_root"),
            config_dir,
            "person_dataset.prepared_output_root",
        ),
        roi_aware_prepared_output_root=resolve_path(
            person_dataset_section.get(
                "roi_aware_prepared_output_root",
                "train-result/prepared/person_roi_aware/sequence_contiguous",
            ),
            config_dir,
            "person_dataset.roi_aware_prepared_output_root",
        ),
        export_alias_path=resolve_path(
            person_dataset_section.get("export_alias_path"),
            config_dir,
            "person_dataset.export_alias_path",
        ),
        export_alias_metadata_path=resolve_path(
            person_dataset_section.get("export_alias_metadata_path"),
            config_dir,
            "person_dataset.export_alias_metadata_path",
        ),
        recommended_run_name=coerce_string(
            person_dataset_section.get("recommended_run_name", "person_fullframe_baseline"),
            "person_dataset.recommended_run_name",
        ),
        roi_aware_recommended_run_name=coerce_string(
            person_dataset_section.get(
                "roi_aware_recommended_run_name",
                "person_roi_aware_baseline",
            ),
            "person_dataset.roi_aware_recommended_run_name",
        ),
        roi=RoiSettings(
            enabled=coerce_bool(roi_section.get("enabled", False), "roi.enabled"),
            mode=roi_mode,
            json_root=resolve_path(
                roi_section.get(
                    "json_root",
                    roi_section.get("work_root", "roi-work"),
                ),
                config_dir,
                "roi.json_root",
            ),
            work_root=resolve_path(
                roi_section.get("work_root", "roi-work"),
                config_dir,
                "roi.work_root",
            ),
            center_inside=roi_center_inside,
            bottom_center_inside=roi_bottom_center_inside,
            min_box_ioa=roi_min_box_ioa,
            config_path=resolve_path(
                roi_section.get(
                    "config_path",
                    "train-result/working/roi/roi_config.generated.json",
                ),
                config_dir,
                "roi.config_path",
            ),
        ),
    )


def assert_directory_within_root(target_path: Path, root_path: Path) -> None:
    target = target_path.resolve()
    root = root_path.resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(
            "目标目录不在允许范围内，拒绝删除: {0} (root={1})".format(target, root)
        ) from exc


def iter_image_paths(image_root: Path, image_extensions: Sequence[str]) -> List[Path]:
    allowed = {suffix.lower() for suffix in image_extensions}
    return sorted(
        [
            path
            for path in image_root.iterdir()
            if path.is_file() and path.suffix.lower() in allowed
        ]
    )


def load_label_lookup(label_root: Path) -> Dict[str, Path]:
    lookup: Dict[str, Path] = {}
    for path in sorted(label_root.glob("*.txt")):
        if path.name.lower() == "classes.txt":
            continue
        if path.stem in lookup:
            raise RuntimeError("标签目录存在重复 stem: {0} -> {1}".format(path.stem, label_root))
        lookup[path.stem] = path
    return lookup


def prepare_person_labels(
    context: PersonProjectContext,
    *,
    overwrite: bool,
) -> Dict[str, object]:
    if context.aggregated_label_root.exists():
        if not overwrite:
            raise RuntimeError(
                "汇总标签目录已存在，请显式传 `--overwrite`: {0}".format(
                    context.aggregated_label_root
                )
            )
        assert_directory_within_root(context.aggregated_label_root, PERSON_ROOT / "train-result")
        shutil.rmtree(context.aggregated_label_root)

    context.aggregated_label_root.mkdir(parents=True, exist_ok=True)

    seen_stems: Dict[str, str] = {}
    missing_labels: List[Dict[str, str]] = []
    empty_source_labels: List[Dict[str, str]] = []
    sequence_summaries: List[Dict[str, object]] = []
    total_images = 0
    total_copied = 0
    total_created_empty = 0
    total_empty_source = 0
    expected_stems_by_label_root: Dict[Path, Set[str]] = {}

    for sequence in context.sequences:
        label_lookup = load_label_lookup(sequence.label_root)
        image_paths = iter_image_paths(sequence.image_root, context.image_extensions)
        image_stems = {path.stem for path in image_paths}
        expected_stems_by_label_root.setdefault(sequence.label_root, set()).update(image_stems)

        copied_count = 0
        created_empty_count = 0
        empty_source_count = 0
        for image_path in image_paths:
            if image_path.stem in seen_stems:
                raise RuntimeError(
                    "检测到跨序列重复 stem，当前结构无法安全配对: {0}\n第一次出现于: {1}\n再次出现于: {2}".format(
                        image_path.stem,
                        seen_stems[image_path.stem],
                        image_path,
                    )
                )
            seen_stems[image_path.stem] = str(image_path)

            target_label = context.aggregated_label_root / "{0}.txt".format(image_path.stem)
            source_label = label_lookup.get(image_path.stem)
            if source_label is None:
                target_label.write_text("", encoding="utf-8")
                created_empty_count += 1
                missing_labels.append(
                    {
                        "source_id": sequence.source_id,
                        "group": sequence.group,
                        "sequence_name": sequence.sequence_name,
                        "image_path": str(image_path),
                        "created_label_path": str(target_label),
                        "policy": "empty_negative",
                    }
                )
            else:
                shutil.copy2(source_label, target_label)
                copied_count += 1
                if not source_label.read_text(encoding="utf-8").strip():
                    empty_source_count += 1
                    empty_source_labels.append(
                        {
                            "source_id": sequence.source_id,
                            "group": sequence.group,
                            "sequence_name": sequence.sequence_name,
                            "image_path": str(image_path),
                            "source_label_path": str(source_label),
                            "copied_label_path": str(target_label),
                            "policy": "existing_empty_negative",
                        }
                    )

        total_images += len(image_paths)
        total_copied += copied_count
        total_created_empty += created_empty_count
        total_empty_source += empty_source_count
        sequence_summaries.append(
            {
                "source_id": sequence.source_id,
                "group": sequence.group,
                "sequence_name": sequence.sequence_name,
                "image_root": str(sequence.image_root),
                "label_root": str(sequence.label_root),
                "image_count": len(image_paths),
                "copied_label_count": copied_count,
                "created_empty_label_count": created_empty_count,
                "empty_source_label_count": empty_source_count,
            }
        )

    source_label_root_summaries: List[Dict[str, object]] = []
    total_extra_labels = 0
    for label_root, expected_stems in sorted(
        expected_stems_by_label_root.items(),
        key=lambda item: str(item[0]),
    ):
        label_lookup = load_label_lookup(label_root)
        extra_labels = sorted(stem for stem in label_lookup.keys() if stem not in expected_stems)
        empty_label_stems = sorted(
            stem
            for stem, label_path in label_lookup.items()
            if stem in expected_stems and not label_path.read_text(encoding="utf-8").strip()
        )
        total_extra_labels += len(extra_labels)
        source_label_root_summaries.append(
            {
                "label_root": str(label_root),
                "source_label_count": len(label_lookup),
                "expected_image_stem_count": len(expected_stems),
                "empty_expected_label_count": len(empty_label_stems),
                "empty_expected_label_stems": empty_label_stems,
                "extra_label_count": len(extra_labels),
                "extra_label_stems": extra_labels,
            }
        )

    classes_path = context.aggregated_label_root / "classes.txt"
    classes_path.write_text(
        "\n".join(name for _, name in sorted(context.class_names.items())) + "\n",
        encoding="utf-8",
    )

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_config": str(context.config_path),
        "aggregated_label_root": str(context.aggregated_label_root),
        "prepared_output_root": str(context.prepared_output_root),
        "recommended_run_name": context.recommended_run_name,
        "class_names": {str(class_id): name for class_id, name in context.class_names.items()},
        "image_extensions": list(context.image_extensions),
        "totals": {
            "images": total_images,
            "copied_labels": total_copied,
            "created_empty_labels": total_created_empty,
            "existing_empty_source_labels": total_empty_source,
            "final_empty_labels": total_created_empty + total_empty_source,
            "extra_source_labels": total_extra_labels,
            "final_training_label_files": total_images,
        },
        "missing_labels_created_as_empty": missing_labels,
        "empty_source_labels": empty_source_labels,
        "source_label_roots": source_label_root_summaries,
        "sequences": sequence_summaries,
    }

    context.summary_path.parent.mkdir(parents=True, exist_ok=True)
    context.summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    args = parse_args()
    context = load_person_project_context(Path(args.project_config))
    summary = prepare_person_labels(context, overwrite=args.overwrite)
    print("汇总标签目录 : {0}".format(context.aggregated_label_root))
    print("统计摘要     : {0}".format(context.summary_path))
    print(
        "总图片={0}, 复制标签={1}, 新建空标签={2}, 源空标签={3}, 最终空标签={4}, 额外源标签={5}".format(
            summary["totals"]["images"],
            summary["totals"]["copied_labels"],
            summary["totals"]["created_empty_labels"],
            summary["totals"]["existing_empty_source_labels"],
            summary["totals"]["final_empty_labels"],
            summary["totals"]["extra_source_labels"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

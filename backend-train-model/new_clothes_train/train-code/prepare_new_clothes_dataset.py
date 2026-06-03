from __future__ import annotations

import csv
import json
import os
import random
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Tuple


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "backend-train-model"
NEW_CLOTHES_ROOT = BACKEND_ROOT / "new_clothes_train"
ALL_TRAIN_ROOT = BACKEND_ROOT / "All-train-model"
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

OLD_BUILD_CONFIG_PATH = ALL_TRAIN_ROOT / "merged_clothes_v2_balanced.build.json"
OLD_TRAINVAL_SPLIT_PATH = ALL_TRAIN_ROOT / "splits" / "trainval_balanced_v1.split.csv"
OLD_HOLDOUT_SPLIT_PATH = ALL_TRAIN_ROOT / "splits" / "unified_holdout_v1.split.csv"

FRAME_LABEL_ROOT = resolve_frame_label_root()
NEW_IMAGE_ROOT = FRAME_LABEL_ROOT / "new_clothes_labels" / "images"
NEW_RAW_LABEL_ROOT = FRAME_LABEL_ROOT / "new_clothes_labels" / "clothes_labels"

NEW_SOURCE_ID = "gnew"
NEW_SEQUENCE_NAME = "new_clothes_flat_2507"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

COMPLETED_LABEL_ROOT = NEW_CLOTHES_ROOT / "train-result" / "working" / "new_source_completed_labels"
SUMMARY_JSON_PATH = NEW_CLOTHES_ROOT / "train-result" / "working" / "new_source_prepare_summary.json"
SPLIT_CSV_PATH = NEW_CLOTHES_ROOT / "splits" / "clothes_merged_with_new_labels_v1.split.csv"
SPLIT_SUMMARY_JSON_PATH = NEW_CLOTHES_ROOT / "splits" / "clothes_merged_with_new_labels_v1_summary.json"

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
SPLIT_SEED = 42


@dataclass(frozen=True)
class SequenceItem:
    source_id: str
    sequence_name: str
    image_root: str
    label_root: str


def load_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_legacy_sequences() -> List[SequenceItem]:
    payload = load_json(OLD_BUILD_CONFIG_PATH)
    sequences: List[SequenceItem] = []
    for raw in payload.get("sequences", []):
        if not isinstance(raw, Mapping):
            continue
        sequences.append(
            SequenceItem(
                source_id=str(raw["source_id"]),
                sequence_name=str(raw["sequence_name"]),
                image_root=str(raw["image_root"]),
                label_root=str(raw["label_root"]),
            )
        )
    return sequences


def load_manifest_rows(path: Path) -> Dict[Tuple[str, str, str], Dict[str, str]]:
    rows: Dict[Tuple[str, str, str], Dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            key = (
                str(row.get("source_id", "")).strip(),
                str(row.get("sequence_name", "")).strip(),
                str(row.get("original_stem", "")).strip(),
            )
            if not all(key):
                raise ValueError(f"manifest 存在空 key: {path}")
            if key in rows:
                raise ValueError(f"manifest 存在重复 key: {key} @ {path}")
            rows[key] = {str(k): str(v or "").strip() for k, v in row.items()}
    return rows


def sanitize_token(raw: str) -> str:
    token = re.sub(r"[^0-9A-Za-z_\-]+", "_", raw.strip())
    return token.strip("_") or "sample"


def build_merged_stem(source_id: str, sequence_name: str, original_stem: str) -> str:
    # 与 build_merged_clothes_dataset.py 的实际 merged_stem 规则保持一致：source_id__original_stem
    _ = sequence_name
    return "__".join([sanitize_token(source_id), sanitize_token(original_stem)])


def sort_stem_key(stem: str) -> Tuple[int, int | str]:
    return (0, int(stem)) if stem.isdigit() else (1, stem)


def list_new_image_paths() -> List[Path]:
    if not NEW_IMAGE_ROOT.exists():
        raise FileNotFoundError(f"图片根目录不存在: {NEW_IMAGE_ROOT}")
    image_paths = [
        path
        for path in NEW_IMAGE_ROOT.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]
    image_paths.sort(key=lambda item: sort_stem_key(item.stem))
    if not image_paths:
        raise RuntimeError(f"未在图片根目录下找到图片: {NEW_IMAGE_ROOT}")
    return image_paths


def has_positive_boxes(label_path: Path) -> bool:
    return any(line.strip() for line in label_path.read_text(encoding="utf-8").splitlines())


def sync_completed_labels(image_paths: Iterable[Path]) -> Dict[str, object]:
    COMPLETED_LABEL_ROOT.mkdir(parents=True, exist_ok=True)

    image_stems = {path.stem for path in image_paths}
    raw_label_paths = {
        path.stem: path
        for path in NEW_RAW_LABEL_ROOT.iterdir()
        if path.is_file() and path.suffix.lower() == ".txt"
    }

    copied_label_count = 0
    created_empty_count = 0
    positive_label_count = 0
    empty_label_count = 0

    for existing in COMPLETED_LABEL_ROOT.glob("*.txt"):
        existing.unlink()

    for image_path in image_paths:
        target_path = COMPLETED_LABEL_ROOT / f"{image_path.stem}.txt"
        source_label_path = raw_label_paths.get(image_path.stem)
        if source_label_path is None:
            target_path.write_text("", encoding="utf-8")
            created_empty_count += 1
            empty_label_count += 1
            continue

        shutil.copyfile(source_label_path, target_path)
        copied_label_count += 1

        stripped_lines = [
            line.strip()
            for line in target_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if stripped_lines:
            positive_label_count += 1
        else:
            empty_label_count += 1

    orphan_label_stems = sorted(set(raw_label_paths) - image_stems, key=sort_stem_key)
    return {
        "new_image_root": str(NEW_IMAGE_ROOT),
        "new_raw_label_root": str(NEW_RAW_LABEL_ROOT),
        "completed_label_root": str(COMPLETED_LABEL_ROOT),
        "image_count": len(image_stems),
        "existing_label_count": copied_label_count,
        "created_empty_label_count": created_empty_count,
        "positive_label_file_count": positive_label_count,
        "empty_label_file_count": empty_label_count,
        "orphan_label_count": len(orphan_label_stems),
        "orphan_label_stems": orphan_label_stems[:50],
    }


def resolve_legacy_split_rows() -> List[Dict[str, str]]:
    trainval_rows = load_manifest_rows(OLD_TRAINVAL_SPLIT_PATH)
    holdout_rows = load_manifest_rows(OLD_HOLDOUT_SPLIT_PATH)

    combined_rows: List[Dict[str, str]] = []
    for key, trainval_row in sorted(trainval_rows.items(), key=lambda item: item[0]):
        holdout_row = holdout_rows.get(key)
        if holdout_row is None:
            raise RuntimeError(f"旧 holdout manifest 缺少样本: {key}")

        holdout_split = holdout_row.get("split", "")
        trainval_split = trainval_row.get("split", "")
        if holdout_split == "test":
            final_split = "test"
            holdout_group = holdout_row.get("holdout_group", "legacy_unified_holdout_v1") or "legacy_unified_holdout_v1"
            note = holdout_row.get("note", "legacy unified holdout v1") or "legacy unified holdout v1"
        else:
            if trainval_split not in {"train", "val"}:
                raise RuntimeError(f"旧 trainval manifest split 非法: {key} -> {trainval_split}")
            final_split = trainval_split
            holdout_group = "legacy_trainval_balanced_v1"
            note = trainval_row.get("note", "legacy trainval balanced v1") or "legacy trainval balanced v1"

        source_id, sequence_name, original_stem = key
        merged_stem = trainval_row.get("merged_stem") or holdout_row.get("merged_stem")
        if not merged_stem:
            merged_stem = build_merged_stem(source_id, sequence_name, original_stem)
        combined_rows.append(
            {
                "source_id": source_id,
                "sequence_name": sequence_name,
                "original_stem": original_stem,
                "split": final_split,
                "merged_stem": merged_stem,
                "holdout_group": holdout_group,
                "note": note,
            }
        )
    return combined_rows


def assign_group_splits(stems: List[str], rng: random.Random) -> Dict[str, str]:
    ordered = list(stems)
    rng.shuffle(ordered)

    total = len(ordered)
    train_count = int(total * TRAIN_RATIO)
    val_count = int(total * VAL_RATIO)
    test_count = total - train_count - val_count

    assignments: Dict[str, str] = {}
    for index, stem in enumerate(ordered):
        if index < train_count:
            split = "train"
        elif index < train_count + val_count:
            split = "val"
        else:
            split = "test"
        assignments[stem] = split
    return assignments


def build_new_source_rows(image_paths: List[Path]) -> List[Dict[str, str]]:
    positive_stems: List[str] = []
    empty_stems: List[str] = []
    for image_path in image_paths:
        label_path = COMPLETED_LABEL_ROOT / f"{image_path.stem}.txt"
        if not label_path.exists():
            raise RuntimeError(f"补齐后的标注不存在: {label_path}")
        if has_positive_boxes(label_path):
            positive_stems.append(image_path.stem)
        else:
            empty_stems.append(image_path.stem)

    rng = random.Random(SPLIT_SEED)
    positive_assignments = assign_group_splits(positive_stems, rng)
    empty_assignments = assign_group_splits(empty_stems, rng)
    split_assignments = {**positive_assignments, **empty_assignments}

    split_counts = Counter(split_assignments.values())
    positive_split_counts = Counter(positive_assignments.values())
    empty_split_counts = Counter(empty_assignments.values())
    note = (
        "new source stratified random split by positive/empty "
        f"seed={SPLIT_SEED}; "
        f"positive(train={positive_split_counts['train']}, val={positive_split_counts['val']}, test={positive_split_counts['test']}), "
        f"empty(train={empty_split_counts['train']}, val={empty_split_counts['val']}, test={empty_split_counts['test']})"
    )

    rows: List[Dict[str, str]] = []
    for image_path in image_paths:
        split = split_assignments[image_path.stem]
        rows.append(
            {
                "source_id": NEW_SOURCE_ID,
                "sequence_name": NEW_SEQUENCE_NAME,
                "original_stem": image_path.stem,
                "split": split,
                "merged_stem": build_merged_stem(NEW_SOURCE_ID, NEW_SEQUENCE_NAME, image_path.stem),
                "holdout_group": "new_source_stratified_random_v2",
                "note": note,
            }
        )

    expected_total = len(image_paths)
    if sum(split_counts.values()) != expected_total:
        raise RuntimeError("gnew stratified split 总数校验失败。")
    return rows


def write_split_csv(rows: List[Dict[str, str]]) -> None:
    SPLIT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source_id",
        "sequence_name",
        "original_stem",
        "split",
        "merged_stem",
        "holdout_group",
        "note",
    ]
    with SPLIT_CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def summarize_split(rows: List[Dict[str, str]], prepare_summary: Dict[str, object]) -> Dict[str, object]:
    split_counts = Counter()
    split_source_counts: Dict[str, Counter[str]] = defaultdict(Counter)
    source_totals = Counter()

    for row in rows:
        split = row["split"]
        source_id = row["source_id"]
        split_counts[split] += 1
        split_source_counts[split][source_id] += 1
        source_totals[source_id] += 1

    return {
        "dataset_name": "clothes_merged_with_new_labels_v1",
        "seed": 42,
        "legacy_old_split_policy": {
            "trainval_manifest": str(OLD_TRAINVAL_SPLIT_PATH),
            "holdout_manifest": str(OLD_HOLDOUT_SPLIT_PATH),
            "description": "旧 7 个 clothes source 保持现有 balanced train/val 与 unified holdout test 分配不变。",
        },
        "new_source_split_policy": {
            "source_id": NEW_SOURCE_ID,
            "sequence_name": NEW_SEQUENCE_NAME,
            "strategy": "stratified_random_by_positive_empty",
            "train_ratio": TRAIN_RATIO,
            "val_ratio": VAL_RATIO,
            "test_ratio": 1.0 - TRAIN_RATIO - VAL_RATIO,
            "seed": SPLIT_SEED,
        },
        "prepare_summary": prepare_summary,
        "overall_split_counts": dict(split_counts),
        "overall_split_source_counts": {
            split: dict(counter) for split, counter in split_source_counts.items()
        },
        "overall_source_totals": dict(source_totals),
    }


def write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    legacy_sequences = load_legacy_sequences()
    if not legacy_sequences:
        raise RuntimeError(f"未从旧 build config 解析到 legacy sequences: {OLD_BUILD_CONFIG_PATH}")

    image_paths = list_new_image_paths()
    prepare_summary = sync_completed_labels(image_paths)

    legacy_rows = resolve_legacy_split_rows()
    new_rows = build_new_source_rows(image_paths)
    all_rows = legacy_rows + new_rows

    unique_keys = {
        (row["source_id"], row["sequence_name"], row["original_stem"])
        for row in all_rows
    }
    if len(unique_keys) != len(all_rows):
        raise RuntimeError("combined split manifest 中存在重复样本键。")

    unique_merged_stems = {row["merged_stem"] for row in all_rows}
    if len(unique_merged_stems) != len(all_rows):
        raise RuntimeError("combined split manifest 中存在重复 merged_stem。")

    write_split_csv(all_rows)
    split_summary = summarize_split(all_rows, prepare_summary)

    write_json(SUMMARY_JSON_PATH, prepare_summary)
    write_json(SPLIT_SUMMARY_JSON_PATH, split_summary)

    print(json.dumps({
        "completed_label_root": str(COMPLETED_LABEL_ROOT),
        "split_csv": str(SPLIT_CSV_PATH),
        "split_summary_json": str(SPLIT_SUMMARY_JSON_PATH),
        "prepare_summary_json": str(SUMMARY_JSON_PATH),
        "prepare_summary": prepare_summary,
        "overall_split_counts": split_summary["overall_split_counts"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

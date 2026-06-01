from __future__ import annotations

import argparse
import json
import math
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from prepare_person_dataset import PERSON_ROOT, assert_directory_within_root


DEFAULT_SOURCE_ROOT = (
    PERSON_ROOT.parents[2] / "all_labels" / "new_hard_examples"
).resolve()
DEFAULT_OUTPUT_PARENT_ROOT = (
    PERSON_ROOT
    / "train-result"
    / "prepared"
    / "person_new_hard_examples_v1"
).resolve()
DEFAULT_SPLIT_RATIOS = {"train": 0.7, "val": 0.15, "test": 0.15}
DEFAULT_CLASS_NAMES = {0: "person"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
DEFAULT_MANIFEST_NAME = "split_manifest.jsonl"


@dataclass(frozen=True)
class HardExampleSequence:
    name: str
    root: Path
    frames_root: Path
    labels_root: Path


@dataclass(frozen=True)
class HardExampleSample:
    sequence_name: str
    image_path: Path
    label_path: Path
    stem: str


def default_output_root_for(split_strategy: str) -> Path:
    return (DEFAULT_OUTPUT_PARENT_ROOT / split_strategy).resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare all_labels/new_hard_examples as a YOLO person dataset."
    )
    parser.add_argument(
        "--source-root",
        default=str(DEFAULT_SOURCE_ROOT),
        help="Root containing hard-example sequence folders with frames/labels children.",
    )
    parser.add_argument(
        "--output-root",
        default=None,
        help=(
            "Prepared YOLO dataset root. Defaults to "
            "train-result/prepared/person_new_hard_examples_v1/<split-strategy>."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing prepared dataset directory.",
    )
    parser.add_argument(
        "--split-strategy",
        choices=["sequence_contiguous", "sequence_holdout"],
        default="sequence_contiguous",
        help="Split strategy. Defaults to the latest person ROI-aware dataset strategy.",
    )
    parser.add_argument(
        "--strict-pairing",
        action="store_true",
        help="Fail when any image is missing a label or any extra label has no paired image.",
    )
    parser.add_argument("--train-ratio", type=float, default=0.7)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--test-ratio", type=float, default=0.15)
    return parser.parse_args()


def image_sort_key(image_path: Path) -> Tuple[str, str]:
    return (image_path.stem.lower(), image_path.name.lower())


def sequence_sort_key(sequence: HardExampleSequence) -> Tuple[int, ...]:
    parts: List[int] = []
    for item in sequence.name.removeprefix("hard_").split("_"):
        try:
            parts.append(int(item))
        except ValueError:
            parts.append(10**9)
    return tuple(parts)


def discover_sequences(source_root: Path) -> List[HardExampleSequence]:
    if not source_root.exists():
        raise RuntimeError("Source root does not exist: {0}".format(source_root))
    if not source_root.is_dir():
        raise RuntimeError("Source root is not a directory: {0}".format(source_root))

    sequences: List[HardExampleSequence] = []
    for candidate in sorted(source_root.rglob("*")):
        if not candidate.is_dir():
            continue
        frames_root = candidate / "frames"
        labels_root = candidate / "labels"
        if not frames_root.is_dir() or not labels_root.is_dir():
            continue
        relative_name = candidate.relative_to(source_root).as_posix().replace("/", "_")
        sequences.append(
            HardExampleSequence(
                name="hard_{0}".format(relative_name),
                root=candidate,
                frames_root=frames_root,
                labels_root=labels_root,
            )
        )
    return sorted(sequences, key=sequence_sort_key)


def label_lookup(labels_root: Path) -> Dict[str, Path]:
    lookup: Dict[str, Path] = {}
    for label_path in sorted(labels_root.glob("*.txt")):
        if label_path.name.lower() == "classes.txt":
            continue
        stem_key = label_path.stem.lower()
        if stem_key in lookup:
            raise RuntimeError(
                "Duplicate label stem in one label directory: {0}".format(label_path.stem)
            )
        lookup[stem_key] = label_path
    return lookup


def collect_samples(
    sequences: Sequence[HardExampleSequence],
    *,
    strict_pairing: bool,
) -> Tuple[Dict[str, List[HardExampleSample]], Dict[str, object]]:
    samples_by_sequence: Dict[str, List[HardExampleSample]] = {}
    sequence_report: Dict[str, object] = {}
    seen_image_names: Dict[str, str] = {}
    seen_stems: Dict[str, str] = {}

    for sequence in sequences:
        labels = label_lookup(sequence.labels_root)
        image_paths = sorted(
            [
                path
                for path in sequence.frames_root.iterdir()
                if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
            ],
            key=image_sort_key,
        )
        image_stems = {path.stem.lower() for path in image_paths}
        missing_label_stems: List[str] = []
        samples: List[HardExampleSample] = []

        for image_path in image_paths:
            image_name_key = image_path.name.lower()
            if image_name_key in seen_image_names:
                raise RuntimeError(
                    "Duplicate image filename would overwrite prepared output: {0}\n"
                    "First: {1}\nSecond: {2}".format(
                        image_path.name,
                        seen_image_names[image_name_key],
                        image_path,
                    )
                )
            seen_image_names[image_name_key] = str(image_path)

            stem_key = image_path.stem.lower()
            if stem_key in seen_stems:
                raise RuntimeError(
                    "Duplicate image stem would overwrite prepared labels: {0}\n"
                    "First: {1}\nSecond: {2}".format(
                        image_path.stem,
                        seen_stems[stem_key],
                        image_path,
                    )
                )
            seen_stems[stem_key] = str(image_path)

            label_path = labels.get(stem_key)
            if label_path is None:
                missing_label_stems.append(image_path.stem)
                continue
            samples.append(
                HardExampleSample(
                    sequence_name=sequence.name,
                    image_path=image_path,
                    label_path=label_path,
                    stem=image_path.stem,
                )
            )

        extra_label_stems = sorted(
            label_path.stem for stem_key, label_path in labels.items() if stem_key not in image_stems
        )
        if strict_pairing and (missing_label_stems or extra_label_stems):
            problems: List[str] = []
            if missing_label_stems:
                problems.append(
                    "missing labels ({0}): {1}".format(
                        len(missing_label_stems),
                        ", ".join(missing_label_stems[:10]),
                    )
                )
            if extra_label_stems:
                problems.append(
                    "extra labels ({0}): {1}".format(
                        len(extra_label_stems),
                        ", ".join(extra_label_stems[:10]),
                    )
                )
            raise RuntimeError(
                "Strict pairing failed for {0}: {1}".format(
                    sequence.name,
                    " | ".join(problems),
                )
            )
        samples_by_sequence[sequence.name] = samples
        sequence_report[sequence.name] = {
            "sequence_root": str(sequence.root),
            "frames_root": str(sequence.frames_root),
            "labels_root": str(sequence.labels_root),
            "image_count": len(image_paths),
            "label_count": len(labels),
            "paired_sample_count": len(samples),
            "missing_label_count": len(missing_label_stems),
            "missing_label_stems": missing_label_stems,
            "extra_label_count": len(extra_label_stems),
            "extra_label_stems": extra_label_stems,
        }
    return samples_by_sequence, sequence_report


def contiguous_split_counts(total: int, split_ratios: Mapping[str, float]) -> Dict[str, int]:
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
    counts = {split_name: int(math.floor(raw_counts[split_name])) for split_name in ordered}
    for split_name in positive_splits:
        if counts[split_name] == 0:
            counts[split_name] = 1

    while sum(counts.values()) > total:
        reducible = max(ordered, key=lambda name: (counts[name], raw_counts[name]))
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
    samples_by_sequence: Mapping[str, List[HardExampleSample]],
    *,
    split_ratios: Mapping[str, float],
    split_strategy: str,
) -> Dict[str, List[HardExampleSample]]:
    ordered_splits = ("train", "val", "test")
    split_map: Dict[str, List[HardExampleSample]] = {"train": [], "val": [], "test": []}
    if split_strategy == "sequence_contiguous":
        for samples in samples_by_sequence.values():
            counts = contiguous_split_counts(len(samples), split_ratios)
            cursor = 0
            for split_name in ordered_splits:
                count = counts[split_name]
                split_map[split_name].extend(samples[cursor : cursor + count])
                cursor += count
        return split_map

    if split_strategy == "sequence_holdout":
        ordered_sequences = list(samples_by_sequence.items())
        sequence_lengths = [len(samples) for _, samples in ordered_sequences]
        counts = contiguous_holdout_sequence_counts(sequence_lengths, split_ratios)
        cursor = 0
        for split_name in ordered_splits:
            count = counts[split_name]
            for _, samples in ordered_sequences[cursor : cursor + count]:
                split_map[split_name].extend(samples)
            cursor += count
        return split_map

    raise RuntimeError("Unknown split strategy: {0}".format(split_strategy))


def contiguous_holdout_sequence_counts(
    sequence_lengths: Sequence[int],
    split_ratios: Mapping[str, float],
) -> Dict[str, int]:
    ordered = ("train", "val", "test")
    total_sequences = len(sequence_lengths)
    if total_sequences == 0:
        return {"train": 0, "val": 0, "test": 0}

    positive_splits = [name for name in ordered if split_ratios.get(name, 0.0) > 0]
    if total_sequences < len(positive_splits):
        counts = {name: 0 for name in ordered}
        for split_name in ordered[:total_sequences]:
            counts[split_name] = 1
        return counts

    target_image_counts = contiguous_split_counts(sum(sequence_lengths), split_ratios)
    prefix_sums = [0]
    for length in sequence_lengths:
        prefix_sums.append(prefix_sums[-1] + length)

    best_counts: Optional[Dict[str, int]] = None
    best_rank: Optional[Tuple[int, int, int, int, int, int, int]] = None
    target_sequence_counts = contiguous_split_counts(total_sequences, split_ratios)

    for train_end in range(total_sequences + 1):
        for val_end in range(train_end, total_sequences + 1):
            candidate = {
                "train": train_end,
                "val": val_end - train_end,
                "test": total_sequences - val_end,
            }
            if any(
                split_ratios.get(split_name, 0.0) > 0 and candidate[split_name] == 0
                for split_name in ordered
            ):
                continue

            actual_image_counts = {
                "train": prefix_sums[train_end],
                "val": prefix_sums[val_end] - prefix_sums[train_end],
                "test": prefix_sums[total_sequences] - prefix_sums[val_end],
            }
            image_diffs = {
                split_name: abs(actual_image_counts[split_name] - target_image_counts[split_name])
                for split_name in ordered
            }
            sequence_diffs = {
                split_name: abs(candidate[split_name] - target_sequence_counts[split_name])
                for split_name in ordered
            }
            rank = (
                sum(image_diffs.values()),
                max(image_diffs.values()),
                sum(sequence_diffs.values()),
                image_diffs["test"],
                image_diffs["val"],
                sequence_diffs["test"],
                sequence_diffs["val"],
            )
            if best_rank is None or rank < best_rank:
                best_rank = rank
                best_counts = candidate

    if best_counts is None:
        raise RuntimeError("Unable to derive contiguous sequence_holdout split counts.")
    return best_counts


def ensure_output_root(output_root: Path, *, overwrite: bool) -> None:
    if output_root.exists():
        if not output_root.is_dir():
            raise RuntimeError("Output root is not a directory: {0}".format(output_root))
        if any(output_root.iterdir()):
            if not overwrite:
                raise RuntimeError(
                    "Output root already exists and is not empty. Use --overwrite: {0}".format(
                        output_root
                    )
                )
            assert_directory_within_root(output_root, PERSON_ROOT / "train-result")
            shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)


def read_box_count(label_path: Path) -> int:
    count = 0
    for line_number, line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        if len(parts) != 5:
            raise RuntimeError(
                "{0}:{1} is not a valid YOLO detection label line".format(
                    label_path,
                    line_number,
                )
            )
        class_id = int(parts[0])
        if class_id not in DEFAULT_CLASS_NAMES:
            raise RuntimeError(
                "{0}:{1} uses unsupported class id {2}".format(
                    label_path,
                    line_number,
                    class_id,
                )
            )
        for raw_value in parts[1:]:
            value = float(raw_value)
            if value < 0.0 or value > 1.0:
                raise RuntimeError(
                    "{0}:{1} has a normalized value outside [0, 1]".format(
                        label_path,
                        line_number,
                    )
                )
        count += 1
    return count


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


def copy_split(
    split_map: Mapping[str, Sequence[HardExampleSample]],
    output_root: Path,
) -> Tuple[Dict[str, int], Dict[str, int], Dict[str, int], List[Dict[str, object]]]:
    split_image_counts = {"train": 0, "val": 0, "test": 0}
    split_label_counts = {"train": 0, "val": 0, "test": 0}
    split_box_counts = {"train": 0, "val": 0, "test": 0}
    manifest_rows: List[Dict[str, object]] = []

    for split_name, samples in split_map.items():
        image_dir = output_root / "images" / split_name
        label_dir = output_root / "labels" / split_name
        image_dir.mkdir(parents=True, exist_ok=True)
        label_dir.mkdir(parents=True, exist_ok=True)

        for sample in samples:
            box_count = read_box_count(sample.label_path)
            output_image_path = image_dir / sample.image_path.name
            output_label_path = label_dir / "{0}.txt".format(sample.stem)
            shutil.copy2(sample.image_path, output_image_path)
            shutil.copy2(sample.label_path, output_label_path)
            split_image_counts[split_name] += 1
            split_label_counts[split_name] += 1
            split_box_counts[split_name] += box_count
            manifest_rows.append(
                {
                    "split": split_name,
                    "sequence_name": sample.sequence_name,
                    "stem": sample.stem,
                    "image_name": sample.image_path.name,
                    "image_path": str(sample.image_path),
                    "label_path": str(sample.label_path),
                    "output_image_path": str(output_image_path),
                    "output_label_path": str(output_label_path),
                    "box_count": box_count,
                }
            )
    return split_image_counts, split_label_counts, split_box_counts, manifest_rows


def write_split_manifest(
    output_root: Path,
    manifest_rows: Sequence[Mapping[str, object]],
) -> Path:
    manifest_path = output_root / DEFAULT_MANIFEST_NAME
    with manifest_path.open("w", encoding="utf-8") as handle:
        for row in manifest_rows:
            handle.write(json.dumps(dict(row), ensure_ascii=False) + "\n")
    return manifest_path


def prepare_dataset(
    *,
    source_root: Path,
    output_root: Path,
    overwrite: bool,
    split_ratios: Mapping[str, float],
    split_strategy: str,
    strict_pairing: bool,
) -> Dict[str, object]:
    ensure_output_root(output_root, overwrite=overwrite)
    sequences = discover_sequences(source_root)
    samples_by_sequence, sequence_report = collect_samples(
        sequences,
        strict_pairing=strict_pairing,
    )
    split_map = build_split_map(
        samples_by_sequence,
        split_ratios=split_ratios,
        split_strategy=split_strategy,
    )
    split_image_counts, split_label_counts, split_box_counts, manifest_rows = copy_split(
        split_map,
        output_root,
    )
    dataset_yaml = write_dataset_yaml(output_root, DEFAULT_CLASS_NAMES)
    manifest_path = write_split_manifest(output_root, manifest_rows)

    total_images = sum(int(item["image_count"]) for item in sequence_report.values())
    total_labels = sum(int(item["label_count"]) for item in sequence_report.values())
    total_paired = sum(len(samples) for samples in samples_by_sequence.values())
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_root": str(source_root),
        "dataset_root": str(output_root),
        "dataset_yaml": str(dataset_yaml),
        "manifest_path": str(manifest_path),
        "class_names": {str(k): v for k, v in DEFAULT_CLASS_NAMES.items()},
        "split_strategy": split_strategy,
        "default_split_strategy": "sequence_contiguous",
        "split_ratios": dict(split_ratios),
        "strict_pairing": strict_pairing,
        "split_image_counts": split_image_counts,
        "split_label_counts": split_label_counts,
        "split_box_counts": split_box_counts,
        "input_image_count": total_images,
        "source_label_count": total_labels,
        "paired_sample_count": total_paired,
        "output_image_count": sum(split_image_counts.values()),
        "output_label_count": sum(split_label_counts.values()),
        "sequence_count": len(sequences),
        "sequence_order": [sequence.name for sequence in sequences],
        "missing_label_stems_by_sequence": {
            sequence_name: info["missing_label_stems"]
            for sequence_name, info in sequence_report.items()
            if info["missing_label_stems"]
        },
        "extra_label_stems_by_sequence": {
            sequence_name: info["extra_label_stems"]
            for sequence_name, info in sequence_report.items()
            if info["extra_label_stems"]
        },
        "sequences": sequence_report,
    }
    report["missing_label_count"] = sum(
        int(item["missing_label_count"]) for item in sequence_report.values()
    )
    report["extra_label_count"] = sum(
        int(item["extra_label_count"]) for item in sequence_report.values()
    )
    report_path = output_root / "prepare_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    args = parse_args()
    split_ratios = {
        "train": args.train_ratio,
        "val": args.val_ratio,
        "test": args.test_ratio,
    }
    if sum(split_ratios.values()) <= 0:
        raise RuntimeError("Split ratios must contain at least one positive value.")

    output_root = (
        Path(args.output_root).expanduser().resolve()
        if args.output_root
        else default_output_root_for(args.split_strategy)
    )

    report = prepare_dataset(
        source_root=Path(args.source_root).expanduser().resolve(),
        output_root=output_root,
        overwrite=args.overwrite,
        split_ratios=split_ratios,
        split_strategy=args.split_strategy,
        strict_pairing=args.strict_pairing,
    )
    print("Dataset root : {0}".format(report["dataset_root"]))
    print("dataset.yaml : {0}".format(report["dataset_yaml"]))
    print("manifest     : {0}".format(report["manifest_path"]))
    print(
        "Images train/val/test: {train}/{val}/{test}".format(
            **report["split_image_counts"]
        )
    )
    print(
        "Boxes  train/val/test: {train}/{val}/{test}".format(
            **report["split_box_counts"]
        )
    )
    print(
        "Paired samples={0}, extra labels={1}, missing labels={2}".format(
            report["paired_sample_count"],
            report["extra_label_count"],
            report["missing_label_count"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

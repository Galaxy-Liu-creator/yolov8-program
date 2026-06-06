from __future__ import annotations

import argparse
import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple


SUPPORTED_OUTPUT_SPLITS = {"train", "val", "test", "skip"}


class SplitPlanError(RuntimeError):
    """生成 split manifest 失败时抛出的业务异常。"""


@dataclass(frozen=True)
class CanonicalSample:
    source_id: str
    sequence_name: str
    original_stem: str
    merged_stem: str
    sample_role: str
    label_origin: str
    box_count: int

    @property
    def key(self) -> Tuple[str, str, str]:
        return (self.source_id, self.sequence_name, self.original_stem)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="根据 canonical manifest 生成 source-balanced 的 train/val/holdout split manifests。"
    )
    parser.add_argument("--source-manifest", required=True, help="canonical manifest.csv 路径。")
    parser.add_argument("--output-dir", required=True, help="输出 split manifest 的目录。")
    parser.add_argument("--holdout-ratio", type=float, default=0.15, help="统一 holdout 占总样本的比例。")
    parser.add_argument("--val-ratio", type=float, default=0.15, help="训练集内部 val 占总样本的比例。")
    parser.add_argument("--seed", type=int, default=42, help="用于稳定打散的随机种子。")
    parser.add_argument(
        "--trainval-name",
        default="trainval_balanced_v1.split.csv",
        help="train/val split manifest 文件名。",
    )
    parser.add_argument(
        "--holdout-name",
        default="unified_holdout_v1.split.csv",
        help="holdout split manifest 文件名。",
    )
    parser.add_argument(
        "--summary-name",
        default="source_balanced_v1_summary.json",
        help="输出的汇总 JSON 文件名。",
    )
    parser.add_argument(
        "--min-eval-sources",
        type=int,
        default=2,
        help="要求 val/test 至少覆盖的 source 数量。",
    )
    return parser.parse_args()


def coerce_ratio(value: float, field_name: str) -> float:
    if value < 0 or value >= 1:
        raise SplitPlanError("{0} 必须位于 [0, 1) 区间。".format(field_name))
    return value


def derive_sample_role(row: Mapping[str, str]) -> str:
    sample_role = str(row.get("sample_role", "") or "").strip()
    if sample_role:
        return sample_role

    try:
        box_count = int(str(row.get("box_count", "0") or "0"))
    except ValueError as exc:
        raise SplitPlanError("manifest 中存在非法 box_count: {0}".format(row.get("box_count"))) from exc
    label_origin = str(row.get("label_origin", "source") or "source").strip()
    if box_count > 0:
        return "positive"
    if label_origin == "review":
        return "review_empty"
    return "source_empty"


def load_canonical_samples(manifest_path: Path) -> List[CanonicalSample]:
    try:
        with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = set(reader.fieldnames or [])
            required_fields = {
                "source_id",
                "sequence_name",
                "original_stem",
                "merged_stem",
                "label_origin",
                "box_count",
            }
            missing_fields = sorted(required_fields - fieldnames)
            if missing_fields:
                raise SplitPlanError(
                    "source manifest 缺少字段 {0}: {1}".format(missing_fields, manifest_path)
                )

            samples: List[CanonicalSample] = []
            seen_keys = set()
            for row_index, row in enumerate(reader, start=2):
                source_id = str(row.get("source_id", "") or "").strip()
                sequence_name = str(row.get("sequence_name", "") or "").strip()
                original_stem = str(row.get("original_stem", "") or "").strip()
                merged_stem = str(row.get("merged_stem", "") or "").strip()
                if not source_id or not sequence_name or not original_stem or not merged_stem:
                    raise SplitPlanError("source manifest 第 {0} 行存在空主键字段。".format(row_index))
                sample_key = (source_id, sequence_name, original_stem)
                if sample_key in seen_keys:
                    raise SplitPlanError(
                        "source manifest 中存在重复样本: {0}/{1}/{2}".format(
                            source_id,
                            sequence_name,
                            original_stem,
                        )
                    )
                seen_keys.add(sample_key)
                try:
                    box_count = int(str(row.get("box_count", "0") or "0"))
                except ValueError as exc:
                    raise SplitPlanError("source manifest 第 {0} 行 box_count 非法。".format(row_index)) from exc
                label_origin = str(row.get("label_origin", "source") or "source").strip()
                samples.append(
                    CanonicalSample(
                        source_id=source_id,
                        sequence_name=sequence_name,
                        original_stem=original_stem,
                        merged_stem=merged_stem,
                        sample_role=derive_sample_role(row),
                        label_origin=label_origin,
                        box_count=box_count,
                    )
                )
    except OSError as exc:
        raise SplitPlanError("读取 source manifest 失败: {0}".format(manifest_path)) from exc

    if not samples:
        raise SplitPlanError("source manifest 不能为空: {0}".format(manifest_path))
    return samples


def stable_shuffle(samples: Sequence[CanonicalSample], *, seed: int, bucket_name: str) -> List[CanonicalSample]:
    ordered = sorted(
        samples,
        key=lambda item: (item.sequence_name, item.original_stem, item.merged_stem),
    )
    shuffled = list(ordered)
    random.Random("{0}:{1}".format(seed, bucket_name)).shuffle(shuffled)
    return shuffled


def pick_bucket_samples(
    samples: Sequence[CanonicalSample],
    *,
    ratio: float,
    seed: int,
    bucket_name: str,
) -> List[CanonicalSample]:
    if not samples or ratio <= 0:
        return []

    shuffled = stable_shuffle(samples, seed=seed, bucket_name=bucket_name)
    target_count = int(round(len(shuffled) * ratio))
    if target_count <= 0 and len(shuffled) >= 3:
        target_count = 1
    if target_count >= len(shuffled) and len(shuffled) > 1:
        target_count = len(shuffled) - 1
    if target_count <= 0:
        return []
    return shuffled[:target_count]


def group_samples_by_source_role(samples: Iterable[CanonicalSample]) -> Dict[Tuple[str, str], List[CanonicalSample]]:
    buckets: Dict[Tuple[str, str], List[CanonicalSample]] = {}
    for sample in samples:
        buckets.setdefault((sample.source_id, sample.sample_role), []).append(sample)
    return buckets


def validate_eval_split(
    *,
    split_name: str,
    assigned_samples: Sequence[CanonicalSample],
    min_eval_sources: int,
) -> None:
    if not assigned_samples:
        raise SplitPlanError("{0} split 为空，无法用于统一比较。".format(split_name))

    source_ids = sorted({sample.source_id for sample in assigned_samples})
    if len(source_ids) < min_eval_sources:
        raise SplitPlanError(
            "{0} split 只覆盖 {1} 个 source，低于最小要求 {2}。".format(
                split_name,
                len(source_ids),
                min_eval_sources,
            )
        )

    positive_count = sum(1 for sample in assigned_samples if sample.sample_role == "positive")
    if positive_count <= 0:
        raise SplitPlanError("{0} split 没有正样本，评估结果没有参考价值。".format(split_name))


def collect_split_stats(assignments: Mapping[Tuple[str, str, str], str], samples: Sequence[CanonicalSample]) -> Dict[str, object]:
    split_counts: Dict[str, int] = {}
    split_source_counts: Dict[str, Dict[str, int]] = {}
    split_role_counts: Dict[str, Dict[str, int]] = {}
    for sample in samples:
        split = assignments[sample.key]
        split_counts[split] = split_counts.get(split, 0) + 1
        split_source_counts.setdefault(split, {})
        split_source_counts[split][sample.source_id] = split_source_counts[split].get(sample.source_id, 0) + 1
        split_role_counts.setdefault(split, {})
        split_role_counts[split][sample.sample_role] = split_role_counts[split].get(sample.sample_role, 0) + 1
    return {
        "split_counts": split_counts,
        "split_source_counts": split_source_counts,
        "split_role_counts": split_role_counts,
    }


def build_assignments(
    samples: Sequence[CanonicalSample],
    *,
    holdout_ratio: float,
    val_ratio: float,
    seed: int,
    min_eval_sources: int,
) -> Tuple[Dict[Tuple[str, str, str], str], Dict[Tuple[str, str, str], str], Dict[str, object]]:
    holdout_assignments = {sample.key: "skip" for sample in samples}
    trainval_assignments = {sample.key: "train" for sample in samples}

    holdout_keys = set()
    for bucket_name, bucket_samples in group_samples_by_source_role(samples).items():
        selected = pick_bucket_samples(
            bucket_samples,
            ratio=holdout_ratio,
            seed=seed,
            bucket_name="holdout::{0}::{1}".format(bucket_name[0], bucket_name[1]),
        )
        holdout_keys.update(sample.key for sample in selected)

    remaining_samples = [sample for sample in samples if sample.key not in holdout_keys]
    effective_val_ratio = 0.0 if val_ratio <= 0 else val_ratio / max(1e-9, 1.0 - holdout_ratio)
    effective_val_ratio = min(effective_val_ratio, 0.99)
    val_keys = set()
    for bucket_name, bucket_samples in group_samples_by_source_role(remaining_samples).items():
        selected = pick_bucket_samples(
            bucket_samples,
            ratio=effective_val_ratio,
            seed=seed,
            bucket_name="val::{0}::{1}".format(bucket_name[0], bucket_name[1]),
        )
        val_keys.update(sample.key for sample in selected)

    for sample in samples:
        if sample.key in holdout_keys:
            holdout_assignments[sample.key] = "test"
            trainval_assignments[sample.key] = "skip"
        elif sample.key in val_keys:
            trainval_assignments[sample.key] = "val"
        else:
            trainval_assignments[sample.key] = "train"

    validate_eval_split(
        split_name="val",
        assigned_samples=[sample for sample in samples if trainval_assignments[sample.key] == "val"],
        min_eval_sources=min_eval_sources,
    )
    validate_eval_split(
        split_name="test",
        assigned_samples=[sample for sample in samples if holdout_assignments[sample.key] == "test"],
        min_eval_sources=min_eval_sources,
    )

    summary = {
        "holdout_ratio": holdout_ratio,
        "val_ratio": val_ratio,
        "seed": seed,
        "min_eval_sources": min_eval_sources,
        "trainval": collect_split_stats(trainval_assignments, samples),
        "holdout": collect_split_stats(holdout_assignments, samples),
    }
    return trainval_assignments, holdout_assignments, summary


def write_split_manifest(
    output_path: Path,
    samples: Sequence[CanonicalSample],
    assignments: Mapping[Tuple[str, str, str], str],
    *,
    notes_by_split: Mapping[str, str],
    holdout_group_name: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source_id",
        "sequence_name",
        "original_stem",
        "merged_stem",
        "split",
        "sample_role",
        "holdout_group",
        "note",
    ]
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for sample in sorted(samples, key=lambda item: (item.source_id, item.sequence_name, item.original_stem)):
            split = assignments[sample.key]
            if split not in SUPPORTED_OUTPUT_SPLITS:
                raise SplitPlanError("存在非法输出 split: {0}".format(split))
            writer.writerow(
                {
                    "source_id": sample.source_id,
                    "sequence_name": sample.sequence_name,
                    "original_stem": sample.original_stem,
                    "merged_stem": sample.merged_stem,
                    "split": split,
                    "sample_role": sample.sample_role,
                    "holdout_group": holdout_group_name if split == "test" else "",
                    "note": notes_by_split.get(split, ""),
                }
            )


def write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    holdout_ratio = coerce_ratio(args.holdout_ratio, "holdout_ratio")
    val_ratio = coerce_ratio(args.val_ratio, "val_ratio")
    if holdout_ratio + val_ratio >= 1:
        raise SystemExit("holdout_ratio + val_ratio 必须小于 1。")

    manifest_path = Path(args.source_manifest).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    try:
        samples = load_canonical_samples(manifest_path)
        trainval_assignments, holdout_assignments, summary = build_assignments(
            samples,
            holdout_ratio=holdout_ratio,
            val_ratio=val_ratio,
            seed=args.seed,
            min_eval_sources=args.min_eval_sources,
        )
        trainval_path = output_dir / args.trainval_name
        holdout_path = output_dir / args.holdout_name
        write_split_manifest(
            trainval_path,
            samples,
            trainval_assignments,
            notes_by_split={
                "train": "source_balanced_trainval_v1",
                "val": "source_balanced_trainval_v1",
                "skip": "reserved_for_unified_holdout_v1",
            },
            holdout_group_name="",
        )
        write_split_manifest(
            holdout_path,
            samples,
            holdout_assignments,
            notes_by_split={
                "test": "unified_holdout_v1",
                "skip": "reserved_for_trainval_balanced_v1",
            },
            holdout_group_name="unified_holdout_v1",
        )
        write_json(output_dir / args.summary_name, summary)
    except SplitPlanError as exc:
        print("生成失败: {0}".format(exc))
        return 1

    print("生成完成")
    print("source_manifest : {0}".format(manifest_path))
    print("trainval_split  : {0}".format(trainval_path))
    print("holdout_split   : {0}".format(holdout_path))
    print("summary_json    : {0}".format(output_dir / args.summary_name))
    print("trainval_counts : {0}".format(summary["trainval"]["split_counts"]))
    print("holdout_counts  : {0}".format(summary["holdout"]["split_counts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

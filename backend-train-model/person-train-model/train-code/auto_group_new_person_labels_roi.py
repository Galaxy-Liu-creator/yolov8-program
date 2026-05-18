from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import cv2
import numpy as np

from prepare_person_dataset import PERSON_ROOT, PersonSequence, load_person_project_context


DEFAULT_PROJECT_CONFIG = PERSON_ROOT / "person_project_config.fullframe_with_new_labels.json"
DEFAULT_OUTPUT_ROOT = PERSON_ROOT / "train-result" / "working" / "new_person_labels_roi_grouping"


@dataclass
class ImageRecord:
    stem: str
    image_path: Path
    label_path: Path
    label_exists: bool
    width: int
    height: int
    feature: np.ndarray
    missing_label_created: bool = False


@dataclass
class Cluster:
    bucket_key: Tuple[int, int]
    group_id: str
    members: List[ImageRecord] = field(default_factory=list)
    centroid: Optional[np.ndarray] = None

    def add(self, record: ImageRecord) -> None:
        if self.centroid is None:
            self.centroid = record.feature.astype(np.float32).copy()
        else:
            count = float(len(self.members))
            self.centroid = (self.centroid * count + record.feature) / (count + 1.0)
        self.members.append(record)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "为 new_person_labels 生成 ROI-aware 首轮自动粗分组结果，"
            "输出分组 manifest、摘要以及可选的 grouped 目录。"
        )
    )
    parser.add_argument(
        "--project-config",
        default=str(DEFAULT_PROJECT_CONFIG),
        help="person 项目配置 JSON 路径，默认使用 fullframe_with_new_labels 配置。",
    )
    parser.add_argument(
        "--sequence-name",
        default="new_person_labels_flat_20260503",
        help="要自动分组的 sequence_name。",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="自动分组输出目录。",
    )
    parser.add_argument(
        "--feature-threshold",
        type=float,
        default=0.08,
        help=(
            "组内图像粗特征阈值，越小分组越细。当前默认值适合做第一轮粗分组，"
            "后续可按结果继续人工拆分。"
        ),
    )
    parser.add_argument(
        "--representatives-per-group",
        type=int,
        default=8,
        help="每组输出多少张最接近组中心的代表帧。",
    )
    parser.add_argument(
        "--materialize-mode",
        choices=["none", "copy", "hardlink", "hardlink_or_copy"],
        default="hardlink_or_copy",
        help=(
            "是否生成 grouped 目录：none 仅输出 manifest；"
            "hardlink_or_copy 会优先硬链接，失败后回退复制。"
        ),
    )
    parser.add_argument(
        "--create-empty-missing-labels",
        action="store_true",
        help="对缺失标签的图片在 grouped 目录中创建空白 txt，方便后续数据准备。",
    )
    parser.add_argument(
        "--clean-output",
        action="store_true",
        help="执行前先清空 output-root，避免旧分组残留干扰当前结果。",
    )
    return parser.parse_args()


def read_gray_image(path: Path) -> np.ndarray:
    raw = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(raw, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise RuntimeError("无法读取图片: {0}".format(path))
    return image


def compute_feature(gray_image: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(gray_image, (5, 5), 0)
    normalized = blurred.astype(np.float32) / 255.0
    small = cv2.resize(normalized, (24, 24), interpolation=cv2.INTER_AREA)
    edges = cv2.Canny(blurred, 60, 120).astype(np.float32) / 255.0
    small_edges = cv2.resize(edges, (24, 24), interpolation=cv2.INTER_AREA)
    return np.concatenate([small.reshape(-1), small_edges.reshape(-1)], axis=0)


def feature_distance(feature_a: np.ndarray, feature_b: np.ndarray) -> float:
    return float(np.mean(np.abs(feature_a - feature_b)))


def resolve_target_sequence(sequence_name: str, sequences: Sequence[PersonSequence]) -> PersonSequence:
    for sequence in sequences:
        if sequence.sequence_name == sequence_name:
            return sequence
    raise RuntimeError("未在 project-config 中找到 sequence_name={0}。".format(sequence_name))


def iter_images(image_root: Path, image_extensions: Sequence[str]) -> List[Path]:
    suffixes = {suffix.lower() for suffix in image_extensions}
    return sorted(
        [path for path in image_root.iterdir() if path.is_file() and path.suffix.lower() in suffixes],
        key=lambda path: path.name,
    )


def build_records(sequence: PersonSequence, image_extensions: Sequence[str]) -> List[ImageRecord]:
    records: List[ImageRecord] = []
    for image_path in iter_images(sequence.image_root, image_extensions):
        gray_image = read_gray_image(image_path)
        height, width = gray_image.shape[:2]
        label_path = sequence.label_root / (image_path.stem + ".txt")
        records.append(
            ImageRecord(
                stem=image_path.stem,
                image_path=image_path,
                label_path=label_path,
                label_exists=label_path.exists(),
                width=width,
                height=height,
                feature=compute_feature(gray_image),
            )
        )
    return records


def assign_clusters(records: Sequence[ImageRecord], threshold: float) -> List[Cluster]:
    by_bucket: Dict[Tuple[int, int], List[ImageRecord]] = {}
    for record in records:
        by_bucket.setdefault((record.width, record.height), []).append(record)

    all_clusters: List[Cluster] = []
    global_index = 1
    for bucket_key in sorted(by_bucket.keys()):
        bucket_records = by_bucket[bucket_key]
        bucket_clusters: List[Cluster] = []
        for record in bucket_records:
            if not bucket_clusters:
                cluster = Cluster(bucket_key=bucket_key, group_id="group_{0:04d}".format(global_index))
                cluster.add(record)
                bucket_clusters.append(cluster)
                global_index += 1
                continue

            best_cluster: Optional[Cluster] = None
            best_distance = float("inf")
            for cluster in bucket_clusters:
                distance = feature_distance(record.feature, cluster.centroid)
                if distance < best_distance:
                    best_distance = distance
                    best_cluster = cluster

            if best_cluster is not None and best_distance <= threshold:
                best_cluster.add(record)
            else:
                cluster = Cluster(bucket_key=bucket_key, group_id="group_{0:04d}".format(global_index))
                cluster.add(record)
                bucket_clusters.append(cluster)
                global_index += 1

        all_clusters.extend(bucket_clusters)
    return all_clusters


def safe_link_or_copy(source_path: Path, target_path: Path, mode: str) -> str:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists():
        return "exists"
    if mode == "copy":
        shutil.copy2(source_path, target_path)
        return "copied"
    if mode == "hardlink":
        os.link(source_path, target_path)
        return "hardlinked"
    if mode == "hardlink_or_copy":
        try:
            os.link(source_path, target_path)
            return "hardlinked"
        except OSError:
            shutil.copy2(source_path, target_path)
            return "copied"
    raise RuntimeError("未知 materialize mode: {0}".format(mode))


def materialize_group(
    cluster: Cluster,
    output_root: Path,
    *,
    materialize_mode: str,
    create_empty_missing_labels: bool,
) -> Dict[str, str]:
    group_dir = output_root / "grouped" / cluster.group_id
    images_dir = group_dir / "images"
    labels_dir = group_dir / "labels"
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    for record in cluster.members:
        safe_link_or_copy(record.image_path, images_dir / record.image_path.name, materialize_mode)
        target_label_path = labels_dir / (record.stem + ".txt")
        if record.label_exists:
            safe_link_or_copy(record.label_path, target_label_path, materialize_mode)
        elif create_empty_missing_labels:
            target_label_path.write_text("", encoding="utf-8")
            record.missing_label_created = True
    return {
        "group_dir": str(group_dir),
        "images_dir": str(images_dir),
        "labels_dir": str(labels_dir),
    }


def representative_members(cluster: Cluster, count: int) -> List[ImageRecord]:
    scored = [
        (feature_distance(record.feature, cluster.centroid), record)
        for record in cluster.members
    ]
    scored.sort(key=lambda item: (item[0], item[1].image_path.name))
    return [record for _, record in scored[: max(1, count)]]


def write_manifest(clusters: Sequence[Cluster], output_root: Path) -> Path:
    manifest_path = output_root / "group_manifest.csv"
    with manifest_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "group_id",
                "image_stem",
                "image_name",
                "image_path",
                "label_path",
                "label_exists",
                "missing_label_created",
                "width",
                "height",
                "group_size",
            ]
        )
        for cluster in sorted(clusters, key=lambda item: item.group_id):
            for record in cluster.members:
                writer.writerow(
                    [
                        cluster.group_id,
                        record.stem,
                        record.image_path.name,
                        str(record.image_path),
                        str(record.label_path),
                        int(record.label_exists),
                        int(record.missing_label_created),
                        record.width,
                        record.height,
                        len(cluster.members),
                    ]
                )
    return manifest_path


def write_summary(
    clusters: Sequence[Cluster],
    output_root: Path,
    *,
    sequence: PersonSequence,
    threshold: float,
    representatives_per_group: int,
    materialize_mode: str,
) -> Path:
    bucket_summary: Dict[str, Dict[str, int]] = {}
    groups_payload: List[Dict[str, object]] = []
    total_missing_labels = 0
    total_created_empty_labels = 0
    for cluster in sorted(clusters, key=lambda item: item.group_id):
        bucket_key = "{0}x{1}".format(cluster.bucket_key[0], cluster.bucket_key[1])
        bucket_info = bucket_summary.setdefault(
            bucket_key,
            {"width": cluster.bucket_key[0], "height": cluster.bucket_key[1], "groups": 0, "images": 0},
        )
        bucket_info["groups"] += 1
        bucket_info["images"] += len(cluster.members)
        missing_count = sum(1 for item in cluster.members if not item.label_exists)
        created_empty_count = sum(1 for item in cluster.members if item.missing_label_created)
        total_missing_labels += missing_count
        total_created_empty_labels += created_empty_count
        groups_payload.append(
            {
                "group_id": cluster.group_id,
                "width": cluster.bucket_key[0],
                "height": cluster.bucket_key[1],
                "image_count": len(cluster.members),
                "missing_label_count": missing_count,
                "created_empty_label_count": created_empty_count,
                "representatives": [item.image_path.name for item in representative_members(cluster, representatives_per_group)],
            }
        )

    summary_path = output_root / "group_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "sequence_name": sequence.sequence_name,
                "image_root": str(sequence.image_root),
                "label_root": str(sequence.label_root),
                "feature_threshold": threshold,
                "materialize_mode": materialize_mode,
                "total_groups": len(clusters),
                "total_images": sum(len(cluster.members) for cluster in clusters),
                "total_missing_labels": total_missing_labels,
                "total_created_empty_labels": total_created_empty_labels,
                "buckets": list(bucket_summary.values()),
                "groups": groups_payload,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return summary_path


def write_readme(
    output_root: Path,
    *,
    sequence: PersonSequence,
    total_images: int,
    total_groups: int,
    threshold: float,
    materialize_mode: str,
) -> Path:
    readme_path = output_root / "README.md"
    readme_path.write_text(
        (
            "# new_person_labels ROI 自动粗分组结果\n\n"
            "## 本次目标\n\n"
            "- 针对 `{sequence_name}` 生成一版**自动粗分组**结果；\n"
            "- 服务于后续 `new_person_labels` 的 ROI-aware 标注；\n"
            "- 该结果是第一轮工程分组建议，不等于最终人工确认后的 ROI 逻辑分组。\n\n"
            "## 本次参数\n\n"
            "- 总图片数：`{total_images}`\n"
            "- 自动分组数：`{total_groups}`\n"
            "- 粗特征阈值：`{threshold}`\n"
            "- materialize_mode：`{materialize_mode}`\n\n"
            "## 输出文件\n\n"
            "- `group_manifest.csv`：逐图分组结果\n"
            "- `group_summary.json`：分组汇总与代表帧\n"
            "- `grouped/`：可选生成的物理分组目录\n\n"
            "## 建议下一步\n\n"
            "1. 先按 `group_summary.json` 回看各组代表帧；\n"
            "2. 把明显混杂的组继续人工细拆；\n"
            "3. 稳定组进入组级 ROI 标注；\n"
            "4. 只有少量仍不稳定的组再考虑逐图 ROI。\n"
        ).format(
            sequence_name=sequence.sequence_name,
            total_images=total_images,
            total_groups=total_groups,
            threshold=threshold,
            materialize_mode=materialize_mode,
        ),
        encoding="utf-8",
    )
    return readme_path


def main() -> None:
    args = parse_args()
    context = load_person_project_context(Path(args.project_config))
    sequence = resolve_target_sequence(args.sequence_name, context.sequences)
    output_root = Path(args.output_root).expanduser().resolve()
    if args.clean_output and output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    records = build_records(sequence, context.image_extensions)
    if not records:
        raise RuntimeError("目标 sequence 没有找到可用图片: {0}".format(sequence.image_root))

    clusters = assign_clusters(records, args.feature_threshold)
    if args.materialize_mode != "none":
        for cluster in clusters:
            materialize_group(
                cluster,
                output_root,
                materialize_mode=args.materialize_mode,
                create_empty_missing_labels=args.create_empty_missing_labels,
            )

    manifest_path = write_manifest(clusters, output_root)
    summary_path = write_summary(
        clusters,
        output_root,
        sequence=sequence,
        threshold=args.feature_threshold,
        representatives_per_group=args.representatives_per_group,
        materialize_mode=args.materialize_mode,
    )
    readme_path = write_readme(
        output_root,
        sequence=sequence,
        total_images=len(records),
        total_groups=len(clusters),
        threshold=args.feature_threshold,
        materialize_mode=args.materialize_mode,
    )

    print("自动粗分组完成。")
    print("manifest : {0}".format(manifest_path))
    print("summary  : {0}".format(summary_path))
    print("readme   : {0}".format(readme_path))


if __name__ == "__main__":
    main()

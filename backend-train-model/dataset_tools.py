from __future__ import annotations

"""数据审计与数据集准备辅助模块。

这个模块主要负责两件事：

1. 对原始图片目录和统一标签目录做一致性检查；
2. 把原始数据整理成可直接给 YOLOv8 训练的标准目录结构。

之所以单独拆出这个文件，是因为“数据检查 / 样本切分 / personcrop 样本生成”
这几类逻辑都明显属于数据工程层，不应该和 CLI 调度、训练、评估、导出等流程
混在一起。
"""

import math
import re
import shutil
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import cv2

import config


class DatasetToolError(RuntimeError):
    """数据工具链中的业务异常。

    这里使用自定义异常的好处是：

    - 上层 CLI 可以统一捕获，并输出更友好的错误提示；
    - 不会把用户暴露给一长串底层 traceback；
    - 便于把“数据错误”和“代码语法错误/第三方库错误”区分开。
    """

    pass


@dataclass
class LabelEntry:
    """表示一行 YOLO 标注。

    所有坐标都使用标准 YOLO 检测格式：

    - `class_id`
    - `x_center`
    - `y_center`
    - `width`
    - `height`

    其中后 4 个值都要求是归一化后的 `[0, 1]` 浮点数。
    """

    class_id: int
    x_center: float
    y_center: float
    width: float
    height: float

    def to_yolo_line(self) -> str:
        """把当前对象重新序列化为 YOLO 文本行。"""

        return (
            f"{self.class_id} "
            f"{self.x_center:.6f} "
            f"{self.y_center:.6f} "
            f"{self.width:.6f} "
            f"{self.height:.6f}"
        )


@dataclass
class ImageSample:
    """表示一张原始图片及其配对标签。

    这个对象在数据审计完成后产生，后续切分、prepare、personcrop 等流程
    都围绕它来传递“样本”。
    """

    sequence_name: str
    image_path: Path
    label_path: Path
    stem: str


@dataclass
class AuditResult:
    """保存一次原始数据审计的结果。

    这里既包含统计信息，也包含通过校验后的样本列表，便于后续直接进入
    `prepare_dataset()`，避免再重复扫描原始目录。
    """

    image_roots: List[Path]
    label_root: Path
    samples_by_sequence: Dict[str, List[ImageSample]]
    total_boxes: int
    boxes_by_sequence: Dict[str, int]
    ignored_label_files: List[Path]

    @property
    def total_images(self) -> int:
        """返回审计通过后的图片总数。"""

        return sum(len(samples) for samples in self.samples_by_sequence.values())

    @property
    def total_labels(self) -> int:
        """返回标签文件总数。

        当前项目要求图片和标签一一对应，因此该值等同于 `total_images`。
        """

        return self.total_images

    def limited(self, limit_per_sequence: Optional[int]) -> "AuditResult":
        """按序列截取前 N 张样本，生成一个缩小版审计结果。

        这个函数主要用于快速烟雾验证：

        - 不改原始数据；
        - 不改真实目录结构；
        - 只是在内存中裁掉每个序列后半段样本。
        """

        if limit_per_sequence is None:
            return self

        if limit_per_sequence <= 0:
            raise DatasetToolError("--limit-per-sequence 必须大于 0。")

        limited_sequences: Dict[str, List[ImageSample]] = {}
        boxes_by_sequence: Dict[str, int] = {}
        total_boxes = 0

        for sequence_name, samples in self.samples_by_sequence.items():
            # 保留每个序列的前 N 张，维持原有时序顺序。
            limited_samples = samples[:limit_per_sequence]
            limited_sequences[sequence_name] = limited_samples
            box_count = 0
            for sample in limited_samples:
                # 重新读取标签，是为了得到“截断后子集”对应的准确框数统计。
                box_count += len(read_label_entries(sample.label_path))
            boxes_by_sequence[sequence_name] = box_count
            total_boxes += box_count

        return AuditResult(
            image_roots=self.image_roots,
            label_root=self.label_root,
            samples_by_sequence=limited_sequences,
            total_boxes=total_boxes,
            boxes_by_sequence=boxes_by_sequence,
            ignored_label_files=self.ignored_label_files,
        )

    def to_report_dict(self) -> Dict[str, object]:
        """把审计结果转成适合写入 JSON 的字典。"""

        return {
            "image_roots": [str(path) for path in self.image_roots],
            "label_root": str(self.label_root),
            "total_images": self.total_images,
            "total_labels": self.total_labels,
            "total_boxes": self.total_boxes,
            "boxes_by_sequence": self.boxes_by_sequence,
            "samples_by_sequence": {
                name: [sample.image_path.name for sample in samples]
                for name, samples in self.samples_by_sequence.items()
            },
            "ignored_label_files": [str(path) for path in self.ignored_label_files],
        }


@dataclass
class PrepareResult:
    """保存一次 `prepare` 输出数据集的摘要信息。

    这些字段会被：

    - CLI 打印成摘要；
    - 写入 `prepare_report.json`；
    - 供 `all` 命令整合进总报告。
    """

    mode: str
    split_strategy: str
    dataset_root: Path
    dataset_yaml: Path
    split_image_counts: Dict[str, int]
    split_label_counts: Dict[str, int]
    split_box_counts: Dict[str, int]
    positive_crops: int
    negative_crops: int
    fallback_fullframes: int
    unmatched_boxes: int
    images_without_person_detection: int
    report_path: Path

    def to_report_dict(self) -> Dict[str, object]:
        """把准备结果转成适合写入 JSON 的字典。"""

        return {
            "mode": self.mode,
            "split_strategy": self.split_strategy,
            "dataset_root": str(self.dataset_root),
            "dataset_yaml": str(self.dataset_yaml),
            "split_image_counts": self.split_image_counts,
            "split_label_counts": self.split_label_counts,
            "split_box_counts": self.split_box_counts,
            "positive_crops": self.positive_crops,
            "negative_crops": self.negative_crops,
            "fallback_fullframes": self.fallback_fullframes,
            "unmatched_boxes": self.unmatched_boxes,
            "images_without_person_detection": self.images_without_person_detection,
            "report_path": str(self.report_path),
        }


# 用于从文件名中抽取 `_frame_123` 这一类帧序号。
# 如果能抽到，就优先按帧号排序；否则退化为按文件名排序。
FRAME_INDEX_RE = re.compile(r"_frame_(\d+)$", re.IGNORECASE)

# 允许标签里存在极小的浮点舍入误差；超出这个量级则视为真正的标注问题。
LABEL_COORD_TOLERANCE = 1e-6
LABEL_BOX_EDGE_TOLERANCE = 1e-6


def collect_image_files(
    image_roots: Sequence[Path],
    image_extensions: Sequence[str],
) -> Dict[str, List[Path]]:
    """收集每个原始序列目录中的图片文件，并按时序尽量排序。

    返回值的 key 是“序列目录名”，value 是该序列下的图片路径列表。
    """

    sequence_files: Dict[str, List[Path]] = {}
    normalized_exts = {suffix.lower() for suffix in image_extensions}

    for image_root in image_roots:
        if not image_root.exists():
            raise DatasetToolError("图片目录不存在: {0}".format(image_root))
        if not image_root.is_dir():
            raise DatasetToolError("图片路径不是目录: {0}".format(image_root))

        files = [
            path
            for path in image_root.iterdir()
            if path.is_file() and path.suffix.lower() in normalized_exts
        ]
        if not files:
            raise DatasetToolError("图片目录为空或无支持图片: {0}".format(image_root))

        # 如果文件名里带 `_frame_xxx`，会优先按帧号排序；
        # 否则退化到按文件名排序，尽量保持确定性。
        files.sort(key=_image_sort_key)
        sequence_files[image_root.name] = files

    return sequence_files


def audit_dataset(
    image_roots: Sequence[Path],
    label_root: Path,
    image_extensions: Sequence[str],
    ignored_label_filenames: Sequence[str],
) -> AuditResult:
    """审计原始图片与标签，确保它们能安全进入训练流程。

    这里会检查：

    - 图片目录和标签目录是否存在；
    - 图片与标签是否可以按同名 stem 一一对应；
    - 不同序列之间是否出现重名图片；
    - 标签文件内容是否满足当前项目的 YOLO 单类检测约定。
    """

    if not label_root.exists():
        raise DatasetToolError("标注目录不存在: {0}".format(label_root))
    if not label_root.is_dir():
        raise DatasetToolError("标注路径不是目录: {0}".format(label_root))

    sequence_files = collect_image_files(image_roots, image_extensions)
    ignored_names = {name.lower() for name in ignored_label_filenames}
    # 统一标签目录下的所有 txt 文件先全部收集出来，再做“忽略 / 建索引 / 配对”。
    label_files = list(label_root.glob("*.txt"))
    label_map: Dict[str, Path] = {}
    ignored_label_files: List[Path] = []

    for label_path in label_files:
        if label_path.name.lower() in ignored_names:
            ignored_label_files.append(label_path)
            continue
        # 统一标签目录下默认要求 stem 全局唯一，后面配对就依赖这个索引。
        label_map[label_path.stem] = label_path

    duplicate_stems: List[str] = []
    missing_labels: List[str] = []
    invalid_messages: List[str] = []
    boxes_by_sequence: Dict[str, int] = {}
    samples_by_sequence: Dict[str, List[ImageSample]] = {}
    seen_stems: Dict[str, Path] = {}
    total_boxes = 0

    for sequence_name, image_paths in sequence_files.items():
        sequence_samples: List[ImageSample] = []
        sequence_boxes = 0

        for image_path in image_paths:
            stem = image_path.stem
            existing = seen_stems.get(stem)
            if existing is not None:
                # 统一标签目录模式下，跨序列重名会导致无法判断该配哪个标签。
                duplicate_stems.append("{0} <-> {1}".format(existing, image_path))
                continue
            seen_stems[stem] = image_path

            label_path = label_map.get(stem)
            if label_path is None:
                missing_labels.append(str(image_path))
                continue

            try:
                # 这里不仅是读取标签，也顺手校验字段合法性。
                entries = read_label_entries(label_path)
            except DatasetToolError as exc:
                invalid_messages.append(str(exc))
                continue

            sequence_boxes += len(entries)
            total_boxes += len(entries)
            sequence_samples.append(
                ImageSample(
                    sequence_name=sequence_name,
                    image_path=image_path,
                    label_path=label_path,
                    stem=stem,
                )
            )

        samples_by_sequence[sequence_name] = sequence_samples
        boxes_by_sequence[sequence_name] = sequence_boxes

    # 剩下没有任何图片认领的标签文件，就是“孤儿标签”。
    orphan_labels = [
        str(label_path)
        for stem, label_path in sorted(label_map.items())
        if stem not in seen_stems
    ]

    error_lines: List[str] = []
    if duplicate_stems:
        error_lines.append("发现重名图片，统一标注目录无法安全配对：")
        error_lines.extend("  - {0}".format(item) for item in duplicate_stems)
    if missing_labels:
        error_lines.append("以下图片缺少同名标注：")
        error_lines.extend("  - {0}".format(item) for item in missing_labels)
    if orphan_labels:
        error_lines.append("以下标注找不到对应图片：")
        error_lines.extend("  - {0}".format(item) for item in orphan_labels)
    if invalid_messages:
        error_lines.append("发现非法标注内容：")
        error_lines.extend("  - {0}".format(item) for item in invalid_messages)

    if error_lines:
        raise DatasetToolError("\n".join(error_lines))

    return AuditResult(
        image_roots=list(image_roots),
        label_root=label_root,
        samples_by_sequence=samples_by_sequence,
        total_boxes=total_boxes,
        boxes_by_sequence=boxes_by_sequence,
        ignored_label_files=sorted(ignored_label_files),
    )


def read_label_entries(label_path: Path) -> List[LabelEntry]:
    """读取并校验单个 YOLO 标签文件。"""

    try:
        lines = label_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        # 某些历史标签文件编码不规范，这里允许尽量容错读取，
        # 但真正格式不合法仍会在下面的字段检查里被拦住。
        lines = label_path.read_text(encoding="utf-8", errors="ignore").splitlines()

    entries: List[LabelEntry] = []
    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        if len(parts) != 5:
            raise DatasetToolError(
                "{0}:{1} 不是合法 YOLO 检测标注，字段数应为 5，实际为 {2}。".format(
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
            raise DatasetToolError(
                "{0}:{1} 含有非数字字段。".format(label_path, line_number)
            ) from exc

        if class_id not in config.CLASS_NAMES:
            raise DatasetToolError(
                "{0}:{1} 类别 ID 非法，当前仅支持 {2}。".format(
                    label_path,
                    line_number,
                    sorted(config.CLASS_NAMES),
                )
            )

        # 当前项目显式约定使用归一化 YOLO 坐标，因此必须落在 [0, 1]。
        numeric_fields = [x_center, y_center, width, height]
        if any(
            value < -LABEL_COORD_TOLERANCE or value > 1.0 + LABEL_COORD_TOLERANCE
            for value in numeric_fields
        ):
            raise DatasetToolError(
                "{0}:{1} 坐标必须归一化到 [0,1]。".format(label_path, line_number)
            )

        # 先把极小的数值误差裁回 [0, 1]，避免 1.0000001 这一类浮点抖动误判。
        x_center = min(max(x_center, 0.0), 1.0)
        y_center = min(max(y_center, 0.0), 1.0)
        width = min(max(width, 0.0), 1.0)
        height = min(max(height, 0.0), 1.0)
        if width <= 0.0 or height <= 0.0:
            raise DatasetToolError(
                "{0}:{1} width/height 必须大于 0。".format(label_path, line_number)
            )

        x1 = x_center - width / 2.0
        y1 = y_center - height / 2.0
        x2 = x_center + width / 2.0
        y2 = y_center + height / 2.0
        edge_overshoot = max(
            0.0,
            -x1,
            -y1,
            x2 - 1.0,
            y2 - 1.0,
        )
        if edge_overshoot > LABEL_BOX_EDGE_TOLERANCE:
            raise DatasetToolError(
                "{0}:{1} 标注框越过图像边界，"
                "要求满足 x_center±width/2 与 y_center±height/2 都落在 [0,1]。".format(
                    label_path,
                    line_number,
                )
            )
        if edge_overshoot > 0.0:
            # 对极小越界做容错裁剪，并在 prepare 时写回规范化后的标签。
            clipped_x1 = min(max(x1, 0.0), 1.0)
            clipped_y1 = min(max(y1, 0.0), 1.0)
            clipped_x2 = min(max(x2, 0.0), 1.0)
            clipped_y2 = min(max(y2, 0.0), 1.0)
            if clipped_x2 <= clipped_x1 or clipped_y2 <= clipped_y1:
                raise DatasetToolError(
                    "{0}:{1} 标注框在边界裁剪后面积为 0，请检查原始标签。".format(
                        label_path,
                        line_number,
                    )
                )
            warnings.warn(
                "{0}:{1} 标注框存在极小越界，已自动裁剪到 [0,1]。".format(
                    label_path,
                    line_number,
                ),
                RuntimeWarning,
                stacklevel=2,
            )
            x_center = (clipped_x1 + clipped_x2) / 2.0
            y_center = (clipped_y1 + clipped_y2) / 2.0
            width = clipped_x2 - clipped_x1
            height = clipped_y2 - clipped_y1

        entries.append(
            LabelEntry(
                class_id=class_id,
                x_center=x_center,
                y_center=y_center,
                width=width,
                height=height,
            )
        )
    return entries


def ensure_output_root(output_root: Path, overwrite: bool) -> None:
    """在真正写数据之前，安全地准备输出目录。

    设计目标是：

    - 防止误把样本写进一个已有的非空目录；
    - 只有显式传入 `--overwrite` 时才允许清空旧目录；
    - 确保后续写文件时目录结构已经存在。
    """

    if output_root.exists():
        if not output_root.is_dir():
            raise DatasetToolError("输出路径不是目录: {0}".format(output_root))
        has_contents = any(output_root.iterdir())
        if has_contents and not overwrite:
            raise DatasetToolError(
                "输出目录已存在且非空: {0}。如需覆盖，请显式传入 --overwrite。".format(
                    output_root
                )
            )
        if has_contents and overwrite:
            shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)


def build_split_map(
    audit_result: AuditResult,
    split_ratios: Dict[str, float],
    split_strategy: str,
) -> Dict[str, List[ImageSample]]:
    """根据切分策略生成 `train / val / test` 样本映射表。"""

    if split_strategy == "sequence_contiguous":
        return split_samples_by_sequence_contiguous(audit_result, split_ratios)
    if split_strategy == "sequence_holdout":
        return split_samples_by_sequence_holdout(audit_result, split_ratios)
    raise DatasetToolError("Unknown split strategy: {0}".format(split_strategy))


def split_samples_by_sequence_contiguous(
    audit_result: AuditResult,
    split_ratios: Dict[str, float],
) -> Dict[str, List[ImageSample]]:
    """在每个序列内部按连续区间切成 train/val/test。

    这种方式适合“序列数很少，但每个序列内部样本较多”的场景。
    好处是每个序列都能参与训练，不至于因为严格按序列隔离而让训练集太小。
    """

    split_map: Dict[str, List[ImageSample]] = {"train": [], "val": [], "test": []}

    for samples in audit_result.samples_by_sequence.values():
        # 每个序列单独计算一套切分数量，然后按顺序切片。
        counts = contiguous_split_counts(len(samples), split_ratios)
        cursor = 0
        for split_name in ("train", "val", "test"):
            count = counts[split_name]
            split_map[split_name].extend(samples[cursor:cursor + count])
            cursor += count

    return split_map


def split_samples_by_sequence_holdout(
    audit_result: AuditResult,
    split_ratios: Dict[str, float],
) -> Dict[str, List[ImageSample]]:
    """按完整序列分配到 train/val/test，不在 split 之间混序列。"""

    # 这里沿用 `samples_by_sequence` 的插入顺序，
    # 当前项目实际就是按 `config.IMAGE_ROOTS` 的顺序切分。
    ordered_sequences = list(audit_result.samples_by_sequence.items())
    counts = contiguous_split_counts(len(ordered_sequences), split_ratios)
    split_map: Dict[str, List[ImageSample]] = {"train": [], "val": [], "test": []}

    cursor = 0
    for split_name in ("train", "val", "test"):
        count = counts[split_name]
        for _, samples in ordered_sequences[cursor:cursor + count]:
            split_map[split_name].extend(samples)
        cursor += count

    return split_map


def contiguous_split_counts(
    total: int,
    split_ratios: Dict[str, float],
) -> Dict[str, int]:
    """把浮点比例转换成整数样本数，并尽量保证每个有效 split 可用。

    难点在于：

    - 比例乘以样本数之后通常不是整数；
    - 样本很少时，某个 split 可能被分成 0；
    - 但训练/评估通常又希望 train/val/test 至少有基本可用样本。

    因此这里做了一个“先 floor，再补足，再回收”的平衡过程。
    """

    ordered = ("train", "val", "test")
    if total <= 0:
        return {"train": 0, "val": 0, "test": 0}

    if total == 1:
        # 只有 1 张时只能给 train，无法再切 val/test。
        return {"train": 1, "val": 0, "test": 0}

    positive_splits = [name for name in ordered if split_ratios.get(name, 0.0) > 0]
    if total < len(positive_splits):
        # 如果样本数比有效 split 还少，就按 train -> val -> test 依次至少分 1 张。
        counts = {name: 0 for name in ordered}
        for split_name in ordered[:total]:
            counts[split_name] = 1
        return counts

    # 原始浮点数量，例如 95 * 0.15 = 14.25。
    raw_counts = {
        split_name: total * float(split_ratios.get(split_name, 0.0))
        for split_name in ordered
    }
    counts = {
        split_name: int(math.floor(raw_counts[split_name]))
        for split_name in ordered
    }

    for split_name in positive_splits:
        if counts[split_name] == 0:
            counts[split_name] = 1

    while sum(counts.values()) > total:
        # 如果补 1 之后总数超了，就优先从“占得最多”的 split 回收。
        reducible = max(
            ordered,
            key=lambda name: (counts[name], raw_counts[name]),
        )
        if counts[reducible] > 1:
            counts[reducible] -= 1
        else:
            break

    while sum(counts.values()) < total:
        # 如果 floor 之后总数不够，就把剩余样本补给“最应该多拿”的 split。
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


def prepare_dataset(
    audit_result: AuditResult,
    output_root: Path,
    mode: str,
    overwrite: bool,
    split_strategy: str,
    person_model_path: Optional[Path],
    person_conf: float,
    person_imgsz: int,
    assignment_min_ioa: float,
    monitored_person_labels: Sequence[str],
    include_empty_person_crops: bool,
    fallback_to_fullframe: bool,
) -> PrepareResult:
    """按照给定模式和切分策略，真正生成训练数据集目录。"""

    if mode not in ("fullframe", "personcrop"):
        raise DatasetToolError("不支持的 prepare mode: {0}".format(mode))

    # 先准备一个干净的输出目录，再开始写图像和标签。
    ensure_output_root(output_root, overwrite=overwrite)
    split_map = build_split_map(audit_result, config.SPLIT_RATIOS, split_strategy)
    if mode == "fullframe":
        return _prepare_fullframe_dataset(
            split_map=split_map,
            output_root=output_root,
            split_strategy=split_strategy,
        )
    return _prepare_personcrop_dataset(
        split_map=split_map,
        output_root=output_root,
        split_strategy=split_strategy,
        person_model_path=person_model_path,
        person_conf=person_conf,
        person_imgsz=person_imgsz,
        assignment_min_ioa=assignment_min_ioa,
        monitored_person_labels=monitored_person_labels,
        include_empty_person_crops=include_empty_person_crops,
        fallback_to_fullframe=fallback_to_fullframe,
    )


def _prepare_fullframe_dataset(
    split_map: Dict[str, List[ImageSample]],
    output_root: Path,
    split_strategy: str,
) -> PrepareResult:
    """生成普通 fullframe 数据集。

    这种模式最直接：

    - 原图复制到 `images/{split}`；
    - 原标签复制到 `labels/{split}`；
    - 不做人裁剪、不做框重映射。
    """

    split_image_counts = {"train": 0, "val": 0, "test": 0}
    split_label_counts = {"train": 0, "val": 0, "test": 0}
    split_box_counts = {"train": 0, "val": 0, "test": 0}

    for split_name, samples in split_map.items():
        image_dir = output_root / "images" / split_name
        label_dir = output_root / "labels" / split_name
        image_dir.mkdir(parents=True, exist_ok=True)
        label_dir.mkdir(parents=True, exist_ok=True)

        for sample in samples:
            # fullframe 模式下保留原图，同时把标签按当前校验规则重写一遍。
            shutil.copy2(sample.image_path, image_dir / sample.image_path.name)
            # 标签这里统一经过一次解析再写回，顺带吸收极小的浮点越界问题。
            label_entries = read_label_entries(sample.label_path)
            write_label_file(label_dir / sample.label_path.name, label_entries)
            split_image_counts[split_name] += 1
            split_label_counts[split_name] += 1
            split_box_counts[split_name] += len(label_entries)

    dataset_yaml = write_dataset_yaml(output_root)
    report_path = output_root / "prepare_report.json"
    return PrepareResult(
        mode="fullframe",
        split_strategy=split_strategy,
        dataset_root=output_root,
        dataset_yaml=dataset_yaml,
        split_image_counts=split_image_counts,
        split_label_counts=split_label_counts,
        split_box_counts=split_box_counts,
        positive_crops=sum(split_image_counts.values()),
        negative_crops=0,
        fallback_fullframes=0,
        unmatched_boxes=0,
        images_without_person_detection=0,
        report_path=report_path,
    )


def _prepare_personcrop_dataset(
    split_map: Dict[str, List[ImageSample]],
    output_root: Path,
    split_strategy: str,
    person_model_path: Optional[Path],
    person_conf: float,
    person_imgsz: int,
    assignment_min_ioa: float,
    monitored_person_labels: Sequence[str],
    include_empty_person_crops: bool,
    fallback_to_fullframe: bool,
) -> PrepareResult:
    """生成人物裁剪版数据集。

    处理流程如下：

    1. 先用人物检测模型找出图中的 person 框；
    2. 再把原始 clothes GT 框分配给最合适的人框；
    3. 对每个人框裁出局部图像，并把 clothes 框映射到 crop 坐标系；
    4. 如果有 clothes 框无法归属到任何人框，可按配置回退为 fullframe 样本。
    """

    if person_model_path is None:
        raise DatasetToolError(
            "personcrop 模式需要可用的人体检测权重，请通过 --person-model 指定，或让默认候选路径存在。"
        )

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise DatasetToolError(
            "未安装 ultralytics，无法执行 personcrop 数据准备。"
        ) from exc

    # 这里的人体检测模型只用于“切 person crop”，不参与最终工服模型训练。
    person_model = YOLO(str(person_model_path))
    monitored_labels = {label.strip() for label in monitored_person_labels if label.strip()}

    split_image_counts = {"train": 0, "val": 0, "test": 0}
    split_label_counts = {"train": 0, "val": 0, "test": 0}
    split_box_counts = {"train": 0, "val": 0, "test": 0}
    positive_crops = 0
    negative_crops = 0
    fallback_fullframes = 0
    unmatched_boxes = 0
    images_without_person_detection = 0

    for split_name, samples in split_map.items():
        image_dir = output_root / "images" / split_name
        label_dir = output_root / "labels" / split_name
        image_dir.mkdir(parents=True, exist_ok=True)
        label_dir.mkdir(parents=True, exist_ok=True)

        for sample in samples:
            image = cv2.imread(str(sample.image_path))
            if image is None:
                raise DatasetToolError("无法读取图片: {0}".format(sample.image_path))

            image_height, image_width = image.shape[:2]
            gt_entries = read_label_entries(sample.label_path)
            # 先把归一化 YOLO 标签转回像素级 xyxy，便于和 person 检测框做几何运算。
            gt_boxes = [
                {
                    "entry": entry,
                    "bbox": yolo_entry_to_xyxy(entry, image_width, image_height),
                }
                for entry in gt_entries
            ]

            person_detections = detect_person_boxes(
                person_model=person_model,
                image=image,
                confidence_threshold=person_conf,
                imgsz=person_imgsz,
                monitored_labels=monitored_labels,
            )
            if not person_detections:
                images_without_person_detection += 1

            # 把每个 clothes GT 框分配给最合适的人框；分不出去的放进 unmatched。
            assignments, unmatched = assign_boxes_to_persons(
                person_detections=person_detections,
                gt_boxes=gt_boxes,
                assignment_min_ioa=assignment_min_ioa,
            )

            for person_index, person_box in enumerate(person_detections):
                assigned_boxes = assignments.get(person_index, [])
                if not assigned_boxes and not include_empty_person_crops:
                    # 如果该 person 没匹配到任何 clothes，且又不想保留空样本，就跳过。
                    continue

                crop_image, local_entries = crop_person_sample(
                    image=image,
                    person_box=person_box,
                    assigned_boxes=assigned_boxes,
                )
                if crop_image is None:
                    continue

                output_stem = "{0}_person_{1:02d}".format(sample.stem, person_index)
                crop_path = image_dir / "{0}.jpg".format(output_stem)
                label_path = label_dir / "{0}.txt".format(output_stem)

                # 保存裁剪图，并把裁剪后局部标签写回 YOLO 格式。
                cv2.imwrite(str(crop_path), crop_image)
                write_label_file(label_path, local_entries)

                split_image_counts[split_name] += 1
                split_label_counts[split_name] += 1
                split_box_counts[split_name] += len(local_entries)
                if local_entries:
                    positive_crops += 1
                else:
                    negative_crops += 1

            if unmatched:
                unmatched_boxes += len(unmatched)

            if unmatched and fallback_to_fullframe:
                # 有些 clothes 框实在匹配不到任何 person 时，为了不丢正样本，
                # 可以把这些框直接回退成一张 fullframe 样本。
                fallback_stem = "{0}_fallback".format(sample.stem)
                fallback_image_path = image_dir / "{0}{1}".format(
                    fallback_stem,
                    sample.image_path.suffix.lower(),
                )
                fallback_label_path = label_dir / "{0}.txt".format(fallback_stem)
                shutil.copy2(sample.image_path, fallback_image_path)
                write_label_file(
                    fallback_label_path,
                    [item["entry"] for item in unmatched],
                )
                split_image_counts[split_name] += 1
                split_label_counts[split_name] += 1
                split_box_counts[split_name] += len(unmatched)
                fallback_fullframes += 1

            if not person_detections and gt_entries and not fallback_to_fullframe:
                raise DatasetToolError(
                    "图片 {0} 未检测到任何 person，且当前禁用了 fullframe 回退，"
                    "会造成正样本丢失。".format(sample.image_path)
                )

    dataset_yaml = write_dataset_yaml(output_root)
    report_path = output_root / "prepare_report.json"
    return PrepareResult(
        mode="personcrop",
        split_strategy=split_strategy,
        dataset_root=output_root,
        dataset_yaml=dataset_yaml,
        split_image_counts=split_image_counts,
        split_label_counts=split_label_counts,
        split_box_counts=split_box_counts,
        positive_crops=positive_crops,
        negative_crops=negative_crops,
        fallback_fullframes=fallback_fullframes,
        unmatched_boxes=unmatched_boxes,
        images_without_person_detection=images_without_person_detection,
        report_path=report_path,
    )


def detect_person_boxes(
    person_model,
    image,
    confidence_threshold: float,
    imgsz: int,
    monitored_labels: Sequence[str],
) -> List[Tuple[int, int, int, int]]:
    """运行人体检测模型，并返回合法的 person 框列表。

    返回的坐标格式为像素级 `xyxy`，便于后续做匹配和裁剪。
    """

    results = person_model(
        image,
        conf=confidence_threshold,
        imgsz=imgsz,
        verbose=False,
    )
    detections: List[Tuple[int, int, int, int]] = []
    for result in results:
        names = result.names
        for box in result.boxes:
            cls_raw = box.cls[0]
            cls_id = int(cls_raw.item()) if hasattr(cls_raw, "item") else int(cls_raw)
            label = names[cls_id] if isinstance(names, (list, dict)) else str(cls_id)
            if monitored_labels and label not in monitored_labels:
                continue
            # 这里把浮点框转成整数像素框，后续裁剪时更直接。
            x1, y1, x2, y2 = [int(value) for value in box.xyxy[0].tolist()]
            if x2 > x1 and y2 > y1:
                detections.append((x1, y1, x2, y2))
    return detections


def assign_boxes_to_persons(
    person_detections: Sequence[Tuple[int, int, int, int]],
    gt_boxes: Sequence[Dict[str, object]],
    assignment_min_ioa: float,
) -> Tuple[Dict[int, List[Dict[str, object]]], List[Dict[str, object]]]:
    """把每个 clothes GT 框分配给最合适的 person 检测框。"""

    assignments: Dict[int, List[Dict[str, object]]] = {
        index: [] for index in range(len(person_detections))
    }
    unmatched: List[Dict[str, object]] = []

    for gt_box in gt_boxes:
        candidate_index = match_clothes_box_to_person(
            clothes_box=gt_box["bbox"],
            person_boxes=person_detections,
            assignment_min_ioa=assignment_min_ioa,
        )
        if candidate_index is None:
            unmatched.append(gt_box)
        else:
            assignments[candidate_index].append(gt_box)

    return assignments, unmatched


def match_clothes_box_to_person(
    clothes_box: Tuple[float, float, float, float],
    person_boxes: Sequence[Tuple[int, int, int, int]],
    assignment_min_ioa: float,
) -> Optional[int]:
    """为单个 clothes 框选出最佳 person 框。

    判定逻辑分两层：

    1. 优先看 clothes 框中心点是否落在 person 框内；
    2. 如果中心点不在，但与 person 框的 IOA 足够大，也允许匹配。

    最终会优先选择“中心点命中”的人框；若有多个，再按 IOA 细分。
    """

    center_x = (clothes_box[0] + clothes_box[2]) / 2.0
    center_y = (clothes_box[1] + clothes_box[3]) / 2.0

    candidates: List[Tuple[float, float, int]] = []
    for index, person_box in enumerate(person_boxes):
        ioa = intersection_over_box(clothes_box, person_box)
        inside_center = point_in_box(center_x, center_y, person_box)
        if not inside_center and ioa < assignment_min_ioa:
            continue
        # 用一个很小的面积惩罚做 tie-break，倾向更紧凑、更贴近目标的人框。
        person_area = max(1.0, box_area(person_box))
        priority = 1.0 if inside_center else 0.0
        candidates.append((priority, ioa - person_area * 1e-9, index))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    return candidates[0][2]


def crop_person_sample(
    image,
    person_box: Tuple[int, int, int, int],
    assigned_boxes: Sequence[Dict[str, object]],
) -> Tuple[Optional[object], List[LabelEntry]]:
    """裁剪单个人物区域，并把 clothes 框映射到 crop 局部坐标系。"""

    image_height, image_width = image.shape[:2]
    x1 = max(0, int(person_box[0]))
    y1 = max(0, int(person_box[1]))
    x2 = min(image_width, int(person_box[2]))
    y2 = min(image_height, int(person_box[3]))
    if x2 <= x1 or y2 <= y1:
        return None, []

    crop = image[y1:y2, x1:x2]
    crop_width = x2 - x1
    crop_height = y2 - y1
    local_entries: List[LabelEntry] = []

    for item in assigned_boxes:
        box = item["bbox"]
        # 先把 clothes 框裁到人物框内部，避免越界到 crop 外部。
        clipped = (
            max(float(box[0]), float(x1)),
            max(float(box[1]), float(y1)),
            min(float(box[2]), float(x2)),
            min(float(box[3]), float(y2)),
        )
        if clipped[2] <= clipped[0] or clipped[3] <= clipped[1]:
            continue
        local_entries.append(
            xyxy_to_yolo_entry(
                # 再把“相对整图”的坐标平移成“相对 crop 左上角”的坐标。
                box=(
                    clipped[0] - x1,
                    clipped[1] - y1,
                    clipped[2] - x1,
                    clipped[3] - y1,
                ),
                image_width=crop_width,
                image_height=crop_height,
                class_id=item["entry"].class_id,
            )
        )

    return crop, local_entries


def yolo_entry_to_xyxy(
    entry: LabelEntry,
    image_width: int,
    image_height: int,
) -> Tuple[float, float, float, float]:
    """把归一化 YOLO `xywh` 坐标转成像素级 `xyxy` 坐标。"""

    x_center = entry.x_center * image_width
    y_center = entry.y_center * image_height
    box_width = entry.width * image_width
    box_height = entry.height * image_height
    x1 = x_center - box_width / 2.0
    y1 = y_center - box_height / 2.0
    x2 = x_center + box_width / 2.0
    y2 = y_center + box_height / 2.0
    return (x1, y1, x2, y2)


def xyxy_to_yolo_entry(
    box: Tuple[float, float, float, float],
    image_width: int,
    image_height: int,
    class_id: int,
) -> LabelEntry:
    """把像素级 `xyxy` 坐标重新转回归一化 YOLO `xywh` 格式。"""

    # 这里至少保留 1 像素宽高，避免极端裁剪后产生 0 面积框。
    width = max(1.0, box[2] - box[0])
    height = max(1.0, box[3] - box[1])
    x_center = box[0] + width / 2.0
    y_center = box[1] + height / 2.0
    return LabelEntry(
        class_id=class_id,
        x_center=min(max(x_center / float(image_width), 0.0), 1.0),
        y_center=min(max(y_center / float(image_height), 0.0), 1.0),
        width=min(max(width / float(image_width), 1e-6), 1.0),
        height=min(max(height / float(image_height), 1e-6), 1.0),
    )


def write_dataset_yaml(dataset_root: Path) -> Path:
    """在准备好的数据集根目录下写出 `dataset.yaml`。"""

    dataset_yaml = dataset_root / "dataset.yaml"
    names_yaml = "".join(
        "  {0}: {1}\n".format(class_id, class_name)
        for class_id, class_name in sorted(config.CLASS_NAMES.items())
    )
    yaml_text = (
        "path: {0}\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n"
        "names:\n"
        "{1}"
    ).format(dataset_root.as_posix(), names_yaml)
    dataset_yaml.write_text(yaml_text, encoding="utf-8")
    return dataset_yaml


def write_label_file(label_path: Path, entries: Iterable[LabelEntry]) -> None:
    """把内存中的标注对象列表写成 YOLO 标签文件。"""

    lines = [entry.to_yolo_line() for entry in entries]
    label_path.write_text("\n".join(lines), encoding="utf-8")


def _image_sort_key(image_path: Path) -> Tuple[int, str]:
    """生成图片排序 key：优先帧序号，其次文件名。"""

    match = FRAME_INDEX_RE.search(image_path.stem)
    if match:
        return (int(match.group(1)), image_path.name)
    return (10**9, image_path.name)


def point_in_box(
    x_coord: float,
    y_coord: float,
    box: Tuple[float, float, float, float],
) -> bool:
    """判断一个点是否落在某个 `xyxy` 框内。"""

    return box[0] <= x_coord <= box[2] and box[1] <= y_coord <= box[3]


def box_area(box: Tuple[float, float, float, float]) -> float:
    """计算一个 `xyxy` 框的非负面积。"""

    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def intersection_over_box(
    small_box: Tuple[float, float, float, float],
    large_box: Tuple[float, float, float, float],
) -> float:
    """计算 IOA（交集面积 / `small_box` 面积）。

    这里不用 IoU，而是用 IOA，是因为我们更关心“clothes 框有多少比例落在人框里”，
    而不是两个框整体是否相似。
    """

    ix1 = max(small_box[0], large_box[0])
    iy1 = max(small_box[1], large_box[1])
    ix2 = min(small_box[2], large_box[2])
    iy2 = min(small_box[3], large_box[3])
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    inter_area = (ix2 - ix1) * (iy2 - iy1)
    return inter_area / max(1.0, box_area(small_box))

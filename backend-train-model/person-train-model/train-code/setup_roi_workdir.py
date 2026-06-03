from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Sequence

from prepare_person_dataset import (
    DEFAULT_PROJECT_CONFIG,
    PERSON_ROOT,
    PersonProjectContext,
    PersonSequence,
    load_person_project_context,
)


DEFAULT_FRAMES_PER_SEQUENCE = 3
FRAME_INDEX_RE = re.compile(r"_frame_(\d+)$", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="为每条 person 序列创建 Labelme ROI 标注工作区并抽取代表帧。"
    )
    parser.add_argument(
        "--project-config",
        default=str(DEFAULT_PROJECT_CONFIG),
        help="person 项目配置 JSON 路径。",
    )
    parser.add_argument(
        "--roi-work-root",
        help="ROI 标注工作区根目录；默认读取 project_config.json 中的 roi.work_root。",
    )
    parser.add_argument(
        "--frames-per-sequence",
        type=int,
        default=DEFAULT_FRAMES_PER_SEQUENCE,
        help="每条序列抽取的代表帧数量。",
    )
    parser.add_argument(
        "--overwrite-frames",
        action="store_true",
        help="允许覆盖 roi-work/<sequence>/frames 下已存在的同名代表帧。",
    )
    return parser.parse_args()


def image_sort_key(image_path: Path) -> tuple:
    match = FRAME_INDEX_RE.search(image_path.stem)
    if match:
        return (int(match.group(1)), image_path.name)
    return (10**9, image_path.name)


def collect_image_paths(
    sequence: PersonSequence,
    image_extensions: Sequence[str],
) -> List[Path]:
    if not sequence.image_root.exists():
        raise RuntimeError("序列图片目录不存在: {0}".format(sequence.image_root))
    if not sequence.image_root.is_dir():
        raise RuntimeError("序列图片路径不是目录: {0}".format(sequence.image_root))
    allowed_suffixes = {suffix.lower() for suffix in image_extensions}
    image_paths = [
        path
        for path in sequence.image_root.iterdir()
        if path.is_file() and path.suffix.lower() in allowed_suffixes
    ]
    return sorted(image_paths, key=image_sort_key)


def representative_indices(total_count: int, desired_count: int) -> List[int]:
    if desired_count <= 0:
        raise RuntimeError("--frames-per-sequence 必须大于 0。")
    if total_count <= 0:
        return []
    if total_count <= desired_count:
        return list(range(total_count))
    if desired_count == 1:
        return [0]

    selected: List[int] = []
    used = set()
    for position in range(desired_count):
        index = int(round(position * (total_count - 1) / float(desired_count - 1)))
        if index not in used:
            selected.append(index)
            used.add(index)

    fallback_index = 0
    while len(selected) < desired_count and fallback_index < total_count:
        if fallback_index not in used:
            selected.append(fallback_index)
            used.add(fallback_index)
        fallback_index += 1
    return sorted(selected)


def select_representative_frames(
    image_paths: Sequence[Path],
    frames_per_sequence: int,
) -> List[Path]:
    return [
        image_paths[index]
        for index in representative_indices(len(image_paths), frames_per_sequence)
    ]


def copy_representative_frame(
    source_path: Path,
    target_dir: Path,
    *,
    overwrite_frames: bool,
) -> Dict[str, str]:
    target_path = target_dir / source_path.name
    status = "copied"
    if target_path.exists() and not overwrite_frames:
        status = "exists"
    else:
        if source_path.resolve() != target_path.resolve():
            shutil.copy2(source_path, target_path)
        else:
            status = "same_path"
    return {
        "source": str(source_path),
        "target": str(target_path),
        "status": status,
    }


def labelme_command(frames_dir: Path, roi_json_dir: Path) -> str:
    return "labelme {0} --output {1} --labels roi".format(
        frames_dir,
        roi_json_dir,
    )


def python_labelme_command(frames_dir: Path, roi_json_dir: Path) -> str:
    return "python -m labelme {0} --output {1} --labels roi".format(
        frames_dir,
        roi_json_dir,
    )


def write_sequence_readme(
    sequence_dir: Path,
    *,
    sequence: PersonSequence,
    frames_dir: Path,
    roi_json_dir: Path,
    selected_frames: Sequence[Path],
) -> None:
    selected_text = "\n".join(
        "- `{0}`".format(path.name)
        for path in selected_frames
    )
    if not selected_text:
        selected_text = "- 当前未找到可抽取图片。"
    sequence_dir.joinpath("README.md").write_text(
        (
            "# ROI 标注工作区 - {sequence_name}\n\n"
            "## 目录说明\n\n"
            "- `frames/`：从原序列抽取的代表帧，用于 Labelme 画 ROI。\n"
            "- `roi-json/`：Labelme 保存的 ROI JSON 输出目录。\n\n"
            "## 原始序列\n\n"
            "- source_id：`{source_id}`\n"
            "- group：`{group}`\n"
            "- sequence_name：`{sequence_name}`\n"
            "- image_root：`{image_root}`\n"
            "- label_root：`{label_root}`\n\n"
            "## 本次抽取代表帧\n\n"
            "{selected_text}\n\n"
            "## Labelme 启动命令\n\n"
            "```powershell\n"
            "{labelme_command}\n"
            "```\n\n"
            "如果 `labelme` 命令不可用，使用：\n\n"
            "```powershell\n"
            "{python_labelme_command}\n"
            "```\n\n"
            "## 标注要求\n\n"
            "- 只画业务 ROI 区域，不需要在这里标 person 框。\n"
            "- 标签名统一使用小写 `roi`。\n"
            "- shape 类型使用 `polygon`。\n"
            "- 第一版每条序列只保留一个 ROI polygon。\n"
            "- 保存后的 `.json` 应位于 `roi-json/` 下。\n"
        ).format(
            sequence_name=sequence.sequence_name,
            source_id=sequence.source_id,
            group=sequence.group,
            image_root=sequence.image_root,
            label_root=sequence.label_root,
            selected_text=selected_text,
            labelme_command=labelme_command(frames_dir, roi_json_dir),
            python_labelme_command=python_labelme_command(frames_dir, roi_json_dir),
        ),
        encoding="utf-8",
    )


def write_root_readme(
    roi_work_root: Path,
    *,
    context: PersonProjectContext,
    sequence_count: int,
    frames_per_sequence: int,
) -> None:
    roi_work_root.joinpath("README.md").write_text(
        (
            "# Person ROI 标注工作区\n\n"
            "本目录用于存放 Labelme ROI 标注输入帧和输出 JSON，服务于 ROI-aware person 数据集生成。\n\n"
            "## 目录结构\n\n"
            "```text\n"
            "roi-work/\n"
            "├─ <sequence_name>/\n"
            "│  ├─ frames/      # 自动抽取的代表帧\n"
            "│  ├─ roi-json/    # Labelme 保存的 ROI JSON\n"
            "│  └─ README.md    # 当前序列的标注命令与注意事项\n"
            "└─ roi_work_manifest.json\n"
            "```\n\n"
            "## 当前生成参数\n\n"
            "- 序列数量：`{sequence_count}`\n"
            "- 每条序列代表帧数量：`{frames_per_sequence}`\n"
            "- ROI 配置输出：`{roi_config_path}`\n\n"
            "## 标注规则\n\n"
            "- 只标 ROI polygon，不在 ROI JSON 里标 person。\n"
            "- 标签名统一为 `roi`。\n"
            "- 第一版建议每条序列只保留一个 JSON、一个 ROI polygon。\n"
            "- 如果同一序列放多个 JSON，里面的 ROI polygon 必须一致。\n\n"
            "## 后续命令\n\n"
            "完成全部 ROI JSON 后，在仓库根目录运行：\n\n"
            "```powershell\n"
            "{python_exe} backend-train-model\\person-train-model\\train-code\\run_person_flow.py extract-roi-config --roi-json-root {roi_work_root} --overwrite\n"
            "{python_exe} backend-train-model\\person-train-model\\train-code\\run_person_flow.py prepare-roi-aware --overwrite\n"
            "```\n"
        ).format(
            sequence_count=sequence_count,
            frames_per_sequence=frames_per_sequence,
            roi_config_path=context.roi.config_path,
            roi_work_root=roi_work_root,
            python_exe=sys.executable,
        ),
        encoding="utf-8",
    )


def write_roi_config_readme(context: PersonProjectContext) -> None:
    context.roi.config_path.parent.mkdir(parents=True, exist_ok=True)
    context.roi.config_path.parent.joinpath("README.md").write_text(
        (
            "# ROI 中间配置目录\n\n"
            "本目录用于保存由 Labelme JSON 提取出的统一 ROI 配置。\n\n"
            "默认生成文件：\n\n"
            "```text\n"
            "{roi_config_path}\n"
            "```\n\n"
            "生成命令：\n\n"
            "```powershell\n"
            "{python_exe} backend-train-model\\person-train-model\\train-code\\run_person_flow.py extract-roi-config --overwrite\n"
            "```\n\n"
            "默认 ROI JSON 根目录读取 `person_project_config.json` 中的 `roi.json_root`；\n"
            "如需从手工工作区提取，显式追加 `--roi-json-root <roi-work-root>`。\n\n"
            "如果当前 `roi_config.generated.json` 是空文件或旧文件，使用 `--overwrite` 重新生成即可。\n"
        ).format(roi_config_path=context.roi.config_path, python_exe=sys.executable),
        encoding="utf-8",
    )


def setup_roi_workdir(
    context: PersonProjectContext,
    *,
    roi_work_root: Path,
    frames_per_sequence: int,
    overwrite_frames: bool,
) -> Dict[str, object]:
    work_root = roi_work_root.expanduser().resolve()
    work_root.mkdir(parents=True, exist_ok=True)
    write_roi_config_readme(context)

    sequence_reports: List[Dict[str, object]] = []
    for sequence in context.sequences:
        sequence_dir = work_root / sequence.sequence_name
        frames_dir = sequence_dir / "frames"
        roi_json_dir = sequence_dir / "roi-json"
        frames_dir.mkdir(parents=True, exist_ok=True)
        roi_json_dir.mkdir(parents=True, exist_ok=True)

        image_paths = collect_image_paths(sequence, context.image_extensions)
        selected_frames = select_representative_frames(
            image_paths,
            frames_per_sequence,
        )
        copied_frames = [
            copy_representative_frame(
                source_path,
                frames_dir,
                overwrite_frames=overwrite_frames,
            )
            for source_path in selected_frames
        ]
        write_sequence_readme(
            sequence_dir,
            sequence=sequence,
            frames_dir=frames_dir,
            roi_json_dir=roi_json_dir,
            selected_frames=selected_frames,
        )
        sequence_reports.append(
            {
                "sequence_name": sequence.sequence_name,
                "source_id": sequence.source_id,
                "group": sequence.group,
                "image_root": str(sequence.image_root),
                "label_root": str(sequence.label_root),
                "sequence_dir": str(sequence_dir),
                "frames_dir": str(frames_dir),
                "roi_json_dir": str(roi_json_dir),
                "image_count": len(image_paths),
                "selected_count": len(selected_frames),
                "copied_frames": copied_frames,
                "labelme_command": labelme_command(frames_dir, roi_json_dir),
                "python_labelme_command": python_labelme_command(frames_dir, roi_json_dir),
            }
        )

    write_root_readme(
        work_root,
        context=context,
        sequence_count=len(sequence_reports),
        frames_per_sequence=frames_per_sequence,
    )
    report: Dict[str, object] = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_config": str(context.config_path),
        "roi_work_root": str(work_root),
        "roi_config_path": str(context.roi.config_path),
        "frames_per_sequence": frames_per_sequence,
        "overwrite_frames": overwrite_frames,
        "sequences": sequence_reports,
    }
    manifest_path = work_root / "roi_work_manifest.json"
    manifest_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report["manifest_path"] = str(manifest_path)
    return report


def main() -> int:
    args = parse_args()
    context = load_person_project_context(Path(args.project_config))
    report = setup_roi_workdir(
        context,
        roi_work_root=(
            Path(args.roi_work_root).expanduser().resolve()
            if args.roi_work_root
            else context.roi.work_root
        ),
        frames_per_sequence=args.frames_per_sequence,
        overwrite_frames=args.overwrite_frames,
    )
    print("ROI 工作区 : {0}".format(report["roi_work_root"]))
    print("序列数量   : {0}".format(len(report["sequences"])))
    print("manifest   : {0}".format(report["manifest_path"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

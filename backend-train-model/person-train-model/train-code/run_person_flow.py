from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from prepare_person_dataset import (
    DEFAULT_PROJECT_CONFIG,
    PERSON_ROOT,
    PersonProjectContext,
    load_person_project_context,
    prepare_person_labels,
)


SCRIPT_ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = PERSON_ROOT.parent
TRAIN_SCRIPT = BACKEND_ROOT / "train_workwear.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="person 检测训练包装脚本，不修改现有 train_workwear 逻辑。"
    )
    parser.add_argument(
        "command",
        choices=[
            "prepare-labels",
            "setup-roi-workdir",
            "extract-roi-config",
            "audit",
            "prepare",
            "prepare-roi-aware",
            "train",
            "evaluate",
            "export",
            "all",
        ],
        help="要执行的阶段。",
    )
    parser.add_argument(
        "--project-config",
        default=str(DEFAULT_PROJECT_CONFIG),
        help="person 项目配置 JSON 路径。",
    )
    parser.add_argument(
        "--python-exe",
        default=sys.executable,
        help="调用 train_workwear.py 时使用的 Python 解释器。",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="允许覆盖 prepare 输出、导出 alias 与汇总标签目录。",
    )
    parser.add_argument("--dataset-yaml", help="显式指定 dataset.yaml。")
    parser.add_argument("--weights", help="显式指定待评估 / 待导出的 best.pt。")
    parser.add_argument("--run-name", help="显式指定训练 run 名称。")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--epochs", type=int, default=180)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--patience", type=int, default=40)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--limit-per-sequence", type=int, help="仅用于快速烟雾验证。")
    parser.add_argument(
        "--roi-json-root",
        help=(
            "Labelme ROI JSON / 工作区根目录。"
            "extract-roi-config 默认读取 project_config.json 中的 roi.json_root；"
            "setup-roi-workdir 默认使用 roi.work_root。"
        ),
    )
    parser.add_argument(
        "--roi-config",
        help="统一 ROI 配置 JSON；默认使用 project_config.json 中的 roi.config_path。",
    )
    parser.add_argument(
        "--roi-label",
        default="roi",
        help="Labelme 中用于 ROI polygon 的标签名。",
    )
    parser.add_argument(
        "--roi-frames-per-sequence",
        type=int,
        default=3,
        help="setup-roi-workdir 每条序列抽取的代表帧数量。",
    )
    parser.add_argument(
        "--overwrite-roi-frames",
        action="store_true",
        help="setup-roi-workdir 允许覆盖已抽取的同名代表帧。",
    )
    parser.add_argument(
        "--output-root",
        help="prepare-roi-aware 的输出目录；默认使用 person_dataset.roi_aware_prepared_output_root。",
    )
    parser.add_argument("--base-model", help="显式指定训练基模。")
    parser.add_argument(
        "--from-scratch",
        action="store_true",
        help="从 `.yaml/.yml` 结构文件开始训练。",
    )
    parser.add_argument("--init-weights", help="从 `.yaml/.yml` 结构文件加载初始化权重。")
    parser.add_argument(
        "--allow-remote-model-download",
        action="store_true",
        help="显式允许 Ultralytics 自动下载默认模型。",
    )
    parser.add_argument("--report-name", help="evaluate 阶段的报告文件名。")
    return parser.parse_args()


def run_command(command: List[str]) -> None:
    print("执行命令 : {0}".format(" ".join(command)))
    subprocess.run(command, check=True)


def ensure_person_labels(
    context: PersonProjectContext,
    *,
    overwrite: bool,
) -> None:
    summary = prepare_person_labels(context, overwrite=overwrite)
    print(
        "已准备汇总标签，总图片={0}，新建空标签={1}，源空标签={2}，最终空标签={3}".format(
            summary["totals"]["images"],
            summary["totals"]["created_empty_labels"],
            summary["totals"]["existing_empty_source_labels"],
            summary["totals"]["final_empty_labels"],
        )
    )


def ensure_person_labels_available(
    context: PersonProjectContext,
    *,
    overwrite: bool,
) -> None:
    if context.aggregated_label_root.exists() and not overwrite:
        print("复用既有汇总标签目录 : {0}".format(context.aggregated_label_root))
        return
    ensure_person_labels(context, overwrite=overwrite)


def dataset_yaml_path_for(context: PersonProjectContext, raw_dataset_yaml: Optional[str]) -> Path:
    if raw_dataset_yaml:
        return Path(raw_dataset_yaml).expanduser().resolve()
    return (context.prepared_output_root / "dataset.yaml").resolve()


def roi_config_path_for(context: PersonProjectContext, raw_roi_config: Optional[str]) -> Path:
    if raw_roi_config:
        return Path(raw_roi_config).expanduser().resolve()
    return context.roi.config_path


def roi_json_root_for(
    context: PersonProjectContext,
    raw_roi_json_root: Optional[str],
    *,
    command: str,
) -> Path:
    if raw_roi_json_root:
        return Path(raw_roi_json_root).expanduser().resolve()
    if command == "setup-roi-workdir":
        return context.roi.work_root
    return context.roi.json_root


def roi_output_root_for(context: PersonProjectContext, raw_output_root: Optional[str]) -> Path:
    if raw_output_root:
        return Path(raw_output_root).expanduser().resolve()
    return context.roi_aware_prepared_output_root


def best_weight_path_for(context: PersonProjectContext, run_name: str, raw_weights: Optional[str]) -> Path:
    if raw_weights:
        return Path(raw_weights).expanduser().resolve()
    return (context.artifacts_root / "runs" / run_name / "weights" / "best.pt").resolve()


def train_report_name_for(run_name: str) -> str:
    return "{0}_eval".format(run_name)


def prepare_command(
    *,
    context: PersonProjectContext,
    args: argparse.Namespace,
) -> List[str]:
    command = [
        args.python_exe,
        str(TRAIN_SCRIPT),
        "prepare",
        "--project-config",
        str(context.config_path),
        "--mode",
        "fullframe",
        "--output-root",
        str(context.prepared_output_root),
    ]
    if args.overwrite:
        command.append("--overwrite")
    if args.limit_per_sequence is not None:
        command.extend(["--limit-per-sequence", str(args.limit_per_sequence)])
    return command


def audit_command(
    *,
    context: PersonProjectContext,
    args: argparse.Namespace,
) -> List[str]:
    command = [
        args.python_exe,
        str(TRAIN_SCRIPT),
        "audit",
        "--project-config",
        str(context.config_path),
    ]
    if args.limit_per_sequence is not None:
        command.extend(["--limit-per-sequence", str(args.limit_per_sequence)])
    return command


def train_command(
    *,
    context: PersonProjectContext,
    args: argparse.Namespace,
    dataset_yaml: Path,
) -> List[str]:
    run_name = args.run_name or context.recommended_run_name
    command = [
        args.python_exe,
        str(TRAIN_SCRIPT),
        "train",
        "--project-config",
        str(context.config_path),
        "--dataset-yaml",
        str(dataset_yaml),
        "--name",
        run_name,
        "--imgsz",
        str(args.imgsz),
        "--epochs",
        str(args.epochs),
        "--batch",
        str(args.batch),
        "--patience",
        str(args.patience),
        "--workers",
        str(args.workers),
        "--device",
        str(args.device),
        "--seed",
        str(args.seed),
    ]
    if args.base_model:
        command.extend(["--base-model", str(args.base_model)])
    if args.from_scratch:
        command.append("--from-scratch")
    if args.init_weights:
        command.extend(["--init-weights", str(args.init_weights)])
    if args.allow_remote_model_download:
        command.append("--allow-remote-model-download")
    return command


def evaluate_command(
    *,
    context: PersonProjectContext,
    args: argparse.Namespace,
    dataset_yaml: Path,
    weight_path: Path,
) -> List[str]:
    run_name = args.run_name or context.recommended_run_name
    report_name = args.report_name or train_report_name_for(run_name)
    return [
        args.python_exe,
        str(TRAIN_SCRIPT),
        "evaluate",
        "--project-config",
        str(context.config_path),
        "--dataset-yaml",
        str(dataset_yaml),
        "--weights",
        str(weight_path),
        "--imgsz",
        str(args.imgsz),
        "--batch",
        str(args.batch),
        "--workers",
        str(args.workers),
        "--device",
        str(args.device),
        "--report-name",
        report_name,
    ]


def export_command(
    *,
    context: PersonProjectContext,
    args: argparse.Namespace,
    weight_path: Path,
) -> List[str]:
    command = [
        args.python_exe,
        str(TRAIN_SCRIPT),
        "export",
        "--project-config",
        str(context.config_path),
        "--weights",
        str(weight_path),
    ]
    if args.overwrite:
        command.append("--overwrite")
    return command


def alias_export(context: PersonProjectContext, *, overwrite: bool) -> None:
    raw_weight = context.artifacts_root / "export" / "workwear_detect_yolov8.pt"
    raw_metadata = context.artifacts_root / "export" / "workwear_detect_yolov8.metadata.json"
    if not raw_weight.exists():
        raise RuntimeError("导出后未找到原始权重: {0}".format(raw_weight))
    if context.export_alias_path.exists() and not overwrite:
        raise RuntimeError(
            "person 导出 alias 已存在，请显式传 `--overwrite`: {0}".format(context.export_alias_path)
        )
    context.export_alias_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(raw_weight, context.export_alias_path)
    if raw_metadata.exists():
        try:
            metadata_payload = json.loads(raw_metadata.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            metadata_payload = {"raw_metadata_path": str(raw_metadata)}
        metadata_payload["alias_export_target"] = str(context.export_alias_path)
        metadata_payload["alias_source_export_target"] = str(raw_weight)
        context.export_alias_metadata_path.write_text(
            json.dumps(metadata_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print("person 导出权重 : {0}".format(context.export_alias_path))


def ensure_prepared_dataset(context: PersonProjectContext, args: argparse.Namespace) -> Path:
    dataset_yaml = dataset_yaml_path_for(context, args.dataset_yaml)
    if dataset_yaml.exists():
        return dataset_yaml
    ensure_person_labels(context, overwrite=args.overwrite)
    run_command(prepare_command(context=context, args=args))
    if not dataset_yaml.exists():
        raise RuntimeError("prepare 完成后仍未找到 dataset.yaml: {0}".format(dataset_yaml))
    return dataset_yaml


def main() -> int:
    args = parse_args()
    context = load_person_project_context(Path(args.project_config))
    run_name = args.run_name or context.recommended_run_name

    if args.command == "prepare-labels":
        ensure_person_labels(context, overwrite=args.overwrite)
        return 0

    if args.command == "setup-roi-workdir":
        from setup_roi_workdir import setup_roi_workdir

        report = setup_roi_workdir(
            context,
            roi_work_root=roi_json_root_for(
                context,
                args.roi_json_root,
                command=args.command,
            ),
            frames_per_sequence=args.roi_frames_per_sequence,
            overwrite_frames=args.overwrite_roi_frames,
        )
        print("ROI 工作区 : {0}".format(report["roi_work_root"]))
        print("序列数量   : {0}".format(len(report["sequences"])))
        print("manifest   : {0}".format(report["manifest_path"]))
        return 0

    if args.command == "extract-roi-config":
        from labelme_roi_to_config import extract_roi_config

        output_path = roi_config_path_for(context, args.roi_config)
        result = extract_roi_config(
            context,
            roi_json_root=roi_json_root_for(
                context,
                args.roi_json_root,
                command=args.command,
            ),
            output_path=output_path,
            label_name=args.roi_label,
            overwrite=args.overwrite,
        )
        print("ROI 配置文件 : {0}".format(output_path))
        per_image_total = sum(len(images) for images in result.get("per_image", {}).values())
        print("序列级 ROI 数 : {0}".format(len(result["per_sequence"])))
        print("逐图 ROI 数   : {0}".format(per_image_total))
        return 0

    if args.command == "audit":
        ensure_person_labels(context, overwrite=args.overwrite)
        run_command(audit_command(context=context, args=args))
        return 0

    if args.command == "prepare":
        ensure_person_labels(context, overwrite=args.overwrite)
        run_command(prepare_command(context=context, args=args))
        return 0

    if args.command == "prepare-roi-aware":
        from prepare_roi_aware_person_dataset import prepare_roi_aware_dataset

        report = prepare_roi_aware_dataset(
            context,
            roi_config_path=roi_config_path_for(context, args.roi_config),
            output_root=roi_output_root_for(context, args.output_root),
            overwrite=args.overwrite,
            limit_per_sequence=args.limit_per_sequence,
        )
        print("ROI-aware 数据集 : {0}".format(report["dataset_root"]))
        print("dataset.yaml    : {0}".format(report["dataset_yaml"]))
        print(
            "输入图片={0}, 输出图片={1}, 保留框={2}, 丢弃框={3}, 空负样本={4}".format(
                report["input_image_count"],
                report["output_image_count"],
                report["kept_boxes"],
                report["dropped_boxes"],
                report["empty_roi_negative_images"],
            )
        )
        return 0

    if args.command == "train":
        dataset_yaml = ensure_prepared_dataset(context, args)
        run_command(train_command(context=context, args=args, dataset_yaml=dataset_yaml))
        return 0

    weight_path = best_weight_path_for(context, run_name, args.weights)

    if args.command == "evaluate":
        dataset_yaml = ensure_prepared_dataset(context, args)
        run_command(
            evaluate_command(
                context=context,
                args=args,
                dataset_yaml=dataset_yaml,
                weight_path=weight_path,
            )
        )
        return 0

    if args.command == "export":
        run_command(export_command(context=context, args=args, weight_path=weight_path))
        alias_export(context, overwrite=args.overwrite)
        return 0

    if args.command == "all":
        dataset_yaml = dataset_yaml_path_for(context, args.dataset_yaml)
        ensure_person_labels(context, overwrite=args.overwrite)
        run_command(audit_command(context=context, args=args))
        run_command(prepare_command(context=context, args=args))
        if not dataset_yaml.exists():
            raise RuntimeError("prepare 完成后仍未找到 dataset.yaml: {0}".format(dataset_yaml))
        run_command(train_command(context=context, args=args, dataset_yaml=dataset_yaml))
        run_command(
            evaluate_command(
                context=context,
                args=args,
                dataset_yaml=dataset_yaml,
                weight_path=best_weight_path_for(context, run_name, args.weights),
            )
        )
        run_command(
            export_command(
                context=context,
                args=args,
                weight_path=best_weight_path_for(context, run_name, args.weights),
            )
        )
        alias_export(context, overwrite=args.overwrite)
        return 0

    raise RuntimeError("未处理的命令: {0}".format(args.command))


if __name__ == "__main__":
    raise SystemExit(main())

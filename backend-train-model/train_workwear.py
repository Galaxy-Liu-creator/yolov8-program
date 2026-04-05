from __future__ import annotations

"""工服检测训练主入口脚本。

这个脚本负责把整个训练链路串起来，包括：

1. 原始数据审计；
2. 训练集准备；
3. 模型训练；
4. 原生 YOLO 验证；
5. 与 `inspection-flask` 联动做项目级复核；
6. 导出与部署最终权重。

可以把它理解为 `backend-train-model` 的总调度器：

- `dataset_tools.py` 负责数据工程逻辑；
- `config.py` 负责集中配置；
- 本文件负责命令行解析、流程编排和结果汇总。
"""

import argparse
import contextlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple, Union

SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

import config
from dataset_tools import AuditResult, DatasetToolError, PrepareResult, audit_dataset, prepare_dataset


def write_json(path: Path, data: Dict[str, object]) -> None:
    """把结构化数据写成 UTF-8 JSON 文件。"""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def timestamp_token() -> str:
    """生成适合做目录名/文件名的时间戳字符串。"""

    return datetime.now().strftime("%Y%m%d_%H%M%S")


def bootstrap_project_config(argv: Optional[List[str]] = None) -> Optional[Path]:
    """在正式构建完整 CLI 前，先解析并应用项目配置。"""

    bootstrap_parser = argparse.ArgumentParser(add_help=False)
    bootstrap_parser.add_argument(
        "--project-config",
        help="项目化 JSON 配置文件；默认尝试读取 backend-train-model/project_config.json。",
    )
    bootstrap_args, _ = bootstrap_parser.parse_known_args(argv)
    return config.apply_project_config(
        getattr(bootstrap_args, "project_config", None),
        allow_missing=getattr(bootstrap_args, "project_config", None) is None,
    )


def build_runtime_context(command_name: str) -> Dict[str, object]:
    """构建当前命令的运行时上下文，便于报告追溯。"""

    return {
        "command": command_name,
        "argv": list(sys.argv[1:]),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "config": config.get_runtime_config_snapshot(),
    }


def normalize_names_mapping(raw_value: object) -> Dict[int, str]:
    """把 dataset.yaml 中的 `names` 字段规范化为 `Dict[int, str]`。"""

    if isinstance(raw_value, dict):
        items = raw_value.items()
    elif isinstance(raw_value, list):
        items = enumerate(raw_value)
    else:
        return {}

    names: Dict[int, str] = {}
    for raw_key, raw_name in items:
        try:
            class_id = int(raw_key)
        except (TypeError, ValueError):
            continue
        names[class_id] = str(raw_name)
    return dict(sorted(names.items()))


def resolve_mode(mode: str, person_model_path: Optional[Path]) -> str:
    """根据用户输入和人物模型可用性，解析最终 prepare 模式。

    规则很简单：

    - 如果用户显式指定了 `fullframe` 或 `personcrop`，就直接用；
    - 如果是 `auto`，则“有 person 模型就走 personcrop，没有就走 fullframe”。
    """

    if mode != "auto":
        return mode
    return "personcrop" if person_model_path is not None else "fullframe"


def resolve_existing_path(
    raw_path: Optional[str],
    default_path: Optional[Path],
    description: str,
    required: bool,
) -> Optional[Path]:
    """解析一个可能来自命令行的路径参数，并在需要时校验存在性。

    这个函数统一处理三种情况：

    - 用户显式传了路径；
    - 用户没传，但有默认候选路径；
    - 路径是必填项，如果最终仍为空或不存在，则抛业务异常。
    """

    if raw_path:
        candidate = Path(raw_path)
    else:
        candidate = default_path

    if candidate is None:
        if required:
            raise DatasetToolError("{0} 未找到，请显式传入路径。".format(description))
        return None

    candidate = Path(candidate)
    if required and not candidate.exists():
        raise DatasetToolError("{0} 不存在: {1}".format(description, candidate))
    return candidate


def is_bare_model_reference(candidate_path: Path) -> bool:
    """判断模型输入是否只是一个裸文件名。"""

    return len(candidate_path.parts) == 1 and candidate_path.parent == Path(".")


def resolve_model_spec(
    raw_spec: Optional[str],
    default_spec: Union[str, Path],
    allow_remote_download: bool,
) -> Tuple[str, str]:
    """解析训练模型来源。

    允许的输入形式主要有两类：

    - `.pt`：已有权重，通常用于微调；
    - `.yaml/.yml`：模型结构定义，通常用于从零训练或改网络结构。

    另外也兼容 Ultralytics 内置模型名这种“路径未必真实存在于本地”的写法。
    """

    candidate = raw_spec or str(default_spec)
    if not candidate:
        raise DatasetToolError("训练模型结构未指定。")

    candidate_path = Path(candidate).expanduser()
    resolution_mode_prefix = "explicit" if raw_spec else "default"
    local_named_asset = (
        config.resolve_local_model_asset(candidate_path.name)
        if is_bare_model_reference(candidate_path)
        else None
    )
    if local_named_asset is not None:
        return str(local_named_asset.resolve()), "{0}_local_named_asset".format(resolution_mode_prefix)

    if candidate_path.suffix.lower() == ".pt":
        if candidate_path.exists():
            return str(candidate_path.resolve()), "{0}_local_path".format(resolution_mode_prefix)
        if is_bare_model_reference(candidate_path):
            expected_local_path = config.build_local_model_asset_path(candidate_path.name)
            if allow_remote_download:
                return candidate, "{0}_remote_model_name".format(resolution_mode_prefix)
            if raw_spec:
                raise DatasetToolError(
                    "未找到本地训练权重: {0}\n"
                    "当前默认不会隐式联网下载模型。\n"
                    "请把 `{1}` 放到 `{0}`，或显式传入其他本地 `--base-model` 路径；"
                    "如确认允许 Ultralytics 自动下载，请追加 `--allow-remote-model-download`。".format(
                        expected_local_path,
                        candidate_path.name,
                    )
                )
            raise DatasetToolError(
                "默认微调模型不存在: {0}\n"
                "当前脚本默认优先使用本地 `.pt` 权重，避免离线环境下隐式联网下载。\n"
                "请把 `{1}` 放到 `{0}`，或显式传入本地 `--base-model`；"
                "如确认允许 Ultralytics 自动下载，请追加 `--allow-remote-model-download`。".format(
                    expected_local_path,
                    candidate_path.name,
                )
            )
        if not raw_spec and candidate_path == config.resolve_default_base_model_path():
            raise DatasetToolError(
                "默认微调模型不存在: {0}\n"
                "当前脚本默认优先使用本地 `.pt` 权重，避免离线环境下隐式联网下载。\n"
                "请把 `{1}` 放到 `{0}`，或显式传入本地 `--base-model`；"
                "如确认允许 Ultralytics 自动下载，请追加 `--allow-remote-model-download`。".format(
                    candidate_path,
                    candidate_path.name,
                )
            )
        raise DatasetToolError("预训练权重不存在: {0}".format(candidate_path))

    if candidate_path.suffix.lower() in (".yaml", ".yml"):
        if candidate_path.exists():
            return str(candidate_path.resolve()), "{0}_local_path".format(resolution_mode_prefix)
        if is_bare_model_reference(candidate_path):
            expected_local_path = config.build_local_model_asset_path(candidate_path.name)
            if allow_remote_download:
                return candidate, "{0}_remote_model_name".format(resolution_mode_prefix)
            if raw_spec:
                raise DatasetToolError(
                    "未找到本地模型结构文件: {0}\n"
                    "当前默认不会隐式联网下载模型结构。\n"
                    "请把 `{1}` 放到 `{0}`，或显式传入其他本地 `--base-model` 路径；"
                    "如确认允许 Ultralytics 自动下载，请追加 `--allow-remote-model-download`。".format(
                        expected_local_path,
                        candidate_path.name,
                    )
                )
            raise DatasetToolError(
                "默认 scratch 结构文件不存在: {0}\n"
                "请确认仓库内的本地模型定义文件仍然存在，或显式传入本地 `--base-model`；"
                "如确认允许 Ultralytics 自动下载，请追加 `--allow-remote-model-download`。".format(
                    expected_local_path
                )
            )
        if not raw_spec and candidate_path == config.resolve_default_scratch_model_path():
            raise DatasetToolError(
                "默认 scratch 结构文件不存在: {0}\n"
                "请确认仓库内的本地模型定义文件仍然存在，或显式传入本地 `--base-model`；"
                "如确认允许 Ultralytics 自动下载，请追加 `--allow-remote-model-download`。".format(
                    candidate_path
                )
            )
        raise DatasetToolError("模型结构文件不存在: {0}".format(candidate_path))

    if candidate_path.exists():
        return str(candidate_path.resolve()), "{0}_local_path".format(resolution_mode_prefix)
    raise DatasetToolError("训练模型文件不存在: {0}".format(candidate_path))


def is_pretrained_model_spec(model_spec: str) -> bool:
    """判断模型描述是否是 `.pt` 权重文件。"""

    return Path(model_spec).suffix.lower() == ".pt"


def is_yaml_model_spec(model_spec: str) -> bool:
    """判断模型描述是否是 `.yaml/.yml` 结构文件。"""

    return Path(model_spec).suffix.lower() in (".yaml", ".yml")


def resolve_init_weights(
    raw_spec: Optional[str],
    allow_remote_download: bool,
) -> Tuple[Optional[str], Optional[str]]:
    """解析“结构文件 + 兼容初始化权重”中的初始化权重参数。"""

    if not raw_spec:
        return None, None

    candidate = str(raw_spec)
    candidate_path = Path(candidate).expanduser()
    if candidate_path.suffix.lower() != ".pt":
        raise DatasetToolError(
            "初始化权重必须是 `.pt` 文件，或显式允许下载的 Ultralytics 权重名: {0}".format(
                candidate
            )
        )

    local_named_asset = (
        config.resolve_local_model_asset(candidate_path.name)
        if is_bare_model_reference(candidate_path)
        else None
    )
    if local_named_asset is not None:
        return str(local_named_asset.resolve()), "explicit_local_named_asset"

    if candidate_path.exists():
        return str(candidate_path.resolve()), "explicit_local_path"
    if is_bare_model_reference(candidate_path):
        expected_local_path = config.build_local_model_asset_path(candidate_path.name)
        if allow_remote_download:
            return candidate, "explicit_remote_model_name"
        raise DatasetToolError(
            "未找到本地初始化权重: {0}\n"
            "当前默认不会隐式联网下载模型。\n"
            "请把 `{1}` 放到 `{0}`，或显式传入其他本地 `--init-weights` 路径；"
            "如确认允许 Ultralytics 自动下载，请追加 `--allow-remote-model-download`。".format(
                expected_local_path,
                candidate_path.name,
            )
        )

    raise DatasetToolError("初始化权重不存在: {0}".format(candidate_path))


def resolve_output_root(raw_path: Optional[str], default_path: Path) -> Path:
    """解析输出目录，并统一转成绝对路径。

    这样做是为了避免：

    - 相对路径在不同工作目录下产生歧义；
    - Ultralytics 实际保存目录与脚本推断目录不一致；
    - 训练产物落到项目之外的意外位置。
    """

    candidate = Path(raw_path) if raw_path else default_path
    return candidate.expanduser().resolve()


def load_dataset_config(dataset_yaml: Path) -> Dict[str, object]:
    """读取并做最小校验 `dataset.yaml`。"""

    try:
        import yaml
    except ImportError as exc:
        raise DatasetToolError("未安装 PyYAML，无法解析 dataset.yaml。") from exc

    try:
        payload = yaml.safe_load(dataset_yaml.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise DatasetToolError("读取 dataset.yaml 失败: {0}".format(dataset_yaml)) from exc

    if not isinstance(payload, dict):
        raise DatasetToolError("dataset.yaml 内容格式无效: {0}".format(dataset_yaml))
    return payload


def resolve_dataset_base_path(
    dataset_yaml: Path,
    config_payload: Optional[Dict[str, object]] = None,
) -> Path:
    """解析 `dataset.yaml` 中的基础数据根目录。"""

    dataset_yaml = dataset_yaml.expanduser().resolve()
    payload = config_payload or load_dataset_config(dataset_yaml)
    base_path_value = payload.get("path")
    if not base_path_value:
        return dataset_yaml.parent

    base_path = Path(str(base_path_value))
    if base_path.is_absolute():
        return base_path

    candidate_paths = [
        (dataset_yaml.parent / base_path).resolve(),
        base_path.expanduser().resolve(),
    ]
    return next(
        (candidate for candidate in candidate_paths if candidate.exists()),
        candidate_paths[0],
    )


def resolve_dataset_split_paths(dataset_yaml: Path) -> Dict[str, Optional[Path]]:
    """把 `dataset.yaml` 里的 train/val/test 条目解析成绝对路径。

    这里额外兼容两种常见情况：

    - `path` 写的是相对路径；
    - 历史数据集中 `path` 实际上已经是“相对当前工作目录”的路径。
    """

    dataset_yaml = dataset_yaml.expanduser().resolve()
    config_payload = load_dataset_config(dataset_yaml)
    base_path = resolve_dataset_base_path(dataset_yaml, config_payload)

    split_paths: Dict[str, Optional[Path]] = {}
    for split_name in ("train", "val", "test"):
        split_value = config_payload.get(split_name)
        if not split_value:
            split_paths[split_name] = None
            continue
        if isinstance(split_value, (list, tuple)):
            raise DatasetToolError(
                "当前脚本暂不支持列表形式的 {0} 数据源，请改为目录或 txt 列表文件。".format(split_name)
            )
        split_path = Path(str(split_value))
        if not split_path.is_absolute():
            split_path = (base_path / split_path).resolve()
        split_paths[split_name] = split_path
    return split_paths


def count_dataset_images(split_path: Optional[Path]) -> int:
    """统计一个 split 实际包含的图片数量。"""

    if split_path is None or not split_path.exists():
        return 0

    if split_path.is_file():
        # 如果是 txt 列表文件，则按非空行计数。
        lines = split_path.read_text(encoding="utf-8").splitlines()
        return sum(1 for line in lines if line.strip())

    # 如果是目录，就递归统计支持的图片文件。
    supported_suffixes = {suffix.lower() for suffix in config.IMAGE_EXTENSIONS}
    return sum(
        1
        for path in split_path.rglob("*")
        if path.is_file() and path.suffix.lower() in supported_suffixes
    )


def collect_dataset_split_counts(dataset_yaml: Path) -> Dict[str, int]:
    """统计 `dataset.yaml` 中 train/val/test 三个 split 的样本数。"""

    split_paths = resolve_dataset_split_paths(dataset_yaml)
    return {
        split_name: count_dataset_images(split_path)
        for split_name, split_path in split_paths.items()
    }


def collect_dataset_metadata(dataset_yaml: Path) -> Dict[str, object]:
    """汇总与训练/评估直接相关的数据集元信息。"""

    config_payload = load_dataset_config(dataset_yaml)
    class_names = normalize_names_mapping(config_payload.get("names", {}))
    prepare_report_path = dataset_yaml.parent / "prepare_report.json"
    prepare_report = load_report_dict(prepare_report_path) if prepare_report_path.exists() else None
    prepare_payload = prepare_report.get("prepare", {}) if isinstance(prepare_report, dict) else {}
    return {
        "dataset_yaml": str(dataset_yaml),
        "dataset_root": str(resolve_dataset_base_path(dataset_yaml, config_payload)),
        "class_names": class_names,
        "class_count": len(class_names),
        "split_image_counts": collect_dataset_split_counts(dataset_yaml),
        "prepare_report_path": str(prepare_report_path) if prepare_report_path.exists() else None,
        "prepare_mode": prepare_payload.get("mode"),
        "prepare_split_strategy": prepare_payload.get("split_strategy"),
    }


def run_audit(limit_per_sequence: Optional[int]) -> AuditResult:
    """执行原始数据审计，并可选地做每序列截断。"""

    audit_result = audit_dataset(
        image_roots=config.IMAGE_ROOTS,
        label_root=config.LABEL_ROOT,
        image_extensions=config.IMAGE_EXTENSIONS,
        ignored_label_filenames=config.IGNORED_LABEL_FILENAMES,
    )
    return audit_result.limited(limit_per_sequence)


def ensure_prepared_dataset(args) -> Tuple[AuditResult, PrepareResult]:
    """确保训练所需数据集已经准备好。

    工作流程是：

    1. 先审计原始数据；
    2. 解析最终模式、切分策略、输出目录；
    3. 调用 `prepare_dataset()` 真正落盘；
    4. 把审计结果和 prepare 结果一起写入报告文件。
    """

    audit_result = run_audit(limit_per_sequence=getattr(args, "limit_per_sequence", None))
    person_model_path = resolve_existing_path(
        raw_path=getattr(args, "person_model", None),
        default_path=config.resolve_default_person_model(),
        description="person 模型权重",
        required=False,
    )
    mode = resolve_mode(args.mode, person_model_path)
    split_strategy = getattr(args, "split_strategy", config.DEFAULT_SPLIT_STRATEGY)
    output_root = resolve_output_root(
        raw_path=getattr(args, "output_root", None),
        default_path=config.PREPARED_ROOT / mode / split_strategy,
    )
    prepare_result = prepare_dataset(
        audit_result=audit_result,
        output_root=output_root,
        mode=mode,
        overwrite=getattr(args, "overwrite", False),
        split_strategy=split_strategy,
        person_model_path=person_model_path,
        person_conf=getattr(args, "person_conf", config.DEFAULT_PERSON_CONF),
        person_imgsz=getattr(args, "person_imgsz", config.DEFAULT_PERSON_IMGSZ),
        assignment_min_ioa=getattr(args, "assignment_min_ioa", config.DEFAULT_ASSIGNMENT_MIN_IOA),
        monitored_person_labels=getattr(
            args,
            "monitored_person_labels",
            list(config.DEFAULT_MONITORED_PERSON_LABELS),
        ),
        include_empty_person_crops=getattr(
            args,
            "include_empty_person_crops",
            config.DEFAULT_INCLUDE_EMPTY_PERSON_CROPS,
        ),
        fallback_to_fullframe=getattr(
            args,
            "fallback_to_fullframe",
            config.DEFAULT_FALLBACK_TO_FULLFRAME,
        ),
    )

    # 把“原始审计 + prepare 输出”合并写入一个报告，方便后续追溯。
    prepare_payload = {
        "runtime": build_runtime_context("prepare"),
        "prepare_request": {
            "requested_mode": getattr(args, "mode", None),
            "resolved_mode": mode,
            "split_strategy": split_strategy,
            "output_root": str(output_root),
            "limit_per_sequence": getattr(args, "limit_per_sequence", None),
            "person_model": str(person_model_path) if person_model_path else None,
            "person_conf": getattr(args, "person_conf", config.DEFAULT_PERSON_CONF),
            "person_imgsz": getattr(args, "person_imgsz", config.DEFAULT_PERSON_IMGSZ),
            "assignment_min_ioa": getattr(
                args,
                "assignment_min_ioa",
                config.DEFAULT_ASSIGNMENT_MIN_IOA,
            ),
            "monitored_person_labels": list(
                getattr(
                    args,
                    "monitored_person_labels",
                    list(config.DEFAULT_MONITORED_PERSON_LABELS),
                )
            ),
            "include_empty_person_crops": getattr(
                args,
                "include_empty_person_crops",
                config.DEFAULT_INCLUDE_EMPTY_PERSON_CROPS,
            ),
            "fallback_to_fullframe": getattr(
                args,
                "fallback_to_fullframe",
                config.DEFAULT_FALLBACK_TO_FULLFRAME,
            ),
        },
        "audit": audit_result.to_report_dict(),
        "prepare": prepare_result.to_report_dict(),
        "resolved_person_model": str(person_model_path) if person_model_path else None,
        "project_fit": {
            "pipeline_target": "person -> crop -> clothes",
            "person_model_available": person_model_path is not None,
            "personcrop_active": mode == "personcrop",
            "class_names": {str(class_id): name for class_id, name in config.CLASS_NAMES.items()},
        },
    }
    write_json(prepare_result.report_path, prepare_payload)
    return audit_result, prepare_result


def print_audit_summary(audit_result: AuditResult) -> None:
    """把审计结果打印成简洁的人类可读摘要。"""

    print("=" * 60)
    print("数据审计完成")
    print("=" * 60)
    print("图片总数       : {0}".format(audit_result.total_images))
    print("标注总数       : {0}".format(audit_result.total_labels))
    print("标注框总数     : {0}".format(audit_result.total_boxes))
    print("忽略标注文件数 : {0}".format(len(audit_result.ignored_label_files)))
    for sequence_name, samples in audit_result.samples_by_sequence.items():
        print(
            "  - {0}: 图片 {1} 张, 标注框 {2}".format(
                sequence_name,
                len(samples),
                audit_result.boxes_by_sequence.get(sequence_name, 0),
            )
        )


def print_prepare_summary(prepare_result: PrepareResult) -> None:
    """把 prepare 结果打印成简洁的人类可读摘要。"""

    print("=" * 60)
    print("数据准备完成")
    print("=" * 60)
    print("模式               : {0}".format(prepare_result.mode))
    print("数据集目录         : {0}".format(prepare_result.dataset_root))
    print("dataset.yaml       : {0}".format(prepare_result.dataset_yaml))
    print("正样本图片数       : {0}".format(prepare_result.positive_crops))
    print("负样本图片数       : {0}".format(prepare_result.negative_crops))
    print("fullframe 回退数   : {0}".format(prepare_result.fallback_fullframes))
    print("未匹配 clothes 框数: {0}".format(prepare_result.unmatched_boxes))
    print("无 person 检出图片 : {0}".format(prepare_result.images_without_person_detection))
    for split_name in ("train", "val", "test"):
        print(
            "  - {0}: images={1}, labels={2}, boxes={3}".format(
                split_name,
                prepare_result.split_image_counts.get(split_name, 0),
                prepare_result.split_label_counts.get(split_name, 0),
                prepare_result.split_box_counts.get(split_name, 0),
            )
        )


def resolve_dataset_yaml(args) -> Path:
    """解析最终要使用的 `dataset.yaml`。

    优先级如下：

    1. 如果用户显式传了 `--dataset-yaml`，直接使用；
    2. 否则尝试按默认规则推导 prepare 输出目录中的 `dataset.yaml`；
    3. 如果推导不到，就即时触发一次 prepare。
    """

    if getattr(args, "dataset_yaml", None):
        dataset_yaml = Path(args.dataset_yaml)
        if not dataset_yaml.exists():
            raise DatasetToolError("dataset.yaml 不存在: {0}".format(dataset_yaml))
        return dataset_yaml

    person_model_path = resolve_existing_path(
        raw_path=getattr(args, "person_model", None),
        default_path=config.resolve_default_person_model(),
        description="person 模型权重",
        required=False,
    )
    mode = resolve_mode(args.mode, person_model_path)
    split_strategy = getattr(args, "split_strategy", config.DEFAULT_SPLIT_STRATEGY)
    default_yaml = resolve_output_root(
        raw_path=getattr(args, "output_root", None),
        default_path=config.PREPARED_ROOT / mode / split_strategy,
    ) / "dataset.yaml"
    if default_yaml.exists():
        return default_yaml

    _, prepare_result = ensure_prepared_dataset(args)
    return prepare_result.dataset_yaml


def resolve_run_name(explicit_name: Optional[str], prefix: str) -> str:
    """生成训练 run 名称；若未显式指定，则自动拼时间戳。"""

    return explicit_name or "{0}_{1}".format(prefix, timestamp_token())


def load_report_dict(report_path: Path) -> Optional[Dict[str, object]]:
    """尽量以容错方式读取训练报告。"""

    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def resolve_report_path_candidate(raw_value: object, report_path: Path) -> Optional[Path]:
    """把报告中的路径字段解析成绝对路径。"""

    if raw_value in (None, ""):
        return None

    candidate = Path(str(raw_value)).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (report_path.parent / candidate).resolve()


def resolve_best_weight_path_and_source(raw_path: Optional[str]) -> Tuple[Path, str, Optional[Path]]:
    """解析要使用的 `best.pt`，并同时返回解析来源。

    - 用户显式传 `--weights` 时，优先使用显式路径；
    - 否则优先回看最近一次训练报告中的 `best_weight`；
    - 再不行才回退到 `artifacts/runs/` 中找最新的 `weights/best.pt`。
    """

    if raw_path:
        best_weight = Path(raw_path).expanduser().resolve()
        if not best_weight.exists():
            raise DatasetToolError("权重文件不存在: {0}".format(best_weight))
        return best_weight, "explicit_weights_path", None

    report_candidates = sorted(
        config.REPORTS_ROOT.glob("*_train.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for report_path in report_candidates:
        payload = load_report_dict(report_path)
        if payload is None:
            continue

        best_weight = resolve_report_path_candidate(payload.get("best_weight"), report_path)
        if best_weight is not None and best_weight.exists():
            return best_weight, "latest_train_report", report_path.resolve()

        run_dir = resolve_report_path_candidate(payload.get("run_dir"), report_path)
        if run_dir is not None:
            best_weight = (run_dir / "weights" / "best.pt").resolve()
            if best_weight.exists():
                return best_weight, "latest_train_report_run_dir", report_path.resolve()

    candidates = sorted(
        config.RUNS_ROOT.rglob("weights/best.pt"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise DatasetToolError(
            "未找到任何训练产物 best.pt，请先执行 train，或显式传入 `--weights`。\n"
            "如果你曾使用自定义 `--project`，优先检查最近一次训练报告中的 `best_weight`。"
        )
    return candidates[0].resolve(), "runs_root_scan", None


def resolve_best_weight_path(raw_path: Optional[str]) -> Path:
    """仅返回 `best.pt` 路径本身，兼容旧调用方式。"""

    return resolve_best_weight_path_and_source(raw_path)[0]


def train_model(args) -> Dict[str, object]:
    """执行一次完整训练，并返回训练摘要。

    这里支持三种常见训练入口：

    - 直接用 `.pt` 微调；
    - 用 `.yaml` 从零训练；
    - 用 `.yaml` 起结构，再额外加载兼容 `.pt` 权重做初始化。
    """

    from ultralytics import YOLO

    dataset_yaml = resolve_dataset_yaml(args)
    dataset_metadata = collect_dataset_metadata(dataset_yaml)
    split_counts = dataset_metadata["split_image_counts"]
    if split_counts.get("train", 0) <= 0:
        raise DatasetToolError("训练集为空，无法启动训练: {0}".format(dataset_yaml))
    if split_counts.get("val", 0) <= 0:
        # Ultralytics 训练阶段默认会构建 val dataloader，因此这里提前拦截并给出中文说明。
        raise DatasetToolError(
            "验证集为空，当前训练命令无法运行。"
            "如使用 --limit-per-sequence 做 smoke test，请至少保证每个序列分到 2 张及以上图片。"
        )
    allow_remote_download = bool(
        getattr(
            args,
            "allow_remote_model_download",
            config.DEFAULT_ALLOW_REMOTE_MODEL_DOWNLOAD,
        )
    )
    from_scratch = bool(getattr(args, "from_scratch", False))
    init_weights, init_weights_source = resolve_init_weights(
        getattr(args, "init_weights", None),
        allow_remote_download=allow_remote_download,
    )
    if from_scratch and init_weights is not None:
        raise DatasetToolError("`--from-scratch` 不能与 `--init-weights` 同时使用。")
    model_spec, base_model_source = resolve_model_spec(
        raw_spec=getattr(args, "base_model", None),
        default_spec=(
            config.resolve_default_scratch_model_spec(
                allow_remote_download=allow_remote_download,
            )
            if from_scratch
            else config.resolve_default_base_model_spec(
                allow_remote_download=allow_remote_download,
            )
        ),
        allow_remote_download=allow_remote_download,
    )
    if from_scratch and is_pretrained_model_spec(model_spec):
        raise DatasetToolError(
            "`--from-scratch` 只能配合 `.yaml/.yml` 模型结构文件使用。"
            "如果你不传 `--base-model`，脚本会默认使用本地 `yolov8n.yaml`。"
        )
    if init_weights is not None and not is_yaml_model_spec(model_spec):
        raise DatasetToolError(
            "`--init-weights` 只能与 `.yaml/.yml` 结构文件一起使用。"
            "如果你想直接微调预训练 checkpoint，请改用 `--base-model xxx.pt`。"
        )
    use_pretrained = is_pretrained_model_spec(model_spec)
    single_cls = (
        dataset_metadata["class_count"] <= 1
        if dataset_metadata["class_count"]
        else len(config.CLASS_NAMES) <= 1
    )
    requested_run_name = resolve_run_name(getattr(args, "name", None), "workwear")
    run_project = resolve_output_root(getattr(args, "project", None), config.RUNS_ROOT)

    # 先根据模型描述创建 YOLO 对象；如果是 `.yaml`，这里只会构建结构。
    model = YOLO(model_spec)
    if init_weights is not None:
        # 仅当使用结构文件起模型时，才允许额外加载兼容初始化权重。
        model = model.load(init_weights)
    model.train(
        data=str(dataset_yaml),
        imgsz=args.imgsz,
        epochs=args.epochs,
        batch=args.batch,
        patience=args.patience,
        workers=args.workers,
        device=args.device,
        project=str(run_project),
        name=requested_run_name,
        pretrained=use_pretrained,
        seed=args.seed,
        deterministic=True,
        single_cls=single_cls,
        verbose=False,
    )

    # 优先读取 Ultralytics 真实 trainer 输出目录，避免相对路径造成推断错误。
    trainer = getattr(model, "trainer", None)
    trainer_save_dir = getattr(trainer, "save_dir", None)
    run_dir = (
        Path(trainer_save_dir).resolve()
        if trainer_save_dir
        else (run_project / requested_run_name).resolve()
    )
    actual_run_name = run_dir.name
    best_weight = run_dir / "weights" / "best.pt"
    last_weight = run_dir / "weights" / "last.pt"
    if not best_weight.exists():
        raise DatasetToolError("训练完成后未找到 best.pt: {0}".format(best_weight))

    summary = {
        "runtime": build_runtime_context("train"),
        "dataset_yaml": str(dataset_yaml),
        "dataset_metadata": dataset_metadata,
        "base_model": model_spec,
        "base_model_source": base_model_source,
        "allow_remote_model_download": allow_remote_download,
        "from_scratch": from_scratch,
        "pretrained": use_pretrained,
        "init_weights": init_weights,
        "init_weights_source": init_weights_source,
        "run_project": str(run_project),
        "requested_run_name": requested_run_name,
        "actual_run_name": actual_run_name,
        "run_name": actual_run_name,
        "run_dir": str(run_dir),
        "best_weight": str(best_weight),
        "last_weight": str(last_weight) if last_weight.exists() else None,
        "imgsz": args.imgsz,
        "epochs": args.epochs,
        "batch": args.batch,
        "patience": args.patience,
        "workers": args.workers,
        "device": args.device,
        "seed": args.seed,
        "single_cls": single_cls,
    }
    report_path = config.REPORTS_ROOT / "{0}_train.json".format(actual_run_name)
    summary["report_path"] = str(report_path)
    write_json(report_path, summary)
    return summary


def evaluate_model(args) -> Dict[str, object]:
    """执行模型评估。

    这里分两层：

    - 原生 YOLO `model.val()` 指标评估；
    - 可选的 `inspection-flask` 项目级双阶段链路复核。
    """

    from ultralytics import YOLO

    weight_path, weights_resolution_mode, weights_report_source = resolve_best_weight_path_and_source(
        getattr(args, "weights", None)
    )
    dataset_yaml = resolve_dataset_yaml(args)
    dataset_metadata = collect_dataset_metadata(dataset_yaml)
    split_counts = dataset_metadata["split_image_counts"]
    model = YOLO(str(weight_path))
    # 对于极小 smoke 数据集，`test` 可能为空；这里只评估非空 split。
    evaluation_splits = [
        split_name for split_name in ("val", "test") if split_counts.get(split_name, 0) > 0
    ]
    skipped_splits = [
        split_name for split_name in ("val", "test") if split_counts.get(split_name, 0) <= 0
    ]
    if not evaluation_splits:
        raise DatasetToolError(
            "dataset.yaml 中没有可评估的 val/test 样本，请先准备非空验证集或测试集。"
        )

    summary = {
        "runtime": build_runtime_context("evaluate"),
        "weights": str(weight_path),
        "weights_resolution_mode": weights_resolution_mode,
        "weights_report_source": (
            str(weights_report_source) if weights_report_source is not None else None
        ),
        "dataset_yaml": str(dataset_yaml),
        "dataset_metadata": dataset_metadata,
        "evaluated_splits": evaluation_splits,
        "skipped_splits": skipped_splits,
        "native_eval": {},
    }

    for split_name in evaluation_splits:
        # 对每个非空 split 分开跑一次 val，便于报告中明确区分 val/test。
        metrics = model.val(
            data=str(dataset_yaml),
            split=split_name,
            imgsz=args.imgsz,
            batch=args.batch,
            workers=args.workers,
            device=args.device,
            verbose=False,
            plots=False,
        )
        results_dict = dict(metrics.results_dict)
        summary["native_eval"][split_name] = {
            "results_dict": results_dict,
            "precision": float(metrics.box.mp),
            "recall": float(metrics.box.mr),
            "map50": float(metrics.box.map50),
            "map75": float(metrics.box.map75),
            "map50_95": float(metrics.box.map),
        }

    if getattr(args, "inspection_validate", False):
        # 原生 YOLO 指标之外，再用项目真实链路做一轮端到端复核。
        inspection_result = run_inspection_validation(
            weights_path=weight_path,
            person_model_path=resolve_existing_path(
                raw_path=getattr(args, "person_model", None),
                default_path=config.resolve_default_person_model(),
                description="person 模型权重",
                required=False,
            ),
            python_executable=resolve_existing_path(
                raw_path=getattr(args, "python_exe", None),
                default_path=config.resolve_default_python(),
                description="Python 解释器",
                required=True,
            ),
            keep_deployed=getattr(args, "keep_inspection_weights", False),
        )
        summary["inspection_validate"] = inspection_result

    report_name = "{0}_eval.json".format(weight_path.parent.parent.name)
    write_json(config.REPORTS_ROOT / report_name, summary)
    return summary


def export_model(args) -> Dict[str, object]:
    """导出最终权重，并可选部署到 `inspection-flask`。"""

    weight_path, weights_resolution_mode, weights_report_source = resolve_best_weight_path_and_source(
        getattr(args, "weights", None)
    )
    export_root = resolve_output_root(getattr(args, "export_root", None), config.EXPORT_ROOT)
    export_root.mkdir(parents=True, exist_ok=True)
    export_target = export_root / "workwear_detect_yolov8.pt"
    safe_copy(weight_path, export_target, overwrite=args.overwrite)

    summary = {
        "runtime": build_runtime_context("export"),
        "source_weight": str(weight_path),
        "weights_resolution_mode": weights_resolution_mode,
        "weights_report_source": (
            str(weights_report_source) if weights_report_source is not None else None
        ),
        "export_target": str(export_target),
        "deployed_target": None,
    }

    if getattr(args, "deploy", False):
        # `deploy` 的意思是把权重同步放到 `inspection-flask` 约定位置。
        config.INSPECTION_WEIGHTS_ROOT.mkdir(parents=True, exist_ok=True)
        safe_copy(weight_path, config.INSPECTION_WORKWEAR_TARGET, overwrite=args.overwrite)
        summary["deployed_target"] = str(config.INSPECTION_WORKWEAR_TARGET)

    metadata_path = export_root / "workwear_detect_yolov8.metadata.json"
    export_metadata = {
        "runtime": build_runtime_context("export_metadata"),
        "source_weight": str(weight_path),
        "weights_resolution_mode": weights_resolution_mode,
        "weights_report_source": (
            str(weights_report_source) if weights_report_source is not None else None
        ),
        "export_target": str(export_target),
        "deployed_target": summary["deployed_target"],
    }
    write_json(metadata_path, export_metadata)
    summary["metadata_path"] = str(metadata_path)

    report_name = "{0}_export.json".format(weight_path.parent.parent.name)
    write_json(config.REPORTS_ROOT / report_name, summary)
    return summary


def safe_copy(source: Path, target: Path, overwrite: bool) -> None:
    """安全复制文件，避免误覆盖。"""

    source = Path(source)
    target = Path(target)
    if source.resolve() == target.resolve():
        # 源和目标是同一个文件时，直接视为无需处理。
        return
    if target.exists() and not overwrite:
        raise DatasetToolError(
            "目标文件已存在: {0}。如需覆盖，请显式传入 --overwrite。".format(target)
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


@contextlib.contextmanager
def temporary_inspection_weights(
    workwear_weight: Path,
    person_weight: Optional[Path],
    keep_deployed: bool,
):
    """临时把权重放到 `inspection-flask` 约定位置。

    这个上下文管理器的目的，是在不永久污染 `inspection-flask/weights/` 的前提下，
    把待评估的 workwear/person 权重暂时复制进去，等复核结束后再恢复原状。
    """

    temp_dir = Path(tempfile.mkdtemp(prefix="inspection_weights_", dir=str(SCRIPT_ROOT)))
    restore_actions: List[Tuple[Path, Optional[Path], bool]] = []

    try:
        mappings = [
            (config.INSPECTION_WORKWEAR_TARGET, workwear_weight),
        ]
        if person_weight is not None:
            mappings.append((config.INSPECTION_PERSON_TARGET, person_weight))

        for target, source in mappings:
            target.parent.mkdir(parents=True, exist_ok=True)
            same_file = target.exists() and target.resolve() == source.resolve()
            backup_path = None
            existed = target.exists()
            if existed and not same_file:
                # 如果目标位已经有旧文件，先做备份，验证后可恢复。
                backup_path = temp_dir / target.name
                shutil.copy2(target, backup_path)
            if not same_file:
                shutil.copy2(source, target)
            restore_actions.append((target, backup_path, existed))
        yield
    finally:
        if not keep_deployed:
            for target, backup_path, existed in restore_actions:
                if backup_path is not None and backup_path.exists():
                    # 有备份则恢复备份。
                    shutil.copy2(backup_path, target)
                elif not existed and target.exists():
                    # 原来不存在的临时文件则直接删掉。
                    target.unlink()
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_inspection_validation(
    weights_path: Path,
    person_model_path: Optional[Path],
    python_executable: Path,
    keep_deployed: bool,
) -> Dict[str, object]:
    """调用 `inspection-flask` 的 `validate` 命令做项目级复核。

    与原生 YOLO 指标不同，这里更接近项目真实推理链路：

    - 逐个原始序列运行；
    - 复用 `inspection-flask` 的模型加载和业务逻辑；
    - 汇总 TP/FP/FN，再计算整体 precision/recall/F1。
    """

    if not config.INSPECTION_MAIN.exists():
        raise DatasetToolError("找不到 inspection-flask/main.py: {0}".format(config.INSPECTION_MAIN))
    if person_model_path is None and not config.INSPECTION_PERSON_TARGET.exists():
        raise DatasetToolError(
            "inspection-flask 复核需要 person 模型。请通过 --person-model 指定，"
            "或先准备 {0}。".format(config.INSPECTION_PERSON_TARGET)
        )

    per_sequence: Dict[str, object] = {}
    aggregate_tp = 0
    aggregate_fp = 0
    aggregate_fn = 0
    clothes_class_id = config.resolve_class_id_by_name("clothes")
    if clothes_class_id is None:
        raise DatasetToolError(
            "当前 backend-train-model 配置中未找到 `clothes` 类别，无法执行 inspection-flask clothes-only 复核。"
        )

    with temporary_inspection_weights(
        workwear_weight=weights_path,
        person_weight=person_model_path,
        keep_deployed=keep_deployed,
    ):
        for image_root in config.IMAGE_ROOTS:
            sequence_name = image_root.name
            # 这里明确使用当前项目数据口径：单类 clothes-only，类别 ID 为 0。
            command = [
                str(python_executable),
                str(config.INSPECTION_MAIN),
                "validate",
                str(image_root),
                "--labels",
                str(config.LABEL_ROOT),
                "--gt-mode",
                "clothes-only",
                "--clothes-cls",
                str(clothes_class_id),
            ]
            completed = subprocess.run(
                command,
                cwd=str(config.INSPECTION_ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
            )
            log_path = config.REPORTS_ROOT / "{0}_inspection_validate.log".format(sequence_name)
            log_path.write_text(completed.stdout + "\n" + completed.stderr, encoding="utf-8")
            if completed.returncode != 0:
                raise DatasetToolError(
                    "inspection-flask validate 执行失败 ({0})，日志见 {1}".format(
                        sequence_name,
                        log_path,
                    )
                )

            # 从 validate 标准输出中提取 TP/FP/FN/Precision/Recall/F1 等指标。
            metrics = parse_inspection_metrics(completed.stdout)
            if "tp" not in metrics or "fn" not in metrics:
                raise DatasetToolError(
                    "inspection-flask validate 输出缺少关键指标，日志见 {0}".format(log_path)
                )
            aggregate_tp += metrics.get("tp", 0)
            aggregate_fp += metrics.get("fp", 0)
            aggregate_fn += metrics.get("fn", 0)
            per_sequence[sequence_name] = {
                "log_path": str(log_path),
                **metrics,
            }

    precision, recall, f1_score = compute_prf(aggregate_tp, aggregate_fp, aggregate_fn)
    return {
        "per_sequence": per_sequence,
        "aggregate": {
            "tp": aggregate_tp,
            "fp": aggregate_fp,
            "fn": aggregate_fn,
            "precision": precision,
            "recall": recall,
            "f1": f1_score,
        },
    }


def parse_inspection_metrics(output_text: str) -> Dict[str, float]:
    """从 `inspection-flask validate` 的标准输出中提取关键指标。"""

    # 这里按固定正则抓最后一次出现的指标值，兼容输出中存在中间日志的情况。
    patterns = {
        "tp": r"\bTP\s*:\s*(\d+)",
        "fp": r"\bFP\s*:\s*(\d+)",
        "fn": r"\bFN\s*:\s*(\d+)",
        "precision": r"\bPrecision\s*:\s*([0-9.]+)",
        "recall": r"\bRecall\s*:\s*([0-9.]+)",
        "f1": r"\bF1\s*:\s*([0-9.]+)",
    }
    metrics: Dict[str, float] = {}
    for key, pattern in patterns.items():
        matches = re.findall(pattern, output_text)
        if not matches:
            continue
        value = matches[-1]
        metrics[key] = float(value) if key in ("precision", "recall", "f1") else int(value)
    return metrics


def compute_prf(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    """根据 TP/FP/FN 计算 precision、recall 和 F1。"""

    precision = tp / float(max(tp + fp, 1))
    recall = tp / float(max(tp + fn, 1))
    f1_score = 2 * precision * recall / max(precision + recall, 1e-9)
    return precision, recall, f1_score


def cmd_audit(args) -> int:
    """`audit` 子命令入口：只做数据审计。"""

    audit_result = run_audit(limit_per_sequence=None)
    print_audit_summary(audit_result)
    write_json(
        config.REPORTS_ROOT / "dataset_audit.json",
        {
            "runtime": build_runtime_context("audit"),
            "audit": audit_result.to_report_dict(),
        },
    )
    return 0


def cmd_prepare(args) -> int:
    """`prepare` 子命令入口：只做数据准备。"""

    audit_result, prepare_result = ensure_prepared_dataset(args)
    print_audit_summary(audit_result)
    print_prepare_summary(prepare_result)
    return 0


def cmd_train(args) -> int:
    """`train` 子命令入口：只做训练。"""

    summary = train_model(args)
    print("=" * 60)
    print("训练完成")
    print("=" * 60)
    print("run_dir   : {0}".format(summary["run_dir"]))
    print("best.pt   : {0}".format(summary["best_weight"]))
    print("dataset   : {0}".format(summary["dataset_yaml"]))
    return 0


def cmd_evaluate(args) -> int:
    """`evaluate` 子命令入口：只做评估。"""

    summary = evaluate_model(args)
    print("=" * 60)
    print("评估完成")
    print("=" * 60)
    for split_name, split_summary in summary["native_eval"].items():
        print(
            "{0}: recall={1:.4f}, precision={2:.4f}, map50={3:.4f}, map50-95={4:.4f}".format(
                split_name,
                split_summary["recall"],
                split_summary["precision"],
                split_summary["map50"],
                split_summary["map50_95"],
            )
        )
    if "inspection_validate" in summary:
        aggregate = summary["inspection_validate"]["aggregate"]
        print(
            "inspection-flask: recall={0:.4f}, precision={1:.4f}, f1={2:.4f}".format(
                aggregate["recall"],
                aggregate["precision"],
                aggregate["f1"],
            )
        )
    return 0


def cmd_export(args) -> int:
    """`export` 子命令入口：导出或部署权重。"""

    summary = export_model(args)
    print("=" * 60)
    print("导出完成")
    print("=" * 60)
    print("导出文件 : {0}".format(summary["export_target"]))
    if summary["deployed_target"]:
        print("部署文件 : {0}".format(summary["deployed_target"]))
    print("元数据   : {0}".format(summary["metadata_path"]))
    return 0


def cmd_all(args) -> int:
    """`all` 子命令入口：串行执行完整链路。

    这里会把一次 run 里最关键的四个阶段顺序串起来：

    - prepare
    - train
    - evaluate
    - export
    """

    audit_result, prepare_result = ensure_prepared_dataset(args)
    print_audit_summary(audit_result)
    print_prepare_summary(prepare_result)

    train_summary = train_model(args)
    print("训练 best.pt: {0}".format(train_summary["best_weight"]))

    # 后续阶段统一使用“本轮训练刚产出的 best.pt”，避免误拿到旧 run 权重。
    evaluate_args = argparse.Namespace(**vars(args))
    evaluate_args.weights = train_summary["best_weight"]
    evaluate_args.dataset_yaml = prepare_result.dataset_yaml
    evaluate_args.inspection_validate = not getattr(args, "skip_inspection_validate", False)
    evaluate_summary = evaluate_model(evaluate_args)

    export_args = argparse.Namespace(**vars(args))
    export_args.weights = train_summary["best_weight"]
    export_summary = export_model(export_args)

    # 把四个阶段的结果合并成一个总报告，便于一次回看全链路。
    final_summary = {
        "runtime": build_runtime_context("all"),
        "prepare": prepare_result.to_report_dict(),
        "train": train_summary,
        "evaluate": evaluate_summary,
        "export": export_summary,
    }
    summary_path = config.REPORTS_ROOT / "{0}_all.json".format(train_summary["run_name"])
    write_json(summary_path, final_summary)
    print("总报告   : {0}".format(summary_path))
    return 0


def add_global_args(parser: argparse.ArgumentParser) -> None:
    """挂载所有命令共用的全局参数。"""

    parser.add_argument(
        "--project-config",
        help="项目化 JSON 配置文件；默认尝试读取 backend-train-model/project_config.json。",
    )


def build_parser() -> argparse.ArgumentParser:
    """构建顶层命令行解析器及所有子命令。"""

    parser = argparse.ArgumentParser(
        description="YOLOv8 工服检测训练工具链（对齐当前 inspection-flask 两阶段链路）",
    )
    add_global_args(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit_parser = subparsers.add_parser("audit", help="只做数据审计，不写训练集")
    add_global_args(audit_parser)
    audit_parser.set_defaults(func=cmd_audit)

    prepare_parser = subparsers.add_parser("prepare", help="生成训练数据集")
    add_global_args(prepare_parser)
    add_prepare_args(prepare_parser)
    prepare_parser.add_argument(
        "--split-strategy",
        choices=["sequence_contiguous", "sequence_holdout"],
        default=config.DEFAULT_SPLIT_STRATEGY,
        help="prepare 阶段使用的数据切分策略。",
    )
    prepare_parser.set_defaults(func=cmd_prepare)

    train_parser = subparsers.add_parser("train", help="训练 clothes 单类检测器")
    add_global_args(train_parser)
    add_prepare_args(train_parser)
    add_train_args(train_parser)
    train_parser.add_argument(
        "--split-strategy",
        choices=["sequence_contiguous", "sequence_holdout"],
        default=config.DEFAULT_SPLIT_STRATEGY,
        help="当 train 需要自动 prepare 数据集时所使用的数据切分策略。",
    )
    train_parser.set_defaults(func=cmd_train)

    evaluate_parser = subparsers.add_parser("evaluate", help="评估已训练权重")
    add_global_args(evaluate_parser)
    add_prepare_args(evaluate_parser)
    add_eval_args(evaluate_parser)
    evaluate_parser.add_argument(
        "--split-strategy",
        choices=["sequence_contiguous", "sequence_holdout"],
        default=config.DEFAULT_SPLIT_STRATEGY,
        help="当 evaluate 需要自动 prepare 数据集时所使用的数据切分策略。",
    )
    evaluate_parser.set_defaults(func=cmd_evaluate)

    export_parser = subparsers.add_parser("export", help="导出或部署训练结果")
    add_global_args(export_parser)
    add_export_args(export_parser)
    export_parser.set_defaults(func=cmd_export)

    all_parser = subparsers.add_parser("all", help="串行执行 prepare -> train -> evaluate -> export")
    add_global_args(all_parser)
    add_prepare_args(all_parser)
    add_all_args(all_parser)
    all_parser.add_argument(
        "--skip-inspection-validate",
        action="store_true",
        help="跳过 inspection-flask 管线级复核。",
    )
    all_parser.add_argument(
        "--split-strategy",
        choices=["sequence_contiguous", "sequence_holdout"],
        default=config.DEFAULT_SPLIT_STRATEGY,
        help="all 流程中 prepare 阶段使用的数据切分策略。",
    )
    all_parser.set_defaults(func=cmd_all)

    return parser


def add_prepare_args(parser: argparse.ArgumentParser) -> None:
    """挂载多个子命令共享的数据准备相关参数。"""

    parser.add_argument(
        "--mode",
        choices=["auto", "personcrop", "fullframe"],
        default=config.DEFAULT_PREPARE_MODE,
        help="auto=有可用 person 模型时优先 personcrop，否则使用 fullframe。",
    )
    parser.add_argument("--output-root", help="prepare 输出目录。")
    parser.add_argument(
        "--limit-per-sequence",
        type=int,
        default=config.DEFAULT_LIMIT_PER_SEQUENCE,
        help="仅用于快速烟雾验证；对每个序列只取前 N 张图片。",
    )
    parser.add_argument(
        "--person-model",
        help="用于 personcrop 数据准备与 inspection-flask 复核的人体检测权重。",
    )
    parser.add_argument(
        "--person-conf",
        type=float,
        default=config.DEFAULT_PERSON_CONF,
        help="personcrop 模式的人体检测置信度阈值。",
    )
    parser.add_argument(
        "--person-imgsz",
        type=int,
        default=config.DEFAULT_PERSON_IMGSZ,
        help="personcrop 模式的人体检测输入尺寸。",
    )
    parser.add_argument(
        "--assignment-min-ioa",
        type=float,
        default=config.DEFAULT_ASSIGNMENT_MIN_IOA,
        help="将 clothes 框匹配到 person 框的最小 IOA。",
    )
    parser.add_argument(
        "--monitored-person-labels",
        nargs="+",
        default=list(config.DEFAULT_MONITORED_PERSON_LABELS),
        help="personcrop 模式中视为人员的标签名。",
    )
    parser.add_argument(
        "--include-empty-person-crops",
        action="store_true",
        help="为未匹配 clothes 的 person crop 生成空标注样本。",
    )
    parser.add_argument(
        "--no-fallback-to-fullframe",
        action="store_true",
        help="禁用 unmatched clothes 的 fullframe 回退。",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="允许覆盖已存在的输出目录或导出文件。",
    )


def add_train_args(parser: argparse.ArgumentParser) -> None:
    """挂载训练阶段专用参数。"""

    parser.add_argument("--dataset-yaml", help="显式指定 dataset.yaml。")
    parser.add_argument(
        "--base-model",
        help="训练模型结构或预训练权重，例如 yolov8n.yaml（从零训练）或自有 .pt。",
    )
    parser.add_argument("--project", help="训练 runs 输出目录。")
    parser.add_argument("--name", help="本次训练 run 名称。")
    parser.add_argument("--imgsz", type=int, default=config.DEFAULT_TRAIN_ARGS["imgsz"])
    parser.add_argument("--epochs", type=int, default=config.DEFAULT_TRAIN_ARGS["epochs"])
    parser.add_argument("--batch", type=int, default=config.DEFAULT_TRAIN_ARGS["batch"])
    parser.add_argument("--patience", type=int, default=config.DEFAULT_TRAIN_ARGS["patience"])
    parser.add_argument("--workers", type=int, default=config.DEFAULT_TRAIN_ARGS["workers"])
    parser.add_argument("--device", default=config.DEFAULT_TRAIN_ARGS["device"])
    parser.add_argument("--seed", type=int, default=config.DEFAULT_TRAIN_ARGS["seed"])
    parser.add_argument(
        "--from-scratch",
        action="store_true",
        help="从 `.yaml/.yml` 结构文件开始训练，而不是默认的本地 `.pt` 微调权重。",
    )
    parser.add_argument(
        "--init-weights",
        help="为 `.yaml/.yml` 结构文件额外加载兼容的 `.pt` 初始化权重，例如 `yolov8n.pt`。",
    )
    parser.add_argument(
        "--allow-remote-model-download",
        action="store_true",
        default=config.DEFAULT_ALLOW_REMOTE_MODEL_DOWNLOAD,
        help="显式允许 Ultralytics 在本地模型缺失时自动下载默认模型；默认关闭，优先保证离线可复现。",
    )


def add_eval_args(parser: argparse.ArgumentParser) -> None:
    """挂载评估阶段专用参数。"""

    parser.add_argument("--weights", help="待评估的 best.pt 路径。")
    parser.add_argument("--dataset-yaml", help="显式指定 dataset.yaml。")
    parser.add_argument("--imgsz", type=int, default=config.DEFAULT_TRAIN_ARGS["imgsz"])
    parser.add_argument("--batch", type=int, default=config.DEFAULT_TRAIN_ARGS["batch"])
    parser.add_argument("--workers", type=int, default=config.DEFAULT_TRAIN_ARGS["workers"])
    parser.add_argument("--device", default=config.DEFAULT_TRAIN_ARGS["device"])
    parser.add_argument(
        "--inspection-validate",
        action="store_true",
        help="额外调用 inspection-flask/main.py validate 做两阶段链路复核。",
    )
    parser.add_argument(
        "--keep-inspection-weights",
        action="store_true",
        help="执行 inspection 验证后保留临时复制进去的权重。",
    )
    parser.add_argument("--python-exe", help="运行 inspection-flask/main.py 的 Python 解释器。")


def add_export_args(parser: argparse.ArgumentParser) -> None:
    """挂载导出与部署相关参数。"""

    parser.add_argument("--weights", help="待导出的 best.pt 路径。")
    parser.add_argument("--export-root", help="导出目录。")
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="同时复制到 inspection-flask/weights/workwear_detect_yolov8.pt。",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="允许覆盖已存在的导出文件。",
    )


def add_all_args(parser: argparse.ArgumentParser) -> None:
    """挂载 `all` 命令需要的综合参数。"""

    parser.add_argument("--dataset-yaml", help="显式指定 dataset.yaml。")
    parser.add_argument(
        "--base-model",
        help="训练模型结构或预训练权重，例如 yolov8n.yaml（从零训练）或自有 .pt。",
    )
    parser.add_argument("--project", help="训练 runs 输出目录。")
    parser.add_argument("--name", help="本次训练 run 名称。")
    parser.add_argument("--export-root", help="导出目录。")
    parser.add_argument("--python-exe", help="运行 inspection-flask/main.py 的 Python 解释器。")
    parser.add_argument("--imgsz", type=int, default=config.DEFAULT_TRAIN_ARGS["imgsz"])
    parser.add_argument("--epochs", type=int, default=config.DEFAULT_TRAIN_ARGS["epochs"])
    parser.add_argument("--batch", type=int, default=config.DEFAULT_TRAIN_ARGS["batch"])
    parser.add_argument("--patience", type=int, default=config.DEFAULT_TRAIN_ARGS["patience"])
    parser.add_argument("--workers", type=int, default=config.DEFAULT_TRAIN_ARGS["workers"])
    parser.add_argument("--device", default=config.DEFAULT_TRAIN_ARGS["device"])
    parser.add_argument("--seed", type=int, default=config.DEFAULT_TRAIN_ARGS["seed"])
    parser.add_argument(
        "--from-scratch",
        action="store_true",
        help="从 `.yaml/.yml` 结构文件开始训练，而不是默认的本地 `.pt` 微调权重。",
    )
    parser.add_argument(
        "--init-weights",
        help="为 `.yaml/.yml` 结构文件额外加载兼容的 `.pt` 初始化权重，例如 `yolov8n.pt`。",
    )
    parser.add_argument(
        "--allow-remote-model-download",
        action="store_true",
        default=config.DEFAULT_ALLOW_REMOTE_MODEL_DOWNLOAD,
        help="显式允许 Ultralytics 在本地模型缺失时自动下载默认模型；默认关闭，优先保证离线可复现。",
    )
    parser.add_argument(
        "--keep-inspection-weights",
        action="store_true",
        help="执行 inspection 验证后保留临时复制进去的权重。",
    )
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="导出后同步复制到 inspection-flask/weights/workwear_detect_yolov8.pt。",
    )


def normalize_args(args) -> None:
    """把兼容性参数整理成运行时统一字段。

    当前主要是把：

    - `--no-fallback-to-fullframe`

    转成内部统一使用的：

    - `fallback_to_fullframe`
    """

    if hasattr(args, "fallback_to_fullframe"):
        return
    if hasattr(args, "no_fallback_to_fullframe"):
        args.fallback_to_fullframe = not args.no_fallback_to_fullframe


def main() -> int:
    """程序主入口：解析命令行并分发到对应子命令。"""

    try:
        bootstrap_project_config()
        parser = build_parser()
        args = parser.parse_args()
        normalize_args(args)
        return int(args.func(args))
    except (DatasetToolError, config.ConfigError) as exc:
        # 对业务异常统一输出简洁中文提示，避免给用户完整 traceback。
        print("[ERROR] {0}".format(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())

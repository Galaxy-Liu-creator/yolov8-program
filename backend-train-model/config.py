from __future__ import annotations

"""`backend-train-model` 训练工具链的集中配置模块。

这个文件的职责是把“与业务环境强相关、但不属于训练流程控制本身”的内容统一收口，例如：

- 原始数据集所在目录；
- 标注类别定义；
- 数据准备与训练的默认参数；
- 训练产物、导出文件、报告文件的默认保存位置；
- 与 `inspection-flask` 联动时所需的脚本和权重路径；
- 可由外部 `project_config.json` 覆盖的项目化配置。

这样做的好处是：

1. CLI 主脚本只负责流程编排，不需要硬编码大量路径；
2. 以后迁移数据目录、切换默认模型、调整默认训练参数时，只改这里或对应配置文件即可；
3. README、脚本行为、项目约定都能围绕这一个配置源保持一致。
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Union

# 当前配置文件所在目录，即 `backend-train-model/`。
SCRIPT_ROOT = Path(__file__).resolve().parent
# 项目根目录，即 `yolov8-program/`。
PROJECT_ROOT = SCRIPT_ROOT.parent
# 后端训练默认读取的项目化配置文件。
DEFAULT_PROJECT_CONFIG_PATH = SCRIPT_ROOT / "project_config.json"

# 训练工具自己的产物根目录。
ARTIFACTS_ROOT = SCRIPT_ROOT / "artifacts"
# 仓库内维护的模型结构定义目录。
MODEL_DEFS_ROOT = SCRIPT_ROOT / "model_defs"
# 仓库内约定的本地权重目录。
WEIGHTS_ROOT = SCRIPT_ROOT / "weights"
# 准备好的 YOLO 数据集目录。
PREPARED_ROOT = ARTIFACTS_ROOT / "prepared"
# 训练 run 目录。
RUNS_ROOT = ARTIFACTS_ROOT / "runs"
# JSON 报告和 inspection 校验日志目录。
REPORTS_ROOT = ARTIFACTS_ROOT / "reports"
# 最终导出权重目录。
EXPORT_ROOT = ARTIFACTS_ROOT / "export"

# `inspection-flask` 项目位置及其关键文件位置。
INSPECTION_ROOT = PROJECT_ROOT / "inspection-flask"
INSPECTION_MAIN = INSPECTION_ROOT / "main.py"
INSPECTION_WEIGHTS_ROOT = INSPECTION_ROOT / "weights"
INSPECTION_PERSON_TARGET = INSPECTION_WEIGHTS_ROOT / "person_detect_yolov8.pt"
INSPECTION_WORKWEAR_TARGET = INSPECTION_WEIGHTS_ROOT / "workwear_detect_yolov8.pt"

# 原始图片目录列表。
# 当前项目的数据由 3 个原始序列共同组成，因此这里写成列表而不是单一路径。
IMAGE_ROOTS = [
    Path(r"E:\University_competition\Innovation_Entrepreneurship\MyProgram\all_labels\clothes\group3_1\clo\D04_20260123074846"),
    Path(r"E:\University_competition\Innovation_Entrepreneurship\MyProgram\all_labels\clothes\group3_1\clo\D05_20260123074841"),
    Path(r"E:\University_competition\Innovation_Entrepreneurship\MyProgram\all_labels\clothes\group3_1\clo\D15_20260123074848"),
]

# 当前项目使用统一标签目录，标签文件通过“同名 stem”与图片配对。
LABEL_ROOT = Path(
    r"E:\University_competition\Innovation_Entrepreneurship\MyProgram\all_labels\clothes\group3_1\clo\label-clo"
)

# 支持识别为训练图片的扩展名。
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")

# 当前项目的类别定义。
# 数据集文档约定当前样例只有 1 个类别，类别 ID 为 0，名称为 clothes。
CLASS_NAMES = {0: "clothes"}

# 某些 YOLO 数据集目录里常见 `classes.txt`，它不是逐图标签，因此要在审计时忽略。
IGNORED_LABEL_FILENAMES = {"classes.txt"}

# 训练/验证/测试的默认划分比例。
SPLIT_RATIOS = {
    "train": 0.70,
    "val": 0.15,
    "test": 0.15,
}

# 当前数据只有少量原始序列，默认采用“每个序列内部连续切分”的方式，
# 这样可以让每个序列都参与训练，同时保留序列后段做验证和测试。
DEFAULT_SPLIT_STRATEGY = "sequence_contiguous"

# `prepare` 命令默认自动选择模式：
# - 有可用人体检测模型时，可切到 personcrop；
# - 否则使用 fullframe。
DEFAULT_PREPARE_MODE = "auto"

# personcrop 模式下，默认不保留“没有 clothes 标签”的空人物裁剪图。
DEFAULT_INCLUDE_EMPTY_PERSON_CROPS = False

# `None` 表示默认不过滤样本数量，使用全量数据。
DEFAULT_LIMIT_PER_SEQUENCE = None

# personcrop 模式下，哪些类别名称被视作“人”。
# 这里默认兼容常见 COCO 风格模型中的 `person` 标签。
DEFAULT_MONITORED_PERSON_LABELS = ("person",)

# personcrop 模式下的人体检测置信度阈值。
DEFAULT_PERSON_CONF = 0.20

# personcrop 模式下送入人体检测模型的输入尺寸。
DEFAULT_PERSON_IMGSZ = 640

# 将 clothes 框分配给 person 框时使用的最小 IOA 阈值。
DEFAULT_ASSIGNMENT_MIN_IOA = 0.35

# 当 clothes 框找不到匹配 person 时，是否允许回退为 fullframe 样本。
DEFAULT_FALLBACK_TO_FULLFRAME = True

# 默认模型资产命名约定：
# - `yolov8n.pt`：带预训练权重，适合直接微调；
# - `yolov8n.yaml`：只有结构定义，适合从零训练或改结构。
DEFAULT_BASE_MODEL_FILENAME = "yolov8n.pt"
DEFAULT_BASE_MODEL_REMOTE_SPEC = DEFAULT_BASE_MODEL_FILENAME
DEFAULT_SCRATCH_MODEL_FILENAME = "yolov8n.yaml"
DEFAULT_SCRATCH_MODEL_REMOTE_SPEC = DEFAULT_SCRATCH_MODEL_FILENAME

# 默认禁止隐式联网下载模型，优先保证离线训练行为可预期。
DEFAULT_ALLOW_REMOTE_MODEL_DOWNLOAD = False

# 默认的人体检测模型候选路径列表。
# 这里优先尝试训练仓库自己的 weights，其次复用 `inspection-flask` 当前约定路径。
DEFAULT_PERSON_MODEL_CANDIDATES = [
    WEIGHTS_ROOT / "person_detect_yolov8.pt",
    INSPECTION_PERSON_TARGET,
]

# 用于跨项目调用（例如调用 `inspection-flask/main.py`）的 Python 解释器候选。
# 优先使用仓库约定的 Conda 环境；如果找不到，再退回当前解释器。
DEFAULT_PYTHON_CANDIDATES = [
    Path(r"D:\Miniconda3_python\envs\yolo_code\python.exe"),
    Path(sys.executable),
]

# 默认训练参数。
# 这些值偏保守，目标是先保证在 CPU 环境下也能稳定工作。
DEFAULT_TRAIN_ARGS = {
    "imgsz": 640,
    "epochs": 180,
    "batch": 4,
    "patience": 40,
    "workers": 0,
    "device": "cpu",
    "seed": 42,
}

_CODE_DEFAULTS = {
    "IMAGE_ROOTS": list(IMAGE_ROOTS),
    "LABEL_ROOT": LABEL_ROOT,
    "IMAGE_EXTENSIONS": tuple(IMAGE_EXTENSIONS),
    "CLASS_NAMES": dict(CLASS_NAMES),
    "IGNORED_LABEL_FILENAMES": set(IGNORED_LABEL_FILENAMES),
    "SPLIT_RATIOS": dict(SPLIT_RATIOS),
    "DEFAULT_SPLIT_STRATEGY": DEFAULT_SPLIT_STRATEGY,
    "DEFAULT_PREPARE_MODE": DEFAULT_PREPARE_MODE,
    "DEFAULT_INCLUDE_EMPTY_PERSON_CROPS": DEFAULT_INCLUDE_EMPTY_PERSON_CROPS,
    "DEFAULT_LIMIT_PER_SEQUENCE": DEFAULT_LIMIT_PER_SEQUENCE,
    "DEFAULT_MONITORED_PERSON_LABELS": tuple(DEFAULT_MONITORED_PERSON_LABELS),
    "DEFAULT_PERSON_CONF": DEFAULT_PERSON_CONF,
    "DEFAULT_PERSON_IMGSZ": DEFAULT_PERSON_IMGSZ,
    "DEFAULT_ASSIGNMENT_MIN_IOA": DEFAULT_ASSIGNMENT_MIN_IOA,
    "DEFAULT_FALLBACK_TO_FULLFRAME": DEFAULT_FALLBACK_TO_FULLFRAME,
    "DEFAULT_ALLOW_REMOTE_MODEL_DOWNLOAD": DEFAULT_ALLOW_REMOTE_MODEL_DOWNLOAD,
    "DEFAULT_PERSON_MODEL_CANDIDATES": list(DEFAULT_PERSON_MODEL_CANDIDATES),
    "DEFAULT_PYTHON_CANDIDATES": list(DEFAULT_PYTHON_CANDIDATES),
    "DEFAULT_TRAIN_ARGS": dict(DEFAULT_TRAIN_ARGS),
}

ACTIVE_PROJECT_CONFIG_PATH: Optional[Path] = None


class ConfigError(RuntimeError):
    """训练配置解析或应用失败时抛出的业务异常。"""


def _clone_path_list(paths: Sequence[Path]) -> list[Path]:
    """复制一个路径列表，避免原地修改默认值快照。"""

    return [Path(path) for path in paths]


def reset_runtime_config() -> None:
    """把运行时配置重置回代码内置默认值。"""

    global IMAGE_ROOTS
    global LABEL_ROOT
    global IMAGE_EXTENSIONS
    global CLASS_NAMES
    global IGNORED_LABEL_FILENAMES
    global SPLIT_RATIOS
    global DEFAULT_SPLIT_STRATEGY
    global DEFAULT_PREPARE_MODE
    global DEFAULT_INCLUDE_EMPTY_PERSON_CROPS
    global DEFAULT_LIMIT_PER_SEQUENCE
    global DEFAULT_MONITORED_PERSON_LABELS
    global DEFAULT_PERSON_CONF
    global DEFAULT_PERSON_IMGSZ
    global DEFAULT_ASSIGNMENT_MIN_IOA
    global DEFAULT_FALLBACK_TO_FULLFRAME
    global DEFAULT_ALLOW_REMOTE_MODEL_DOWNLOAD
    global DEFAULT_PERSON_MODEL_CANDIDATES
    global DEFAULT_PYTHON_CANDIDATES
    global DEFAULT_TRAIN_ARGS
    global ACTIVE_PROJECT_CONFIG_PATH

    IMAGE_ROOTS = _clone_path_list(_CODE_DEFAULTS["IMAGE_ROOTS"])
    LABEL_ROOT = Path(_CODE_DEFAULTS["LABEL_ROOT"])
    IMAGE_EXTENSIONS = tuple(_CODE_DEFAULTS["IMAGE_EXTENSIONS"])
    CLASS_NAMES = dict(_CODE_DEFAULTS["CLASS_NAMES"])
    IGNORED_LABEL_FILENAMES = set(_CODE_DEFAULTS["IGNORED_LABEL_FILENAMES"])
    SPLIT_RATIOS = dict(_CODE_DEFAULTS["SPLIT_RATIOS"])
    DEFAULT_SPLIT_STRATEGY = str(_CODE_DEFAULTS["DEFAULT_SPLIT_STRATEGY"])
    DEFAULT_PREPARE_MODE = str(_CODE_DEFAULTS["DEFAULT_PREPARE_MODE"])
    DEFAULT_INCLUDE_EMPTY_PERSON_CROPS = bool(
        _CODE_DEFAULTS["DEFAULT_INCLUDE_EMPTY_PERSON_CROPS"]
    )
    DEFAULT_LIMIT_PER_SEQUENCE = _CODE_DEFAULTS["DEFAULT_LIMIT_PER_SEQUENCE"]
    DEFAULT_MONITORED_PERSON_LABELS = tuple(
        _CODE_DEFAULTS["DEFAULT_MONITORED_PERSON_LABELS"]
    )
    DEFAULT_PERSON_CONF = float(_CODE_DEFAULTS["DEFAULT_PERSON_CONF"])
    DEFAULT_PERSON_IMGSZ = int(_CODE_DEFAULTS["DEFAULT_PERSON_IMGSZ"])
    DEFAULT_ASSIGNMENT_MIN_IOA = float(_CODE_DEFAULTS["DEFAULT_ASSIGNMENT_MIN_IOA"])
    DEFAULT_FALLBACK_TO_FULLFRAME = bool(_CODE_DEFAULTS["DEFAULT_FALLBACK_TO_FULLFRAME"])
    DEFAULT_ALLOW_REMOTE_MODEL_DOWNLOAD = bool(
        _CODE_DEFAULTS["DEFAULT_ALLOW_REMOTE_MODEL_DOWNLOAD"]
    )
    DEFAULT_PERSON_MODEL_CANDIDATES = _clone_path_list(
        _CODE_DEFAULTS["DEFAULT_PERSON_MODEL_CANDIDATES"]
    )
    DEFAULT_PYTHON_CANDIDATES = _clone_path_list(_CODE_DEFAULTS["DEFAULT_PYTHON_CANDIDATES"])
    DEFAULT_TRAIN_ARGS = dict(_CODE_DEFAULTS["DEFAULT_TRAIN_ARGS"])
    ACTIVE_PROJECT_CONFIG_PATH = None


def _resolve_config_path(value: Union[str, Path], base_dir: Path) -> Path:
    """把配置文件里的路径值解析成绝对路径。"""

    candidate = Path(str(value)).expanduser()
    if candidate.is_absolute():
        return candidate
    return (base_dir / candidate).resolve()


def _coerce_path_list(values: Sequence[object], base_dir: Path, field_name: str) -> list[Path]:
    """把路径列表配置标准化为 `Path` 列表。"""

    paths: list[Path] = []
    for value in values:
        if value in (None, ""):
            continue
        paths.append(_resolve_config_path(str(value), base_dir))
    if not paths:
        raise ConfigError("{0} 不能为空。".format(field_name))
    return paths


def _coerce_string_list(values: Sequence[object], field_name: str) -> list[str]:
    """把配置中的字符串列表规范化。"""

    items: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        items.append(text)
    if not items:
        raise ConfigError("{0} 不能为空。".format(field_name))
    return items


def _coerce_class_names(raw_value: object) -> Dict[int, str]:
    """把类别配置规范化为 `Dict[int, str]`。"""

    if isinstance(raw_value, Mapping):
        items = raw_value.items()
    elif isinstance(raw_value, Sequence) and not isinstance(raw_value, (str, bytes)):
        items = enumerate(raw_value)
    else:
        raise ConfigError("data.class_names 必须是对象或字符串列表。")

    normalized: Dict[int, str] = {}
    for raw_key, raw_name in items:
        try:
            class_id = int(raw_key)
        except (TypeError, ValueError) as exc:
            raise ConfigError(
                "data.class_names 中存在无法解析的类别 ID: {0}".format(raw_key)
            ) from exc
        class_name = str(raw_name).strip()
        if not class_name:
            raise ConfigError("data.class_names 中存在空类别名。")
        normalized[class_id] = class_name

    if not normalized:
        raise ConfigError("data.class_names 不能为空。")
    return dict(sorted(normalized.items()))


def _coerce_split_ratios(raw_value: object) -> Dict[str, float]:
    """规范化 train/val/test 的切分比例配置。"""

    if not isinstance(raw_value, Mapping):
        raise ConfigError("data.split_ratios 必须是对象。")

    ratios = dict(SPLIT_RATIOS)
    for split_name in ("train", "val", "test"):
        if split_name not in raw_value:
            continue
        try:
            ratios[split_name] = float(raw_value[split_name])
        except (TypeError, ValueError) as exc:
            raise ConfigError(
                "data.split_ratios.{0} 不是合法数字。".format(split_name)
            ) from exc
    return ratios


def _coerce_train_args(raw_value: object) -> Dict[str, object]:
    """规范化默认训练参数配置。"""

    if not isinstance(raw_value, Mapping):
        raise ConfigError("training.default_train_args 必须是对象。")

    merged: Dict[str, object] = dict(DEFAULT_TRAIN_ARGS)
    integer_keys = {"imgsz", "epochs", "batch", "patience", "workers", "seed"}
    string_keys = {"device"}

    for key, value in raw_value.items():
        if key in integer_keys:
            try:
                merged[key] = int(value)
            except (TypeError, ValueError) as exc:
                raise ConfigError(
                    "training.default_train_args.{0} 不是合法整数。".format(key)
                ) from exc
            continue
        if key in string_keys:
            merged[key] = str(value)
            continue
        raise ConfigError(
            "training.default_train_args 中包含当前脚本未支持的键: {0}".format(key)
        )

    return merged


def _load_project_config_payload(config_path: Path) -> Dict[str, object]:
    """读取并校验项目配置 JSON。"""

    try:
        payload = json.loads(config_path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise ConfigError("读取项目配置失败: {0}".format(config_path)) from exc
    except json.JSONDecodeError as exc:
        raise ConfigError("项目配置 JSON 格式无效: {0}".format(config_path)) from exc

    if not isinstance(payload, dict):
        raise ConfigError("项目配置顶层必须是对象: {0}".format(config_path))
    return payload


def apply_project_config(
    config_path: Optional[Union[str, Path]] = None,
    *,
    allow_missing: bool = False,
) -> Optional[Path]:
    """应用项目化 JSON 配置。

    约定如下：

    - 未显式传入 `config_path` 时，默认尝试读取 `backend-train-model/project_config.json`；
    - 如果 `allow_missing=True` 且文件不存在，则静默保留代码默认值；
    - 如果显式传入路径但文件不存在，则抛出 `ConfigError`。
    """

    global IMAGE_ROOTS
    global LABEL_ROOT
    global IMAGE_EXTENSIONS
    global CLASS_NAMES
    global IGNORED_LABEL_FILENAMES
    global SPLIT_RATIOS
    global DEFAULT_SPLIT_STRATEGY
    global DEFAULT_PREPARE_MODE
    global DEFAULT_INCLUDE_EMPTY_PERSON_CROPS
    global DEFAULT_LIMIT_PER_SEQUENCE
    global DEFAULT_MONITORED_PERSON_LABELS
    global DEFAULT_PERSON_CONF
    global DEFAULT_PERSON_IMGSZ
    global DEFAULT_ASSIGNMENT_MIN_IOA
    global DEFAULT_FALLBACK_TO_FULLFRAME
    global DEFAULT_ALLOW_REMOTE_MODEL_DOWNLOAD
    global DEFAULT_PERSON_MODEL_CANDIDATES
    global DEFAULT_PYTHON_CANDIDATES
    global DEFAULT_TRAIN_ARGS
    global ACTIVE_PROJECT_CONFIG_PATH

    reset_runtime_config()

    resolved_path = (
        DEFAULT_PROJECT_CONFIG_PATH if config_path is None else Path(config_path).expanduser()
    )
    if not resolved_path.is_absolute():
        resolved_path = (SCRIPT_ROOT / resolved_path).resolve()

    if not resolved_path.exists():
        if allow_missing:
            return None
        raise ConfigError("项目配置文件不存在: {0}".format(resolved_path))

    payload = _load_project_config_payload(resolved_path)
    config_dir = resolved_path.parent

    data_section = payload.get("data")
    if data_section is not None:
        if not isinstance(data_section, Mapping):
            raise ConfigError("data 段必须是对象。")
        if "image_roots" in data_section:
            IMAGE_ROOTS = _coerce_path_list(
                data_section["image_roots"],
                config_dir,
                "data.image_roots",
            )
        if "label_root" in data_section:
            LABEL_ROOT = _resolve_config_path(data_section["label_root"], config_dir)
        if "image_extensions" in data_section:
            IMAGE_EXTENSIONS = tuple(
                item.lower()
                for item in _coerce_string_list(
                    data_section["image_extensions"],
                    "data.image_extensions",
                )
            )
        if "class_names" in data_section:
            CLASS_NAMES = _coerce_class_names(data_section["class_names"])
        if "ignored_label_filenames" in data_section:
            IGNORED_LABEL_FILENAMES = set(
                _coerce_string_list(
                    data_section["ignored_label_filenames"],
                    "data.ignored_label_filenames",
                )
            )
        if "split_ratios" in data_section:
            SPLIT_RATIOS = _coerce_split_ratios(data_section["split_ratios"])
        if "default_split_strategy" in data_section:
            DEFAULT_SPLIT_STRATEGY = str(data_section["default_split_strategy"]).strip()

    prepare_section = payload.get("prepare")
    if prepare_section is not None:
        if not isinstance(prepare_section, Mapping):
            raise ConfigError("prepare 段必须是对象。")
        if "default_mode" in prepare_section:
            DEFAULT_PREPARE_MODE = str(prepare_section["default_mode"]).strip()
        if "include_empty_person_crops" in prepare_section:
            DEFAULT_INCLUDE_EMPTY_PERSON_CROPS = bool(
                prepare_section["include_empty_person_crops"]
            )
        if "limit_per_sequence" in prepare_section:
            raw_limit = prepare_section["limit_per_sequence"]
            DEFAULT_LIMIT_PER_SEQUENCE = None if raw_limit is None else int(raw_limit)
        if "monitored_person_labels" in prepare_section:
            DEFAULT_MONITORED_PERSON_LABELS = tuple(
                _coerce_string_list(
                    prepare_section["monitored_person_labels"],
                    "prepare.monitored_person_labels",
                )
            )
        if "person_conf" in prepare_section:
            DEFAULT_PERSON_CONF = float(prepare_section["person_conf"])
        if "person_imgsz" in prepare_section:
            DEFAULT_PERSON_IMGSZ = int(prepare_section["person_imgsz"])
        if "assignment_min_ioa" in prepare_section:
            DEFAULT_ASSIGNMENT_MIN_IOA = float(prepare_section["assignment_min_ioa"])
        if "fallback_to_fullframe" in prepare_section:
            DEFAULT_FALLBACK_TO_FULLFRAME = bool(prepare_section["fallback_to_fullframe"])

    models_section = payload.get("models")
    if models_section is not None:
        if not isinstance(models_section, Mapping):
            raise ConfigError("models 段必须是对象。")
        if "allow_remote_model_download" in models_section:
            DEFAULT_ALLOW_REMOTE_MODEL_DOWNLOAD = bool(
                models_section["allow_remote_model_download"]
            )
        if "person_model_candidates" in models_section:
            DEFAULT_PERSON_MODEL_CANDIDATES = _coerce_path_list(
                models_section["person_model_candidates"],
                config_dir,
                "models.person_model_candidates",
            )
        if "python_candidates" in models_section:
            DEFAULT_PYTHON_CANDIDATES = _coerce_path_list(
                models_section["python_candidates"],
                config_dir,
                "models.python_candidates",
            )

    training_section = payload.get("training")
    if training_section is not None:
        if not isinstance(training_section, Mapping):
            raise ConfigError("training 段必须是对象。")
        if "default_train_args" in training_section:
            DEFAULT_TRAIN_ARGS = _coerce_train_args(training_section["default_train_args"])

    ACTIVE_PROJECT_CONFIG_PATH = resolved_path
    return ACTIVE_PROJECT_CONFIG_PATH


def get_runtime_config_snapshot() -> Dict[str, object]:
    """把当前运行时配置序列化成 JSON 友好的字典。"""

    return {
        "project_config_path": (
            str(ACTIVE_PROJECT_CONFIG_PATH) if ACTIVE_PROJECT_CONFIG_PATH is not None else None
        ),
        "image_roots": [str(path) for path in IMAGE_ROOTS],
        "label_root": str(LABEL_ROOT),
        "image_extensions": list(IMAGE_EXTENSIONS),
        "class_names": {str(class_id): name for class_id, name in CLASS_NAMES.items()},
        "ignored_label_filenames": sorted(IGNORED_LABEL_FILENAMES),
        "split_ratios": dict(SPLIT_RATIOS),
        "default_split_strategy": DEFAULT_SPLIT_STRATEGY,
        "default_prepare_mode": DEFAULT_PREPARE_MODE,
        "default_include_empty_person_crops": DEFAULT_INCLUDE_EMPTY_PERSON_CROPS,
        "default_limit_per_sequence": DEFAULT_LIMIT_PER_SEQUENCE,
        "default_monitored_person_labels": list(DEFAULT_MONITORED_PERSON_LABELS),
        "default_person_conf": DEFAULT_PERSON_CONF,
        "default_person_imgsz": DEFAULT_PERSON_IMGSZ,
        "default_assignment_min_ioa": DEFAULT_ASSIGNMENT_MIN_IOA,
        "default_fallback_to_fullframe": DEFAULT_FALLBACK_TO_FULLFRAME,
        "default_allow_remote_model_download": DEFAULT_ALLOW_REMOTE_MODEL_DOWNLOAD,
        "default_person_model_candidates": [
            str(path) for path in DEFAULT_PERSON_MODEL_CANDIDATES
        ],
        "default_python_candidates": [str(path) for path in DEFAULT_PYTHON_CANDIDATES],
        "default_train_args": dict(DEFAULT_TRAIN_ARGS),
        "artifacts_root": str(ARTIFACTS_ROOT),
        "prepared_root": str(PREPARED_ROOT),
        "runs_root": str(RUNS_ROOT),
        "reports_root": str(REPORTS_ROOT),
        "export_root": str(EXPORT_ROOT),
    }


def resolve_class_id_by_name(class_name: str) -> Optional[int]:
    """按类别名查找对应的类别 ID。"""

    target = class_name.strip().lower()
    for class_id, current_name in CLASS_NAMES.items():
        if str(current_name).strip().lower() == target:
            return int(class_id)
    return None


def resolve_first_existing_path(candidates: Iterable[Path]) -> Optional[Path]:
    """从候选路径列表中返回第一个真实存在的路径。"""

    for candidate in candidates:
        if candidate is None:
            continue
        candidate_path = Path(candidate)
        if candidate_path.exists():
            return candidate_path
    return None


def build_local_model_asset_path(filename: Union[str, Path]) -> Optional[Path]:
    """按仓库约定推导模型资产文件名对应的本地路径。"""

    candidate_name = Path(filename).name
    suffix = Path(candidate_name).suffix.lower()
    if suffix == ".pt":
        return WEIGHTS_ROOT / candidate_name
    if suffix in (".yaml", ".yml"):
        return MODEL_DEFS_ROOT / candidate_name
    return None


def resolve_local_model_asset(filename: Union[str, Path]) -> Optional[Path]:
    """按仓库约定解析模型资产文件名对应的本地路径。"""

    candidate_path = build_local_model_asset_path(filename)
    if candidate_path is None:
        return None
    return resolve_first_existing_path([candidate_path])


def resolve_default_base_model_path() -> Path:
    """返回默认本地微调权重应当存放的位置。"""

    return WEIGHTS_ROOT / DEFAULT_BASE_MODEL_FILENAME


def resolve_default_scratch_model_path() -> Path:
    """返回默认本地结构定义文件的位置。"""

    return MODEL_DEFS_ROOT / DEFAULT_SCRATCH_MODEL_FILENAME


def resolve_default_base_model_spec(
    allow_remote_download: bool = DEFAULT_ALLOW_REMOTE_MODEL_DOWNLOAD,
) -> Union[str, Path]:
    """返回默认的微调起点模型。"""

    local_path = resolve_default_base_model_path()
    if local_path.exists():
        return local_path
    if allow_remote_download:
        return DEFAULT_BASE_MODEL_REMOTE_SPEC
    return local_path


def resolve_default_scratch_model_spec(
    allow_remote_download: bool = DEFAULT_ALLOW_REMOTE_MODEL_DOWNLOAD,
) -> Union[str, Path]:
    """返回默认的从零训练模型结构定义。"""

    local_path = resolve_default_scratch_model_path()
    if local_path.exists():
        return local_path
    if allow_remote_download:
        return DEFAULT_SCRATCH_MODEL_REMOTE_SPEC
    return local_path


def resolve_default_person_model() -> Optional[Path]:
    """返回默认可用的人体检测模型路径。"""

    return resolve_first_existing_path(DEFAULT_PERSON_MODEL_CANDIDATES)


def resolve_default_python() -> Optional[Path]:
    """返回跨项目调用时优先使用的 Python 解释器。"""

    return resolve_first_existing_path(DEFAULT_PYTHON_CANDIDATES)

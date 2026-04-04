from __future__ import annotations

"""`backend-train-model` 训练工具链的集中配置模块。

这个文件的职责是把“与业务环境强相关、但不属于训练流程控制本身”的内容统一收口，
例如：

- 原始数据集所在目录；
- 标签类别定义；
- 数据准备与训练的默认参数；
- 训练产物、导出文件、报告文件的默认保存位置；
- 与 `inspection-flask` 联动时所需的脚本和权重路径。

这样做的好处是：

1. CLI 主脚本只负责流程编排，不需要硬编码大量路径；
2. 以后迁移数据目录、切换默认模型、调整默认训练参数时，只改这里即可；
3. README、脚本行为、项目约定都能围绕这一个配置源保持一致。
"""

import sys
from pathlib import Path
from typing import Iterable, Optional, Union

# 当前配置文件所在目录，即 `backend-train-model/`。
SCRIPT_ROOT = Path(__file__).resolve().parent
# 项目根目录，即 `yolov8-program/`。
PROJECT_ROOT = SCRIPT_ROOT.parent

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
# 数据集文档约定只有 1 个类别，类别 ID 为 0，名称为 clothes。
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
# 目前留空，表示不假定仓库内一定已经提供人物检测权重。
DEFAULT_PERSON_MODEL_CANDIDATES = []

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


def resolve_first_existing_path(candidates: Iterable[Path]) -> Optional[Path]:
    """从候选路径列表中返回第一个真实存在的路径。

    这个函数常用于“给默认路径做兜底”：

    - 如果候选列表里某个路径存在，就直接返回它；
    - 如果都不存在，就返回 `None`，交由上层决定是否报错或继续回退。
    """

    for candidate in candidates:
        if candidate is None:
            continue
        candidate_path = Path(candidate)
        if candidate_path.exists():
            return candidate_path
    return None


def build_local_model_asset_path(filename: Union[str, Path]) -> Optional[Path]:
    """按仓库约定推导模型资产文件名应对应的本地路径。"""

    candidate_name = Path(filename).name
    suffix = Path(candidate_name).suffix.lower()
    if suffix == ".pt":
        return WEIGHTS_ROOT / candidate_name
    if suffix in (".yaml", ".yml"):
        return MODEL_DEFS_ROOT / candidate_name
    return None


def resolve_local_model_asset(filename: Union[str, Path]) -> Optional[Path]:
    """按仓库约定解析模型资产文件名对应的本地路径。

    典型场景：

    - `yolov8n.pt` -> `backend-train-model/weights/yolov8n.pt`
    - `yolov8n.yaml` -> `backend-train-model/model_defs/yolov8n.yaml`
    """

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
    """返回默认的微调起点模型。

    正常项目训练时，通常优先使用带预训练权重的 `yolov8n.pt`，
    因为它对当前这种样本量不算大的检测任务更稳定。
    """

    local_path = resolve_default_base_model_path()
    if local_path.exists():
        return local_path
    if allow_remote_download:
        return DEFAULT_BASE_MODEL_REMOTE_SPEC
    return local_path


def resolve_default_scratch_model_spec(
    allow_remote_download: bool = DEFAULT_ALLOW_REMOTE_MODEL_DOWNLOAD,
) -> Union[str, Path]:
    """返回默认的从零训练模型结构定义。

    当用户显式传入 `--from-scratch` 时，训练脚本会优先使用这里的配置，
    也就是 `yolov8n.yaml`。
    """

    local_path = resolve_default_scratch_model_path()
    if local_path.exists():
        return local_path
    if allow_remote_download:
        return DEFAULT_SCRATCH_MODEL_REMOTE_SPEC
    return local_path


def resolve_default_person_model() -> Optional[Path]:
    """返回默认可用的人体检测模型路径。

    如果未来你希望 personcrop 模式“开箱即用”，可以把默认候选路径填进
    `DEFAULT_PERSON_MODEL_CANDIDATES`；这里会自动返回第一个存在的文件。
    """

    return resolve_first_existing_path(DEFAULT_PERSON_MODEL_CANDIDATES)


def resolve_default_python() -> Optional[Path]:
    """返回跨项目调用时优先使用的 Python 解释器。

    典型场景是：

    - 在 `evaluate --inspection-validate` 中调用 `inspection-flask/main.py`；
    - 希望优先使用 `yolo_code` 环境，而不是随机落到系统 Python。
    """

    return resolve_first_existing_path(DEFAULT_PYTHON_CANDIDATES)

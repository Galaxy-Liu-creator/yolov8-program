from __future__ import annotations

import logging
from pathlib import Path

import settings

try:
    import torch
    _torch_available = True
except ImportError:
    _torch_available = False

try:
    from ultralytics import YOLO
    _ultralytics_available = True
except ImportError:
    _ultralytics_available = False

LOGGER = logging.getLogger(__name__)


def select_runtime_device() -> str:
    """返回可用的推理设备标识（'cuda:0' 或 'cpu'）。"""
    if _torch_available and torch.cuda.is_available():
        return "cuda:0"
    return "cpu"


def _validate_weight_path(weight_path, detector_name: str) -> Path:
    path = Path(weight_path)
    if not path.exists():
        raise FileNotFoundError(f"{detector_name} 权重文件不存在: {path}")
    return path


def _parse_boxes(result) -> list[dict]:
    """将 ultralytics Result 中的 boxes 统一解析为标准字典列表。

    兼容 YOLOv8 / YOLO11 不同版本下 box.cls / box.conf 的张量形态差异。
    """
    detections: list[dict] = []
    for box in result.boxes:
        cls_raw = box.cls[0]
        cls_id = int(cls_raw.item()) if hasattr(cls_raw, "item") else int(cls_raw)
        conf_raw = box.conf[0]
        conf = float(conf_raw.item()) if hasattr(conf_raw, "item") else float(conf_raw)
        label = result.names[cls_id] if isinstance(result.names, (list, dict)) else str(cls_id)
        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
        detections.append({
            "bbox": [x1, y1, x2, y2],
            "confidence": conf,
            "label": label,
        })
    return detections


def _build_predict_kwargs(conf: float, device: str, classes=None) -> dict:
    """构建传给 model() 的统一预测参数。"""
    kwargs = {
        "conf": conf,
        "imgsz": getattr(settings, "IMGSZ", 640),
        "device": device,
        "verbose": False,
        "iou": getattr(settings, "PREDICT_IOU", 0.45),
        "max_det": getattr(settings, "PREDICT_MAX_DET", 100),
    }
    if classes is not None:
        kwargs["classes"] = classes
    return kwargs


class PersonDetector:
    """YOLOv8 人员检测器。

    输入整帧图像，输出人员候选框列表，统一格式为：
        {"bbox": [x1, y1, x2, y2], "confidence": float, "label": "person"}
    """

    def __init__(self, weight_path, device: str = "cpu"):
        if not _ultralytics_available:
            raise ImportError("ultralytics 未安装，请执行 pip install ultralytics")
        path = _validate_weight_path(weight_path, "人员检测模型")
        self.model = YOLO(str(path))
        self.device = device
        LOGGER.info(
            "PersonDetector 已加载: weight=%s device=%s family=%s",
            path.name, device, getattr(settings, "YOLO_FAMILY", "yolov8"),
        )

    def get_class_names(self) -> dict | list:
        """返回模型的类别名映射（用于校验标签口径）。"""
        return self.model.names

    def infer(self, frame, conf_threshold: float = 0.55) -> list[dict]:
        """对整帧图像执行人员检测，返回置信度高于阈值的监管对象列表。

        过滤标签由 settings.MONITORED_PERSON_LABELS 驱动，不硬绑 "person"。
        """
        monitored = set(getattr(settings, "MONITORED_PERSON_LABELS", ["person"]))
        classes = getattr(settings, "PERSON_CLASSES", None)
        predict_kwargs = _build_predict_kwargs(conf_threshold, self.device, classes)
        results = self.model(frame, **predict_kwargs)
        detections: list[dict] = []
        for result in results:
            for det in _parse_boxes(result):
                if det["label"] in monitored:
                    detections.append(det)
        return detections


class WorkwearDetector:
    """YOLOv8 工服检测器。

    输入单个人员框区域图像（裁剪图），输出工服相关类别列表，统一格式为：
        {"bbox": [x1, y1, x2, y2], "confidence": float, "label": "clothes"}

    bbox 坐标为相对裁剪图的局部坐标。
    """

    def __init__(self, weight_path, device: str = "cpu"):
        if not _ultralytics_available:
            raise ImportError("ultralytics 未安装，请执行 pip install ultralytics")
        path = _validate_weight_path(weight_path, "工服检测模型")
        self.model = YOLO(str(path))
        self.device = device
        LOGGER.info(
            "WorkwearDetector 已加载: weight=%s device=%s family=%s",
            path.name, device, getattr(settings, "YOLO_FAMILY", "yolov8"),
        )

    def get_class_names(self) -> dict | list:
        """返回模型的类别名映射（用于校验标签口径）。"""
        return self.model.names

    def infer(self, person_crop, conf_threshold: float = 0.45) -> list[dict]:
        """对人员裁剪图执行工服检测，返回检测到的工服目标列表。"""
        if person_crop is None or person_crop.size == 0:
            return []
        classes = getattr(settings, "WORKWEAR_CLASSES", None)
        predict_kwargs = _build_predict_kwargs(conf_threshold, self.device, classes)
        results = self.model(person_crop, **predict_kwargs)
        detections: list[dict] = []
        for result in results:
            detections.extend(_parse_boxes(result))
        return detections


def load_person_detector(device: str = "cpu") -> PersonDetector:
    """根据 settings.PERSON_WEIGHT 加载人员检测器。"""
    return PersonDetector(settings.PERSON_WEIGHT, device)


def load_workwear_detector(device: str = "cpu") -> WorkwearDetector:
    """根据 settings.WORKWEAR_WEIGHT 加载工服检测器。"""
    return WorkwearDetector(settings.WORKWEAR_WEIGHT, device)


def load_detection_models(device: str | None = None) -> tuple[PersonDetector, WorkwearDetector]:
    """统一加载 YOLOv8 人员模型与工服模型。"""
    runtime_device = device or select_runtime_device()
    person_model = load_person_detector(runtime_device)
    workwear_model = load_workwear_detector(runtime_device)
    LOGGER.info(
        "检测模型加载完成 family=%s person_classes=%s workwear_classes=%s",
        getattr(settings, "YOLO_FAMILY", "yolov8"),
        person_model.get_class_names(),
        workwear_model.get_class_names(),
    )
    return person_model, workwear_model

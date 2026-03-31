"""工服合规判定与人员裁剪的唯一共享策略模块。

所有在线检测线程、离线验证脚本、违规规则判定均应通过本模块调用，
确保裁剪策略和合规口径的全局一致性。
"""

from __future__ import annotations

import numpy as np

import settings


def crop_person(frame: np.ndarray, bbox: list) -> np.ndarray | None:
    """直接裁剪人员框区域，坐标越界时做边界修正。"""
    x1, y1, x2, y2 = [int(v) for v in bbox]
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(frame.shape[1], x2)
    y2 = min(frame.shape[0], y2)
    if x2 <= x1 or y2 <= y1:
        return None
    return frame[y1:y2, x1:x2]


def make_white_bg_crop(frame: np.ndarray, bbox: list) -> np.ndarray:
    """将帧中人员框外区域替换为白色后裁剪。

    兼容在白底格式数据上训练的工服检测模型，
    当 settings.USE_WHITE_BG_MASK=True 时使用。
    """
    h, w = frame.shape[:2]
    x1 = max(0, int(bbox[0]))
    y1 = max(0, int(bbox[1]))
    x2 = min(w, int(bbox[2]))
    y2 = min(h, int(bbox[3]))
    white = np.ones((h, w, 3), dtype=np.uint8) * 255
    white[y1:y2, x1:x2] = frame[y1:y2, x1:x2]
    return white[y1:y2, x1:x2]


def get_person_crop(
    frame: np.ndarray,
    bbox: list,
    use_white_bg: bool | None = None,
) -> np.ndarray | None:
    """根据裁剪策略获取人员区域图像。

    Args:
        frame: 原始帧。
        bbox: 人员框坐标 [x1, y1, x2, y2]。
        use_white_bg: 是否使用白底裁剪。None 时从 settings.USE_WHITE_BG_MASK 读取。
    """
    if use_white_bg is None:
        use_white_bg = getattr(settings, "USE_WHITE_BG_MASK", False)
    if use_white_bg:
        return make_white_bg_crop(frame, bbox)
    return crop_person(frame, bbox)


def extract_detected_labels(workwear_items: list[dict]) -> set[str]:
    """从工服检测结果中提取所有检测到的标签名。"""
    return {
        str(item.get("label", "")).strip()
        for item in workwear_items
        if isinstance(item, dict) and str(item.get("label", "")).strip()
    }


def evaluate_workwear_compliance(
    workwear_items: list[dict],
    workwear_labels: set[str] | list[str] | None = None,
    mode: str | None = None,
    required_labels: set[str] | list[str] | None = None,
) -> bool:
    """判定工服是否合规（全局唯一口径）。

    Args:
        workwear_items: 工服检测器的输出列表。
        workwear_labels: 合规标签集合。None 时从 settings.WORKWEAR_LABELS 读取。
        mode: "any" 或 "all"。None 时从 settings.WORKWEAR_COMPLIANCE_MODE 读取。
        required_labels: mode="all" 时必须命中的标签。None 时从 settings 读取。

    Returns:
        True 表示合规（检测到工服），False 表示不合规。
    """
    if not isinstance(workwear_items, list):
        return False

    if workwear_labels is None:
        workwear_labels = set(getattr(settings, "WORKWEAR_LABELS", []))
    else:
        workwear_labels = set(workwear_labels)

    if mode is None:
        mode = getattr(settings, "WORKWEAR_COMPLIANCE_MODE", "any")

    detected = extract_detected_labels(workwear_items)

    if mode == "all":
        if required_labels is None:
            required_labels = set(getattr(settings, "WORKWEAR_REQUIRED_LABELS", []))
        else:
            required_labels = set(required_labels)
        if required_labels:
            return required_labels.issubset(detected)
        return bool(detected & workwear_labels)

    return bool(detected & workwear_labels)

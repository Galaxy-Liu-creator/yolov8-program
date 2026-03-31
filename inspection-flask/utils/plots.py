"""证据图绘制工具函数。

提供 plot_one_box 和 plot_txt_PIL 两个函数，
供 violation_module/base.py 保存证据图时调用。
"""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

_FONT_CACHE: dict[int, ImageFont.FreeTypeFont | ImageFont.ImageFont] = {}

_FALLBACK_FONT_PATHS = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]


def _get_font(size: int = 28) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if size in _FONT_CACHE:
        return _FONT_CACHE[size]

    font: ImageFont.FreeTypeFont | ImageFont.ImageFont | None = None
    for path in _FALLBACK_FONT_PATHS:
        try:
            font = ImageFont.truetype(path, size)
            break
        except (OSError, IOError):
            continue

    if font is None:
        font = ImageFont.load_default()

    _FONT_CACHE[size] = font
    return font


def plot_one_box(
    box,
    img: np.ndarray,
    color: list | tuple | None = None,
    label: str | None = None,
    line_thickness: int = 2,
) -> None:
    """在 img 上绘制矩形框和标签（原地修改）。"""
    if color is None:
        color = [0, 165, 255]
    c1 = (int(box[0]), int(box[1]))
    c2 = (int(box[2]), int(box[3]))
    tl = line_thickness or round(0.002 * max(img.shape[:2])) + 1
    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)

    if label:
        tf = max(tl - 1, 1)
        font_scale = tl / 3.0
        (tw, th), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, tf,
        )
        c2_label = (c1[0] + tw + 4, c1[1] - th - baseline - 4)
        cv2.rectangle(img, c1, c2_label, color, -1, cv2.LINE_AA)
        cv2.putText(
            img, label,
            (c1[0] + 2, c1[1] - baseline - 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale, [255, 255, 255], thickness=tf, lineType=cv2.LINE_AA,
        )


def plot_txt_PIL(
    box: list | tuple,
    img: np.ndarray,
    label: str,
    color: list | tuple | None = None,
) -> np.ndarray:
    """使用 PIL 在图像左上角绘制中文文本标签，返回标注后的图像。"""
    if color is None:
        color = [0, 165, 255]
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)

    font = _get_font(28)
    x, y = int(box[0]), int(box[1])
    text_bbox = draw.textbbox((x, y), label, font=font)
    tw = text_bbox[2] - text_bbox[0]
    th = text_bbox[3] - text_bbox[1]
    padding = 6
    draw.rectangle(
        [x - padding, y - padding, x + tw + padding, y + th + padding],
        fill=tuple(color),
    )
    draw.text((x, y), label, fill=(255, 255, 255), font=font)

    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

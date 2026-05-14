from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont


SCRIPT_PATH = Path(__file__).resolve()
PERSON_ROOT = SCRIPT_PATH.parents[1]
BY_SOURCE_ROOT = (
    PERSON_ROOT
    / "train-result"
    / "review"
    / "person_fullframe_with_new_labels_hard_sample_review"
    / "by_source"
)

FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/msyh.ttc"),
    Path("C:/Windows/Fonts/msyhbd.ttc"),
    Path("C:/Windows/Fonts/simhei.ttf"),
    Path("C:/Windows/Fonts/simsun.ttc"),
]

TITLE = "框颜色说明（GT=人工标注，Pred=模型检测）"
LEGEND_ITEMS: Sequence[Tuple[Tuple[int, int, int], str]] = (
    ((0, 128, 255), "蓝色框：Pred 预测框（与 GT 成功匹配）"),
    ((0, 200, 0), "绿色框：GT 真值框（已匹配 / TP 对应 GT）"),
    ((255, 0, 0), "红色框：GT 真值框（人工标注有，但模型漏检 / FN）"),
    ((255, 165, 0), "橙色框：Pred 预测框（模型多检 / FP，若出现）"),
)


def load_font(size: int) -> ImageFont.ImageFont:
    for font_path in FONT_CANDIDATES:
        if not font_path.exists():
            continue
        try:
            return ImageFont.truetype(str(font_path), size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def choose_fonts(draw: ImageDraw.ImageDraw, image_width: int) -> Tuple[ImageFont.ImageFont, ImageFont.ImageFont]:
    for title_size, body_size in ((28, 24), (24, 20), (22, 18), (20, 16)):
        title_font = load_font(title_size)
        body_font = load_font(body_size)
        title_width, _ = text_size(draw, TITLE, title_font)
        max_line_width = max(text_size(draw, line, body_font)[0] for _, line in LEGEND_ITEMS)
        content_width = max(title_width, 34 + max_line_width)
        if content_width + 40 <= image_width - 16:
            return title_font, body_font
    return load_font(18), load_font(16)


def overlay_paths(root: Path) -> List[Path]:
    return sorted(root.rglob("overlays/*.jpg"))


def draw_legend(image: Image.Image) -> Image.Image:
    canvas = image.convert("RGB")
    draw = ImageDraw.Draw(canvas)
    title_font, body_font = choose_fonts(draw, canvas.width)

    margin_x = 14
    margin_y = 34
    padding = 12
    row_gap = 10
    swatch_size = 22
    swatch_gap = 12

    title_width, title_height = text_size(draw, TITLE, title_font)
    line_sizes = [text_size(draw, line, body_font) for _, line in LEGEND_ITEMS]
    max_line_width = max(width for width, _ in line_sizes)
    line_height = max(height for _, height in line_sizes)

    legend_width = max(title_width, swatch_size + swatch_gap + max_line_width) + padding * 2
    legend_height = (
        padding * 2
        + title_height
        + 10
        + len(LEGEND_ITEMS) * line_height
        + (len(LEGEND_ITEMS) - 1) * row_gap
    )

    x1 = margin_x
    y1 = margin_y
    x2 = min(canvas.width - margin_x, x1 + legend_width)
    y2 = min(canvas.height - margin_x, y1 + legend_height)

    shadow_offset = 4
    draw.rectangle((x1 + shadow_offset, y1 + shadow_offset, x2 + shadow_offset, y2 + shadow_offset), fill=(0, 0, 0))
    draw.rectangle((x1, y1, x2, y2), fill=(255, 255, 255), outline=(0, 0, 0), width=2)

    current_y = y1 + padding
    draw.text((x1 + padding, current_y), TITLE, fill=(0, 0, 0), font=title_font)
    current_y += title_height + 10

    for color, line in LEGEND_ITEMS:
        swatch_y = current_y + max(0, (line_height - swatch_size) // 2)
        draw.rectangle(
            (x1 + padding, swatch_y, x1 + padding + swatch_size, swatch_y + swatch_size),
            outline=color,
            width=5,
        )
        draw.text(
            (x1 + padding + swatch_size + swatch_gap, current_y),
            line,
            fill=(0, 0, 0),
            font=body_font,
        )
        current_y += line_height + row_gap
    return canvas


def annotate_image(path: Path) -> None:
    with Image.open(path) as image:
        annotated = draw_legend(image)
        annotated.save(path, quality=95)


def main() -> None:
    paths = overlay_paths(BY_SOURCE_ROOT)
    if not paths:
        print(f"[WARN] 未找到 overlay 图片: {BY_SOURCE_ROOT}")
        return
    for path in paths:
        annotate_image(path)
    print(f"[OK] 已为 {len(paths)} 张 overlay 图片添加中文图例。")
    print(f"[ROOT] {BY_SOURCE_ROOT}")


if __name__ == "__main__":
    main()

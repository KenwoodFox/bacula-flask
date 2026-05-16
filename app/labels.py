"""
LTO-style tape labels (colored char boxes + Code128), built from stacked Pillow helpers.

Internal routes: routes.py — not linked from the public UI.
"""

from __future__ import annotations

import re
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

# Printable sheet
LABEL_WIDTH = 720
LABEL_HEIGHT = 220
SHEET_GUTTER = 16

# LTO Digit colors (from quantum)
DIGIT_COLORS: dict[str, str] = {
    "0": "#E2231A",
    "1": "#FFD800",
    "2": "#00A651",
    "3": "#00AEEF",
    "4": "#9D9D9C",
    "5": "#F7941D",
    "6": "#92278F",
    "7": "#EC008C",
    "8": "#2E3192",
    "9": "#795548",
}

LETTER_BG = "#FFFFFF"
CHAR_INK = "#000000"
BOX_LINE = "#000000"


def _load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    paths = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    )
    if not bold:
        paths = (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
        ) + paths
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def char_box_background(character: str) -> str:
    """Background color for one character cell."""
    if character.isdigit():
        return DIGIT_COLORS.get(character, LETTER_BG)
    return LETTER_BG


def segment_volume_label(volumename: str) -> list[tuple[str, bool]]:
    """
    Split a volume name into (text, is_wide) segments for the top row.
    Trailing LTO generation codes (e.g. L3, L8) use one wide box.
    """
    clean = "".join(c for c in volumename.strip().upper() if c.isalnum())
    if not clean:
        return []

    match = re.match(r"^(.+?)(L\d+)$", clean)
    if match and len(match.group(1)) >= 1:
        base, suffix = match.group(1), match.group(2)
        return [(char, False) for char in base] + [(suffix, True)]

    return [(char, False) for char in clean]


def _row_unit_count(segments: list[tuple[str, bool]]) -> int:
    return sum(2 if wide else 1 for _, wide in segments)


def render_char_box(
    text: str,
    width: int,
    height: int,
    *,
    background: str | None = None,
) -> Image.Image:
    """One colored character cell (or wide cell for suffixes like L3)."""
    bg = background if background is not None else char_box_background(text[0])
    box = Image.new("RGB", (max(1, width), max(1, height)), bg)
    draw = ImageDraw.Draw(box)

    draw.rectangle((0, 0, width - 1, height - 1), outline=BOX_LINE, width=1)

    display = text if len(text) > 1 else text[0]
    font_size = max(10, int(height * 0.62) if len(display) == 1 else int(height * 0.48))
    font = _load_font(font_size)

    bbox = draw.textbbox((0, 0), display, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((width - tw) // 2 - bbox[0], (height - th) // 2 - bbox[1]),
        display,
        fill=CHAR_INK,
        font=font,
    )
    return box


def render_char_row(
    segments: list[tuple[str, bool]],
    total_width: int,
    row_height: int,
) -> Image.Image:
    """Row of adjacent colored boxes (no gaps), scaled to total_width."""
    if not segments:
        return Image.new("RGB", (total_width, row_height), LETTER_BG)

    units = _row_unit_count(segments)
    unit_w = max(1, total_width // units)
    row = Image.new("RGB", (total_width, row_height), LETTER_BG)
    x = 0

    for text, wide in segments:
        cell_w = min(unit_w * (2 if wide else 1), total_width - x)
        if cell_w <= 0:
            break
        if wide:
            cell = render_char_box(text, cell_w, row_height, background=LETTER_BG)
        else:
            cell = render_char_box(text[0], cell_w, row_height)
        row.paste(cell, (x, 0))
        x += cell_w

    if x < total_width:
        draw = ImageDraw.Draw(row)
        draw.rectangle((x, 0, total_width - 1, row_height - 1), fill=LETTER_BG, outline=BOX_LINE)

    return row


def trim_barcode_bars(image: Image.Image) -> Image.Image:
    """Crop to bar modules only — drops caption text under a white gap."""
    img = image.convert("RGB")
    w, h = img.size
    pixels = img.load()

    def row_is_dark(y: int) -> bool:
        dark = sum(1 for x in range(w) if pixels[x, y] != (255, 255, 255))
        return dark > max(2, w // 50)

    runs: list[tuple[int, int]] = []
    start: int | None = None
    for y in range(h):
        if row_is_dark(y):
            if start is None:
                start = y
        elif start is not None:
            runs.append((start, y - 1))
            start = None
    if start is not None:
        runs.append((start, h - 1))

    if not runs:
        return image

    # Main barcode is the tallest dark band; caption text is a smaller band below a gap.
    ymin, ymax = max(runs, key=lambda span: span[1] - span[0])
    return img.crop((0, ymin, w, ymax + 1))


def render_barcode_bitmap(text: str) -> Image.Image:
    """Plain Code128 bars only — no human-readable text under the bars."""
    from barcode import Code128
    from barcode.writer import ImageWriter

    writer = ImageWriter()
    writer.write_text = False
    writer.set_options(
        {
            "module_width": 0.35,
            "module_height": 14.0,
            "quiet_zone": 1.0,
            "font_size": 0,
            "text_distance": 0,
            "write_text": False,
        }
    )
    code = Code128(text, writer=writer)
    buffer = BytesIO()
    code.write(buffer, options={"write_text": False})
    buffer.seek(0)
    return trim_barcode_bars(Image.open(buffer).convert("RGB"))


def render_barcode_strip(text: str, width: int, height: int) -> Image.Image:
    """Barcode scaled to exact width × height."""
    barcode = render_barcode_bitmap(text)
    return barcode.resize((max(1, width), max(1, height)), Image.Resampling.LANCZOS)


def build_lto_tape_label(
    volumename: str,
    width: int,
    height: int,
    *,
    row_ratio: float = 0.34,
    corner_radius: int = 6,
) -> Image.Image:
    """
    Full LTO-style label: colored char row + barcode, composed from parts.
  """
    code = "".join(c for c in volumename.strip().upper() if c.isalnum())
    if not code:
        raise ValueError("empty volume name")

    row_h = max(12, int(height * row_ratio))
    bar_h = height - row_h

    segments = segment_volume_label(volumename)
    char_row = render_char_row(segments, width, row_h)
    barcode = render_barcode_strip(code, width, bar_h)

    label = Image.new("RGB", (width, height), LETTER_BG)
    label.paste(char_row, (0, 0))
    label.paste(barcode, (0, row_h))

    if corner_radius > 0:
        label = _round_label_corners(label, corner_radius)

    return label


def _round_label_corners(image: Image.Image, radius: int) -> Image.Image:
    """Clip label to rounded rect (LTO sticker shape)."""
    w, h = image.size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    out = Image.new("RGB", (w, h), LETTER_BG)
    out.paste(image, (0, 0), mask=mask)
    draw = ImageDraw.Draw(out)
    draw.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, outline=BOX_LINE, width=1)
    return out


def build_tape_label(volumename: str, pool_name: str | None = None) -> Image.Image:
    """Large printable label (pool name is omitted to match library sticker layout)."""
    _ = pool_name
    return build_lto_tape_label(volumename, LABEL_WIDTH, LABEL_HEIGHT, corner_radius=10)


def build_tape_label_sheet(
    entries: list[tuple[str, str | None]],
    columns: int = 3,
) -> Image.Image:
    """Grid of printable labels."""
    if not entries:
        return Image.new("RGB", (LABEL_WIDTH, LABEL_HEIGHT), LETTER_BG)

    columns = max(1, columns)
    rows = (len(entries) + columns - 1) // columns
    sheet_w = columns * LABEL_WIDTH + (columns + 1) * SHEET_GUTTER
    sheet_h = rows * LABEL_HEIGHT + (rows + 1) * SHEET_GUTTER
    sheet = Image.new("RGB", (sheet_w, sheet_h), "#e8e8e8")

    for index, (volume, _pool) in enumerate(entries):
        label = build_tape_label(volume)
        col = index % columns
        row = index // columns
        x = SHEET_GUTTER + col * (LABEL_WIDTH + SHEET_GUTTER)
        y = SHEET_GUTTER + row * (LABEL_HEIGHT + SHEET_GUTTER)
        sheet.paste(label, (x, y))

    return sheet


def build_vault_barcode(volumename: str, width: int = 280, height: int = 76) -> Image.Image:
    """Vault tape-cell strip (char row + barcode)."""
    return build_lto_tape_label(
        volumename,
        width=width,
        height=height,
        row_ratio=0.36,
        corner_radius=4,
    )


def png_bytes(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()

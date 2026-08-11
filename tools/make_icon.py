"""Generate convert.ico — the application icon.

Committed so the icon is reproducible rather than an opaque binary. Run with:

    .venv\\Scripts\\python.exe tools\\make_icon.py

Design notes: the mark has to survive being drawn at 16x16 on a taskbar, so it
is one bold shape — a page with a conversion arrow wrapping around it — on a
high-contrast indigo tile matching the app accent (#6C8CFF).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

MASTER = 1024
ROOT = Path(__file__).resolve().parent.parent
OUT_ICO = ROOT / "convert.ico"
OUT_PNG = ROOT / "tools" / "icon_preview.png"

TOP = (124, 150, 255)      # #7C96FF
BOTTOM = (58, 82, 214)     # #3A52D6
PAGE = (255, 255, 255)
PAGE_SHADE = (214, 222, 255)
ARROW = (255, 255, 255)


def rounded_mask(size: int, radius_pct: float = 0.225) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * radius_pct), fill=255)
    return mask


def vertical_gradient(size: int, top: tuple, bottom: tuple) -> Image.Image:
    grad = Image.new("RGB", (1, size))
    for y in range(size):
        f = y / max(1, size - 1)
        grad.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * f) for i in range(3)))
    return grad.resize((size, size), Image.Resampling.BICUBIC)


def draw_icon(size: int = MASTER, simple: bool = False) -> Image.Image:
    """Draw the mark. ``simple`` drops fine detail for 16/24px renderings."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    tile = vertical_gradient(size, TOP, BOTTOM).convert("RGBA")
    img.paste(tile, (0, 0), rounded_mask(size))

    d = ImageDraw.Draw(img)
    u = size / 100.0  # work in percentage units

    # --- page: a sheet with a folded top-right corner -----------------------
    if simple:
        left, top, right, bottom = 27 * u, 17 * u, 73 * u, 68 * u
        fold = 17 * u
    else:
        left, top, right, bottom = 29 * u, 20 * u, 71 * u, 72 * u
        fold = 14 * u
    radius = 3 * u

    d.rounded_rectangle([left, top, right, bottom], radius=radius, fill=PAGE)
    # knock the corner out, then lay the fold triangle over it
    d.polygon([(right - fold, top), (right, top), (right, top + fold)], fill=BOTTOM)
    d.polygon([(right - fold, top), (right, top + fold), (right - fold, top + fold)],
              fill=PAGE_SHADE)

    # Text lines hint "document", but they collapse into grey mush below ~32px.
    if not simple:
        line_h = 3.4 * u
        for i, y in enumerate((35 * u, 44 * u, 53 * u)):
            end = right - 6 * u - (8 * u if i == 2 else 0)
            d.rounded_rectangle([left + 6 * u, y, end, y + line_h],
                                radius=line_h / 2, fill=(150, 168, 235))

    # --- conversion arrow sweeping under the page ---------------------------
    if simple:
        bar_y0, bar_y1 = 74 * u, 87 * u
        bar_x0, bar_x1 = 18 * u, 64 * u
        head = 14 * u
    else:
        bar_y0, bar_y1 = 78 * u, 87 * u
        bar_x0, bar_x1 = 21 * u, 65 * u
        head = 11.5 * u

    d.rounded_rectangle([bar_x0, bar_y0, bar_x1, bar_y1],
                        radius=(bar_y1 - bar_y0) / 2, fill=ARROW)
    mid = (bar_y0 + bar_y1) / 2
    d.polygon([(bar_x1 - 1 * u, mid - head), (bar_x1 - 1 * u, mid + head),
               (bar_x1 + head * 1.3, mid)], fill=ARROW)

    return img


SIZES = [16, 24, 32, 48, 64, 128, 256]


def render(size: int) -> Image.Image:
    master = draw_icon(MASTER, simple=size <= 24)
    return master.resize((size, size), Image.Resampling.LANCZOS)


def main():
    frames = {s: render(s) for s in SIZES}

    largest = frames[256]
    largest.save(OUT_ICO, format="ICO",
                 sizes=[(s, s) for s in SIZES],
                 append_images=[frames[s] for s in SIZES if s != 256])
    print(f"wrote {OUT_ICO}")

    # side-by-side preview so the small sizes can be eyeballed
    pad = 12
    strip = [256, 128, 64, 48, 32, 24, 16]
    w = sum(strip) + pad * (len(strip) + 1)
    h = 256 + pad * 2
    preview = Image.new("RGB", (w, h), (18, 21, 30))
    x = pad
    for s in strip:
        tile = frames[s]
        preview.paste(tile, (x, h - pad - s), tile)
        x += s + pad
    preview.save(OUT_PNG)
    print(f"wrote {OUT_PNG}")


if __name__ == "__main__":
    main()

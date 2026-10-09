"""Draw the two MENU icons for the add-in (92 x 64, as the fx-CG50 wants).

The tile, its dithered gradient, bevel and the cyan "selected" background come
from the icon template in the fxSDK (Copyright (C) 2015-2022 gint/fxSDK
contributors, MIT licence; see LICENSE-fxsdk-template.txt), stored here
as template-uns.png / template-sel.png. The tile is recoloured orange and a
white conical flask is drawn on it. The add-in NAME below the tile (y >= 43) is
printed by the calculator itself, so nothing is drawn there.

Both images must be opaque RGB: fxgxa turns transparent pixels black.
"""
from pathlib import Path

from PIL import Image, ImageDraw

# The icons go next to this script, wherever the repo is checked out.
HERE = Path(__file__).resolve().parent

TILE = (242, 138, 36)           # saturated orange; no built-in app uses it
MID = (151, 184, 185)           # the template tile's middle grey-teal band
LREF = sum(MID) / 3
X0, Y0, X1, Y1 = 5, 5, 86, 42   # the tile, inclusive
CORNER_X = (5, 6, 7, 84, 85, 86)
CORNER_Y = (5, 6, 41, 42)


def recolour(p):
    """Keep the template's light/dark structure, swap the hue for TILE."""
    lum = sum(p[:3]) / 3
    if lum <= LREF:
        return tuple(round(c * lum / LREF) for c in TILE)
    k = (lum - LREF) / (255 - LREF)
    return tuple(round(c + (255 - c) * k) for c in TILE)


def tile_image(selected):
    base = Image.open(HERE / ("template-sel.png" if selected else "template-uns.png"))
    base = base.convert("RGB")
    out = base.copy()
    for y in range(Y0, Y1 + 1):
        for x in range(X0, X1 + 1):
            p = base.getpixel((x, y))
            if x in CORNER_X and y in CORNER_Y:
                # a rounded corner: tile blended into the background, so
                # recolour the tile part only, keeping the blend amount
                bg = base.getpixel((x, 46)) if selected else (255, 255, 255)
                ref = base.getpixel((min(max(x, 8), 83), y))
                span = sum(abs(a - b) for a, b in zip(ref, bg)) or 1
                a = min(1.0, sum(abs(q - b) for q, b in zip(p, bg)) / span)
                t = recolour(ref)
                out.putpixel((x, y), tuple(round(b + a * (c - b)) for b, c in zip(bg, t)))
            else:
                out.putpixel((x, y), recolour(p))
    return out


def flask():
    """The glyph as a mask: 2 px strokes, inside x 10..68, y 8..39."""
    m = Image.new("L", (92, 64), 0)
    d = ImageDraw.Draw(m)
    d.rectangle([31, 9, 47, 10], fill=255)                  # lip
    d.rectangle([34, 11, 35, 20], fill=255)                 # neck
    d.rectangle([43, 11, 44, 20], fill=255)
    d.line([(35, 20), (18, 36)], fill=255, width=2)         # shoulders
    d.line([(43, 20), (60, 36)], fill=255, width=2)
    d.rectangle([18, 37, 60, 38], fill=255)                 # base
    d.rectangle([28, 29, 50, 30], fill=255)                 # liquid level
    for x, y in ((34, 34), (44, 33)):                       # bubbles
        d.ellipse([x - 2, y - 2, x + 2, y + 2], outline=255)
    d.rectangle([40, 23, 41, 24], fill=255)
    return m


def draw(selected):
    image = tile_image(selected)
    mask = flask()
    shadow = Image.new("L", mask.size, 0)
    shadow.paste(mask.point(lambda v: v * 3 // 10), (0, 1))     # 30% black, +1 y
    image.paste((0, 0, 0), mask=shadow)
    image.paste((255, 255, 255), mask=mask)
    return image


if __name__ == "__main__":
    draw(False).save(HERE / "icon-uns.png")
    draw(True).save(HERE / "icon-sel.png")
    print("icons written to", HERE)

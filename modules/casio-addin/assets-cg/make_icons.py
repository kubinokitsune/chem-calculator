"""Draw the two MENU icons for the add-in (92 x 64, as the fx-CG50 wants).

Unselected is the flat version, selected is the brighter one the calculator
shows when the cursor is on it.
"""
from PIL import Image, ImageDraw

OUT = ("C:/Users/pipef/OneDrive/Desktop/chem calculator project/chem Calculator/"
       "modules/casio-addin/assets-cg/")

W, H = 92, 64


def draw(selected):
    image = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    d = ImageDraw.Draw(image)

    glass = (70, 110, 200) if not selected else (40, 90, 210)
    liquid = (60, 170, 120) if not selected else (40, 190, 120)
    ink = (20, 30, 50)

    if selected:
        d.rectangle([0, 0, W - 1, H - 1], fill=(232, 240, 255, 255))

    # a conical flask: neck, shoulders, body
    neck_left, neck_right, neck_top = 40, 52, 6
    base_left, base_right, base_y = 20, 72, 50

    d.rectangle([neck_left, neck_top, neck_right, 20], outline=glass, width=2)
    d.polygon([(neck_left, 20), (base_left, base_y), (base_right, base_y),
               (neck_right, 20)], outline=glass)
    d.line([(neck_left, 20), (base_left, base_y)], fill=glass, width=2)
    d.line([(neck_right, 20), (base_right, base_y)], fill=glass, width=2)
    d.line([(base_left, base_y), (base_right, base_y)], fill=glass, width=2)

    # the liquid inside
    d.polygon([(30, 38), (23, base_y - 1), (69, base_y - 1), (62, 38)], fill=liquid)

    # three bubbles
    for x, y, r in ((36, 44, 2), (46, 42, 3), (56, 46, 2)):
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255))

    # the name along the bottom
    d.text((26, 53), "ChemCalc", fill=ink)
    return image


draw(False).save(OUT + "icon-uns.png")
draw(True).save(OUT + "icon-sel.png")
print("icons written to", OUT)

"""Make the add-in's two text fonts, font-body.png and font-bold.png.

They are the 10 x 20 bitmaps of Terminus Font ("ter-u20n" and "ter-u20b"),
Copyright (C) 2020 Dimitar Toshkov Zhekov, SIL Open Font License 1.1; see
LICENSE-terminus-OFL.txt. The glyphs are copied pixel for pixel, only laid out
as the grid fxconv wants: printable ASCII 0x20-0x7E, 16 glyphs a row, black on
white. fxconv-metadata.txt turns each PNG into a gint font.

The Terminus bitmaps come from the Debian/Ubuntu package xfonts-terminus
(sudo apt install xfonts-terminus), which keeps them in /usr/share/fonts/X11/misc.

    py make_font.py [directory with ter-u20n_unicode.pcf.gz and ter-u20b_unicode.pcf.gz]

Needs Pillow. The PNGs are written next to this script.
"""
import gzip
import sys
from pathlib import Path

from PIL import Image, PcfFontFile

HERE = Path(__file__).resolve().parent
SOURCE = Path(sys.argv[1] if len(sys.argv) > 1 else "/usr/share/fonts/X11/misc")

W, H = 10, 20
COLUMNS = 16
FIRST, COUNT = 0x20, 95         # gint's "print" character set


def make(name, source):
    path = SOURCE / source
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as fp:
        font = PcfFontFile.PcfFontFile(fp)
    rows = -(-COUNT // COLUMNS)
    sheet = Image.new("RGB", (COLUMNS * W, rows * H), "white")
    for i in range(COUNT):
        glyph = font.glyph[FIRST + i][3]            # a W x H bitmap, ink = set
        assert glyph.size == (W, H), (name, i, glyph.size)
        cell = Image.new("RGB", (W, H), "white")
        cell.paste((0, 0, 0), mask=glyph)
        sheet.paste(cell, (i % COLUMNS * W, i // COLUMNS * H))
    sheet.save(HERE / name)
    print("wrote", HERE / name)


make("font-body.png", "ter-u20n_unicode.pcf.gz")
make("font-bold.png", "ter-u20b_unicode.pcf.gz")

#!/usr/bin/env python3
"""Turn a zoomed screenshot of a hat sprite into a native-size transparent PNG in assets/sprites/<view id>.png.
  import_sprite.py IMAGE VIEW_ID --scale N
The background is the colour of the top-left pixel; the art is cropped to its bounding box and sampled once per NxN block
(the screenshot must be a nearest-neighbour zoom). build_data.py uses assets/sprites/<view id>.png in place of the viewlist
sprite, for hats whose viewlist sprite is damaged or shows the wrong side."""
import argparse
from pathlib import Path
from PIL import Image

ap = argparse.ArgumentParser(); ap.add_argument('image'); ap.add_argument('view'); ap.add_argument('--scale', type=int, required=True); a = ap.parse_args()
im = Image.open(a.image).convert('RGB'); w, h = im.size; px = im.load(); bg = px[0, 0]; n = a.scale
mask = Image.new('L', im.size); m = mask.load()
for y in range(h):
    for x in range(w):
        if px[x, y] != bg: m[x, y] = 255
x0, y0, x1, y1 = mask.getbbox()
cols, rows = -(-(x1 - x0) // n), -(-(y1 - y0) // n)
out = Image.new('RGBA', (cols, rows), (0, 0, 0, 0)); o = out.load()
for j in range(rows):
    for i in range(cols):
        c = px[min(x0 + i * n + n // 2, w - 1), min(y0 + j * n + n // 2, h - 1)]
        if c != bg: o[i, j] = c + (255,)
dst = Path(__file__).resolve().parent.parent / 'assets/sprites' / f'{a.view}.png'
out.save(dst); print(f'{dst}: {cols}x{rows}')

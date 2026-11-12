#!/usr/bin/env python3
"""Make the favicon, app icons and web manifest from the Teddybear Hat sprite (public/img/view/143.png, built by build_data.py).
Run: python3 scripts/make_icons.py
Sprites are scaled by whole numbers so the pixels stay sharp."""
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent / 'public'
SPRITE = ROOT / 'img/view/143.png'
BG = (246, 244, 239, 255)      # --bg in light mode
ACCENT = (166, 63, 37, 255)    # --accent
OUT = ROOT / 'icons'

def icon(size, bg, fill):
    """Square icon with the sprite centred; fill is the share of the width the sprite may take."""
    s = Image.open(SPRITE).convert('RGBA')
    k = max(1, int(size * fill) // s.width)
    s = s.resize((s.width * k, s.height * k), Image.NEAREST)
    im = Image.new('RGBA', (size, size), bg)
    im.alpha_composite(s, ((size - s.width) // 2, (size - s.height) // 2))
    return im

def main():
    OUT.mkdir(exist_ok=True)
    icon(32, (0, 0, 0, 0), 1.0).save(OUT / 'favicon-32.png')                 # tab icon, transparent
    icon(48, (0, 0, 0, 0), 1.0).save(OUT / 'favicon-48.png')
    icon(180, BG, .8).save(OUT / 'apple-touch-icon.png')                     # iOS draws its own corners
    icon(192, BG, .8).save(OUT / 'icon-192.png')
    icon(512, BG, .8).save(OUT / 'icon-512.png')
    icon(512, BG, .62).save(OUT / 'icon-maskable-512.png')                   # keeps the hat inside the safe zone
    (ROOT / 'manifest.webmanifest').write_text(json.dumps({
        'name': "Rhya's Hat Tracker", 'short_name': 'Hat Tracker', 'start_url': './', 'display': 'standalone',
        'background_color': '#f6f4ef', 'theme_color': '#f6f4ef',
        'icons': [{'src': 'icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
                  {'src': 'icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png'},
                  {'src': 'icons/icon-maskable-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'}]}, indent=1) + '\n')
    print('wrote', *sorted(p.name for p in OUT.iterdir()), 'and manifest.webmanifest')

if __name__ == '__main__': main()

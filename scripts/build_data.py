#!/usr/bin/env python3
"""Build public/hats.json from game-data-tools data.
Run: GAME_DATA=/Users/jax/Projects/game-data-tools python3 scripts/build_data.py
Hats = reward items of uaRO quests that are headgear, plus quests named after a headgear item.
Emulator values (rathena renewal items, pre-renewal drops) are official iRO, not uaRO. Drop rates get uaRO x5 (cap 100%), MvP x3."""
import glob, json, os, re, shutil, sys, time
from pathlib import Path
import yaml

GD = os.environ.get('GAME_DATA', '/Users/jax/Projects/game-data-tools')
OUT = Path(__file__).resolve().parent.parent / 'public'
LOAD = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)

def yml(p): return yaml.load(Path(p).read_text(encoding='utf-8'), Loader=LOAD).get('Body', [])

items = {}
for f in glob.glob(f'{GD}/rathena/db/re/item_db_*.yml'):
    for d in yml(f): items[d['Id']] = d
aegis = {d['AegisName']: i for i, d in items.items()}
for f in glob.glob(f'{GD}/rathena/db/pre-re/item_db_*.yml'):  # drops come from pre-renewal, so resolve its item names
    for d in yml(f): aegis[d['AegisName']] = d['Id']
is_head = lambda i: i in items and any(k.startswith('Head_') for k in (items[i].get('Locations') or {}))
by_name = {}
for i, d in items.items():
    if is_head(i): by_name.setdefault(d['Name'].lower(), []).append(i)

info = {}
for l in open(f'{GD}/index/iteminfo.jsonl', encoding='utf-8'):
    r = json.loads(l); info[r['id']] = r

spawns = set()  # mob ids that spawn in the pre-renewal field/dungeon/city scripts (not event or summon-only mobs)
for f in glob.glob(f'{GD}/rathena/npc/pre-re/mobs/**/*.txt', recursive=True):
    for l in open(f, encoding='utf-8', errors='replace'):
        m = re.match(r'[^/\s]+,[^\t]*\t(?:boss_)?monster\t[^\t]+\t(\d+)', l)
        if m: spawns.add(int(m.group(1)))
print(f'{len(spawns)} naturally spawning mobs')
drops = {}  # item id -> [(mob, rate, mvp)]
for d in yml(f'{GD}/rathena/db/pre-re/mob_db.yml'):
    if d['Id'] not in spawns: continue
    for key, mvp in (('Drops', False), ('MvpDrops', True)):
        for x in d.get(key) or []:
            i = aegis.get(x.get('Item'))
            if i is None: continue
            pct = x.get('Rate', 0) / 100 * (3 if mvp else 5)
            drops.setdefault(i, []).append({'mob': d['Name'], 'mob_id': d['Id'], 'rate': round(min(pct, 100), 3), 'mvp': mvp})
for v in drops.values(): v.sort(key=lambda x: -x['rate'])

from PIL import Image
sys.path.insert(0, f'{GD}/bin')
import sprite_clean  # shared sprite cleanup and its exception list (game-data-tools/data/sprite-fixes.json)
SCALE = {}  # sprite id -> display size multiplier, for any hat that looks off next to a character
ICON_ART = set()  # sprites broken in the source (Red Ribbon keeps 36 of 684 pixels); show the item icon instead
_STALE = max(Path(sprite_clean.__file__).stat().st_mtime, sprite_clean.FIXES_FILE.stat().st_mtime)
def clean(src, dst):
    """Cleaned PNG at dst; reused unless the cleanup code or its fixes file changed since it was written."""
    if dst.exists() and dst.stat().st_mtime > _STALE: return
    sprite_clean.clean_image(src, dst)

V = int(time.time())  # appended to image URLs so browsers don't keep stale copies
def icon(i):
    s = Path(GD) / f'images/items/item{i}.gif'
    if s.exists():
        clean(s, OUT / f'img/item{i}.png'); return f'img/item{i}.png?v={V}'
def viewimg(v):
    own = OUT.parent / 'assets/sprites' / f'{v}.png'  # hand-supplied sprite (scripts/import_sprite.py) beats the viewlist one
    if v and own.exists():
        (OUT / 'img/view').mkdir(parents=True, exist_ok=True); shutil.copy(own, OUT / f'img/view/{v}.png'); return f'img/view/{v}.png?v={V}'
    s = Path(GD) / f'index/viewlist_img/{v}.gif'
    if v and s.exists():
        clean(s, OUT / f'img/view/{v}.png'); return f'img/view/{v}.png?v={V}'
def sprite_size(v):
    f = OUT / f'img/view/{v}.png'
    return list(Image.open(f).size) if v and f.exists() else None
def iname(i, fb):
    return (info.get(i) or {}).get('name') or (items.get(i) or {}).get('Name') or fb

quests = json.load(open(f'{GD}/data/uaro-quests.json'))['quests']
try: rms = json.load(open(f'{GD}/index/rms-quests.json'))  # bin/fetch_rms_quests.py; official iRO quest pages on RateMyServer
except OSError: rms = {}
try: rms_npc = json.load(open(f'{GD}/index/rms-quest-npcs.json'))  # bin/fetch_rms_npcs.py; NPC + location of the official iRO quest
except OSError: rms_npc = {}
# uaRO changes to official recipes (uaro-docs improvements.md): quest id -> {ingredient item id: qty}
QTY = {'uaro-boy-s-cap': {1030: 5}}
NO_RECIPE = {'uaro-apple-of-archer'}  # no quest makes it: RateMyServer has it as a drop and as an ingredient of Model Training Hat, so the loot sheet's Arrow + Model Training Hat row would be a loop
OVERRIDE = {'uaro-evil-wing-ears': 5068}  # same name as 5044 (upper) and 18519; the quest takes Elven Ears (mid)
CUSTOM = {'Server Hat Quest', 'Headgear Quest'}
hats, seen, missing = {}, set(), {'icon': set(), 'unknown_item': set()}
for q in quests:
    rew = [r for r in (q.get('rewards') or {}).get('items', []) if r.get('item_id')]
    found = [r for r in rew if is_head(r['item_id'])]
    custom = False
    if not found and rew and CUSTOM & set(q['categories']):
        found, custom = rew, True  # uaRO-only item, not in the emulator db
    if not found and not rew:
        base = re.sub(r'\s*\[\d+\]\s*$', '', q['name']).lower()
        ids = [OVERRIDE[q['id']]] if q['id'] in OVERRIDE else by_name.get(base) or by_name.get(base + ' [1]')
        if ids and q.get('ingredients'): found = [{'item_id': ids[0], 'item': q['name'], 'qty': 1}]
    for r in found:
        hid = r['item_id']
        if hid in hats: hats[hid]['quests'].append(q['id']); continue
        d, inf = items.get(hid) or {}, info.get(hid) or {}
        desc = inf.get('description') or []
        ings = []
        for g in [g for g in q.get('ingredients') or [] if g.get('item_id') and q['id'] not in NO_RECIPE]:
            gi = g['item_id']
            if gi and not icon(gi): missing['icon'].add(gi)
            ings.append({'id': gi, 'name': iname(gi, g['item']), 'qty': QTY.get(q['id'], {}).get(gi, g['qty']), 'icon': icon(gi), 'drops': drops.get(gi, [])[:6]})
        if not icon(hid): missing['icon'].add(hid)
        hats[hid] = {
            'id': hid, 'name': iname(hid, r['item']), 'icon': icon(hid), 'custom': custom or hid not in items,
            'slots': inf.get('slots', d.get('Slots', 0)), 'view': inf.get('view'), 'sprite': icon(hid) if str(inf.get('view')) in ICON_ART else viewimg(inf.get('view')), 'size': [24, 24] if str(inf.get('view')) in ICON_ART else sprite_size(inf.get('view')), 'scale': SCALE.get(str(inf.get('view')), 1),
            'locations': [k[5:] for k in (d.get('Locations') or {})], 'def': d.get('Defense'),
            'level': d.get('EquipLevelMin'), 'jobs': [j for j, v in (d.get('Jobs') or {}).items() if v] if d.get('Jobs') else [],
            'desc': [x for x in desc if x],
            'quests': [q['id']], 'quest_name': q['name'], 'npc': q.get('npc') or (rms_npc.get(str(hid)) or {}).get('npc'), 'location': q.get('location') or (rms_npc.get(str(hid)) or {}).get('navi'),
            'min_level': q.get('min_level'), 'wiki': q.get('wiki'), 'categories': q['categories'],
            'rms': [{'title': x['title'], 'url': x['url']} for x in rms.get(str(hid), []) if x['role'] == 'makes'],
            'origin': 'classic' if rms.get(str(hid)) and any(x['role'] == 'makes' for x in rms[str(hid)]) else 'uaro',  # classic = an official iRO quest makes it
            'ingredients': ings, 'drops': drops.get(hid, [])[:6],
        }
OUT.mkdir(exist_ok=True)
if (Path(GD)/'images/items/card.gif').exists(): clean(Path(GD)/'images/items/card.gif', OUT/'img/card.png')
data = {'note': 'Item data is official iRO (rathena); drops are pre-renewal and rates have uaRO x5 (MvP x3) applied. Custom uaRO items have no emulator data.',
        'hats': sorted(hats.values(), key=lambda h: h['name'].lower())}
(OUT / 'hats.json').write_text(json.dumps(data, ensure_ascii=False, indent=1))
print(f"{len(hats)} hats ({sum(h['custom'] for h in hats.values())} custom uaRO), "
      f"{sum(1 for h in hats.values() if h['icon'])} with icons, {sum(1 for h in hats.values() if h['drops'])} drop somewhere")
print('ids without icon:', sorted(missing['icon']))

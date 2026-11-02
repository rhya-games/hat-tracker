# Hat Tracker

A local page for tracking and crafting uaRO hats: status, shared material counts, a combined materials list, drop sources and links to official quests. Progress is saved in the browser (export/import as JSON).

The hat data and images come from [game-data-tools](../game-data-tools) and are not stored here (`public/hats.json` and `public/img/` are git-ignored; the data belongs to its original projects).

## Run

```bash
GAME_DATA=/Users/jax/Projects/game-data-tools python3 scripts/build_data.py
cd public && python3 -m http.server 8765
```

Open http://localhost:8765/.

## Needs from game-data-tools

- `data/uaro-quests.json`, `index/iteminfo.jsonl`, `index/viewlist_img/`, `images/items/`, `rathena/` databases and NPC scripts
- `index/rms-quests.json`, built with `bin/fetch_rms_quests.py <item ids>`; without it the RMS quest links are left out

`scripts/build_data.py` holds the uaRO-specific corrections (`QTY`, `OVERRIDE`) and the sprite fixes (`HOLES`, `WHITE`, `STRIP`, `SCALE`).

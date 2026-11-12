# Hat Tracker

A local page for tracking and crafting uaRO hats: status, shared material counts, a combined materials list, drop sources and links to official quests. Progress is saved to `progress.json` in this repo (also kept in the browser; export/import as JSON).

The hat data and images come from [game-data-tools](../game-data-tools) and are not stored here (`public/hats.json` and `public/img/` are git-ignored; the data belongs to its original projects).

## Run

With the `hats` command installed (`ln -s "$PWD/scripts/hats" ~/.local/bin/hats`), just type `hats`: it starts the server and opens the page, or just opens it if it's already running. Manually:

```bash
GAME_DATA=/Users/jax/Projects/game-data-tools python3 scripts/build_data.py
python3 scripts/serve.py 8765
```

Open http://localhost:8765/. `scripts/serve.py` serves `public/` and saves your progress to `progress.json` in this folder after every change; commit that file to keep a history. Open the page any other way and progress is kept in the browser only (the page says which). Progress loads from `progress.json` first, and a browser-only copy is uploaded the first time if the file doesn't exist yet.

## Needs from game-data-tools

- `data/uaro-quests.json`, `index/iteminfo.jsonl`, `index/viewlist_img/`, `images/items/`, `rathena/` databases and NPC scripts
- `index/rms-quests.json`, built with `bin/fetch_rms_quests.py <item ids>`; without it the RMS quest links are left out

`scripts/build_data.py` holds the uaRO-specific corrections (`QTY`, `OVERRIDE`) and the display scale (`SCALE`). Sprite cleanup and its per-sprite exceptions live in game-data-tools (`bin/sprite_clean.py`, `data/sprite-fixes.json`); `scripts/import_sprite.py` adds a hand-captured sprite under `assets/sprites/`.

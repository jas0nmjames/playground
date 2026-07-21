# Strikefleet Omega — Recreated

A browser-based fan tribute to **Strikefleet Omega** (Zynga/Kabam, ~2012), the
draw-a-flight-path carrier-defense game that was delisted from Google Play.
Vanilla JavaScript + HTML5 Canvas. No build step, no dependencies.

## Play

Open `index.html` in any modern browser, or serve the folder:

```bash
python3 -m http.server 8734
# then open http://localhost:8734
```

Works with mouse or touch. Best experienced fullscreen / on a tablet or phone.

## How to play

Your carrier is the fleet's heart — if it dies, the run ends.

- **Fighters & bombers** — Tap a squadron button (`F1`, `B1`, …) or the carrier,
  then **drag to draw a flight path**. The squadron flies the path and
  automatically engages: fighters shred drones/raiders, bombers launch homing
  torpedoes at cruisers and asteroids. They patrol at the end of the path, then
  return to rearm. Tap a deployed squadron's button to **recall** it early.
- **Artillery cruisers** — Tap an artillery button (`A1`), then **tap the map**
  to call in an off-screen bombardment (area damage, then a reload cooldown).
- **Between waves** you dock at **Fleet Command** to spend credits on new
  squadrons, artillery, hull repairs, and reinforcements.
- Clear all 5 waves of a sector to **warp** to the next, tougher sector.

Kills pay credits. Spend them well. Hold the line.

## Structure

- `index.html` — canvas host + viewport setup
- `game.js` — the entire engine: state machine, waves, squadrons, enemies,
  projectiles, artillery, shop, HUD, and rendering
- `.claude/launch.json` — dev-server config for the preview tooling

## Credits & attribution

### Original game

**Strikefleet Omega** was created and published by **Zynga / Kabam** and released
around 2012. It was later delisted from Google Play and the App Store. This
project is an unofficial, non-commercial **fan tribute** to that game. All credit
for the original concept, design, art direction, and brand belongs to its
original creators and rights holders. No affiliation or endorsement is implied.

This repository is an **original reimplementation of the game *design*** from
memory. It ships **no original art, code, audio, or other assets** from the
delisted title, and the name is used only to identify the work being paid tribute
to. If you are a rights holder and have concerns, please open an issue.

### This recreation

Built by **Jason James** in collaboration with **Claude** (Anthropic's
[Claude Code](https://claude.com/claude-code), model *Claude Fable 5*), which
wrote and iteratively tested the engine, gameplay, and UI in this repository.

Code in this repository is released for personal, educational, and non-commercial
use. It is provided as-is, with no warranty.

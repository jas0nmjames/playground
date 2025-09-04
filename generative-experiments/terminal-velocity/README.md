# Velocity.js — Web-based Terminal Velocity–style Prototype

A lightweight first-person flying/shooter prototype built with **Three.js** (ES modules).It runs entirely in the browser and is deployable to **Netlify** from a GitHub repo.

## Features (v0.2)
- Forward flight over infinite, altitude-colored terrain (grass/rock/snow) + soft fog + distant mountain ring + realistic blue sky
- Mouse look (Pointer Lock) + WASD strafe, Shift boost
- Simple enemies that spawn ahead and move toward you
- Firing bullets (click/Space) with collision + scoring
- HUD overlay with speed, health, score, FPS, and a crosshair
- No build step required (imports via ESM CDN; pin versions in import map)

> This is a foundation for you to iterate on. The code is small, annotated, and intentionally straightforward.

---

## Run locally
You must serve the files (due to ES module imports). Any static server works:
```bash
# Python 3
python -m http.server 8080

# or Node (if installed)
npx http-server -p 8080
```
Then open http://localhost:8080 — click the screen to lock pointer and play.

## Deploy to Netlify
1. Push this folder to a GitHub repo (e.g., `velocity-js`).
2. In Netlify, **New site from Git**, pick the repo.
3. **Build command**: _None_ (or `""`)  
   **Publish directory**: `/` (root)
4. Deploy. That’s it.

> The `netlify.toml` here sets sensible defaults for a static site and basic security headers.

## Controls
- **Click**: enter pointer lock, also fires
- **Mouse**: look/aim
- **W/S**: pitch up/down
- **A/D**: strafe left/right
- **Shift**: boost forward
- **Space / Left click**: fire
- **P**: pause/resume

## Project structure
```
velocity-js/
├─ index.html
├─ styles.css
├─ netlify.toml
├─ README.md
└─ src/
   ├─ main.js
   ├─ Game.js
   ├─ Input.js
   ├─ Player.js
   ├─ Bullet.js
   ├─ Enemy.js
   ├─ Terrain.js
   └─ utils/
      └─ Noise.js
```

## Roadmap ideas
- Add different biomes & skyboxes, distant mountains
- Enemies with behaviors (patrols, formations, projectiles)
- Power-ups, shields, afterburner overheating
- Mission system (objectives, checkpoints), boss fights
- Sound effects & music, explosions, particles
- Save high scores in localStorage
- Switch to local-bundled libs (no CDN) if preferred

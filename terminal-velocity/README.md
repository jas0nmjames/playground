---
published: 2025-09-03
updated: 2026-03-10
tags: generative
---

# Velocity — Textured v1.1.0

**What's new** (for richer land texture):
- **Triplanar** texture mapping (no stretching on slopes)
- **Macro + micro detail layers** (procedural noise) modulate color
- **Faux AO** using slope/altitude darkening
- **Clutter scatter**: lightweight **instanced rocks** across terrain
- Higher terrain resolution (per-tile)

## Run
```bash
npm install
npm run dev
```

## Deploy (Netlify)
- build: `npm run build`
- publish: `dist/`

Tune it
- Textures/noise: `src/utils/TextureGen.js`
- Shader (triplanar + blend): `src/materials/TerrainTriplanarMaterial.js`
- Terrain shaping & density: `src/world/Terrain.js`

## Claude

Frontmatter (`published`, `updated`, `tags`) added with [Claude](https://claude.ai) (claude-sonnet-4-6) on March 26, 2026.

| Created | Tool | Model | Estimated energy consumption[^claude] | Estimated carbon emissions | Estimated water usage |
|---|---|---|---|---|---|
| March 26, 2026 | Claude Code | claude-sonnet-4-6 | 0.036 kWh | 0.014 kg CO₂ | 0.018 L |

[^claude]: assuming 18 Wh per prompt; does not include estimate for foundation model training

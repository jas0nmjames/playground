
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

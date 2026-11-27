# Medianville Miniature: realism design record

November 19, 2026. How v3's miniature went from a model on a screen toward a photographed miniature.

## Brief

Jason shared seven tilt-shift photographs as references:

- an architectural model at dusk, with street lamps out of focus as soft discs;
- a city intersection and a London bus lane, full of street paint, buses and parked cars;
- a San Francisco corner;
- 2nd & Market and Sunshine on Leith, both in low, warm sun with long shadows;
- Mini-Stadt, a city seen from high up, its rooftops fading into haze.

The question was how to make the animation look more like them.

## Why v3 read as a model on a screen

1. There was no tone mapping, so highlights clipped and there was no print-like contrast curve.
2. There were no contact shadows, so buildings, cars and trees floated.
3. Everything had one roughness, and nothing reflected the sky.
4. The ground was flat colour, with no grain and no lane paint.
5. The sun's colour and angle were loosely tied to the clock, and nothing glowed at night.
6. The blur is a band fixed to the screen, where in a photograph blur follows depth.

## The lab

A separate page built a 13 × 13 tile Courthouse Square in v3's kit, with cars that queue at signals and pegs on the sidewalks. Each fix was a switch, grouped into cumulative iterations, so each could be judged on its own and against v3 ("hold to compare").

| Iteration | Adds | Kept |
|---|---|---|
| Lens | A plane of focus tilted through one street. Blur follows depth, and bright points open into bokeh. Tap to refocus. | No. Dropped by Jason; the v3 focus band stays. |
| Light | Filmic tone and grade, sun and sky, contact shadows, night lights | Yes |
| Surface | Street detail, materials with grain, haze | Yes |
| Horizon | No table; the city continues past the board into haze; a low skyline camera | Yes. The skyline camera became tilting. |

Jason also asked for the board to turn, with the mouse, the keyboard and touch. The lab's second version added that, and the decisions above were made on it.

Two lessons from the lab carried over:

- **Where the sun sits relative to the camera matters as much as how it is lit.** Lighting the faces the camera can't see, or backlighting the evening, made frames murky. In the viewer, north is up as on the Map, so from v3's opening angle the noon sun is behind the camera, morning light comes from the right and evening light from the left.
- **Without lens blur, distance needs haze.** Otherwise the repeated blocks past the board show.

## How it works in v3

- **Rendering, in order:**
  1. A depth pass of the town.
  2. A colour pass into a high-dynamic-range target with shadows (4,096² map, PCF soft).
  3. Contact shadows at half resolution: hemisphere SSAO from depth, 12 samples, radius 0.11.
  4. Haze toward the sky colour, starting 4 units past the view distance, density 0.035, up to 90%.
  5. The v3 focus band, unchanged: Off, Subtle or Full.
  6. Bloom at quarter and eighth resolution.
  7. ACES fitted tone mapping with auto exposure, saturation 1.14, an S-curve, split toning, vignette and grain.
  8. A sharp pass that copies the town's depth and draws records, pins and stopped pegs on top, as before.
- **Sun and sky**
  - A solar path for March 3 near 39° N: sunrise 6:48 a.m., sunset 6:12 p.m., noon elevation 44°.
  - Sky colours are keyed to the sun's height. They feed a sky dome, an environment map rebuilt every six simulated minutes, and the haze.
- **Night lights**
  - Windows glow in v3's occupancy pattern and flash when a paycheck lands.
  - Lamps throw additive pools of light.
  - Cars carry headlights, tail lights and beams.
  - Signals cycle on a shared 15-second plan.
- **Materials.** Eleven classes: wall, roof, concrete, paint, metal, car, glass, leaf, bark, water and wood. Most take a world-space grain from one 256² noise texture. Colours get a small random shift, and the ground is desaturated (grass the most).
- **Street detail.** 1,704 parts on the plan, marked `d: 1`.
- **Past the board**
  - The board sits in a wider region out to 42 tiles beyond it.
  - Land use follows the board: suburbs; farms to the south-west, with crop rows, farmhouses and barns; industry to the south-east.
  - Roads continue the board's lines, and the rail line runs on south.
  - None of it casts shadows.
- **Turning**
  - The heading and tilt belong to the Miniature; centre and zoom are still shared with the Map.
  - Buildings now have windows on all four faces. v3 only placed them on the two its fixed camera saw.

## Determinism

The shared plan is consumed in a fixed order by one random stream, and the Map, the real-day fold and the household anchors depend on it. Everything new draws from separate streams:

- back-face windows, one stream per tile;
- street detail, one stream per road tile;
- rooftop units, one stream per roof.

The new windows carry no footprint, so the Map's night occupancy is unchanged. A comparison of the plan before and after found:

- every building part identical, in the same order;
- footprints, homes, anchors, symbols, front-facing windows, 225 households and 101 organisations all unchanged.

The only change to the base is the 61 plain centre dashes on the main roads, which the double yellow line replaces.

## Fidelity pass, Nov 2026

The first part of look 4, "Photographed, alive" ([decisions 3.12](../decisions.md)). Render time only: the plan, its parts and their order are untouched, and there are no new random draws in the plan.

What landed, all in `index.html`:

- **Walking legs.** A person is a box torso and a head (plain meshes in a group, so a stopped failure can still turn primer on layer 1) and two legs. The legs of every walker are one shared `InstancedMesh` (256 legs at most): a box 0.16 × 0.86 × 0.15 m, pivoted at the hip, scaled to viewer units once in the geometry (instance scale 1, so the swing doesn't distort). A per-instance attribute `aPh` (x = phase, y = 1 if walking) feeds a vertex-shader swing, `sin(uTime * 7.5 + aPh.x) * 0.5 * aPh.y * uWalk`, with the two legs π apart. People now face their direction of travel. A stopped failure keeps two still legs in primer.
- **Trees in the wind.** A patch to the leaf material only: a slow gust and a faster sway in the vertex shader, phase from the instance's position, stronger toward the top. Flat leaf pieces (crop rows) are excluded by their instance height.
- **Softer contact shadows.** The light composite takes nine AO taps (0.36 centre, 0.11 sides, 0.05 corners) 1.5 AO texels apart, in place of four.
- **Cloud shadows.** In the shared material patch, a three-octave value-noise `fbm` of world position, drifting slowly, multiplies the direct light after `lights_fragment_end` (uniform branch skips it when `uCloud` is 0). Cells are about 6 tiles wide.
- **Reduced motion and night.** One set of uniforms (`FID`: time, walk, life, cloud) drives all three; walk, sway and cloud are 0 under `prefers-reduced-motion`, and clouds fade with sun height, so they are off at night.

Known limits: the depth pre-pass and the sun's shadow map draw the straight legs and the still crowns, so the shadow of a leg doesn't swing. Not done in this pass: half-full lots and loose placement, the handheld camera.

## Not yet verified

- Frame rate on real GPUs. The container renders in software at about a frame a second.
- A screen reader pass of the new controls. They have labels and key shortcuts, and turning announces the heading and tilt.

## Not tried

- Motion blur on fast cars.
- Chromatic aberration at the frame edge.
- The lab's lane-following traffic, where cars queue at signals. v3's cars still follow their paths and ignore the signals.

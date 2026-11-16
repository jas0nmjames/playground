# Prompt: double liquid hourglass

Paste everything below the line into a fresh Claude Code session opened at the root of this repo.

---

I want you to build a browser simulation of a toy I own: a double liquid-motion hourglass (the kind sold as a "liquid motion bubbler"). The goal is something I could leave running on a screen and that someone who owns the real toy would recognise as behaving correctly, because the drops are actually simulated rather than animated along scripted paths. Work in `liquid-hourglass/` in this repo.

## Reference material

I filmed the real one. Stills from that video are in `liquid-hourglass/reference/`. Look at all four before you design anything, and keep coming back to them as the ground truth:

- `front.jpg`: front view in steady state. This is the main visual target.
- `drip-sequence-12fps.jpg`: twelve consecutive frames at 12 fps (one second, read left to right, top row then bottom row). Use it for timing: drop formation, pinch-off, fall speed, and how drops behave on the ramps.
- `side-view.jpg`: the toy turned edge-on, showing how it is built.
- `just-flipped.jpg`: about a second after being turned over, before the flow has settled.

## What the object is

This is what I can see in the footage. Where I am inferring rather than observing, I say so.

**Construction.** A clear acrylic block about three times as tall as it is wide, with a gently pinched waist and rounded corners. Inside are two thin, flat chambers, one behind the other, completely sealed from each other (the side view shows this clearly). Each chamber is filled with clear oil plus one dyed liquid that is denser than the oil and does not mix with it: magenta in one chamber, cyan-blue in the other. Because the chambers are thin, the liquid behaves almost two-dimensionally: falling drops are flat discs with crisp edges and uniform colour, not shaded spheres.

**Colour.** The two colours never physically mix. Wherever a magenta shape and a cyan shape overlap from the viewer's angle, they read as a deep indigo-violet, like two stacked colour filters. The two chambers are seen with slight parallax, so the top reservoir looks solid indigo with a thin magenta fringe on one edge and a cyan fringe on the other, and falling drops from the two chambers partly overlap as offset pairs.

**Top reservoir.** The dyed liquid pools on a floor shaped like a shallow V, which funnels it to a small nozzle at the centre. Above the liquid there is clear oil and a few trapped air bubbles against the ceiling.

**Dripping.** At each nozzle a pendant drop swells, forms a neck, and pinches off. The detached drop relaxes into a slightly oblate disc and sinks at a steady, unhurried speed: the oil is viscous, so this is slow creeping flow with no splashing and no acceleration to speak of after the first moment. From the sequence, each chamber releases a drop roughly every 0.4 to 0.5 seconds and a drop takes a bit over a second to cross the middle section, so there are usually about three drops in flight per chamber. The two chambers drip independently and drift in and out of phase. Tiny satellite droplets left over from pinch-off hang almost motionless in the oil.

**Landing and ramps.** Below the middle section is an inverted-V ramp (a chevron) with a small gap at its peak. Drops land on it, flatten, and creep outward down the slope toward the side walls. They queue up along the ramp as a row of squashed blobs pressed against each other, and they do not merge immediately on contact: neighbours sit touching for a while before coalescing. At the outer ends the liquid squeezes down past the wall and drips into the bottom chamber.

**Bottom pool.** Liquid collects at the bottom. Fresh arrivals sit on the pool as distinct beads before merging into it, so the pool surface looks lumpy and beaded rather than flat. There is a small cluster of air bubbles here too.

**Flipping (my inference).** The toy appears to be symmetric end to end: the chevron ramp at the bottom looks like the same part as the V-shaped funnel at the top, seen upside down, and the gap at its peak is the other nozzle. So turning it over turns the ramp into the funnel and the pool into the reservoir, and the cycle restarts. `just-flipped.jpg` shows the transient: larger, irregular blobs and a messier stream before it settles into the regular drip.

## What I mean by real fluid dynamics

The behaviour should come out of a simulation, not out of keyframes or per-drop scripted paths. If I change a parameter, or flip the toy halfway through, the right thing should happen without a special case. Specifically, these should emerge from the model:

- Surface tension between the dyed liquid and the oil: drops round off, necks form and pinch, and blobs resist merging then snap together.
- Buoyancy-driven sinking through a viscous surrounding fluid, giving a near-constant fall speed that depends on drop size.
- Drip rate driven by the head of liquid above the nozzle, so dripping slows as the reservoir empties and stops when it is empty.
- Volume conservation per colour: what leaves the top arrives at the bottom, and levels change accordingly.
- Drops deforming against the ramp and walls, sliding under gravity, and coalescing after a delay rather than instantly.
- The two chambers as two independent simulations that only interact visually, through the colour overlap.

Choosing the method is your call, and I would like you to weigh the options before committing: particle approaches (SPH or position-based fluids with a smooth surface reconstruction), grid approaches (multiphase lattice Boltzmann, phase-field or level-set on a GPU), or something else. What matters is that pinch-off, coalescence and volume conservation are believable at interactive frame rates, and that the rendered drops have clean, crisp silhouettes like the photos rather than a visibly blobby or grainy particle look. Physical constants do not need to be the real-world values; tune dimensionless behaviour until it matches the footage. Say plainly in the README what is physically modelled and what is approximated or faked.

## Constraints

- Plain HTML, CSS and JavaScript with no build step and no dependencies, so that opening `liquid-hourglass/index.html` directly works. Canvas 2D, WebGL or WebGPU are all fine; if you use WebGPU, include a fallback, since not every browser I use has it.
- It should hold 60 fps on a recent laptop and stay usable on a phone.
- Tapping or clicking the hourglass flips it. The flip should be a visible rotation with gravity staying world-down throughout, so the liquid responds during the turn rather than being reset.
- Draw the acrylic body too: the waisted outline, thick clear walls, soft highlights and the trapped air bubbles. Keep the background plain and neutral; do not recreate my kitchen.
- Respect `prefers-reduced-motion` by starting paused with a visible play control.
- Other folders in this repo are unrelated projects. Leave them alone.

## How to work

Start by studying the reference stills and writing down, briefly, the method you chose and why. Then get the physics right in a bare debug rendering before spending any time on the glass and lighting: a single chamber dripping convincingly is the hard part and everything else depends on it.

Verify by looking, not by reasoning about the code. Chromium and Playwright are available: load the page headlessly, capture screenshots at several moments (and short frame sequences like my 12 fps strip), and compare them side by side with the reference stills. Check each of the behaviours listed above explicitly, including a mid-run flip and a full run until the top is empty. Keep iterating until the comparison holds up; expect that to take many rounds of tuning. If headless rendering differs from a real GPU (for example software WebGL), say so and tell me what I need to check by eye.

When you are done, commit and push to the current branch and give me:

- A short account of what matches the footage well and what does not yet, with screenshots.
- The tuning parameters that most affect the look, and where they live.
- Anything you faked, stated as such.

---
published: 2026-09-25
updated: 2026-09-25
tags: generative
---

# Marimba navigator

A playable marimba that lights up cards as you play: thirteen bars (E♭4–E♭5) colored by scale degree in the key you pick, a synthesized marimba note on every hit, and cards for the tonic, mediant, dominant and leading tone that pulse when you play their degree.

## Playing it

Tap or click a bar, drag across bars for a glissando, or use the keyboard: Q–I play the bars left to right (A S D F G H J for the front row, Q E R T U I for the back). Pick a key and major/minor to recolor the bars; bars outside the key stay neutral.

## Running it

No build step. Serve the folder and open it:

```bash
python3 -m http.server 5175 --directory marimba
```

## How it works

- `index.html` — the page title, the four scale-degree cards, the key and mode controls, the secret-melody control, an empty marimba frame, and the hidden card's dialog
- `styles.css` — color tokens (OKLCH) and layout; each scale degree's color is `--deg-1` … `--deg-7`
- `marimba.js` — bar data and geometry, key/mode state, the Web Audio synth, pointer/keyboard input, and the easter egg. It also keeps each card's degree name (e.g. *Leading tone*, or *Subtonic* in minor), its interval above the tonic, and its note in the current key in step with the controls

The bars sit in an 8 × 5 frame that scales with the viewport height: naturals in front, accidentals behind, each semitone 2^(−1/24) shorter than the last. The synth layers a sine fundamental with the two overtones a marimba bar is tuned to (4× and ~10×) over a short noise burst for the mallet. `SETTINGS` at the top of `marimba.js` mirrors the design's tweakable props: note names, degree numbers, and decay length.

## Easter egg (spoiler)

Play E♭ – G – B♭ – E♭ from low to high, which is 1, 3, 5, 1 in E♭ major (the key the page opens in), and a hidden fifth card unlocks: **8 · Do**, the *Octave* that completes the arpeggio. The card opens in a dialog, and afterwards the ✓ button reopens it.

Visitors who don't know the melody can use the **Secret melody** control next to Major/Minor. It works like a "verify you're human" check, but with sound:

- **▶ plays the melody** through the same synth as the bars, so it can be matched by ear.
- **Each bar lights up with a high-contrast ring as its note sounds**, so it can also be matched by eye, with the sound off or for visitors who can't hear it. The matching cards pulse too.
- **The dots fill as the visitor plays it back.** A wrong note resets them.
- **The status next to the dots is a live region.** Screen readers hear each step, and once the melody finishes they also hear its notes and keys ("E flat, G, B flat, E flat (keys Q, D, T, I)").
- **Everything works from the keyboard.** While the dialog is open, keys stop playing the marimba.

The melody is `SECRET` in `marimba.js` (bar indexes into `BARS`), and the hidden card is the `<dialog>` at the end of `index.html`. The melody uses fixed pitches rather than scale degrees because E♭ is the only key where both 1s fit on the 13 bars. The melody is therefore the same whichever key is selected, and playing it without the demo unlocks the card too.

## From Claude Design to code

This page was designed in [Claude Design](https://claude.ai/design) — file `Marimba Flat.dc.html` in the project [Virtual Marimba Styles](https://claude.ai/design/p/5d0f7a80-e825-4220-b1f2-4a7b0d0c09d4), whose 3D variant was dropped — and built here by Claude Code from a handoff. The design is a portfolio page; for the playground, its name, nav and project cards became a page title and cards for the scale degrees. To take a design of your own down the same path:

### 1. Design it in Claude Design

Start a project at [claude.ai/design](https://claude.ai/design) and describe the page. Claude Design saves each design as a `.dc.html` file: an HTML template with `{{ }}` bindings, a `class Component extends DCLogic` script that holds state and behavior, and tweakable props that show up as controls in the editor (here: note names, degree numbers, and decay). `support.js` is the runtime that renders them in the browser.

To start from this design, here's a brief that describes it (it isn't the original prompt):

> Design a personal portfolio homepage with a playable marimba. Header: name on the left, Work / About / Notes / Contact on the right. Four slightly tilted project cards, each tagged with a scale degree (1 Do, 3 Mi, 5 Sol, 7 Ti) in that degree's color. Below them: a key picker, a Major/Minor toggle, and 13 bars from E♭4 to E♭5 — naturals in front, accidentals behind, bars shortening as the pitch rises, all resting on rails. Color in-key bars by scale degree, label each bar with its degree and note name, and leave out-of-key bars neutral. Hitting a bar plays a synthesized marimba note and pulses the card for its degree. Support tap, click, dragging across bars, and keys Q–I. Warm off-white palette; Fredoka for headings, DM Sans for body text.

### 2. Connect Claude Code to Claude Design (once per machine)

In a terminal, run `claude` to start an interactive Claude Code session, then type `/design-login` and follow the sign-in. That lets Claude Code read your Claude Design projects, and sessions that can't run the command themselves — the Claude desktop app's Code tab, headless and SDK runs — reuse the authorization.

In Claude Code on the web (claude.ai/code), skip this step: use Claude Design's **Send to Claude Code Web**, which copies the project files into the session's workspace.

### 3. Hand the design off

Claude Design's handoff to Claude Code gives you a prompt. Open Claude Code in the folder the code should live in (here, `marimba/`) and paste it. This is the one used for this project:

```text
Use the claude_design MCP (https://api.anthropic.com/v1/design/mcp, auth via /design-login) to import this project:
https://claude.ai/design/p/5d0f7a80-e825-4220-b1f2-4a7b0d0c09d4?file=Marimba+Flat.dc.html

Focus on these files (the whole project is readable):
- `Marimba Flat.dc.html`

Also read these files the selection imports:
- `support.js`

Implement: `Marimba Flat.dc.html`
```

If Claude Code can't reach the project (usually because step 2 hasn't been done), download the handoff bundle from Claude Design instead: a zip with a README for coding agents plus the project files (`Virtual Marimba Styles-handoff.zip` here). Put it in the folder and tell Claude Code which file to implement. Delete the zip once the work is done, because everything committed in the folder is published to GitHub Pages.

### 4. Implement, preview, and list it

Claude Code reads the `.dc.html` file in full plus what it imports, then rebuilds the design for the target — here plain HTML/CSS/JS, so GitHub Pages can serve it without a build step. Where each part of the design ended up:

| In `Marimba Flat.dc.html` | In this folder |
|---|---|
| `<x-dc>` template, with fonts and base styles in `<helmet>` | `index.html`, `styles.css` |
| Inline `oklch()` colors and the `DEG` palette | CSS variables in `styles.css` (`--deg-1` … `--deg-7`) |
| `Component`: `state`, `renderVals()`, `hit()`, key and pointer handlers | `marimba.js`: `state`, `render()`, `hit()`, the same handlers |
| `Synth` class | `Synth` in `marimba.js`, same sound |
| Tweakable props `showNoteNames`, `showDegrees`, `decay` | `SETTINGS` in `marimba.js` |

Along the way it fixed three input quirks of the prototype: a phone's first tap could be silent, a drag starting on a bar's label didn't glide onto other bars, and releasing the mouse outside the window left bars playing on hover.

To check the result, `.claude/launch.json` starts a local server on port 5175 that the Claude desktop app opens in its browser pane. To list the project in the root README, give this README its frontmatter and run `node scripts/build-readme.js` from the repo root.

## Claude

Built with [Claude](https://claude.ai) (claude-opus-5-5) in one session on September 25, 2026, in five passes:

1. **Implementation**: read the design and its runtime, rebuilt the page as static HTML/CSS/JS, checked it in a browser (layout, key spelling, keyboard, click and drag input, card pulses), and wrote this README.
2. **Walkthrough**: added the Claude Design section above.
3. **Commit and pull request**: committed the project and opened the pull request.
4. **Easter egg**: the secret melody, its audio-and-visual demo, and the hidden card's dialog, checked in the browser (demo timing, playback progress and resets, unlocking, reopening, closing, desktop layout).
5. **Playground framing**: swapped the portfolio name, nav and project cards for a page title and scale-degree cards that follow the key and mode. The hidden card became the *Octave*.

| Created | Tool | Model | Estimated energy consumption[^claude] | Estimated carbon emissions | Estimated water usage |
|---|---|---|---|---|---|
| September 25, 2026 | Claude Code | claude-opus-5-5 | 0.828 kWh | 0.320 kg CO₂ | 0.414 L |
| September 25, 2026 | Claude Code | claude-opus-5-5 | 0.054 kWh | 0.021 kg CO₂ | 0.027 L |
| September 25, 2026 | Claude Code | claude-opus-5-5 | 0.144 kWh | 0.056 kg CO₂ | 0.072 L |
| September 25, 2026 | Claude Code | claude-opus-5-5 | 0.216 kWh | 0.083 kg CO₂ | 0.108 L |
| September 25, 2026 | Claude Code | claude-opus-5-5 | 0.234 kWh | 0.090 kg CO₂ | 0.117 L |
| September 2026 | Claude Design | (unknown) | not measurable from here | — | — |

[^claude]: assuming 18 Wh per model API request; does not include estimate for foundation model training. The Claude Code rows are the five passes above. They count the API requests measured in the local session transcript: 46, 3, 8, 12, and 13, where the 13 include this README edit and the reply after it. That's ≈ 19M tokens in all, about 97% of them cache reads.

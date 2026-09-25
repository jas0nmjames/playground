---
published: 2026-09-25
updated: 2026-09-25
tags: generative
---

# Marimba

A playable marimba for a portfolio homepage: thirteen bars (E♭4–E♭5) colored by scale degree in the key you pick, a synthesized marimba note on every hit, and project cards that pulse when you play their degree (do, mi, sol, ti).

## Playing it

Tap or click a bar, drag across bars for a glissando, or use the keyboard: Q–I play the bars left to right (A S D F G H J for the front row, Q E R T U I for the back). Pick a key and major/minor to recolor the bars; bars outside the key stay neutral.

## Running it

No build step. Serve the folder and open it:

```bash
python3 -m http.server 5175 --directory marimba
```

## How it works

- `index.html` — header, the four project cards, the key and mode controls, and an empty marimba frame
- `styles.css` — color tokens (OKLCH) and layout; each scale degree's color is `--deg-1` … `--deg-7`
- `marimba.js` — bar data and geometry, key/mode state, the Web Audio synth, and pointer/keyboard input

The bars sit in an 8 × 5 frame that scales with the viewport height: naturals in front, accidentals behind, each semitone 2^(−1/24) shorter than the last. The synth layers a sine fundamental with the two overtones a marimba bar is tuned to (4× and ~10×) over a short noise burst for the mallet. `SETTINGS` at the top of `marimba.js` mirrors the design's tweakable props: note names, degree numbers, and decay length.

## From Claude Design to code

This page was designed in [Claude Design](https://claude.ai/design) — file `Marimba Flat.dc.html` in the project [Virtual Marimba Styles](https://claude.ai/design/p/5d0f7a80-e825-4220-b1f2-4a7b0d0c09d4), whose 3D variant was dropped — and built here by Claude Code from a handoff. To take a design of your own down the same path:

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

Implemented from the Claude Design handoff with [Claude](https://claude.ai) (claude-opus-5-5) on September 25, 2026: read the design and its runtime, rebuilt the page as static HTML/CSS/JS, checked it in a browser (layout, key spelling, keyboard, click and drag input, card pulses), and wrote this README. A second pass the same day added the Claude Design walkthrough above.

| Created | Tool | Model | Estimated energy consumption[^claude] | Estimated carbon emissions | Estimated water usage |
|---|---|---|---|---|---|
| September 25, 2026 | Claude Code | claude-opus-5-5 | 0.828 kWh | 0.320 kg CO₂ | 0.414 L |
| September 25, 2026 | Claude Code | claude-opus-5-5 | 0.054 kWh | 0.021 kg CO₂ | 0.027 L |
| September 2026 | Claude Design | (unknown) | not measurable from here | — | — |

[^claude]: assuming 18 Wh per model API request; does not include estimate for foundation model training. The Claude Code rows count API requests from the local session transcript: 46 for the implementation (≈ 7.7M tokens, 96% of them cache reads) and 3 for the walkthrough.

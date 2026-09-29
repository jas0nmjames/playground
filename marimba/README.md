---
published: 2026-09-25
updated: 2026-09-29
tags: generative
---

# Marimba navigator

A playable three-octave marimba (C3–C6) that lights up cards as you play: bars colored by scale degree in the key you pick, one octave in view at a time, a synthesized marimba note on every hit, and cards for the tonic, mediant, dominant and leading tone that pulse when you play their degree.

## Playing it

Tap or click a bar, or drag across bars for a glissando. One octave shows at a time: drag, flick or tap the strip under the marimba to move between the C3, C4 and C5 octaves, or scroll sideways with a trackpad.

On a keyboard, the home row plays the octave in view like a piano: A S D F G H J K, then L ; ', with sharps and flats on the row above (W E, T Y U, O P). Z X or ← → change octave. Pick a key and major/minor to recolor the bars; bars outside the key stay neutral.

## Running it

No build step. Serve the folder and open it:

```bash
python3 -m http.server 5175 --directory marimba
```

## How it works

- `index.html` — the page title, the four scale-degree cards, the key and mode controls, the secret-melody control, the marimba's scroller and scrub strip, the footer, and the hidden card's dialog
- `styles.css` — color tokens (OKLCH), type and layout; each scale degree's color is `--deg-1` … `--deg-7`
- `marimba.js` — bar data and geometry, key/mode state, the Web Audio synth, pointer and keyboard input, octave scrolling, the easter egg, and the footer's per-visit carbon figure. It also keeps each card's degree name (e.g. *Leading tone*, or *Subtonic* in minor), its interval above the tonic, and its note in the current key in step with the controls
- `assets/claude-symbol.svg` — the Claude logo in the footer's credit (CC0, from [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Claude_AI_symbol.svg))

The marimba is 22 naturals wide. The scroller shows 8 of them, one octave from C to C, in an 8 × 5 window that scales with the viewport height, and snaps to the C3, C4 or C5 octave. Naturals sit in front and accidentals behind, each octave 2^(−1/3) as long as the one below, and the rails bend through every bar's nail holes. The strip under the scroller is a minimap of all three octaves. When a bar that's cut off or off screen is played, the view moves to the nearest octave that shows it whole.

The synth layers a sine fundamental with the two overtones a marimba bar is tuned to (4× and ~10×) over a short noise burst for the mallet. `SETTINGS` at the top of `marimba.js` mirrors the design's tweakable props: note names, degree numbers, and decay length.

The title is set in Bungee and everything else in Readex Pro. Neither has ♭ or ♯, so Noto Music supplies them, loaded as just those two glyphs. Readex Pro has no italic, so italic text is a synthesized oblique.

The footer credits the page and estimates its environmental impact: a one-time figure for making it, and a per-visit figure from [Website Carbon](https://www.websitecarbon.com)'s API, cached in the browser for a day. If Website Carbon fails (its API has been answering 503 since late September 2026) or takes over 10 seconds, the page estimates the figure itself from its own download size, using Website Carbon's formula, and says so. It remembers each file's size in the browser, because a file the browser only revalidates reports just its headers; that way every visit estimates the same page. The estimate itself isn't cached, so the next visit asks Website Carbon again. The one-time figure is the total from the table below.

## Easter egg (spoiler)

Play C – E – G – C from middle C (C4) up to C5, which is 1, 3, 5, 1 in C major (the key the page opens in), and a hidden fifth card unlocks: **8 · Do**, the *Octave* that completes the arpeggio. The card opens in a dialog, and afterwards the ✓ button reopens it.

Visitors who don't know the melody can use the **Secret melody** control next to Major/Minor. It works like a "verify you're human" check, but with sound:

- **▶ plays the melody** through the same synth as the bars, so it can be matched by ear. If the middle octave isn't in view, the marimba scrolls to it as the melody plays.
- **Each bar lights up with a high-contrast ring as its note sounds**, so it can also be matched by eye, with the sound off or for visitors who can't hear it. The matching cards pulse too.
- **The dots fill as the visitor plays it back.** A wrong note resets them.
- **The status next to the dots is a live region.** Screen readers hear each step, and once the melody finishes they also hear its notes and keys ("C, E, G, C (from the middle octave, keys A, D, G, K)").
- **Everything works from the keyboard.** While the dialog is open, keys stop playing the marimba.

The melody is `SECRET` in `marimba.js` (bar indexes into `BARS`), and the hidden card is the `<dialog>` at the end of `index.html`. The melody is fixed pitches (C4 E4 G4 C5), so it's the same whichever key is selected, and playing it without the demo unlocks the card too.

## From Claude Design to code

This page was designed in [Claude Design](https://claude.ai/design) and built here by Claude Code from two handoffs. The first was `Marimba Flat.dc.html` in the project [Virtual Marimba Styles](https://claude.ai/design/p/5d0f7a80-e825-4220-b1f2-4a7b0d0c09d4), a portfolio page whose 3D variant was dropped. The playground framing and the easter egg were then built in code and carried back into Claude Design, which added the three-octave marimba, the footer and the current type in `Marimba Navigator v2.dc.html`. To take a design of your own down the same path:

### 1. Design it in Claude Design

Start a project at [claude.ai/design](https://claude.ai/design) and describe the page. Claude Design saves each design as a `.dc.html` file: an HTML template with `{{ }}` bindings, a `class Component extends DCLogic` script that holds state and behavior, and tweakable props that show up as controls in the editor (here: note names, degree numbers, and decay). `support.js` is the runtime that renders them in the browser.

To start from this design, here's a brief that describes the first version (it isn't the original prompt):

> Design a personal portfolio homepage with a playable marimba. Header: name on the left, Work / About / Notes / Contact on the right. Four slightly tilted project cards, each tagged with a scale degree (1 Do, 3 Mi, 5 Sol, 7 Ti) in that degree's color. Below them: a key picker, a Major/Minor toggle, and 13 bars from E♭4 to E♭5 — naturals in front, accidentals behind, bars shortening as the pitch rises, all resting on rails. Color in-key bars by scale degree, label each bar with its degree and note name, and leave out-of-key bars neutral. Hitting a bar plays a synthesized marimba note and pulses the card for its degree. Support tap, click, dragging across bars, and keys Q–I. Warm off-white palette; Fredoka for headings, DM Sans for body text.

### 2. Connect Claude Code to Claude Design (once per machine)

In a terminal, run `claude` to start an interactive Claude Code session, then type `/design-login` and follow the sign-in. That lets Claude Code read your Claude Design projects, and sessions that can't run the command themselves — the Claude desktop app's Code tab, headless and SDK runs — reuse the authorization.

In Claude Code on the web (claude.ai/code), skip this step: use Claude Design's **Send to Claude Code Web**, which copies the project files into the session's workspace.

### 3. Hand the design off

Claude Design's handoff to Claude Code gives you a prompt. Open Claude Code in the folder the code should live in (here, `marimba/`) and paste it. This is the one used for the first version:

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

| In the `.dc.html` design | In this folder |
|---|---|
| `<x-dc>` template, with fonts and base styles in `<helmet>` | `index.html`, `styles.css` |
| Inline `oklch()` colors and the `DEG` palette | CSS variables in `styles.css` (`--deg-1` … `--deg-7`) |
| `Component`: `state`, `renderVals()`, `hit()`, key and pointer handlers | `marimba.js`: `state`, `render()`, `hit()`, the same handlers |
| `Synth` class | `Synth` in `marimba.js`, same sound |
| Tweakable props `showNoteNames`, `showDegrees`, `decay` | `SETTINGS` in `marimba.js` |

Along the way it fixed three input quirks of the prototype: a phone's first tap could be silent, a drag starting on a bar's label didn't glide onto other bars, and releasing the mouse outside the window left bars playing on hover.

To check the result, `.claude/launch.json` starts a local server on port 5175 that the Claude desktop app opens in its browser pane. To list the project in the root README, give this README its frontmatter and run `node scripts/build-readme.js` from the repo root.

### 5. Bring code changes back, then hand off again

Claude Code can't write your changes back into a design project: its Claude Design connector only syncs design-system projects. So the changes go back through Claude Design's chat. Attach `index.html`, `styles.css` and `marimba.js` and ask Claude to update the design to match them, keeping the original as it was:

```text
The attached index.html, styles.css and marimba.js are Marimba Flat.dc.html as built in Claude Code, with changes made there. Create Marimba Navigator.dc.html from Marimba Flat.dc.html so it matches the attached code, and leave Marimba Flat.dc.html unchanged. Keep the showNoteNames, showDegrees and decay props (SETTINGS in marimba.js).

Changes to bring over:
1. …one line per change, with the exact values…
```

Keep designing there, then hand off again. The second handoff here was a bundle: `Marimba Navigator v2.dc.html`, its `support.js`, and a README that lists each change relative to the live code with exact values. That made the second pass a diff rather than a rebuild. Claude Code implemented it in the existing HTML/CSS/JS, as the README asked, then compared the result with the reference in a browser; the bars, rails, strip and footer matched it to the tenth of a pixel. One rule was changed on purpose. The spec centered any played bar within 24px of an edge, but every octave view has a C at each edge, so that made the view jump between octaves mid-melody. Instead, only a bar that's cut off or off screen moves the view.

## Claude

Built with [Claude](https://claude.ai) (claude-opus-5-5) in one session, September 25–29, 2026, in nine passes:

1. **Implementation**: read the design and its runtime, rebuilt the page as static HTML/CSS/JS, checked it in a browser (layout, key spelling, keyboard, click and drag input, card pulses), and wrote this README.
2. **Walkthrough**: added the Claude Design section above.
3. **Commits and pull request**: committed and pushed the work in two rounds, opened the pull request, and kept its description current.
4. **Easter egg**: the secret melody, its audio-and-visual demo, and the hidden card's dialog, checked in the browser (demo timing, playback progress and resets, unlocking, reopening, closing, desktop layout).
5. **Playground framing**: swapped the portfolio name, nav and project cards for a page title and scale-degree cards that follow the key and mode. The hidden card became the *Octave*.
6. **Typography**: re-set the page like a printed score in Bodoni Moda. Replaced by the design's own type in pass 8 before it shipped.
7. **Round trip**: explained how to bring the code changes back into Claude Design, with a prompt for it.
8. **Design v2**: implemented the second handoff (Bungee and Readex Pro, the footer, the three-octave scrolling marimba with its scrub strip, piano keys, C major, and the new secret melody), saved the Claude logo, compared the build with the reference in a browser, tested input, octave scrolling and the footer's states, and updated this README.
9. **Usage and carbon fallback**: recounted the whole project's usage from the session transcripts, which moved one request from pass 5 to pass 6, put the same total in the page's footer, added a local fallback for the per-visit carbon figure, then committed it all and opened the pull request.

| Created | Tool | Model | Estimated energy consumption[^claude] | Estimated carbon emissions | Estimated water usage |
|---|---|---|---|---|---|
| September 25, 2026 | Claude Code | claude-opus-5-5 | 0.828 kWh | 0.320 kg CO₂ | 0.414 L |
| September 25, 2026 | Claude Code | claude-opus-5-5 | 0.054 kWh | 0.021 kg CO₂ | 0.027 L |
| September 25, 2026 | Claude Code | claude-opus-5-5 | 0.198 kWh | 0.076 kg CO₂ | 0.099 L |
| September 25, 2026 | Claude Code | claude-opus-5-5 | 0.216 kWh | 0.083 kg CO₂ | 0.108 L |
| September 25, 2026 | Claude Code | claude-opus-5-5 | 0.216 kWh | 0.083 kg CO₂ | 0.108 L |
| September 25, 2026 | Claude Code | claude-opus-5-5 | 0.252 kWh | 0.097 kg CO₂ | 0.126 L |
| September 29, 2026 | Claude Code | claude-opus-5-5 | 0.054 kWh | 0.021 kg CO₂ | 0.027 L |
| September 29, 2026 | Claude Code | claude-opus-5-5 | 0.972 kWh | 0.375 kg CO₂ | 0.486 L |
| September 29, 2026 | Claude Code | claude-opus-5-5 | 0.378 kWh | 0.146 kg CO₂ | 0.189 L |
| **Total** | Claude Code | claude-opus-5-5 | **3.168 kWh** | **1.223 kg CO₂** | **1.584 L** |
| September 2026 | Claude Design | (unknown) | not measurable from here | — | — |

[^claude]: assuming 18 Wh per model API request; does not include estimate for foundation model training. The Claude Code rows are the nine passes above. They count the API requests measured in the local session transcripts: 46, 3, 11, 12, 12, 14, 3, 54, and 21, where the 21 include the commit, the pull request and the reply after them. That's 176 requests and ≈ 61M tokens in all, about 97% of them cache reads. The page's footer shows the same total, rounded. Claude Design's requests can't be counted from here, so neither figure includes them.

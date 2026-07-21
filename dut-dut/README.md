---
published: 2026-07-20
updated: 2026-07-21
---

# dut dut

A web-based app to annotate, create, and preview drumline cadences. Paint hits, accents, flams, diddles, and buzz rolls onto a per-voice grid (cymbal, snare, 6 tenors, 5 basses) across multiple named sections; see the pattern render as percussion staff notation; preview it with a synthesized drumline; and export it as MIDI, WAV audio, or a score image. Work autosaves in the browser and can be saved/loaded as a JSON project file.

## Getting started

```bash
cd dut-dut
npm install
npm run dev     # opens http://localhost:5174
```

To ship it:

```bash
npm run build   # outputs a self-contained dist/ with relative paths
```

`dist/` deploys anywhere static files are served — `netlify.toml` is included (same setup as `terminal-velocity`), and `base: './'` in [vite.config.js](vite.config.js) means the build also works from a subfolder or GitHub Pages without changes.

## How it works

React 19 + Vite. One class component owns all state; everything else is presentational or pure.

- `src/App.jsx` — all state and actions (sections, notes, painting, transport, save/load/export), mirroring the Claude Design source almost line-for-line
- `src/components/BlocksPanel.jsx` — the editable step grid: tool buttons, subdivision ruler (16th → triplet → 8th per beat), drag-to-paint cells
- `src/components/StaffPanel.jsx` — percussion staff notation as SVG, with playhead
- `src/components/SettingsDrawer.jsx` — tempo, metronome, swing, mutes, section management, project save/load, exports
- `src/staff.js` — pure staff-geometry function (noteheads, stems, beams, flags, tuplets, accents, grace notes, buzz z's); shared by the on-screen SVG staff and the PNG export
- `src/audio-engine.js` — synthesized drum voices (oscillators + filtered noise) and a variable-duration lookahead scheduler, so beats can mix 16th/triplet/8th subdivisions in one loop
- `src/export-utils.js` — MIDI file writer, offline WAV renderer, score-PNG renderer, download helper
- `src/constants.js` — instrument/tool definitions, project validation (`normalizeProject`)

Audio and export code load on demand (dynamic `import()`), so Vite splits them into separate chunks — the initial page load doesn't include them.

## Attribution, licenses & copyright

Things to know about what this project contains and depends on:

- **This repo's license**: the playground repo is licensed [MPL-2.0](../LICENSE); this project inherits that unless you decide otherwise.
- **React & ReactDOM** (MIT, © Meta Platforms) and **Vite / @vitejs/plugin-react** (MIT) — permissive; the production bundle includes React, and bundlers preserve the required license notices. Nothing further to do.
- **Fonts**: [Atkinson Hyperlegible](https://www.brailleinstitute.org/freefont/) (© Braille Institute of America) and [IBM Plex Mono](https://github.com/IBM/plex) (© IBM) — both SIL Open Font License 1.1, loaded at runtime from Google Fonts, not bundled. If you ever self-host them, keep their OFL license files alongside. Privacy note: loading from Google Fonts sends visitor IPs to Google — a GDPR consideration if EU traffic matters to you; self-hosting avoids it. The staff/score rendering also names **Georgia** in font stacks — it's a system font that is referenced, not distributed, which is fine.
- **Audio scheduling pattern**: the lookahead scheduler follows Chris Wilson's ["A Tale of Two Clocks"](https://web.dev/articles/audio-scheduling) approach — a well-known public technique; attribution here is a courtesy, not a legal requirement.
- **MIDI mapping**: note numbers follow the General MIDI percussion map — an open spec, no license concerns.
- **Music notation conventions** (staff lines, flam/diddle/buzz symbols, tuplet marks) are not copyrightable — no concerns there.
- **Reference material caution**: the Claude Design project this app was built from contains an uploaded PDF (`2016 Part 1.pdf`) that appears to be real drumline sheet music. It is not in this repo — keep it that way unless you hold the rights to redistribute it. Cadences you *transcribe* from copyrighted arrangements and export/publish from this app could also raise rights questions; your own original patterns are yours.
- **AI authorship**: the design and code were generated with Claude (see below). Under Anthropic's terms, the outputs belong to you. One nuance worth knowing: purely AI-generated material may not qualify for copyright protection in some jurisdictions (per current US Copyright Office guidance, human authorship is required), which can matter if you ever want to enforce a license on this code.

## Claude

Built with Claude across three passes, all in July 2026:

1. **Scaffold** (July 20, claude-sonnet-5) — initial Vite + vanilla-JS project with a canvas step grid and Web Audio playback.
2. **Design import** (July 20, claude-sonnet-5) — full app implemented from the Claude Design project `Drumline App v2.dc.html`, ported to vanilla JS with a hand-rolled DOM layer.
3. **React rewrite from updated design** (July 20–21, claude-fable-5) — the design gained project save/load, localStorage autosave, and MIDI/WAV/PNG export; the app was reimplemented in React 19 (the design source is written as a React-style class component, so the port is nearly line-for-line) and the vanilla DOM layer, its focus-preservation workaround, and a drawer-transform workaround were all deleted. Design artifacts (`app` logic, `audio-engine.js`, `export-utils.js`, staff-geometry algorithm) come from the [Claude Design project](https://claude.ai/design/p/71d60cb1-de19-4900-b73f-0eb03a2a3519); Jason designed and iterated the app there.

### Consumption

| Created | Tool | Model | Estimated energy consumption[^claude] | Estimated carbon emissions | Estimated water usage |
|---|---|---|---|---|---|
| July 20, 2026 | Claude Code | claude-sonnet-5 | 0.018 kWh | 0.007 kg CO₂ | 0.009 L |
| July 20, 2026 | Claude Code | claude-sonnet-5 | 0.756 kWh | 0.292 kg CO₂ | 0.378 L |
| July 20–21, 2026 | Claude Code | claude-fable-5 | 2.232 kWh | 0.861 kg CO₂ | 1.116 L |
| July 2026 | Claude Design | (unknown) | not measurable from here | — | — |

[^claude]: assuming 18 Wh per model API request; does not include estimate for foundation model training. Rows use the request counts from the measured token usage below (1, 42, and 124 requests respectively).

### Token usage

Measured from the local Claude Code session transcripts for this project (one session, 9 user prompts, 167 API requests, July 20–21 2026):

| Category | Tokens |
|---|---|
| Input (uncached) | 327 |
| Cache creation | 1,019,468 |
| Cache read | 35,210,930 |
| Output | 224,716 |
| **Total** | **≈ 36.5M** |

Almost all of it is cache *reads* — the conversation context re-read on each of the 167 requests — which is far cheaper (in both cost and energy) than uncached input. The count excludes the final README-writing requests of the last session.

**Claude Design usage is not measurable from this machine** — the claude.ai/design service doesn't expose per-project token counts. As a floor estimate: the four generated artifacts total ≈ 103 KB of code (≈ 29K output tokens) if each had been generated exactly once; with design iteration, realistic totals are plausibly 100K–500K output tokens plus a few million context-input tokens, depending on how many revisions were run. Your claude.ai account usage page (if your plan shows it) is the authoritative source.

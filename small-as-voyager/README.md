---
published: 2026-04-22
updated: 2026-11-20
status: done
---

# Small as Voyager

A one-page portfolio small enough to fit in Voyager's memory: about 5.5 KB of hand-written HTML and CSS, with no scripts, web fonts or images, ending in a line drawing of the spacecraft.

## The idea

Each Voyager spacecraft flies with about 70 KB of memory in all. This page is one file of about 5.5 KB (about 2.4 KB gzipped), so roughly thirteen copies of it would fit. The budget shapes everything: the system font stack instead of web fonts, one blue accent, and an inline SVG for the only picture.

## Running it

No build step. Serve the folder and open it:

```bash
python3 -m http.server 5176 --directory small-as-voyager
```

`.claude/launch.json` starts the same server for the Claude desktop app's browser pane.

## How it works

- `index.html` is the whole page: About, Selected Work, Contact, and a footer, with the styles inline in `<head>`.
- The Voyager drawing is an inline SVG at the end of the page. It's a side-view schematic, not to scale: the 3.7 m high-gain antenna dish, the ten-sided bus, the boom with the three RTGs (the radioisotope generators that power it), the scan platform, the low-gain antenna (LGA) and the dashed magnetometer boom.

## Claude

The page was drafted with Claude Code in April 2026 and left as an untracked file inside a stray worktree. That session's transcript is gone, so its usage can't be counted. In November 2026, [Claude](https://claude.ai) (claude-opus-5-5) found the draft, removed the stray worktree, made the draft this project, moved two drawing labels that overlapped the dish and the RTG boom, corrected the size in the caption (it said ~5 KB and 1/14th), checked the page in a browser at desktop and phone widths, and wrote this README.

| Created | Tool | Model | Estimated energy consumption[^claude] | Estimated carbon emissions | Estimated water usage |
|---|---|---|---|---|---|
| April 2026 | Claude Code | (unknown) | not measurable from here | — | — |
| November 20, 2026 | Claude Code | claude-opus-5-5 | 0.594 kWh | 0.229 kg CO₂ | 0.297 L |

[^claude]: assuming 18 Wh per model API request; does not include estimate for foundation model training. The November row counts the 33 API requests in that session's local transcript, including the commit and the merge into `development`.

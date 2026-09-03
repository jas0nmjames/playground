---
published: 2026-09-03
updated: 2026-09-03
tags: generative
---

# TI-83+ Emulated Portfolio

A TI-83 Plus graphing calculator emulator with a working TI-BASIC interpreter, hosting a portfolio that lives entirely inside the calculator. `PORTFOLIO` runs on power-on; you navigate it the way you'd navigate any TI-BASIC program — number keys, arrows, and `ENTER` to clear a `Pause`.

## Running it

```bash
npm install
npm run dev      # http://localhost:5173
npm run build
```

## What's actually emulated

**Display.** A true 16&times;8 character grid with the hardware's scroll
semantics — there is no scrollback buffer, so writing past the last row shifts
everything up by one. `Disp` left-aligns strings and right-aligns numbers.
The graph screen is a separate 96&times;64 one-bit framebuffer, upscaled with
`image-rendering: pixelated`.

**Expressions.** Source is tokenized and parsed into an AST by a
recursive-descent parser, then evaluated. Implicit multiplication works
(`2X`, `3(X+1)`, `Asin(B)`) and binds at the same precedence as an explicit
`*` — the TI-83+ rule, so `1/2X` is `(1/2)*X`. Numbers format to 10
significant digits, drop the leading zero below 1 (`.5`, not `0.5`), and
switch to scientific notation outside `[1e-3, 1e10)`.

**TI-BASIC.** Programs compile to a flat instruction array with jump targets
resolved in a linking pass, executed against a program counter. That shape —
rather than a tree walk — is what makes `Goto`/`Lbl` work, and `Goto` is
load-bearing because `Menu(` dispatches to labels.

Implemented: `Disp`, `Output(`, `Pause`, `ClrHome`, `Input`, `Prompt`,
`Menu(`, `Lbl`/`Goto`, `If`/`Then`/`Else`/`End` (including the single-line
form), `For(`/`End`, `While`/`End`, `Repeat`/`End`, `Stop`, `Return`,
`DelVar`, `getKey`, stores to `A`–`Z`, `Str1`–`Str9` and `Y1`–`Y9`.

**Blocking without blocking.** The interpreter is a generator that yields
effects the host services — `pause`, `input`, `menu`, plus a periodic `tick`
so a runaway loop can't lock the tab. The React host resumes it with the
user's answer. This is why `Input` and `Menu(` can suspend mid-program
without callbacks or `async` plumbing.

**Graphing.** `Y=` editor for `Y1`–`Y9`, `WINDOW` for the viewport, `ZOOM`
with ZStandard/ZSquare/ZTrig/ZDecimal/in/out, `GRAPH`, and `TRACE` with a
per-pixel cursor and live X/Y readout. Functions are sampled once per pixel
column and connected with Bresenham segments — the same approach the hardware
takes, which is why a pole in `tan(X)` draws a near-vertical connector rather
than a clean break.

**Keypad.** The full TI-83+ layout at the correct grid positions, with `2nd`
and `ALPHA` modifiers and the real A–Z letter assignments (`MATH`=A,
`APPS`=B, … `STO▸`=X, `1`=Y, `2`=Z). The physical keyboard is wired to the
same dispatcher.

## Layout

```
src/
  lib/
    tokenize.js   Lexer — TI function names carry their open paren
    parse.js      Recursive descent → AST, implicit multiplication
    evaluate.js   AST evaluation; numbers and strings
    format.js     TI number formatting (10 sig digits, .5 not 0.5)
    screen.js     8×16 character grid with hardware scroll semantics
    basic.js      TI-BASIC compiler + generator runtime
    graph.js      Pixel mapping, sampling, zoom presets
    render.js     Builds display rows for every mode
    keys.js       Keypad layout, 2nd/ALPHA maps, getKey codes
    programs.js   PORTFOLIO, QUAD, COUNT
  components/
    Calculator.jsx  State machine and key dispatch
    Display.jsx     Routes to the character grid or the graph
    GraphCanvas.jsx 96×64 framebuffer rendering
    Keypad.jsx      The key matrix
```

## Programs on board

| Name | Exercises |
|---|---|
| `PORTFOLIO` | `Menu(`, `Goto`/`Lbl`, `Disp`, `Pause` — the portfolio itself |
| `QUAD` | `Input`, `If`/`Then`/`Else`, `√(`, the math library |
| `COUNT` | `For(`/`End` with a negative step |

`PRGM → EDIT` shows any program's source on the calculator.

## Known limits

Lists, matrices, and the STAT editor are stubs — the `STAT`, `MATRIX`, `MATH`
and `VARS` screens acknowledge the keypress and say so rather than pretending.
Programs are read-only in this build; `PRGM → NEW` is not wired up.

## Claude

Built with [Claude](https://claude.ai) in Claude Code on September 3, 2026.
The engine is covered by a Node harness (45 assertions over expression
parsing, number formatting, control flow and error handling) and a Playwright
pass that drives the real UI through the portfolio, arithmetic, graphing,
tracing and program execution.

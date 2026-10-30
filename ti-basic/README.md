---
published: 2026-10-30
updated: 2026-10-30
tags: generative
---

# TI-BASIC Home Screen

A TI-84-style calculator that runs a home-screen menu program written in TI-BASIC, right in the browser. Pick About, Dice, Counter, a number-guessing game, or a key-code viewer from the menu, then edit the program and run it again.

## Using it

Press **ENTER** on the calculator to run `prgmHOME`. Move through the menu with the arrows or press its number. **ON** (or Ctrl+B) breaks a running program; on the error screen, **2:Goto** jumps to the line in the editor.

On a keyboard: arrows, Enter, Esc = CLEAR, Backspace = DEL; digits and letters type.

## Running it

No build step. Serve the folder and open it:

```bash
python3 -m http.server 5180 --directory ti-basic
```

## How it works

- `interpreter.js` — a small TI-BASIC interpreter with no DOM: an 8×16 home-screen model, a tokenizer and parser (including implied multiplication and unclosed parentheses), and a runner for `ClrHome`, `Disp`, `Output(`, `Pause`, `Wait`, `Menu(`, `Input`, `Prompt`, `If`/`Then`/`Else`/`End`, `While`, `Repeat`, `For(`, `Lbl`/`Goto`, `Stop`, `DelVar`, `→` and `getKey` (real TI key codes)
- `prgm-home.js` — the TI-BASIC source of `prgmHOME`
- `app.js` — draws the screen, builds the keypad (with ALPHA letters), runs the home screen (you can also type math like `2+3` there), shows TI-style error menus, and keeps your edits in local storage
- `styles.css` — the calculator, LCD and editor

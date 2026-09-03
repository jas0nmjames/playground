import Calculator from './components/Calculator.jsx';

const GUIDE = [
  ['Portfolio', 'Runs on load. Pick items with 1-4 or ▲▼ then ENTER. ENTER also clears a Pause.'],
  ['Re-run it', 'PRGM → ENTER on 1:PORTFOLIO. The EDIT tab shows the TI-BASIC source.'],
  ['Arithmetic', '2nd → MODE quits to the home screen. Try 2+2, sin(π/6), 5→A, then A².'],
  ['Graphing', 'Y= to enter a function (X types the variable), then GRAPH. TRACE walks it.'],
  ['Window', 'WINDOW edits the viewport; ZOOM has ZStandard, ZSquare, ZTrig and friends.'],
  ['Keyboard', 'Digits, operators, Enter, Backspace, Esc and the arrow keys all work.'],
];

export default function App() {
  return (
    <div className="page">
      <header className="page-header">
        <h1>TI-83 Plus</h1>
        <p>
          A graphing calculator emulator with a working TI-BASIC interpreter —
          hosting a portfolio that lives entirely inside the calculator.
        </p>
      </header>

      <main className="layout">
        <Calculator />

        <aside className="guide">
          <h2>How to drive it</h2>
          <dl>
            {GUIDE.map(([term, detail]) => (
              <div className="guide-item" key={term}>
                <dt>{term}</dt>
                <dd>{detail}</dd>
              </div>
            ))}
          </dl>

          <h2>What's real here</h2>
          <ul className="notes">
            <li>
              Expressions are tokenized and parsed into an AST, including
              implicit multiplication, so <code>2X</code> and{' '}
              <code>3(X+1)</code> behave.
            </li>
            <li>
              TI-BASIC compiles to a flat instruction list with resolved jump
              targets — which is what makes <code>Goto</code>,{' '}
              <code>Menu(</code> and nested loops work.
            </li>
            <li>
              The display is a true 16&times;8 character grid; the graph is a
              96&times;64 pixel buffer sampled one column at a time.
            </li>
          </ul>
        </aside>
      </main>
    </div>
  );
}

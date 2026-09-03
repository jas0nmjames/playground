import { buildScreen } from '../lib/render.js';
import { COLS } from '../lib/screen.js';
import GraphCanvas from './GraphCanvas.jsx';

/**
 * The LCD. Text modes render an 8x16 character grid; graph modes hand off to
 * the pixel canvas. The busy indicator in the corner mirrors the dashed
 * marker the real calculator shows while a program is running or paused.
 */
export default function Display({ state, evalCtx }) {
  const isGraph = state.mode === 'graph' || state.mode === 'trace';

  if (isGraph) {
    return (
      <div className="lcd">
        <GraphCanvas
          win={state.win}
          yvars={state.yvars}
          evalCtx={evalCtx}
          trace={state.mode === 'trace' ? state.trace : null}
        />
        {state.busy && <span className="busy" aria-hidden="true" />}
      </div>
    );
  }

  const { rows, cursor } = buildScreen(state);
  const cursorChar = state.second ? '↑' : state.alpha ? 'A' : '█';

  return (
    <div className="lcd">
      <div className="lcd-grid" role="img" aria-label={rows.map((r) => r.text.trim()).join('. ')}>
        {rows.map((r, ri) => (
          <div key={ri} className={`lcd-row${r.inverse ? ' inverse' : ''}`}>
            {Array.from({ length: COLS }, (_, ci) => {
              const onCursor = cursor && cursor.r === ri && cursor.c === ci;
              const ch = r.text[ci] ?? ' ';
              return (
                <span key={ci} className={onCursor ? 'cell cursor' : 'cell'}>
                  {onCursor ? cursorChar : ch === ' ' ? ' ' : ch}
                </span>
              );
            })}
          </div>
        ))}
      </div>
      {(state.busy || state.waiting?.kind === 'pause') && (
        <span className="busy" aria-hidden="true" />
      )}
    </div>
  );
}

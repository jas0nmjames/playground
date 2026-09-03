import { KEYS } from '../lib/keys.js';

/**
 * The keypad. Grid positions come straight from the key table, so the layout
 * matches the hardware; the arrow cluster is placed explicitly across
 * columns 4-5 of rows 2-3, where it sits on a real TI-83+.
 */
function Key({ k, active, onPress }) {
  const classes = ['key'];
  if (k.variant) classes.push(`key-${k.variant}`);
  if (active) classes.push('key-active');

  return (
    <button
      type="button"
      className={classes.join(' ')}
      style={{ gridRow: k.r, gridColumn: k.c }}
      onClick={() => onPress(k.id)}
      aria-label={k.main}
    >
      {(k.second || k.alpha) && (
        <span className="key-above">
          <span className="key-second-label">{k.second || ''}</span>
          <span className="key-alpha-label">{k.alpha || ''}</span>
        </span>
      )}
      <span className="key-main">{k.main}</span>
    </button>
  );
}

const ARROWS = [
  { id: 'UP', glyph: '▲', cls: 'up' },
  { id: 'LEFT', glyph: '◀', cls: 'left' },
  { id: 'RIGHT', glyph: '▶', cls: 'right' },
  { id: 'DOWN', glyph: '▼', cls: 'down' },
];

export default function Keypad({ onPress, second, alpha }) {
  return (
    <div className="keypad">
      {KEYS.map((k) => (
        <Key
          key={k.id}
          k={k}
          active={(k.id === '2ND' && second) || (k.id === 'ALPHA' && alpha)}
          onPress={onPress}
        />
      ))}

      <div className="dpad" style={{ gridRow: '2 / span 2', gridColumn: '4 / span 2' }}>
        {ARROWS.map((a) => (
          <button
            key={a.id}
            type="button"
            className={`arrow arrow-${a.cls}`}
            onClick={() => onPress(a.id)}
            aria-label={a.id}
          >
            {a.glyph}
          </button>
        ))}
      </div>
    </div>
  );
}

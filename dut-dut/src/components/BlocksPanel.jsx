import { GROUPS_META, TOOLS, COLORS } from '../constants.js';

export default function BlocksPanel({
  style, isMobile, section, subs, sectionNotes, tool, setTool, tempo,
  muted, toggleMute, cycleBeatSub, cellDown, cellEnter, playheadPos,
  tintByGroup = null, focusColor = null,
}) {
  const beats = section.measures * 4;
  const beatW = isMobile ? 112 : 128;
  const cellH = isMobile ? 40 : 34;
  const { accent, onAccent, text, mutedText, ink, border } = COLORS;

  // Flat position index of each beat's first cell, for playhead matching.
  const flatBase = [];
  let acc = 0;
  for (let b = 0; b < beats; b++) { flatBase.push(acc); acc += subs[b]; }

  return (
    <div className="blocks-panel" style={style}>
      <div className="panel-header">
        <div className="panel-title">Blocks</div>
        <div className="panel-meta">{section.measures} measures · {tempo} BPM</div>
      </div>

      <div className="tools-row">
        {TOOLS.map(tl => {
          const active = tl.id === tool;
          return (
            <button
              key={tl.id}
              className="tool-btn"
              onClick={() => setTool(tl.id)}
              style={{
                background: active ? accent : 'oklch(95% 0.008 80)',
                color: active ? onAccent : mutedText,
                borderColor: active ? accent : border,
              }}
            >
              {tl.label}
            </button>
          );
        })}
      </div>
      <div className="hint-text">Click / drag paints the tool · click a beat number for 16th → triplet → 8th</div>

      <div className="blocks-scroll">
        <div className="blocks-inner">
          <div className="ruler-row">
            <div className="ruler-corner" />
            {Array.from({ length: beats }, (_, b) => {
              const sc = subs[b];
              const isMeasureStart = b % 4 === 0;
              return (
                <button
                  key={b}
                  className="ruler-btn"
                  title="Cycle subdivision: 16th → triplet → 8th"
                  onClick={() => cycleBeatSub(b)}
                  style={{
                    width: beatW,
                    background: isMeasureStart ? 'oklch(94% 0.01 80)' : 'oklch(97% 0.007 80)',
                    borderLeft: isMeasureStart ? '2px solid oklch(75% 0.015 80)' : '1px solid oklch(89% 0.01 80)',
                  }}
                >
                  <span className="ruler-label">{isMeasureStart ? `${Math.floor(b / 4) + 1}.1` : String(b % 4 + 1)}</span>
                  <span
                    className="ruler-sub"
                    style={{
                      color: sc === 3 ? onAccent : mutedText,
                      background: sc === 3 ? accent : 'oklch(92% 0.01 80)',
                    }}
                  >
                    {sc === 4 ? '16' : sc === 3 ? '3' : '8'}
                  </span>
                </button>
              );
            })}
          </div>

          {GROUPS_META.map(g => (
            <div key={g.id}>
              <div className="group-header">
                <div className="group-dot" style={{ background: g.color }} />
                <div className="group-name">{g.name}</div>
                <button
                  className="mute-btn"
                  onClick={() => toggleMute(g.id)}
                  style={{ background: muted[g.id] ? 'oklch(72% 0.12 25)' : 'transparent', color: muted[g.id] ? text : mutedText }}
                >
                  {muted[g.id] ? 'Muted' : 'Mute'}
                </button>
              </div>
              {g.rowDefs.map(rowDef => (
                <div key={rowDef.id} className="row-line">
                  <div className="row-label">{rowDef.label}</div>
                  <div className="row-cells">
                    {Array.from({ length: beats }, (_, b) => {
                      const sc = subs[b];
                      const w = beatW / sc;
                      return Array.from({ length: sc }, (_, s) => {
                        const v = sectionNotes[rowDef.id][b][s];
                        const isMeasureStart = b % 4 === 0 && s === 0;
                        const baseBg = isMeasureStart ? 'oklch(91% 0.012 80)' : s === 0 ? 'oklch(93% 0.01 80)' : 'oklch(96% 0.007 80)';
                        const hl = tintByGroup && tintByGroup[g.id] && tintByGroup[g.id].has(b);
                        return (
                          <div
                            key={`${b}-${s}`}
                            className="cell"
                            onMouseDown={() => cellDown(rowDef.id, b, s)}
                            onMouseEnter={() => cellEnter(rowDef.id, b, s)}
                            style={{
                              width: w,
                              height: cellH,
                              background: hl ? `color-mix(in oklch, ${baseBg} 55%, ${focusColor})` : baseBg,
                            }}
                          >
                            {v === 3 && <div className="grace-dot" style={{ background: g.color }} />}
                            {(v === 1 || v === 2 || v === 3 || v === 5) && (
                              <div
                                className="note-dot"
                                style={{
                                  width: v === 2 ? 17 : v === 5 ? 16 : 13,
                                  height: v === 2 ? 17 : v === 5 ? 16 : 13,
                                  background: g.color,
                                  border: v === 2 ? `2px solid ${ink}` : 'none',
                                }}
                              >
                                {v === 5 && <span className="dot-z">z</span>}
                              </div>
                            )}
                            {v === 4 && (
                              <>
                                <div className="twin-dot" style={{ background: g.color }} />
                                <div className="twin-dot" style={{ background: g.color }} />
                              </>
                            )}
                            {flatBase[b] + s === playheadPos && <div className="cell-playhead" />}
                          </div>
                        );
                      });
                    })}
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

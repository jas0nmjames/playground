import { GROUPS_META, ALL_ROWS, ROW_GROUP, TOOLS, COLORS } from '../constants.js';

const subLabel = (sc) => (sc === 4 ? '16' : sc === 3 ? '3' : '8');

export default function BlocksPanel({
  style, isMobile, section, masterSubs, subsByGroup, overrides, sectionNotes, sectionLive,
  tool, setTool, tempo, muted, toggleMute,
  cycleBeatSub, cycleGroupBeatSub, resetGroupSubs, perPart, togglePerPart,
  selectedRowId, selectRow, armGroup, selRow, tapMode, setTapMode,
  hasTake, clearTake, takeColor, cellDown, cellEnter, playBeat,
  tintByGroup = null, focusColor = null,
}) {
  const beats = section.measures * 4;
  const beatW = isMobile ? 112 : 128;
  const cellH = isMobile ? 40 : 34;
  const { accent, onAccent, text, mutedText, ink, border } = COLORS;
  const tapExactOn = tapMode === 'exact';

  const modeStyle = (active) => ({ background: active ? takeColor : 'transparent', color: active ? onAccent : mutedText });

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

      <div className="hint-row">
        <span className="hint-text">Click / drag paints · beat number cycles 16th → triplet → 8th · ÷ splits it per part</span>
        <div className="hint-right">
          <span
            className="tap-target-pill"
            style={{
              background: selRow ? takeColor : 'transparent',
              color: selRow ? onAccent : mutedText,
              borderColor: selRow ? takeColor : border,
            }}
          >
            {selRow ? `Space → ${selRow.label}` : 'Space → pick a drum'}
          </span>
          {hasTake && (
            <div className="take-legend-row">
              <span className="take-legend"><span className="take-dot" style={{ background: takeColor }} />tapped in</span>
              <button className="clear-take-btn" onClick={clearTake}>Clear taps</button>
            </div>
          )}
        </div>
      </div>

      <div className="blocks-scroll">
        <div className="blocks-inner">
          <div className="ruler-row">
            <div className="ruler-corner">
              <button
                className="perpart-btn"
                title="Per-part subdivisions — give each drum family its own 16th / triplet / 8th on any beat"
                onClick={togglePerPart}
                style={{
                  background: perPart ? accent : 'oklch(94% 0.01 80)',
                  color: perPart ? onAccent : mutedText,
                  borderColor: perPart ? accent : border,
                }}
              >
                ÷
              </button>
            </div>
            {Array.from({ length: beats }, (_, b) => {
              const sc = masterSubs[b];
              const isMeasureStart = b % 4 === 0;
              const mixed = GROUPS_META.some(g => (overrides[g.id] || [])[b]);
              return (
                <button
                  key={b}
                  className="ruler-btn"
                  title="Cycle subdivision for every part: 16th → triplet → 8th"
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
                      border: `1px ${mixed ? 'dashed' : 'solid'} ${mixed ? 'oklch(50% 0.02 260)' : 'transparent'}`,
                    }}
                  >
                    {subLabel(sc)}
                  </span>
                </button>
              );
            })}
          </div>

          {GROUPS_META.map(g => {
            const gsubs = subsByGroup[g.id];
            const ov = overrides[g.id] || [];
            const armed = ROW_GROUP[selectedRowId] === g.id;
            const armedRow = armed ? ALL_ROWS.find(r => r.id === selectedRowId) : null;
            return (
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
                  <button
                    className="arm-btn"
                    title="Play along on this part — hit Play, then tap Space in time and the notes land here"
                    onClick={() => armGroup(g.id)}
                    style={{
                      background: armedRow ? takeColor : 'transparent',
                      color: armedRow ? onAccent : mutedText,
                      borderColor: armedRow ? takeColor : border,
                    }}
                  >
                    {armedRow ? `Tap: ${armedRow.label}` : 'Tap in'}
                  </button>
                  {armed && (
                    <div className="tap-mode-track">
                      <button title="Keep the exact moment you tapped" onClick={() => setTapMode('exact')} style={modeStyle(tapExactOn)}>Exact</button>
                      <button title="Pull each tap to the nearest subdivision" onClick={() => setTapMode('quant')} style={modeStyle(!tapExactOn)}>Auto-rhythm</button>
                    </div>
                  )}
                  {ov.some(v => v) && (
                    <button
                      className="own-subs-btn"
                      title="Reset this part to the measure subdivision"
                      onClick={() => resetGroupSubs(g.id)}
                      style={{ borderColor: g.color, color: g.color }}
                    >
                      own ÷ ×
                    </button>
                  )}
                </div>

                <div className="subchip-row" style={{ display: perPart ? 'flex' : 'none' }}>
                  <div className="subchip-label">÷</div>
                  {Array.from({ length: beats }, (_, b) => {
                    const own = ov[b] || 0;
                    const sc = own || masterSubs[b];
                    const isMeasureStart = b % 4 === 0;
                    return (
                      <button
                        key={b}
                        className="subchip-btn"
                        title="This part only, this beat: inherit → 16th → triplet → 8th"
                        onClick={() => cycleGroupBeatSub(g.id, b)}
                        style={{
                          width: beatW,
                          background: isMeasureStart ? 'oklch(96% 0.008 80)' : 'oklch(98% 0.006 80)',
                          borderLeft: isMeasureStart ? '2px solid oklch(88% 0.012 80)' : '1px solid oklch(93% 0.008 80)',
                        }}
                      >
                        <span
                          className="subchip-pill"
                          style={{
                            color: own ? onAccent : 'oklch(60% 0.02 260)',
                            background: own ? g.color : 'transparent',
                            border: `1px ${own ? 'solid' : 'dashed'} ${own ? g.color : 'oklch(86% 0.012 80)'}`,
                          }}
                        >
                          {subLabel(sc)}
                        </span>
                      </button>
                    );
                  })}
                </div>

                {g.rowDefs.map(rowDef => {
                  const selected = selectedRowId === rowDef.id;
                  return (
                    <div key={rowDef.id} className="row-line">
                      <button
                        className="row-label"
                        title="Select this drum as the play-along target (Space taps notes in)"
                        onClick={() => selectRow(rowDef.id)}
                        style={{
                          background: selected ? takeColor : 'oklch(98% 0.006 80)',
                          color: selected ? onAccent : mutedText,
                          fontWeight: selected ? 700 : 500,
                        }}
                      >
                        {rowDef.label}
                      </button>
                      <div className="row-cells">
                        {Array.from({ length: beats }, (_, b) => {
                          const sc = gsubs[b];
                          const w = beatW / sc;
                          return Array.from({ length: sc }, (_, s) => {
                            const v = sectionNotes[rowDef.id][b][s];
                            const m = (sectionLive[rowDef.id][b] && sectionLive[rowDef.id][b][s]) || 0;
                            const liveKind = m === 0 ? 0 : m === 1 ? 1 : 2;
                            const shift = liveKind === 2 ? Math.round(Math.min(m - 2, 0.85) * w) : 0;
                            const isMeasureStart = b % 4 === 0 && s === 0;
                            const baseBg = isMeasureStart ? 'oklch(91% 0.012 80)' : s === 0 ? 'oklch(93% 0.01 80)' : 'oklch(96% 0.007 80)';
                            const hl = tintByGroup && tintByGroup[g.id] && tintByGroup[g.id].has(b);
                            const dotColor = liveKind ? takeColor : g.color;
                            const isPlayhead = playBeat >= 0 && playBeat >= b + s / sc && playBeat < b + (s + 1) / sc;
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
                                  zIndex: liveKind === 2 ? 1 : 0,
                                }}
                              >
                                {liveKind === 2 && shift > 3 && (
                                  <div className="dev-line" style={{ width: shift, background: takeColor }} />
                                )}
                                {v === 3 && <div className="grace-dot" style={{ background: dotColor }} />}
                                {(v === 1 || v === 2 || v === 3 || v === 5) && (
                                  <div
                                    className="note-dot"
                                    style={{
                                      width: v === 2 ? 17 : v === 5 ? 16 : 13,
                                      height: v === 2 ? 17 : v === 5 ? 16 : 13,
                                      background: dotColor,
                                      border: v === 2 ? `2px solid ${ink}` : 'none',
                                      transform: `translateX(${shift}px)`,
                                    }}
                                  >
                                    {v === 5 && <span className="dot-z">z</span>}
                                  </div>
                                )}
                                {v === 4 && (
                                  <>
                                    <div className="twin-dot" style={{ background: dotColor }} />
                                    <div className="twin-dot" style={{ background: dotColor }} />
                                  </>
                                )}
                                {liveKind === 1 && <div className="snap-bar" style={{ background: takeColor }} />}
                                {isPlayhead && <div className="cell-playhead" />}
                              </div>
                            );
                          });
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

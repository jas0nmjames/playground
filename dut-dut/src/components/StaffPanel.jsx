import { GROUPS_META } from '../constants.js';
import { buildStaffShapes } from '../staff.js';

const INK = 'oklch(24% 0.015 260)';

function StaffSvg({ sg, showPlayhead, playheadX, takeColor }) {
  return (
    <svg width={sg.width} height={sg.height} style={{ display: 'block' }}>
      {sg.bands.map(bd => (
        <rect
          key={bd.key}
          x={bd.x} y={bd.y} width={bd.w} height={bd.h} rx={5}
          fill={bd.fill} opacity={bd.opacity}
          style={{ cursor: 'help' }}
          onMouseEnter={bd.enter}
          onMouseLeave={bd.leave}
        />
      ))}
      {sg.lines.map((ln, i) => (
        <line key={i} x1={16} x2={sg.lineEndX} y1={ln.y} y2={ln.y} stroke="oklch(55% 0.02 260)" strokeWidth={1} />
      ))}
      {sg.barlines.map((bl, i) => (
        <line key={i} x1={bl.x} x2={bl.x} y1={sg.barTop} y2={sg.barBot} stroke="oklch(35% 0.02 260)" strokeWidth={bl.w} />
      ))}
      <rect x={20} y={sg.clefY} width={3.6} height={16} rx={1} fill={INK} />
      <rect x={27} y={sg.clefY} width={3.6} height={16} rx={1} fill={INK} />
      <text x={42} y={sg.ts1Y} fill={INK} style={{ font: '700 15px Georgia,serif' }}>4</text>
      <text x={42} y={sg.ts2Y} fill={INK} style={{ font: '700 15px Georgia,serif' }}>4</text>
      {sg.measureNums.map(mn => (
        <text key={mn.n} x={mn.x} y={sg.numY} fill="oklch(55% 0.02 260)" style={{ font: 'italic 9px Georgia,serif' }}>{mn.n}</text>
      ))}
      {showPlayhead && (
        <line x1={playheadX} x2={playheadX} y1={0} y2={sg.height} stroke="oklch(58% 0.16 235)" strokeWidth={2} opacity={0.8} />
      )}
      {sg.stems.map(st => <line key={st.key} x1={st.x} x2={st.x} y1={st.y1} y2={st.y2} stroke={INK} strokeWidth={1.3} />)}
      {sg.beams.map(bm => <line key={bm.key} x1={bm.x1} x2={bm.x2} y1={bm.y} y2={bm.y} stroke={INK} strokeWidth={3.4} />)}
      {sg.beams2.map(b2 => <line key={b2.key} x1={b2.x1} x2={b2.x2} y1={b2.y} y2={b2.y} stroke={INK} strokeWidth={3.4} />)}
      {sg.flags.map(fl => <line key={fl.key} x1={fl.x1} y1={fl.y1} x2={fl.x2} y2={fl.y2} stroke={INK} strokeWidth={2.2} />)}
      {sg.tuplets.map(tp => (
        <text key={tp.key} x={tp.x} y={tp.y} textAnchor="middle" fill={INK} style={{ font: 'italic 700 10px Georgia,serif' }}>3</text>
      ))}
      {sg.accents.map(ac => (
        <text key={ac.key} x={ac.x} y={ac.y} textAnchor="middle" fill={INK} style={{ font: '700 11px Georgia,serif' }}>&gt;</text>
      ))}
      {sg.slashes.map(sl => <line key={sl.key} x1={sl.x1} y1={sl.y1} x2={sl.x2} y2={sl.y2} stroke={INK} strokeWidth={1.8} />)}
      {sg.zs.map(zz => (
        <text key={zz.key} x={zz.x} y={zz.y} textAnchor="middle" fill={INK} style={{ font: 'italic 700 11px Georgia,serif' }}>z</text>
      ))}
      {sg.graces.map(gr => (
        <g key={gr.key}>
          <circle cx={gr.x} cy={gr.y} r={3.1} fill={INK} />
          <line x1={gr.sx} x2={gr.sx} y1={gr.sy1} y2={gr.sy2} stroke={INK} strokeWidth={1.1} />
          <line x1={gr.k1x} y1={gr.k1y} x2={gr.k2x} y2={gr.k2y} stroke={INK} strokeWidth={1.1} />
        </g>
      ))}
      {sg.notes.map(nt => nt.isX ? (
        <g key={nt.key}>
          <line x1={nt.x1a} y1={nt.y1a} x2={nt.x2a} y2={nt.y2a} stroke={nt.fill} strokeWidth={1.7} />
          <line x1={nt.x1b} y1={nt.y1b} x2={nt.x2b} y2={nt.y2b} stroke={nt.fill} strokeWidth={1.7} />
        </g>
      ) : (
        <ellipse key={nt.key} cx={nt.x} cy={nt.y} rx={5.2} ry={3.9} transform={`rotate(-18 ${nt.x} ${nt.y})`} fill={nt.fill} />
      ))}
      {sg.unisons.map(un => (
        <rect key={un.key} x={un.x} y={un.y} width={un.w} height={un.h} rx={un.rx} fill={un.fill} />
      ))}
      {sg.snapBars.map(sb => (
        <line key={sb.key} x1={sb.x1} x2={sb.x2} y1={sb.y} y2={sb.y} stroke={takeColor} strokeWidth={2} />
      ))}
      {sg.takeTicks.map(tk => (
        <line key={tk.key} x1={tk.x} x2={tk.x} y1={tk.y1} y2={tk.y2} stroke={takeColor} strokeWidth={1.4} />
      ))}
    </svg>
  );
}

export default function StaffPanel({
  style, isMobile, isPreview, section, subsByGroup, sectionNotes, sectionLive, tempo,
  playing, onTogglePlay, playBeat, unison = true, takeColor, hasTake = false,
  insights = [], showBands = false, focusId = null, focusColor = null, tintByGroup = null,
  onBandEnter, onBandLeave,
}) {
  const beatW = isMobile ? 112 : 128;
  const leftPad = 60;
  const playheadX = playBeat >= 0 ? leftPad + playBeat * beatW : -100;

  const staffGroups = GROUPS_META.map(g => {
    const shapes = buildStaffShapes(
      g,
      g.rowDefs.map(rd => sectionNotes[rd.id]),
      g.rowDefs.map(rd => sectionLive[rd.id]),
      subsByGroup[g.id], section.measures, beatW, leftPad, { unison },
    );

    // Translucent hover bands over each insight's target beats
    const bands = [];
    if (showBands) {
      for (const ins of insights) {
        for (const tg of ins.targets) {
          if (tg.sectionId !== section.id) continue;
          if (tg.groupId && tg.groupId !== g.id) continue;
          let run = null;
          const sorted = [...new Set(tg.beats)].sort((x, y) => x - y);
          const flush = () => {
            if (!run) return;
            bands.push({
              key: ins.id + '-' + g.id + '-' + run[0],
              x: leftPad + run[0] * beatW + 1.5, y: 4, w: (run[1] - run[0] + 1) * beatW - 3, h: shapes.height - 8,
              fill: ins.color, opacity: focusId === ins.id ? 0.3 : 0.1,
              enter: (e) => onBandEnter(ins, e), leave: onBandLeave,
            });
            run = null;
          };
          for (const bb of sorted) { if (run && bb === run[1] + 1) run[1] = bb; else { flush(); run = [bb, bb]; } }
          flush();
        }
      }
    }

    const tintSet = tintByGroup ? tintByGroup[g.id] : null;
    const tinted = (n) => (tintSet && tintSet.has(n.b) ? focusColor : n.live ? takeColor : INK);
    const notes = shapes.notes.map(n => ({ ...n, fill: tinted(n) }));
    const unisons = shapes.unisons.map(n => ({ ...n, fill: tinted(n) }));

    return { id: g.id, name: g.name, color: g.color, shapes: { ...shapes, notes, unisons, bands } };
  });

  return (
    <div className="staff-panel" style={style}>
      <div
        className="staff-header"
        style={isPreview ? { padding: '18px 16px 0', alignItems: 'center' } : { padding: '10px 16px 6px', alignItems: 'flex-start' }}
      >
        <div className="staff-title">{isPreview ? 'Score — Preview' : 'Score'}</div>
        <div className="staff-meta">{section.name} · {tempo} BPM</div>
      </div>
      {isPreview && (
        <div className="preview-play-wrap">
          <button className="preview-play-btn" onClick={onTogglePlay}>{playing ? '■ Stop' : '▶ Play'}</button>
        </div>
      )}
      <div className="staff-scroll">
        <div className="staff-inner" style={{ margin: isPreview ? '0 auto' : '0' }}>
          {staffGroups.map(sg => (
            <div key={sg.id} className="staff-group">
              <div className="staff-group-label" style={{ color: sg.color }}>{sg.name}</div>
              <StaffSvg sg={sg.shapes} showPlayhead={playBeat >= 0} playheadX={playheadX} takeColor={takeColor} />
            </div>
          ))}
          {hasTake && (
            <div className="take-key">
              <span><span className="take-key-dot" style={{ background: takeColor }} />tapped in live</span>
              <span><span className="take-key-tick" style={{ background: takeColor }} />where you actually played it</span>
              <span><span className="take-key-bar" style={{ background: takeColor }} />snapped to the grid</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

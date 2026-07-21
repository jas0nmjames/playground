import { LANE_Y } from './constants.js';

// Computes all staff-notation geometry (noteheads, stems, beams, flags, tuplets,
// accents, diddle slashes, buzz z's, grace notes) for one group's staff.
// Pure — used by both the on-screen SVG staff and the PNG score export.
export function buildStaffShapes(g, rowsArr, subs, measures, beatW, leftPad) {
  const beats = measures * 4;
  const laneYs = LANE_Y[g.id];
  const single = g.single;
  const staffH = single ? 84 : 134;
  const lines = single ? [{ y: 56 }] : [44, 60, 76, 92, 108].map(y => ({ y }));
  const midY = single ? 56 : 76;
  const lineEndX = leftPad + beats * beatW + 2;
  const barlines = [];
  for (let m = 0; m <= measures; m++) {
    const x = leftPad + m * 4 * beatW;
    if (m === measures) { barlines.push({ x: x - 5, w: 1 }); barlines.push({ x, w: 2.6 }); }
    else barlines.push({ x, w: 1 });
  }
  const measureNums = [];
  for (let m = 0; m < measures; m++) measureNums.push({ x: leftPad + m * 4 * beatW + 4, n: m + 1 });

  const notes = [], stems = [], beams = [], beams2 = [], flags = [], tuplets = [], accents = [], slashes = [], zs = [], graces = [];
  for (let b = 0; b < beats; b++) {
    const sc = subs[b];
    const subW = beatW / sc;
    const positions = [];
    for (let s = 0; s < sc; s++) {
      const x = leftPad + b * beatW + s * subW + subW / 2;
      const lanes = [];
      rowsArr.forEach((beatArr, laneIdx) => { const v = beatArr[b][s]; if (v) lanes.push({ laneIdx, v }); });
      positions.push({ s, x, lanes, sounded: lanes.length > 0 });
    }
    let beatMinStemTop = Infinity;
    let beatHasNotes = false;
    let i = 0;
    while (i < sc) {
      if (!positions[i].sounded) { i++; continue; }
      let j = i;
      while (j + 1 < sc && positions[j + 1].sounded) j++;
      const run = positions.slice(i, j + 1);
      const beamed = run.length > 1;
      let minHeadY = Infinity;
      run.forEach(p => p.lanes.forEach(l => { minHeadY = Math.min(minHeadY, laneYs[l.laneIdx]); }));
      const stemTopBeamed = minHeadY - 26;
      run.forEach(p => {
        beatHasNotes = true;
        let maxHeadY = -Infinity, pMinHeadY = Infinity;
        let hasAccent = false, hasDiddle = false, hasRoll = false;
        p.lanes.forEach(l => {
          const y = laneYs[l.laneIdx];
          maxHeadY = Math.max(maxHeadY, y); pMinHeadY = Math.min(pMinHeadY, y);
          if (l.v === 2) hasAccent = true;
          if (l.v === 4) hasDiddle = true;
          if (l.v === 5) hasRoll = true;
          if (l.v === 3) {
            const gx = p.x - 12, gy = y, gsx = gx + 3.2;
            graces.push({ key: g.id + '-gr-' + b + '-' + p.s + '-' + l.laneIdx, x: gx, y: gy, sx: gsx, sy1: gy - 1, sy2: gy - 13, k1x: gsx - 3, k1y: gy - 5, k2x: gsx + 3.5, k2y: gy - 11 });
          }
          const isX = g.id === 'cymbal';
          notes.push({
            key: g.id + '-n-' + b + '-' + p.s + '-' + l.laneIdx,
            b, x: p.x, y, isX, isOval: !isX,
            x1a: p.x - 4.6, y1a: y - 4.6, x2a: p.x + 4.6, y2a: y + 4.6,
            x1b: p.x - 4.6, y1b: y + 4.6, x2b: p.x + 4.6, y2b: y - 4.6,
          });
        });
        const stemTop = beamed ? stemTopBeamed : pMinHeadY - 20;
        beatMinStemTop = Math.min(beatMinStemTop, stemTop);
        const stemX = p.x + 4.8;
        stems.push({ key: g.id + '-st-' + b + '-' + p.s, x: stemX, y1: maxHeadY, y2: stemTop });
        if (!beamed) {
          let nextIdx = sc;
          for (let q = p.s + 1; q < sc; q++) { if (positions[q].sounded) { nextIdx = q; break; } }
          const frac = (nextIdx - p.s) / sc;
          const ticks = frac >= 1 ? 0 : frac >= 0.5 ? 1 : sc === 3 ? 1 : 2;
          for (let f = 0; f < ticks; f++) flags.push({ key: g.id + '-fl-' + b + '-' + p.s + '-' + f, x1: stemX, y1: stemTop + f * 6, x2: stemX + 7, y2: stemTop + f * 6 + 7 });
        }
        if (hasAccent) accents.push({ key: g.id + '-ac-' + b + '-' + p.s, x: p.x, y: stemTop - 5 });
        const midStem = (maxHeadY + stemTop) / 2;
        if (hasDiddle) slashes.push({ key: g.id + '-sl-' + b + '-' + p.s, x1: stemX - 4.5, y1: midStem + 4.5, x2: stemX + 4.5, y2: midStem - 4.5 });
        if (hasRoll) zs.push({ key: g.id + '-z-' + b + '-' + p.s, x: stemX, y: midStem + 3.5 });
      });
      if (beamed) {
        const x1 = run[0].x + 4.8, x2 = run[run.length - 1].x + 4.8;
        beams.push({ key: g.id + '-bm-' + b + '-' + i, x1, x2, y: stemTopBeamed });
        if (sc === 4) beams2.push({ key: g.id + '-bm2-' + b + '-' + i, x1, x2, y: stemTopBeamed + 6 });
      }
      i = j + 1;
    }
    if (sc === 3 && beatHasNotes) {
      tuplets.push({ key: g.id + '-tp-' + b, x: leftPad + b * beatW + beatW / 2, y: Math.max(beatMinStemTop - 7, 9) });
    }
  }
  return {
    width: lineEndX + 16, height: staffH,
    lineEndX, lines, barlines, measureNums,
    barTop: 44, barBot: single ? 68 : 108,
    clefY: midY - 8, ts1Y: midY - 2, ts2Y: midY + 13, numY: staffH - 4,
    notes, stems, beams, beams2, flags, tuplets, accents, slashes, zs, graces,
  };
}

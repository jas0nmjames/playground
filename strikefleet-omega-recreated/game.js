// ============================================================
// STRIKEFLEET OMEGA — RECREATED
// A fan tribute to the delisted 2012 carrier-command classic.
// Vanilla JS + Canvas. No dependencies.
// ============================================================
'use strict';

const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
let W = 0, H = 0, DPR = 1;

function resize() {
  DPR = Math.min(window.devicePixelRatio || 1, 2);
  W = window.innerWidth; H = window.innerHeight;
  canvas.width = W * DPR; canvas.height = H * DPR;
  canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
}
window.addEventListener('resize', resize);
resize();

// ---------- utils ----------
const TAU = Math.PI * 2;
const rand = (a, b) => a + Math.random() * (b - a);
const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const angTo = (a, b) => Math.atan2(b.y - a.y, b.x - a.x);

// ---------- game state ----------
const G = {
  state: 'menu',           // menu | playing | shop | warp | gameover
  wave: 0,
  sector: 1,
  credits: 0,
  totalKills: 0,
  time: 0,
  shake: 0,
  ships: [],               // player capital ships
  squads: [],              // fighter / bomber squadrons
  enemies: [],
  bullets: [],
  torps: [],
  shells: [],              // artillery shells in flight
  fx: [],
  pickups: [],
  spawnQueue: [],
  waveActive: false,
  warpT: 0,
  msg: null, msgT: 0,
};

const WAVES_PER_SECTOR = 5;

function announce(text, t = 2.5) { G.msg = text; G.msgT = t; }

// ---------- starfield ----------
const stars = [];
for (let i = 0; i < 160; i++) stars.push({ x: Math.random(), y: Math.random(), z: rand(0.3, 1) });

// ---------- player ships ----------
function makeCarrier(x, y) {
  return {
    kind: 'carrier', x, y, r: 34, hp: 300, maxHp: 300, angle: -Math.PI / 2,
    flash: 0,
  };
}
function makeArtillery(x, y) {
  return {
    kind: 'artillery', x, y, r: 22, hp: 160, maxHp: 160, angle: -Math.PI / 2,
    cooldown: 0, flash: 0,
  };
}

// squadron: group of small craft that share a path
function makeSquad(type, carrier) {
  const isF = type === 'fighter';
  const squad = {
    type, carrier,
    state: 'docked',        // docked | flying | patrol | returning
    path: [], pathI: 0,
    x: carrier.x, y: carrier.y,
    patrolT: 0,
    ammo: isF ? Infinity : 2,
    craft: [],
    label: '',
  };
  const n = isF ? 3 : 2;
  for (let i = 0; i < n; i++) {
    squad.craft.push({
      x: carrier.x, y: carrier.y, angle: 0,
      hp: isF ? 20 : 30, maxHp: isF ? 20 : 30,
      cd: rand(0, 0.5), alive: true, wob: rand(0, TAU),
    });
  }
  return squad;
}

// ---------- enemies ----------
const ENEMY_DEFS = {
  drone:    { r: 9,  hp: 18,  speed: 85,  dmg: 4,  fireCd: 1.1, range: 130, credits: 15, color: '#ff5252' },
  raider:   { r: 12, hp: 40,  speed: 55,  dmg: 14, fireCd: 2.2, range: 110, credits: 30, color: '#ff9138' },
  cruiser:  { r: 24, hp: 170, speed: 26,  dmg: 10, fireCd: 1.6, range: 210, credits: 90, color: '#c65bff' },
  asteroid: { r: 26, hp: 220, speed: 30,  dmg: 60, fireCd: 0,   range: 0,   credits: 60, color: '#a8895c' },
};

function spawnEnemy(type) {
  const d = ENEMY_DEFS[type];
  // spawn just off a random edge
  const side = Math.floor(rand(0, 4));
  let x, y;
  if (side === 0) { x = rand(0, W); y = -50; }
  else if (side === 1) { x = W + 50; y = rand(0, H * 0.6); }
  else if (side === 2) { x = -50; y = rand(0, H * 0.6); }
  else { x = rand(0, W); y = -50; }
  const mult = 1 + (G.sector - 1) * 0.35;
  G.enemies.push({
    type, x, y, r: d.r,
    hp: d.hp * mult, maxHp: d.hp * mult,
    speed: d.speed, dmg: d.dmg * (1 + (G.sector - 1) * 0.2),
    fireCd: d.fireCd, cd: rand(0.5, 2), range: d.range,
    credits: Math.round(d.credits * (1 + (G.sector - 1) * 0.25)),
    color: d.color, angle: 0, spin: rand(-1, 1), flash: 0,
    target: null,
  });
}

// ---------- waves ----------
function buildWave(n) {
  // n is global wave number (1-based)
  const q = [];
  const push = (type, count, t0, gap) => {
    for (let i = 0; i < count; i++) q.push({ type, t: t0 + i * gap });
  };
  const s = G.sector;
  const local = ((n - 1) % WAVES_PER_SECTOR) + 1;
  push('drone', 3 + local + s, 1, 1.2);
  if (local >= 2) push('raider', 1 + Math.floor(local / 2) + Math.floor(s / 2), 5, 2.5);
  if (local >= 3) push('asteroid', Math.floor(local / 2), 4, 6);
  if (local >= 4) push('cruiser', local - 3 + Math.floor(s / 2), 8, 8);
  if (local === WAVES_PER_SECTOR) { push('cruiser', 1 + Math.floor(s / 2), 14, 6); push('drone', 4 + s, 10, 0.8); }
  return q;
}

function startWave() {
  G.wave++;
  G.spawnQueue = buildWave(G.wave);
  G.waveActive = true;
  const local = ((G.wave - 1) % WAVES_PER_SECTOR) + 1;
  announce(`SECTOR ${G.sector} — WAVE ${local} / ${WAVES_PER_SECTOR}`);
}

// ---------- shop ----------
const SHOP = [
  { id: 'fighter',  name: 'FIGHTER SQUADRON', desc: '3 interceptors. Fast, anti-drone.', cost: 200, },
  { id: 'bomber',   name: 'BOMBER SQUADRON',  desc: '2 torpedo craft. Kills big ships.', cost: 300, },
  { id: 'artillery',name: 'ARTILLERY CRUISER',desc: 'Tap to bombard. Area damage.',      cost: 450, },
  { id: 'repair',   name: 'FLEET REPAIR',     desc: 'Restore all hulls to full.',        cost: 150, },
  { id: 'reinforce',name: 'REINFORCE HULLS',  desc: '+60 max HP on capital ships.',      cost: 250, },
];

function buy(item) {
  if (G.credits < item.cost) { announce('INSUFFICIENT CREDITS', 1.2); return; }
  const carrier = G.ships.find(s => s.kind === 'carrier');
  if (item.id === 'fighter' || item.id === 'bomber') {
    if (!carrier) return;
    if (G.squads.length >= 6) { announce('HANGARS FULL', 1.2); return; }
    G.squads.push(makeSquad(item.id, carrier));
    relabelSquads();
  } else if (item.id === 'artillery') {
    if (G.ships.length >= 5) { announce('FLEET AT CAPACITY', 1.2); return; }
    const a = makeArtillery(clamp(carrier.x + rand(-140, 140), 60, W - 60), clamp(carrier.y + rand(30, 80), H * 0.55, H - 80));
    G.ships.push(a);
  } else if (item.id === 'repair') {
    for (const s of G.ships) s.hp = s.maxHp;
    for (const sq of G.squads) for (const c of sq.craft) { c.alive = true; c.hp = c.maxHp; }
  } else if (item.id === 'reinforce') {
    for (const s of G.ships) { s.maxHp += 60; s.hp += 60; }
  }
  G.credits -= item.cost;
  announce(item.name + ' ACQUIRED', 1.2);
}

function relabelSquads() {
  let f = 0, b = 0;
  for (const sq of G.squads) sq.label = sq.type === 'fighter' ? 'F' + (++f) : 'B' + (++b);
}

// ---------- new game ----------
function newGame() {
  Object.assign(G, {
    state: 'playing', wave: 0, sector: 1, credits: 250, totalKills: 0,
    ships: [], squads: [], enemies: [], bullets: [], torps: [], shells: [],
    fx: [], pickups: [], spawnQueue: [], waveActive: false, shake: 0,
  });
  const carrier = makeCarrier(W / 2, H * 0.68);
  G.ships.push(carrier);
  G.ships.push(makeArtillery(W / 2 - 150, H * 0.78));
  G.squads.push(makeSquad('fighter', carrier));
  G.squads.push(makeSquad('fighter', carrier));
  G.squads.push(makeSquad('bomber', carrier));
  relabelSquads();
  startWave();
}

// ---------- input ----------
const input = {
  selected: null,          // { squad } or { ship } (artillery)
  drawing: false,
  path: [],
  px: 0, py: 0,
};

function uiButtons() {
  // bottom bar buttons for squads + artillery ships
  const btns = [];
  const bw = 64, bh = 58, gap = 10;
  const items = [...G.squads.map(sq => ({ squad: sq })),
                 ...G.ships.filter(s => s.kind === 'artillery').map((s, i) => ({ ship: s, label: 'A' + (i + 1) }))];
  const total = items.length * (bw + gap) - gap;
  let x = W / 2 - total / 2;
  for (const it of items) {
    btns.push({ ...it, x, y: H - bh - 12, w: bw, h: bh });
    x += bw + gap;
  }
  return btns;
}

canvas.addEventListener('pointerdown', e => {
  const x = e.clientX, y = e.clientY;
  input.px = x; input.py = y;

  if (G.state === 'menu' || G.state === 'gameover') { newGame(); return; }

  if (G.state === 'shop') {
    const r = shopRects();
    for (const it of r.items) if (inRect(x, y, it)) { buy(it.item); return; }
    if (inRect(x, y, r.launch)) { G.state = 'playing'; startWave(); return; }
    return;
  }

  if (G.state !== 'playing') return;

  // UI buttons
  for (const b of uiButtons()) {
    if (inRect(x, y, b)) {
      if (b.squad) {
        const sq = b.squad;
        if (sq.state === 'flying' || sq.state === 'patrol') { recallSquad(sq); input.selected = null; }
        else if (sq.state === 'docked' && squadAlive(sq)) input.selected = { squad: sq };
      } else if (b.ship) {
        input.selected = { ship: b.ship };
      }
      return;
    }
  }

  // tap directly on a ship / squad
  for (const s of G.ships) {
    if (dist({ x, y }, s) < s.r + 14) {
      if (s.kind === 'artillery') { input.selected = { ship: s }; return; }
      if (s.kind === 'carrier') {
        const sq = G.squads.find(q => q.carrier === s && q.state === 'docked' && squadAlive(q));
        if (sq) { input.selected = { squad: sq }; input.drawing = true; input.path = [{ x, y }]; }
        return;
      }
    }
  }

  // with a squad selected, start drawing a path from squad position
  if (input.selected && input.selected.squad) {
    input.drawing = true;
    input.path = [{ x: input.selected.squad.x, y: input.selected.squad.y }, { x, y }];
    return;
  }

  // with artillery selected, tap = fire mission
  if (input.selected && input.selected.ship) {
    fireArtillery(input.selected.ship, x, y);
    input.selected = null;
    return;
  }
});

canvas.addEventListener('pointermove', e => {
  if (!input.drawing) return;
  const x = e.clientX, y = e.clientY;
  const last = input.path[input.path.length - 1];
  if (!last || dist(last, { x, y }) > 14) input.path.push({ x, y });
});

canvas.addEventListener('pointerup', () => {
  if (input.drawing && input.selected && input.selected.squad && input.path.length >= 2) {
    launchSquad(input.selected.squad, input.path.slice());
    input.selected = null;
  }
  input.drawing = false;
  input.path = [];
});

function inRect(x, y, r) { return x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h; }

// ---------- squadron logic ----------
function squadAlive(sq) { return sq.craft.some(c => c.alive); }

function launchSquad(sq, path) {
  if (sq.type === 'bomber' && sq.ammo <= 0) sq.ammo = 2; // rearmed while docked
  sq.path = path; sq.pathI = 0; sq.state = 'flying'; sq.patrolT = 0;
  let i = 0;
  for (const c of sq.craft) {
    if (!c.alive) continue;
    c.x = sq.carrier.x + rand(-8, 8); c.y = sq.carrier.y + rand(-8, 8);
    i++;
  }
}

function recallSquad(sq) { sq.state = 'returning'; }

function updateSquads(dt) {
  for (const sq of G.squads) {
    if (!squadAlive(sq)) { sq.state = 'docked'; continue; }
    const speed = sq.type === 'fighter' ? 160 : 120;

    if (sq.state === 'docked') { sq.x = sq.carrier.x; sq.y = sq.carrier.y; continue; }

    let target;
    if (sq.state === 'flying') {
      target = sq.path[sq.pathI];
      if (dist(sq, target) < 18) {
        sq.pathI++;
        if (sq.pathI >= sq.path.length) { sq.state = 'patrol'; sq.patrolT = 6; }
      }
    } else if (sq.state === 'patrol') {
      sq.patrolT -= dt;
      target = sq.path[sq.path.length - 1];
      if (sq.patrolT <= 0 || (sq.type === 'bomber' && sq.ammo <= 0)) sq.state = 'returning';
    } else { // returning
      target = sq.carrier;
      if (dist(sq, target) < 24) {
        sq.state = 'docked';
        if (sq.type === 'bomber') sq.ammo = 2;
        for (const c of sq.craft) if (c.alive) c.hp = c.maxHp;
        continue;
      }
    }
    // move squad anchor
    if (target) {
      const a = angTo(sq, target);
      sq.x += Math.cos(a) * speed * dt;
      sq.y += Math.sin(a) * speed * dt;
    }

    // move individual craft in formation + combat
    let idx = 0;
    for (const c of sq.craft) {
      if (!c.alive) continue;
      c.wob += dt * 3;
      const off = idx * TAU / sq.craft.length;
      const fx = sq.x + Math.cos(c.wob * 0.5 + off) * 16;
      const fy = sq.y + Math.sin(c.wob * 0.5 + off) * 16;
      c.angle = angTo(c, { x: fx, y: fy });
      c.x = lerp(c.x, fx, clamp(dt * 4, 0, 1));
      c.y = lerp(c.y, fy, clamp(dt * 4, 0, 1));
      c.cd -= dt;
      idx++;

      if (sq.type === 'fighter') {
        // shoot nearest enemy in range
        const en = nearestEnemy(c, 150);
        if (en && c.cd <= 0) {
          c.cd = 0.35;
          G.bullets.push({ x: c.x, y: c.y, a: angTo(c, en), sp: 460, dmg: 6, life: 0.6, friendly: true, color: '#5ce1ff' });
        }
      } else {
        // bombers: torpedo big targets
        if (sq.ammo > 0 && c.cd <= 0) {
          const en = nearestEnemy(c, 190, e => e.type === 'cruiser' || e.type === 'asteroid' || e.type === 'raider');
          if (en) {
            c.cd = 1.6;
            sq.ammo -= 0.5;   // each craft firing costs half a salvo
            G.torps.push({ x: c.x, y: c.y, a: angTo(c, en), sp: 150, dmg: 45, life: 4, target: en, friendly: true });
          }
        }
      }
    }
  }
}

function nearestEnemy(p, range, filter) {
  let best = null, bd = range;
  for (const e of G.enemies) {
    if (filter && !filter(e)) continue;
    const d = dist(p, e);
    if (d < bd) { bd = d; best = e; }
  }
  return best;
}

// ---------- artillery ----------
function fireArtillery(ship, tx, ty) {
  if (ship.cooldown > 0) { announce('ARTILLERY RELOADING', 1); return; }
  ship.cooldown = 5;
  for (let i = 0; i < 4; i++) {
    G.shells.push({
      sx: ship.x, sy: ship.y,
      tx: tx + rand(-30, 30), ty: ty + rand(-30, 30),
      t: 0, dur: 1.1 + i * 0.22,
    });
  }
  ship.flash = 0.2;
}

function updateShells(dt) {
  for (let i = G.shells.length - 1; i >= 0; i--) {
    const s = G.shells[i];
    s.t += dt;
    if (s.t >= s.dur) {
      G.shells.splice(i, 1);
      boom(s.tx, s.ty, 46, '#ffd24a');
      G.shake = Math.min(G.shake + 5, 14);
      for (const e of G.enemies) {
        const d = dist(e, { x: s.tx, y: s.ty });
        if (d < 70) damageEnemy(e, lerp(60, 15, d / 70));
      }
    }
  }
}

// ---------- enemies update ----------
function updateEnemies(dt) {
  for (const e of G.enemies) {
    e.flash = Math.max(0, e.flash - dt * 4);
    // pick target: nearest player capital ship (drones may chase squads)
    let tgt = null, bd = 1e9;
    for (const s of G.ships) { const d = dist(e, s); if (d < bd) { bd = d; tgt = s; } }
    if (e.type === 'drone') {
      for (const sq of G.squads) {
        if (sq.state === 'docked') continue;
        for (const c of sq.craft) if (c.alive) { const d = dist(e, c); if (d < bd * 0.7) { bd = d / 0.7; tgt = c; } }
      }
    }
    if (!tgt) continue;
    e.angle = angTo(e, tgt);

    const standoff = e.type === 'asteroid' ? 0 : e.range * 0.75;
    if (bd > standoff) {
      e.x += Math.cos(e.angle) * e.speed * dt;
      e.y += Math.sin(e.angle) * e.speed * dt;
    }

    if (e.type === 'asteroid') {
      // ram damage
      if (bd < e.r + (tgt.r || 8)) {
        damagePlayer(tgt, e.dmg);
        damageEnemy(e, 9999);
      }
      continue;
    }

    e.cd -= dt;
    if (e.cd <= 0 && bd < e.range) {
      e.cd = e.fireCd;
      G.bullets.push({ x: e.x, y: e.y, a: e.angle, sp: 260, dmg: e.dmg, life: 1.4, friendly: false, color: e.color });
    }
  }
}

function damageEnemy(e, dmg) {
  e.hp -= dmg;
  e.flash = 1;
  if (e.hp <= 0 && !e.dead) {
    e.dead = true;
    G.totalKills++;
    boom(e.x, e.y, e.r * 1.6, e.color);
    G.pickups.push({ x: e.x, y: e.y, v: e.credits, t: 1.4 });
    G.credits += e.credits;
  }
}

function damagePlayer(s, dmg) {
  if (s.maxHp) { // capital ship
    s.hp -= dmg; s.flash = 1;
    if (s.hp <= 0 && !s.dead) {
      s.dead = true;
      boom(s.x, s.y, s.r * 2.2, '#7fd4ff');
      G.shake = 16;
    }
  } else { // squadron craft
    s.hp -= dmg;
    if (s.hp <= 0 && s.alive) { s.alive = false; boom(s.x, s.y, 14, '#5ce1ff'); }
  }
}

// ---------- projectiles ----------
function updateBullets(dt) {
  for (let i = G.bullets.length - 1; i >= 0; i--) {
    const b = G.bullets[i];
    b.life -= dt;
    b.x += Math.cos(b.a) * b.sp * dt;
    b.y += Math.sin(b.a) * b.sp * dt;
    let hit = false;
    if (b.friendly) {
      for (const e of G.enemies) if (dist(b, e) < e.r + 3) { damageEnemy(e, b.dmg); hit = true; break; }
    } else {
      for (const s of G.ships) if (dist(b, s) < s.r + 3) { damagePlayer(s, b.dmg); hit = true; break; }
      if (!hit) outer: for (const sq of G.squads) {
        if (sq.state === 'docked') continue;
        for (const c of sq.craft) if (c.alive && dist(b, c) < 9) { damagePlayer(c, b.dmg); hit = true; break outer; }
      }
    }
    if (hit || b.life <= 0) G.bullets.splice(i, 1);
  }
  for (let i = G.torps.length - 1; i >= 0; i--) {
    const t = G.torps[i];
    t.life -= dt;
    if (t.target && t.target.hp > 0) {
      const want = angTo(t, t.target);
      let d = ((want - t.a + Math.PI * 3) % TAU) - Math.PI;
      t.a += clamp(d, -2.2 * dt, 2.2 * dt);
    }
    t.sp = Math.min(t.sp + 160 * dt, 320);
    t.x += Math.cos(t.a) * t.sp * dt;
    t.y += Math.sin(t.a) * t.sp * dt;
    G.fx.push({ type: 'trail', x: t.x, y: t.y, t: 0.3, max: 0.3, color: '#ffb46b', r: 3 });
    let hit = false;
    for (const e of G.enemies) if (dist(t, e) < e.r + 4) { damageEnemy(e, t.dmg); boom(t.x, t.y, 20, '#ffb46b'); hit = true; break; }
    if (hit || t.life <= 0) G.torps.splice(i, 1);
  }
}

// ---------- fx ----------
function boom(x, y, r, color) {
  G.fx.push({ type: 'boom', x, y, r, t: 0.5, max: 0.5, color });
  for (let i = 0; i < 10; i++) {
    const a = rand(0, TAU), sp = rand(30, 140);
    G.fx.push({ type: 'spark', x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, t: rand(0.3, 0.7), max: 0.7, color });
  }
}

function updateFx(dt) {
  for (let i = G.fx.length - 1; i >= 0; i--) {
    const f = G.fx[i];
    f.t -= dt;
    if (f.type === 'spark') { f.x += f.vx * dt; f.y += f.vy * dt; f.vx *= 0.96; f.vy *= 0.96; }
    if (f.t <= 0) G.fx.splice(i, 1);
  }
  for (let i = G.pickups.length - 1; i >= 0; i--) {
    const p = G.pickups[i];
    p.t -= dt; p.y -= 24 * dt;
    if (p.t <= 0) G.pickups.splice(i, 1);
  }
}

// ---------- main update ----------
function update(dt) {
  G.time += dt;
  G.shake = Math.max(0, G.shake - dt * 30);
  if (G.msgT > 0) G.msgT -= dt;

  if (G.state === 'warp') {
    G.warpT -= dt;
    if (G.warpT <= 0) { G.state = 'shop'; }
    return;
  }
  if (G.state !== 'playing') return;

  // spawn queue
  for (let i = G.spawnQueue.length - 1; i >= 0; i--) {
    G.spawnQueue[i].t -= dt;
    if (G.spawnQueue[i].t <= 0) { spawnEnemy(G.spawnQueue[i].type); G.spawnQueue.splice(i, 1); }
  }

  for (const s of G.ships) { s.flash = Math.max(0, s.flash - dt * 4); if (s.cooldown) s.cooldown = Math.max(0, s.cooldown - dt); }

  updateSquads(dt);
  updateEnemies(dt);
  updateBullets(dt);
  updateShells(dt);
  updateFx(dt);

  // cull dead
  G.enemies = G.enemies.filter(e => !e.dead);
  const before = G.ships.length;
  G.ships = G.ships.filter(s => !s.dead);
  if (G.ships.length < before) {
    // squads whose carrier died are lost
    G.squads = G.squads.filter(sq => G.ships.includes(sq.carrier));
    relabelSquads();
  }

  // defeat?
  if (!G.ships.some(s => s.kind === 'carrier')) { G.state = 'gameover'; return; }

  // wave clear?
  if (G.waveActive && G.spawnQueue.length === 0 && G.enemies.length === 0) {
    G.waveActive = false;
    for (const sq of G.squads) recallSquad(sq);
    const local = ((G.wave - 1) % WAVES_PER_SECTOR) + 1;
    if (local === WAVES_PER_SECTOR) {
      G.sector++;
      G.state = 'warp'; G.warpT = 2.2;
      announce('SECTOR CLEAR — WARPING', 2.2);
    } else {
      G.state = 'shop';
    }
  }
}

// ============================================================
// RENDERING
// ============================================================
function draw() {
  ctx.clearRect(0, 0, W, H);
  const shx = rand(-G.shake, G.shake), shy = rand(-G.shake, G.shake);
  ctx.save();
  ctx.translate(shx, shy);

  drawBackground();

  if (G.state === 'menu') { drawMenu(); ctx.restore(); return; }

  drawPickups();
  drawShips();
  drawSquads();
  drawEnemies();
  drawProjectiles();
  drawFx();
  drawPathPreview();
  ctx.restore();

  drawHud();
  if (G.state === 'shop') drawShop();
  if (G.state === 'warp') drawWarp();
  if (G.state === 'gameover') drawGameover();
  if (G.msgT > 0 && G.state === 'playing') {
    ctx.globalAlpha = clamp(G.msgT, 0, 1);
    text(G.msg, W / 2, H * 0.22, 26, '#8fdcff', 'center', true);
    ctx.globalAlpha = 1;
  }
}

function drawBackground() {
  const grad = ctx.createLinearGradient(0, 0, 0, H);
  grad.addColorStop(0, '#0a0d24');
  grad.addColorStop(1, '#05060f');
  ctx.fillStyle = grad;
  ctx.fillRect(-20, -20, W + 40, H + 40);
  const warp = G.state === 'warp';
  for (const s of stars) {
    const sx = s.x * W, sy = (s.y * H + (warp ? G.time * 900 * s.z % H : 0)) % H;
    ctx.fillStyle = `rgba(180,200,255,${0.25 + s.z * 0.5})`;
    if (warp) ctx.fillRect(sx, sy, 1.5, 30 * s.z);
    else ctx.fillRect(sx, sy, 1.5 * s.z + 0.5, 1.5 * s.z + 0.5);
  }
}

function shipGlow(x, y, r, color) {
  const g = ctx.createRadialGradient(x, y, 0, x, y, r * 2.2);
  g.addColorStop(0, color); g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.globalAlpha = 0.18; ctx.fillStyle = g;
  ctx.beginPath(); ctx.arc(x, y, r * 2.2, 0, TAU); ctx.fill();
  ctx.globalAlpha = 1;
}

function drawShips() {
  for (const s of G.ships) {
    shipGlow(s.x, s.y, s.r, '#4aa8ff');
    ctx.save();
    ctx.translate(s.x, s.y);
    ctx.rotate(s.angle);
    const hurt = s.flash > 0;
    if (s.kind === 'carrier') {
      ctx.fillStyle = hurt ? '#fff' : '#274a73';
      ctx.strokeStyle = '#7fd4ff'; ctx.lineWidth = 2;
      poly([[38, 0], [10, -14], [-30, -14], [-38, -6], [-38, 6], [-30, 14], [10, 14]]);
      ctx.fill(); ctx.stroke();
      // deck stripe
      ctx.fillStyle = '#12233b';
      ctx.fillRect(-26, -5, 52, 10);
      ctx.strokeStyle = '#3f6f9f'; ctx.strokeRect(-26, -5, 52, 10);
    } else {
      ctx.fillStyle = hurt ? '#fff' : '#3d5a3f';
      ctx.strokeStyle = '#9fe6a0'; ctx.lineWidth = 2;
      poly([[24, 0], [4, -10], [-20, -10], [-24, 0], [-20, 10], [4, 10]]);
      ctx.fill(); ctx.stroke();
      // barrels
      ctx.strokeStyle = '#cfeecf';
      ctx.beginPath(); ctx.moveTo(4, -4); ctx.lineTo(20, -4); ctx.moveTo(4, 4); ctx.lineTo(20, 4); ctx.stroke();
      if (s.cooldown > 0) {
        ctx.rotate(-s.angle);
        ctx.strokeStyle = 'rgba(159,230,160,0.5)';
        ctx.beginPath(); ctx.arc(0, 0, s.r + 8, -Math.PI / 2, -Math.PI / 2 + TAU * (1 - s.cooldown / 5)); ctx.stroke();
      }
    }
    ctx.restore();
    hpBar(s.x, s.y - s.r - 12, s.r * 2, s.hp / s.maxHp);
  }
}

function poly(pts) {
  ctx.beginPath();
  ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
  ctx.closePath();
}

function drawSquads() {
  for (const sq of G.squads) {
    if (sq.state === 'docked') continue;
    // path
    if (sq.state === 'flying') {
      ctx.strokeStyle = 'rgba(92,225,255,0.25)'; ctx.lineWidth = 2; ctx.setLineDash([6, 8]);
      ctx.beginPath();
      ctx.moveTo(sq.x, sq.y);
      for (let i = sq.pathI; i < sq.path.length; i++) ctx.lineTo(sq.path[i].x, sq.path[i].y);
      ctx.stroke(); ctx.setLineDash([]);
    }
    for (const c of sq.craft) {
      if (!c.alive) continue;
      ctx.save();
      ctx.translate(c.x, c.y); ctx.rotate(c.angle);
      if (sq.type === 'fighter') {
        ctx.fillStyle = '#173a52'; ctx.strokeStyle = '#5ce1ff'; ctx.lineWidth = 1.5;
        poly([[8, 0], [-6, -5], [-3, 0], [-6, 5]]);
      } else {
        ctx.fillStyle = '#40331c'; ctx.strokeStyle = '#ffb46b'; ctx.lineWidth = 1.5;
        poly([[9, 0], [-5, -7], [-7, 0], [-5, 7]]);
      }
      ctx.fill(); ctx.stroke();
      ctx.restore();
    }
  }
}

function drawEnemies() {
  for (const e of G.enemies) {
    ctx.save();
    ctx.translate(e.x, e.y);
    const c = e.flash > 0.4 ? '#ffffff' : e.color;
    if (e.type === 'asteroid') {
      ctx.rotate(G.time * e.spin);
      ctx.fillStyle = e.flash > 0.4 ? '#fff' : '#4a3d2c';
      ctx.strokeStyle = e.color; ctx.lineWidth = 2;
      ctx.beginPath();
      for (let i = 0; i < 8; i++) {
        const a = i / 8 * TAU, rr = e.r * (0.75 + 0.25 * Math.sin(i * 2.7));
        const px = Math.cos(a) * rr, py = Math.sin(a) * rr;
        i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
      }
      ctx.closePath(); ctx.fill(); ctx.stroke();
    } else {
      ctx.rotate(e.angle);
      ctx.fillStyle = e.flash > 0.4 ? '#fff' : '#2a1520';
      ctx.strokeStyle = c; ctx.lineWidth = 2;
      if (e.type === 'drone') poly([[8, 0], [-7, -6], [-4, 0], [-7, 6]]);
      else if (e.type === 'raider') poly([[12, 0], [-4, -9], [-10, -4], [-10, 4], [-4, 9]]);
      else poly([[26, 0], [8, -12], [-18, -12], [-24, 0], [-18, 12], [8, 12]]);
      ctx.fill(); ctx.stroke();
    }
    ctx.restore();
    if (e.hp < e.maxHp) hpBar(e.x, e.y - e.r - 9, e.r * 2, e.hp / e.maxHp, '#ff5252');
  }
}

function drawProjectiles() {
  for (const b of G.bullets) {
    ctx.strokeStyle = b.color; ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(b.x, b.y);
    ctx.lineTo(b.x - Math.cos(b.a) * 9, b.y - Math.sin(b.a) * 9);
    ctx.stroke();
  }
  for (const t of G.torps) {
    ctx.save(); ctx.translate(t.x, t.y); ctx.rotate(t.a);
    ctx.fillStyle = '#ffb46b';
    ctx.fillRect(-5, -2, 10, 4);
    ctx.restore();
  }
  // artillery shell reticles + shells
  for (const s of G.shells) {
    const p = s.t / s.dur;
    // reticle
    ctx.strokeStyle = `rgba(255,210,74,${0.4 + 0.4 * Math.sin(G.time * 10)})`;
    ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.arc(s.tx, s.ty, 16 * (1 - p * 0.5), 0, TAU); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(s.tx - 22, s.ty); ctx.lineTo(s.tx + 22, s.ty);
    ctx.moveTo(s.tx, s.ty - 22); ctx.lineTo(s.tx, s.ty + 22); ctx.stroke();
    // shell arc (fake ballistic: rises then falls onto target)
    const x = lerp(s.sx, s.tx, p), y = lerp(s.sy, s.ty, p) - Math.sin(p * Math.PI) * 120;
    ctx.fillStyle = '#ffd24a';
    ctx.beginPath(); ctx.arc(x, y, 3, 0, TAU); ctx.fill();
  }
}

function drawFx() {
  for (const f of G.fx) {
    const p = f.t / f.max;
    if (f.type === 'boom') {
      ctx.globalAlpha = p;
      ctx.strokeStyle = f.color; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.arc(f.x, f.y, f.r * (1.4 - p), 0, TAU); ctx.stroke();
      ctx.globalAlpha = p * 0.4;
      ctx.fillStyle = f.color;
      ctx.beginPath(); ctx.arc(f.x, f.y, f.r * (1 - p) , 0, TAU); ctx.fill();
    } else if (f.type === 'spark') {
      ctx.globalAlpha = p;
      ctx.fillStyle = f.color;
      ctx.fillRect(f.x - 1.5, f.y - 1.5, 3, 3);
    } else if (f.type === 'trail') {
      ctx.globalAlpha = p * 0.5;
      ctx.fillStyle = f.color;
      ctx.beginPath(); ctx.arc(f.x, f.y, f.r * p, 0, TAU); ctx.fill();
    }
    ctx.globalAlpha = 1;
  }
}

function drawPickups() {
  for (const p of G.pickups) {
    ctx.globalAlpha = clamp(p.t, 0, 1);
    text('+' + p.v, p.x, p.y, 13, '#ffd24a', 'center');
    ctx.globalAlpha = 1;
  }
}

function drawPathPreview() {
  if (input.drawing && input.path.length > 1) {
    ctx.strokeStyle = 'rgba(92,225,255,0.8)'; ctx.lineWidth = 2.5; ctx.setLineDash([8, 6]);
    ctx.beginPath();
    ctx.moveTo(input.path[0].x, input.path[0].y);
    for (const p of input.path) ctx.lineTo(p.x, p.y);
    ctx.stroke(); ctx.setLineDash([]);
    const last = input.path[input.path.length - 1];
    ctx.strokeStyle = '#5ce1ff';
    ctx.beginPath(); ctx.arc(last.x, last.y, 10, 0, TAU); ctx.stroke();
  }
  // artillery targeting hint
  if (input.selected && input.selected.ship && G.state === 'playing') {
    text('TAP TO SET BOMBARDMENT TARGET', W / 2, H * 0.3, 16, '#9fe6a0', 'center', true);
  }
}

function hpBar(x, y, w, p, color = '#6be29a') {
  p = clamp(p, 0, 1);
  ctx.fillStyle = 'rgba(0,0,0,0.55)';
  ctx.fillRect(x - w / 2, y, w, 4);
  ctx.fillStyle = p > 0.35 ? color : '#ff5252';
  ctx.fillRect(x - w / 2, y, w * p, 4);
}

function text(str, x, y, size, color, align = 'left', glow = false) {
  ctx.font = `bold ${size}px "Courier New", monospace`;
  ctx.textAlign = align; ctx.textBaseline = 'middle';
  if (glow) { ctx.shadowColor = color; ctx.shadowBlur = 12; }
  ctx.fillStyle = color;
  ctx.fillText(str, x, y);
  ctx.shadowBlur = 0;
}

// ---------- HUD ----------
function drawHud() {
  if (G.state === 'menu' || G.state === 'gameover') return;
  // top bar
  text(`CREDITS ${G.credits}`, 16, 24, 16, '#ffd24a');
  const local = ((G.wave - 1) % WAVES_PER_SECTOR) + 1;
  text(`SECTOR ${G.sector}  WAVE ${local}/${WAVES_PER_SECTOR}`, W - 16, 24, 16, '#8fdcff', 'right');
  text(`KILLS ${G.totalKills}`, W / 2, 24, 14, '#666e8f', 'center');

  // bottom squadron bar
  for (const b of uiButtons()) {
    const sel = input.selected && (input.selected.squad === b.squad || input.selected.ship === b.ship);
    ctx.fillStyle = sel ? 'rgba(92,225,255,0.25)' : 'rgba(10,16,34,0.85)';
    ctx.strokeStyle = sel ? '#5ce1ff' : '#2c3a5e';
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.roundRect(b.x, b.y, b.w, b.h, 8); ctx.fill(); ctx.stroke();
    if (b.squad) {
      const sq = b.squad;
      const alive = sq.craft.filter(c => c.alive).length;
      const col = sq.type === 'fighter' ? '#5ce1ff' : '#ffb46b';
      text(sq.label, b.x + b.w / 2, b.y + 16, 17, col, 'center');
      const st = !squadAlive(sq) ? 'LOST' : sq.state === 'docked' ? 'READY' : sq.state === 'returning' ? 'RTB' : 'OUT';
      text(st, b.x + b.w / 2, b.y + 34, 11, st === 'READY' ? '#6be29a' : st === 'LOST' ? '#ff5252' : '#aab3d0', 'center');
      // craft pips
      for (let i = 0; i < sq.craft.length; i++) {
        ctx.fillStyle = i < alive ? col : '#333c58';
        ctx.fillRect(b.x + b.w / 2 - sq.craft.length * 5 + i * 10 + 2, b.y + b.h - 12, 6, 6);
      }
    } else {
      text(b.label, b.x + b.w / 2, b.y + 16, 17, '#9fe6a0', 'center');
      const rdy = b.ship.cooldown <= 0;
      text(rdy ? 'READY' : Math.ceil(b.ship.cooldown) + 's', b.x + b.w / 2, b.y + 34, 11, rdy ? '#6be29a' : '#aab3d0', 'center');
      text('TAP MAP', b.x + b.w / 2, b.y + b.h - 10, 9, '#666e8f', 'center');
    }
  }
}

// ---------- shop ----------
function shopRects() {
  const w = Math.min(460, W - 40), x = W / 2 - w / 2;
  const ih = 64, gap = 10;
  let y = H * 0.2;
  const items = SHOP.map(item => {
    const r = { x, y, w, h: ih, item };
    y += ih + gap;
    return r;
  });
  return { items, launch: { x, y: y + 8, w, h: 56 } };
}

function drawShop() {
  ctx.fillStyle = 'rgba(3,5,14,0.82)';
  ctx.fillRect(0, 0, W, H);
  text('FLEET COMMAND — RESUPPLY', W / 2, H * 0.11, 26, '#8fdcff', 'center', true);
  text(`CREDITS: ${G.credits}`, W / 2, H * 0.155, 18, '#ffd24a', 'center');
  const r = shopRects();
  for (const it of r.items) {
    const afford = G.credits >= it.item.cost;
    ctx.fillStyle = 'rgba(14,22,44,0.95)';
    ctx.strokeStyle = afford ? '#3f6f9f' : '#2a3050';
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.roundRect(it.x, it.y, it.w, it.h, 8); ctx.fill(); ctx.stroke();
    text(it.item.name, it.x + 16, it.y + 22, 15, afford ? '#dbe6ff' : '#5a6382');
    text(it.item.desc, it.x + 16, it.y + 44, 12, '#7a86ab');
    text(it.item.cost + 'c', it.x + it.w - 16, it.y + 32, 17, afford ? '#ffd24a' : '#5a6382', 'right');
  }
  ctx.fillStyle = '#123a24'; ctx.strokeStyle = '#6be29a'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.roundRect(r.launch.x, r.launch.y, r.launch.w, r.launch.h, 8); ctx.fill(); ctx.stroke();
  text('▶ LAUNCH NEXT WAVE', W / 2, r.launch.y + r.launch.h / 2, 20, '#6be29a', 'center', true);
}

function drawWarp() {
  text(`WARPING TO SECTOR ${G.sector}`, W / 2, H / 2, 30, '#8fdcff', 'center', true);
}

// ---------- menu / gameover ----------
function drawMenu() {
  text('STRIKEFLEET', W / 2, H * 0.32, 52, '#8fdcff', 'center', true);
  text('OMEGA — RECREATED', W / 2, H * 0.32 + 48, 24, '#ffd24a', 'center', true);
  const lines = [
    'Your carrier is Earth\'s last hope. Hold the line.',
    '',
    'DRAG from your carrier (or tap a squadron button, then drag)',
    'to draw a flight path — fighters & bombers follow it and engage.',
    'Tap an ARTILLERY button, then tap the map to bombard.',
    'Tap a deployed squadron\'s button to recall it.',
    'Survive the waves. Buy reinforcements. Warp onward.',
  ];
  lines.forEach((l, i) => text(l, W / 2, H * 0.48 + i * 24, 14, '#aab3d0', 'center'));
  if (Math.sin(G.time * 4) > -0.3) text('— TAP TO BEGIN —', W / 2, H * 0.78, 22, '#6be29a', 'center', true);
}

function drawGameover() {
  ctx.fillStyle = 'rgba(3,5,14,0.8)';
  ctx.fillRect(0, 0, W, H);
  text('FLEET DESTROYED', W / 2, H * 0.38, 40, '#ff5252', 'center', true);
  text(`You held for ${G.wave} waves across ${G.sector} sector${G.sector > 1 ? 's' : ''} — ${G.totalKills} kills`, W / 2, H * 0.48, 17, '#aab3d0', 'center');
  if (Math.sin(G.time * 4) > -0.3) text('— TAP TO TRY AGAIN —', W / 2, H * 0.6, 20, '#6be29a', 'center', true);
}

// ---------- loop ----------
let last = performance.now();
function frame(now) {
  const dt = Math.min((now - last) / 1000, 0.05);
  last = now;
  update(dt); // update() advances G.time every frame, in all states
  draw();
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

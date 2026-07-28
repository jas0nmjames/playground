import { Component } from 'react';
import {
  GROUPS_META, ALL_ROWS, ROW_GROUP, TOOLS, STORAGE_KEY, COLORS, TAKE_DEFAULT,
  defaultSections, beatCount, makeSectionNotes, makeBeatSubs, makeGroupSubs, resizeBeatArray, normalizeProject,
} from './constants.js';
import { buildStaffShapes } from './staff.js';
import BlocksPanel from './components/BlocksPanel.jsx';
import StaffPanel from './components/StaffPanel.jsx';
import SettingsDrawer from './components/SettingsDrawer.jsx';
import InsightsPanel, { InsightTooltip } from './components/InsightsPanel.jsx';
import ExplainModal from './components/ExplainModal.jsx';

const HANDOFF_ACK_KEY = 'dut-dut-handoff-ack-v1';
const EXPLAIN_LEVEL_KEY = 'dut-dut-explain-level-v1';

export default class App extends Component {
  state = {
    screen: 'editor',        // 'editor' | 'preview'
    viewport: 'desktop',     // 'desktop' | 'mobile'
    mobileTab: 'blocks',     // 'blocks' | 'staff' | 'learn'
    settingsOpen: false,
    sections: defaultSections(),
    activeSectionId: 'intro',
    beatSubs: null,          // { [sectionId]: number[] } — ruler subdivisions (2/3/4) per beat
    groupSubs: null,         // { [sectionId]: { [groupId]: number[] } } — per-part overrides, 0 = inherit
    notes: null,             // { [sectionId]: { [rowId]: number[][] } } — [beat][sub] note values
    live: null,              // { [sectionId]: { [rowId]: number[][] } } — [beat][sub] tap metadata
    tool: 'hit',
    perPart: false,          // show the per-part ÷ chip row
    selectedRowId: null,     // the drum Space taps into
    tapMode: 'quant',        // 'quant' | 'exact'
    swing: 0,
    metronome: false,
    tempo: 120,
    playing: false,
    playBeat: -1,            // fractional beat position of the playhead
    muted: { cymbal: false, snare: false, tenor: false, bass: false },
    painting: null,          // { value } while a drag-paint is in progress
    rendering: false,        // WAV export in progress
    projectStatus: 'Autosaves in this browser as you edit',
    insightsOpen: true,
    insightScope: 'section', // 'section' | 'cadence'
    pinnedInsightId: null,
    hoverInsightId: null,
    tip: null,               // { id, x, y } for the staff-band hover tooltip
    llmText: '',
    llmLabel: '',
    llmLoading: false,
    explainOpen: false,
    explainLevel: 'new',     // see LEVELS in insights-engine
    handoffAcked: false,     // first-run handoff disclosure dismissed
  };

  constructor(props) {
    super(props);
    const notes = {}, live = {}, beatSubs = {}, groupSubs = {};
    for (const s of this.state.sections) {
      notes[s.id] = makeSectionNotes(s);
      live[s.id] = makeSectionNotes(s);
      beatSubs[s.id] = makeBeatSubs(s);
      groupSubs[s.id] = makeGroupSubs(s);
    }
    this.state = { ...this.state, notes, live, beatSubs, groupSubs };
    this._marks = [];        // recent { beat, time } scheduler marks, for the visual clock
  }

  componentDidMount() {
    if (window.innerWidth < 820) this.setState({ viewport: 'mobile' });
    this._mouseUpHandler = () => this.cellUp();
    window.addEventListener('mouseup', this._mouseUpHandler);
    this._keyHandler = (e) => this.onKeyDown(e);
    window.addEventListener('keydown', this._keyHandler);
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) this._applyProject(JSON.parse(saved));
    } catch (e) { /* keep defaults */ }
    this._llmOk = typeof window !== 'undefined' && window.claude && typeof window.claude.complete === 'function';
    import('./insights-engine.js').then(m => { this._insights = m; this.forceUpdate(); }).catch(() => {});
    try {
      const acked = localStorage.getItem(HANDOFF_ACK_KEY) === '1';
      const lvl = localStorage.getItem(EXPLAIN_LEVEL_KEY);
      this.setState({ handoffAcked: acked, explainLevel: lvl || 'new' });
    } catch (e) { /* keep defaults */ }
  }
  componentWillUnmount() {
    window.removeEventListener('mouseup', this._mouseUpHandler);
    window.removeEventListener('keydown', this._keyHandler);
    clearTimeout(this._saveT);
    clearTimeout(this._tipT);
    cancelAnimationFrame(this._raf);
    this._scheduler?.stop();
  }

  _persist() {
    clearTimeout(this._saveT);
    this._saveT = setTimeout(() => {
      try { localStorage.setItem(STORAGE_KEY, this._serializeProject()); } catch (e) { /* storage full/blocked */ }
    }, 400);
  }
  _serializeProject() {
    const { tempo, swing, sections, beatSubs, groupSubs, notes, live, activeSectionId } = this.state;
    return JSON.stringify({ v: 3, app: 'dut-dut', tempo, swing, sections, beatSubs, groupSubs, notes, live, activeSectionId });
  }
  _project() {
    const { tempo, swing, sections, beatSubs, groupSubs, notes, live } = this.state;
    return { tempo, swing, sections, beatSubs, groupSubs, notes, live };
  }
  _applyProject(p) {
    const norm = normalizeProject(p);
    if (this.state.playing) this._stopClock();
    this.setState({ ...norm, playing: false, playBeat: -1 });
    this._persist();
  }

  _activeSection() {
    return this.state.sections.find(s => s.id === this.state.activeSectionId) || this.state.sections[0];
  }
  // Effective subdivisions for one part: its own override where set, else the ruler.
  _subsFor(sectionId, groupId) {
    const master = this.state.beatSubs[sectionId];
    const ov = (this.state.groupSubs[sectionId] || {})[groupId];
    if (!ov) return master;
    return master.map((m, i) => ov[i] || m);
  }

  async _ensureAudio() {
    if (!this._enginePromise) this._enginePromise = import('./audio-engine.js');
    const mod = await this._enginePromise;
    if (!this._voicePlayers) this._voicePlayers = mod.buildVoicePlayers();
    if (!this._audioCtx) this._audioCtx = new AudioContext();
    this._audioCtx.resume();
    if (!this._scheduler) {
      this._scheduler = new mod.VarScheduler({
        audioContext: this._audioCtx,
        getPositionCount: () => beatCount(this._activeSection()),
        getDuration: () => 60 / this.state.tempo,
        onScheduleStep: (beat, time) => this._onStep(mod, beat, time),
      });
    }
    return mod;
  }

  // One scheduler step is one beat: every part places its own subdivisions inside it.
  _onStep(mod, beat, time) {
    const section = this._activeSection();
    const notesFor = this.state.notes[section.id];
    const liveFor = this.state.live[section.id];
    const beatDur = 60 / this.state.tempo;
    const ctx = this._audioCtx, dest = ctx.destination;
    this._marks.push({ beat, time });
    if (this._marks.length > 32) this._marks.shift();
    if (this.state.metronome) mod.playMetronome(ctx, time, dest, beat % 4 === 0);
    for (const row of ALL_ROWS) {
      if (this.state.muted[row.groupId]) continue;
      const sc = this._subsFor(section.id, row.groupId)[beat];
      const dur = beatDur / sc;
      const arr = notesFor[row.id][beat] || [];
      const larr = (liveFor && liveFor[row.id] && liveFor[row.id][beat]) || [];
      const play = this._voicePlayers[row.id];
      for (let s = 0; s < sc; s++) {
        const v = arr[s];
        if (!v) continue;
        let t = time + s * dur;
        const m = larr[s] || 0;
        if (m >= 2) t += (m - 2) * dur;
        else if (sc % 2 === 0 && s % 2 === 1) t += dur * (this.state.swing / 100) * 0.5;
        if (v === 1) play(ctx, t, dest, 1);
        else if (v === 2) play(ctx, t, dest, 2);
        else if (v === 3) { play(ctx, Math.max(0.001, t - 0.028), dest, 0); play(ctx, t, dest, 1); }
        else if (v === 4) { play(ctx, t, dest, 1); play(ctx, t + dur / 2, dest, 1); }
        else if (v === 5) { for (let i = 0; i < 4; i++) play(ctx, t + i * dur / 4, dest, i === 0 ? 1 : 0); }
      }
    }
  }

  _markAt(now) {
    let best = null;
    for (const m of this._marks) if (m.time <= now && (!best || m.time > best.time)) best = m;
    return best;
  }
  // Where the music actually is right now, in fractional beats.
  _beatPos(now) {
    const m = this._markAt(now);
    if (!m) return -1;
    const beatDur = 60 / this.state.tempo;
    const beats = beatCount(this._activeSection());
    const pos = m.beat + Math.max(0, Math.min(1.2, (now - m.time) / beatDur));
    return ((pos % beats) + beats) % beats;
  }
  _startClock() {
    cancelAnimationFrame(this._raf);
    const loop = () => {
      if (!this.state.playing) return;
      this._raf = requestAnimationFrame(loop);
      const now = performance.now();
      if (now - (this._lastPaint || 0) < 55) return;
      this._lastPaint = now;
      const pos = this._beatPos(this._audioCtx.currentTime);
      if (pos >= 0) this.setState({ playBeat: pos });
    };
    this._raf = requestAnimationFrame(loop);
  }
  _stopClock() {
    cancelAnimationFrame(this._raf);
    this._scheduler?.stop();
    this._marks = [];
  }

  togglePlay = async () => {
    if (this.state.playing) {
      this._stopClock();
      this.setState({ playing: false, playBeat: -1 });
      return;
    }
    await this._ensureAudio();
    this._marks = [];
    this._scheduler.start();
    this.setState({ playing: true }, () => this._startClock());
  };

  // Space is a drumstick, never a transport control: it only writes notes.
  onKeyDown = (e) => {
    if (e.code !== 'Space' || e.metaKey || e.ctrlKey || e.altKey) return;
    const t = e.target;
    if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
    e.preventDefault();
    if (e.repeat) return;
    if (this.state.playing && this.state.selectedRowId) this._recordTap();
  };

  // Space during playback writes into the selected drum — either at the moment it was
  // played (exact) or pulled to the nearest subdivision (auto-rhythm).
  _recordTap() {
    if (!this._audioCtx) return;
    const rowId = this.state.selectedRowId;
    const section = this._activeSection();
    const beats = beatCount(section);
    const now = this._audioCtx.currentTime - (this._audioCtx.outputLatency || this._audioCtx.baseLatency || 0);
    const pos = this._beatPos(now);
    if (pos < 0) return;
    const subs = this._subsFor(section.id, ROW_GROUP[rowId]);
    let b = Math.floor(pos);
    const frac = pos - b;
    const sc = subs[b] || 4;
    const toolV = (TOOLS.find(tl => tl.id === this.state.tool) || {}).v || 1;
    const value = toolV || 1;
    let sub, meta;
    if (this.state.tapMode === 'quant') {
      let k = Math.round(frac * sc);
      if (k >= sc) { b = (b + 1) % beats; k = 0; }
      sub = k; meta = 1;
    } else {
      const k = Math.max(0, Math.min(sc - 1, Math.floor(frac * sc)));
      sub = k; meta = 2 + Math.max(0, Math.min(0.995, frac * sc - k));
    }
    this._writeCell(rowId, b, sub, value, meta);
    if (this._voicePlayers && !this.state.muted[ROW_GROUP[rowId]]) {
      this._voicePlayers[rowId](this._audioCtx, this._audioCtx.currentTime + 0.005, this._audioCtx.destination, value === 2 ? 2 : 1);
    }
  }

  setTempo = (v) => { this.setState({ tempo: Math.max(40, Math.min(240, Math.round(Number(v) || 120))) }); this._persist(); };

  selectSection = (id) => {
    if (this.state.playing) { this._stopClock(); this.setState({ playing: false, playBeat: -1 }); }
    this.setState({ activeSectionId: id });
    this._persist();
  };
  addSection = () => {
    const id = 'section' + Date.now();
    const section = { id, name: 'Section ' + (this.state.sections.length + 1), measures: 4 };
    this.setState({
      sections: [...this.state.sections, section],
      notes: { ...this.state.notes, [id]: makeSectionNotes(section) },
      live: { ...this.state.live, [id]: makeSectionNotes(section) },
      beatSubs: { ...this.state.beatSubs, [id]: makeBeatSubs(section) },
      groupSubs: { ...this.state.groupSubs, [id]: makeGroupSubs(section) },
      activeSectionId: id,
    });
    this._persist();
  };
  renameSection = (id, name) => { this.setState({ sections: this.state.sections.map(s => s.id === id ? { ...s, name } : s) }); this._persist(); };
  setSectionMeasures = (id, measures) => {
    measures = Math.max(1, Math.min(16, Math.round(Number(measures) || 1)));
    const sections = this.state.sections.map(s => s.id === id ? { ...s, measures } : s);
    const count = measures * 4;
    const subs = resizeBeatArray(this.state.beatSubs[id], count, () => 4);
    const gs = {};
    for (const gm of GROUPS_META) gs[gm.id] = resizeBeatArray((this.state.groupSubs[id] || {})[gm.id] || [], count, () => 0);
    const rows = {}, lrows = {};
    for (const row of ALL_ROWS) {
      const sizeAt = (i) => gs[row.groupId][i] || subs[i];
      rows[row.id] = resizeBeatArray(this.state.notes[id][row.id], count, (i) => new Array(sizeAt(i)).fill(0));
      lrows[row.id] = resizeBeatArray(this.state.live[id][row.id], count, (i) => new Array(sizeAt(i)).fill(0));
    }
    this.setState({
      sections,
      beatSubs: { ...this.state.beatSubs, [id]: subs },
      groupSubs: { ...this.state.groupSubs, [id]: gs },
      notes: { ...this.state.notes, [id]: rows },
      live: { ...this.state.live, [id]: lrows },
    });
    this._persist();
  };
  deleteSection = (id) => {
    if (this.state.sections.length <= 1) return;
    const sections = this.state.sections.filter(s => s.id !== id);
    const notes = { ...this.state.notes }; delete notes[id];
    const live = { ...this.state.live }; delete live[id];
    const beatSubs = { ...this.state.beatSubs }; delete beatSubs[id];
    const groupSubs = { ...this.state.groupSubs }; delete groupSubs[id];
    const activeSectionId = this.state.activeSectionId === id ? sections[0].id : this.state.activeSectionId;
    this.setState({ sections, notes, live, beatSubs, groupSubs, activeSectionId });
    this._persist();
  };

  // Any subdivision change re-buckets every row to its part's new cell count.
  _applySubs(master, gsubs) {
    const sid = this._activeSection().id;
    const beats = master.length;
    const rows = {}, lrows = {};
    for (const row of ALL_ROWS) {
      const oldN = this.state.notes[sid][row.id], oldL = this.state.live[sid][row.id];
      const nb = [], nl = [];
      for (let b = 0; b < beats; b++) {
        const sc = (gsubs[row.groupId] && gsubs[row.groupId][b]) || master[b];
        const on = oldN[b] || [], ol = (oldL && oldL[b]) || [];
        const na = new Array(sc).fill(0), la = new Array(sc).fill(0);
        for (let i = 0; i < Math.min(sc, on.length); i++) { na[i] = on[i]; la[i] = ol[i] || 0; }
        nb.push(na); nl.push(la);
      }
      rows[row.id] = nb; lrows[row.id] = nl;
    }
    this.setState({
      beatSubs: { ...this.state.beatSubs, [sid]: master },
      groupSubs: { ...this.state.groupSubs, [sid]: gsubs },
      notes: { ...this.state.notes, [sid]: rows },
      live: { ...this.state.live, [sid]: lrows },
    });
    this._persist();
  }
  cycleBeatSub = (beatIdx) => {
    const sid = this._activeSection().id;
    const master = this.state.beatSubs[sid].slice();
    master[beatIdx] = master[beatIdx] === 4 ? 3 : master[beatIdx] === 3 ? 2 : 4;
    this._applySubs(master, this.state.groupSubs[sid]);
  };
  cycleGroupBeatSub = (groupId, beatIdx) => {
    const sid = this._activeSection().id;
    const gsubs = { ...this.state.groupSubs[sid] };
    const arr = (gsubs[groupId] || []).slice();
    const cur = arr[beatIdx] || 0;
    arr[beatIdx] = cur === 0 ? 4 : cur === 4 ? 3 : cur === 3 ? 2 : 0;
    gsubs[groupId] = arr;
    this._applySubs(this.state.beatSubs[sid], gsubs);
  };
  resetGroupSubs = (groupId) => {
    const sid = this._activeSection().id;
    const gsubs = { ...this.state.groupSubs[sid] };
    gsubs[groupId] = new Array(this.state.beatSubs[sid].length).fill(0);
    this._applySubs(this.state.beatSubs[sid], gsubs);
  };
  resetAllSubs = () => {
    const sid = this._activeSection().id;
    const gsubs = {};
    for (const gm of GROUPS_META) gsubs[gm.id] = new Array(this.state.beatSubs[sid].length).fill(0);
    this._applySubs(this.state.beatSubs[sid], gsubs);
  };
  togglePerPart = () => this.setState({ perPart: !this.state.perPart });

  setSwing = (v) => { this.setState({ swing: Number(v) }); this._persist(); };
  toggleMetronome = () => this.setState({ metronome: !this.state.metronome });
  toggleMute = (groupId) => this.setState({ muted: { ...this.state.muted, [groupId]: !this.state.muted[groupId] } });
  setTool = (id) => this.setState({ tool: id });
  selectRow = (rowId) => {
    this._lastRow = { ...(this._lastRow || {}), [ROW_GROUP[rowId]]: rowId };
    this.setState({ selectedRowId: this.state.selectedRowId === rowId ? null : rowId });
  };
  armGroup = (groupId) => {
    if (ROW_GROUP[this.state.selectedRowId] === groupId) { this.setState({ selectedRowId: null }); return; }
    const gm = GROUPS_META.find(g => g.id === groupId);
    const rowId = ((this._lastRow || {})[groupId]) || gm.rowDefs[0].id;
    this.setState({ selectedRowId: rowId });
  };
  setTapMode = (m) => this.setState({ tapMode: m });

  _writeCell(rowId, beat, sub, value, meta) {
    const sid = this._activeSection().id;
    const beats = this.state.notes[sid][rowId].slice();
    const na = beats[beat].slice();
    na[sub] = value;
    beats[beat] = na;
    const lbeats = this.state.live[sid][rowId].slice();
    const la = (lbeats[beat] || []).slice();
    la[sub] = value ? (meta || 0) : 0;
    lbeats[beat] = la;
    this.setState({
      notes: { ...this.state.notes, [sid]: { ...this.state.notes[sid], [rowId]: beats } },
      live: { ...this.state.live, [sid]: { ...this.state.live[sid], [rowId]: lbeats } },
    });
    this._persist();
  }
  cellDown = (rowId, beat, sub) => {
    const section = this._activeSection();
    const cur = this.state.notes[section.id][rowId][beat][sub];
    const toolV = TOOLS.find(tl => tl.id === this.state.tool).v;
    const value = (toolV !== 0 && cur === toolV) ? 0 : toolV;
    this._writeCell(rowId, beat, sub, value, 0);
    this.setState({ painting: { value } });
  };
  cellEnter = (rowId, beat, sub) => {
    if (!this.state.painting) return;
    this._writeCell(rowId, beat, sub, this.state.painting.value, 0);
  };
  cellUp = () => this.state.painting && this.setState({ painting: null });
  clearSection = () => {
    const sid = this._activeSection().id;
    const rows = {}, lrows = {};
    for (const row of ALL_ROWS) {
      const sizes = this._subsFor(sid, row.groupId);
      rows[row.id] = sizes.map(sc => new Array(sc).fill(0));
      lrows[row.id] = sizes.map(sc => new Array(sc).fill(0));
    }
    this.setState({ notes: { ...this.state.notes, [sid]: rows }, live: { ...this.state.live, [sid]: lrows } });
    this._persist();
  };
  clearTake = () => {
    const sid = this._activeSection().id;
    const rows = {}, lrows = {};
    for (const row of ALL_ROWS) {
      const nb = this.state.notes[sid][row.id], lb = this.state.live[sid][row.id];
      rows[row.id] = nb.map((cell, b) => cell.map((v, s) => ((lb[b] && lb[b][s]) ? 0 : v)));
      lrows[row.id] = lb.map(cell => cell.map(() => 0));
    }
    this.setState({ notes: { ...this.state.notes, [sid]: rows }, live: { ...this.state.live, [sid]: lrows } });
    this._persist();
  };

  setViewport = (v) => this.setState({ viewport: v });
  setScreen = (s) => this.setState({ screen: s });
  setMobileTab = (t) => this.setState({ mobileTab: t });
  toggleSettings = () => this.setState({ settingsOpen: !this.state.settingsOpen });

  toggleInsights = () => this.setState({ insightsOpen: !this.state.insightsOpen });
  setInsightScope = (s) => this.setState({ insightScope: s });
  hoverInsight = (id) => { clearTimeout(this._tipT); this.setState({ hoverInsightId: id }); };
  unhoverInsight = () => {
    clearTimeout(this._tipT);
    this._tipT = setTimeout(() => this.setState({ hoverInsightId: null, tip: null }), 160);
  };
  tipKeep = () => clearTimeout(this._tipT);
  bandEnter = (ins, e) => {
    clearTimeout(this._tipT);
    const x = Math.min(e.clientX + 14, (window.innerWidth || 1200) - 286);
    const y = Math.min(e.clientY + 16, (window.innerHeight || 800) - 200);
    this.setState({ hoverInsightId: ins.id, tip: { id: ins.id, x, y } });
  };
  pinInsight = (ins) => {
    if (this.state.pinnedInsightId === ins.id) { this.setState({ pinnedInsightId: null }); return; }
    const tg = (ins.targets || []).find(x => x.beats && x.beats.length);
    if (tg && tg.sectionId !== this.state.activeSectionId) this.selectSection(tg.sectionId);
    this.setState({ pinnedInsightId: ins.id });
  };
  _analysisOpts() {
    return {
      scope: this.state.insightScope, activeSectionId: this.state.activeSectionId,
      groups: GROUPS_META.map(g => ({ id: g.id, name: g.name })),
      rows: ALL_ROWS.map(r => ({ id: r.id, groupId: r.groupId })),
    };
  }
  openExplain = () => this.setState({ explainOpen: true });
  closeExplain = () => this.setState({ explainOpen: false });
  setExplainLevel = (id) => {
    this.setState({ explainLevel: id });
    try { localStorage.setItem(EXPLAIN_LEVEL_KEY, id); } catch (e) { /* storage blocked */ }
  };
  ackHandoff = () => {
    this.setState({ handoffAcked: true });
    try { localStorage.setItem(HANDOFF_ACK_KEY, '1'); } catch (e) { /* storage blocked */ }
  };
  // The exact text the user previews and sends — nothing else leaves the app.
  _explainText() {
    if (!this._insights) return '';
    try {
      const ctx = this._insights.buildCadenceContext(this._project(), this._analysisOpts());
      return this._insights.renderContextMarkdown(ctx, { level: this.state.explainLevel });
    } catch (e) {
      return '';
    }
  }

  askClaude = async () => {
    if (this.state.llmLoading || !this._llmOk || !this._insights) return;
    const label = this.state.insightScope === 'cadence' ? 'Claude on the full cadence' : 'Claude on "' + this._activeSection().name + '"';
    this.setState({ llmLoading: true });
    try {
      const prompt = this._insights.buildLLMPrompt(this._project(), { ...this._analysisOpts(), level: this.state.explainLevel });
      const text = await window.claude.complete(prompt);
      this.setState({ llmText: String(text || '').trim(), llmLabel: label, llmLoading: false });
    } catch (e) {
      this.setState({ llmText: 'Could not reach Claude just now — try again in a moment.', llmLabel: 'Claude', llmLoading: false });
    }
  };

  onSaveProject = async () => {
    const u = await import('./export-utils.js');
    u.downloadBlob(new Blob([this._serializeProject()], { type: 'application/json' }), 'dut-dut-project.json');
  };
  onLoadFile = async (e) => {
    const f = e.target.files && e.target.files[0];
    if (!f) return;
    try {
      const txt = await f.text();
      this._applyProject(JSON.parse(txt));
      this.setState({ projectStatus: 'Loaded "' + f.name + '"' });
    } catch (err) {
      this.setState({ projectStatus: 'Could not read that file — expected a dut dut project .json' });
    }
    e.target.value = '';
  };
  onExportMidi = async () => {
    const u = await import('./export-utils.js');
    u.downloadBlob(new Blob([u.buildMidi(this._project())], { type: 'audio/midi' }), 'dut-dut.mid');
  };
  onExportWav = async () => {
    if (this.state.rendering) return;
    this.setState({ rendering: true });
    try {
      const u = await import('./export-utils.js');
      const blob = await u.renderWav(this._project());
      u.downloadBlob(blob, 'dut-dut.wav');
    } finally {
      this.setState({ rendering: false });
    }
  };
  onExportPng = async () => {
    const u = await import('./export-utils.js');
    const beatW = 96, leftPad = 60;
    const opts = { unison: this.props.unisonNotation ?? true };
    const render = this.state.sections.map(sec => ({
      name: sec.name,
      groups: GROUPS_META.map(g => ({
        name: g.name, color: g.color,
        shapes: buildStaffShapes(
          g,
          g.rowDefs.map(rd => this.state.notes[sec.id][rd.id]),
          g.rowDefs.map(rd => this.state.live[sec.id][rd.id]),
          this._subsFor(sec.id, g.id), sec.measures, beatW, leftPad, opts,
        ),
      })),
    }));
    await u.renderScorePng(render, { title: 'dut dut — cadence', tempo: this.state.tempo });
  };

  render() {
    const { screen, viewport, mobileTab, settingsOpen, sections, tempo, playing, playBeat } = this.state;
    const section = this._activeSection();
    const isMobile = viewport === 'mobile';
    const isEditor = screen === 'editor';
    const isPreview = screen === 'preview';
    const { accent, onAccent, text, mutedText, border } = COLORS;
    const takeColor = this.props.takeColor || TAKE_DEFAULT;

    const tabStyle = (active) => ({ background: active ? accent : 'transparent', color: active ? onAccent : mutedText });

    const subsByGroup = {};
    for (const g of GROUPS_META) subsByGroup[g.id] = this._subsFor(section.id, g.id);
    const overrides = this.state.groupSubs[section.id] || {};
    const anyOverride = GROUPS_META.some(g => (overrides[g.id] || []).some(v => v));
    const selRow = ALL_ROWS.find(r => r.id === this.state.selectedRowId) || null;
    const hasTake = ALL_ROWS.some(r => (this.state.live[section.id][r.id] || []).some(cell => cell.some(m => m)));

    // ---- Insights ----
    const insightsLayout = ['sidebar', 'bottom', 'inline'].includes(this.props.insightsLayout) ? this.props.insightsLayout : 'sidebar';
    const showHighlights = this.props.insightHighlights ?? true;
    let insights = [];
    if (this._insights) {
      try {
        insights = this._insights.analyzeProject(this._project(), this._analysisOpts());
      } catch (e) { insights = []; }
    }
    const focusId = this.state.hoverInsightId || this.state.pinnedInsightId;
    const focusInsight = insights.find(ins => ins.id === focusId) || null;
    let focusBeatByGroup = null;
    if (isEditor && focusInsight) {
      focusBeatByGroup = {};
      for (const tg of focusInsight.targets) {
        if (tg.sectionId !== section.id) continue;
        const gids = tg.groupId ? [tg.groupId] : GROUPS_META.map(g => g.id);
        for (const gid of gids) {
          if (!focusBeatByGroup[gid]) focusBeatByGroup[gid] = new Set();
          tg.beats.forEach(bb => focusBeatByGroup[gid].add(bb));
        }
      }
    }

    const sectionNameOf = (sid) => { const sx = sections.find(x => x.id === sid); return sx ? sx.name : ''; };
    let prevCardSection = null;
    const insightCards = insights.map(ins => {
      const pinned = this.state.pinnedInsightId === ins.id;
      const focused = focusId === ins.id;
      const secLabel = this.state.insightScope === 'cadence' ? (ins.sectionId ? sectionNameOf(ins.sectionId) : 'Overall') : null;
      const showSectionLabel = secLabel !== null && secLabel !== prevCardSection;
      if (secLabel !== null) prevCardSection = secLabel;
      return {
        key: ins.id,
        title: ins.title, body: ins.body, color: ins.color,
        terms: ins.terms || [],
        hasTerms: !!(ins.terms && ins.terms.length),
        showSectionLabel, sectionLabel: secLabel || '',
        border: focused || pinned ? ins.color : 'oklch(88% 0.01 80)',
        bg: pinned ? 'color-mix(in oklch, oklch(98% 0.006 80) 86%, ' + ins.color + ')' : 'oklch(98% 0.006 80)',
        enter: () => this.hoverInsight(ins.id),
        leave: this.unhoverInsight,
        pin: () => this.pinInsight(ins),
      };
    });
    const tipIns = this.state.tip ? insights.find(ins => ins.id === this.state.tip.id) : null;
    const tipData = tipIns ? {
      x: this.state.tip.x, y: this.state.tip.y, color: tipIns.color,
      title: tipIns.title, body: tipIns.body, terms: tipIns.terms || [],
    } : null;

    const sidebarInsightsDisplay = isEditor && this.state.insightsOpen && (isMobile ? mobileTab === 'learn' : insightsLayout === 'sidebar') ? 'flex' : 'none';
    const bottomInsightsDisplay = isEditor && !isMobile && this.state.insightsOpen && insightsLayout === 'bottom' ? 'flex' : 'none';
    const showLearnBtn = !isMobile && isEditor && insightsLayout !== 'inline';
    const llmProps = {
      llmAvailable: !!this._llmOk && !!this._insights,
      onAskClaude: this.askClaude,
      askClaudeLabel: this.state.llmLoading ? 'Asking Claude…' : 'Ask Claude to explain this pattern',
      llmText: this.state.llmText,
      llmLabel: this.state.llmLabel,
      explainAvailable: !!this._insights,
      onExplain: this.openExplain,
    };
    const insightsPanelProps = {
      cards: insightCards,
      scope: this.state.insightScope,
      setScope: this.setInsightScope,
      onClose: this.toggleInsights,
      ...llmProps,
    };

    return (
      <div className="app-shell" onMouseUp={this.cellUp}>
        <div
          className="device-frame"
          style={isMobile
            ? { width: '430px', height: '844px', margin: '28px 0', borderRadius: '32px', boxShadow: '0 30px 90px rgba(0,0,0,0.25)' }
            : { width: '100%', height: '100vh' }}
        >
          <div className="app-header">
            <div className="header-left">
              <div className="app-title">dut dut</div>
              <div className="tab-track">
                <button className="tab-btn" onClick={() => this.setScreen('editor')} style={tabStyle(isEditor)}>Editor</button>
                <button className="tab-btn" onClick={() => this.setScreen('preview')} style={tabStyle(isPreview)}>Preview</button>
              </div>
            </div>
            <div className="header-right">
              {showLearnBtn && (
                <button
                  className="learn-btn"
                  onClick={this.toggleInsights}
                  style={this.state.insightsOpen
                    ? { background: accent, color: onAccent, borderColor: accent }
                    : { background: 'oklch(96% 0.008 80)', color: mutedText, borderColor: border }}
                >
                  Learn
                </button>
              )}
              <button className="play-btn" onClick={this.togglePlay}>{playing ? '■ Stop' : '▶ Play'}</button>
              <button className="icon-btn" aria-label="Settings" onClick={this.toggleSettings}>⚙</button>
            </div>
          </div>

          <div className="section-tabs-bar">
            {sections.map(s => {
              const active = s.id === section.id;
              return (
                <button
                  key={s.id}
                  className="chip"
                  onClick={() => this.selectSection(s.id)}
                  style={{ background: active ? accent : 'oklch(96% 0.008 80)', color: active ? onAccent : text, borderColor: active ? accent : border }}
                >
                  {s.name} <span className="chip-sub">· {s.measures}m</span>
                </button>
              );
            })}
            <button className="chip chip--dashed" onClick={this.addSection}>+ Section</button>
            {isEditor && isMobile && (
              <div className="mode-toggle">
                <button onClick={() => this.setMobileTab('blocks')} style={tabStyle(mobileTab === 'blocks')}>Blocks</button>
                <button onClick={() => this.setMobileTab('staff')} style={tabStyle(mobileTab === 'staff')}>Staff</button>
                <button onClick={() => this.setMobileTab('learn')} style={tabStyle(mobileTab === 'learn')}>Learn</button>
              </div>
            )}
          </div>

          <div className="main-column">
            <div className="main-area" style={{ flexDirection: isEditor && !isMobile ? 'row' : 'column' }}>
              <BlocksPanel
                style={{
                  display: isEditor && (!isMobile || mobileTab === 'blocks') ? 'flex' : 'none',
                  flex: !isMobile ? '1.35 1 0%' : '1 1 auto',
                }}
                isMobile={isMobile}
                section={section}
                masterSubs={this.state.beatSubs[section.id]}
                subsByGroup={subsByGroup}
                overrides={overrides}
                sectionNotes={this.state.notes[section.id]}
                sectionLive={this.state.live[section.id]}
                tool={this.state.tool}
                setTool={this.setTool}
                tempo={tempo}
                muted={this.state.muted}
                toggleMute={this.toggleMute}
                cycleBeatSub={this.cycleBeatSub}
                cycleGroupBeatSub={this.cycleGroupBeatSub}
                resetGroupSubs={this.resetGroupSubs}
                perPart={this.state.perPart}
                togglePerPart={this.togglePerPart}
                selectedRowId={this.state.selectedRowId}
                selectRow={this.selectRow}
                armGroup={this.armGroup}
                selRow={selRow}
                tapMode={this.state.tapMode}
                setTapMode={this.setTapMode}
                hasTake={hasTake}
                clearTake={this.clearTake}
                takeColor={takeColor}
                cellDown={this.cellDown}
                cellEnter={this.cellEnter}
                playBeat={playBeat}
                tintByGroup={focusBeatByGroup}
                focusColor={focusInsight ? focusInsight.color : null}
              />
              <StaffPanel
                style={{
                  display: isPreview || (isEditor && (!isMobile || mobileTab === 'staff')) ? 'flex' : 'none',
                  flex: !isMobile && isEditor ? '1 1 0%' : '1 1 auto',
                }}
                isMobile={isMobile}
                isPreview={isPreview}
                section={section}
                subsByGroup={subsByGroup}
                sectionNotes={this.state.notes[section.id]}
                sectionLive={this.state.live[section.id]}
                tempo={tempo}
                playing={playing}
                onTogglePlay={this.togglePlay}
                playBeat={playBeat}
                unison={this.props.unisonNotation ?? true}
                takeColor={takeColor}
                hasTake={hasTake}
                insights={insights}
                showBands={isEditor && showHighlights}
                focusId={focusId}
                focusColor={focusInsight ? focusInsight.color : null}
                tintByGroup={focusBeatByGroup}
                onBandEnter={this.bandEnter}
                onBandLeave={this.unhoverInsight}
              />
              <InsightsPanel
                variant="sidebar"
                style={{ display: sidebarInsightsDisplay, flex: isMobile ? '1 1 auto' : '0 0 300px' }}
                showClose={!isMobile}
                {...insightsPanelProps}
              />
            </div>
            <InsightsPanel
              variant="bottom"
              style={{ display: bottomInsightsDisplay }}
              {...insightsPanelProps}
            />
          </div>

          <div className="footer-bar">
            <span>Created by Jason James · designed &amp; built with <a href="https://claude.ai" target="_blank" rel="noopener noreferrer">Claude</a></span>
          </div>

          {settingsOpen && <div className="settings-backdrop" onClick={this.toggleSettings} />}
          <SettingsDrawer
            open={settingsOpen}
            onClose={this.toggleSettings}
            isMobile={isMobile}
            tempo={tempo}
            setTempo={this.setTempo}
            metronome={this.state.metronome}
            toggleMetronome={this.toggleMetronome}
            setViewport={this.setViewport}
            clearSection={this.clearSection}
            selRow={selRow}
            tapMode={this.state.tapMode}
            setTapMode={this.setTapMode}
            hasTake={hasTake}
            clearTake={this.clearTake}
            takeColor={takeColor}
            perPart={this.state.perPart}
            togglePerPart={this.togglePerPart}
            anyOverride={anyOverride}
            resetAllSubs={this.resetAllSubs}
            swing={this.state.swing}
            setSwing={this.setSwing}
            muted={this.state.muted}
            toggleMute={this.toggleMute}
            sections={sections}
            addSection={this.addSection}
            renameSection={this.renameSection}
            setSectionMeasures={this.setSectionMeasures}
            deleteSection={this.deleteSection}
            onSaveProject={this.onSaveProject}
            onLoadFile={this.onLoadFile}
            onExportMidi={this.onExportMidi}
            onExportWav={this.onExportWav}
            onExportPng={this.onExportPng}
            projectStatus={this.state.projectStatus}
            rendering={this.state.rendering}
          />
          <InsightTooltip tip={tipData} tipKeep={this.tipKeep} tipLeave={this.unhoverInsight} />
          <ExplainModal
            open={this.state.explainOpen}
            onClose={this.closeExplain}
            text={this.state.explainOpen ? this._explainText() : ''}
            levels={(this._insights && this._insights.LEVELS) || []}
            level={this.state.explainLevel}
            setLevel={this.setExplainLevel}
            scopeLabel={this.state.insightScope === 'cadence'
              ? `The whole cadence — ${sections.length} sections`
              : `The "${section.name}" section only`}
            showDisclosure={!this.state.handoffAcked}
            onDismissDisclosure={this.ackHandoff}
          />
        </div>
      </div>
    );
  }
}

import { Component } from 'react';
import {
  GROUPS_META, ALL_ROWS, TOOLS, STORAGE_KEY, COLORS,
  defaultSections, makeSectionNotes, makeBeatSubs, resizeBeatArray, normalizeProject,
} from './constants.js';
import { buildStaffShapes } from './staff.js';
import BlocksPanel from './components/BlocksPanel.jsx';
import StaffPanel from './components/StaffPanel.jsx';
import SettingsDrawer from './components/SettingsDrawer.jsx';

export default class App extends Component {
  state = {
    screen: 'editor',        // 'editor' | 'preview'
    viewport: 'desktop',     // 'desktop' | 'mobile'
    mobileTab: 'blocks',     // 'blocks' | 'staff'
    settingsOpen: false,
    sections: defaultSections(),
    activeSectionId: 'intro',
    beatSubs: null,          // { [sectionId]: number[] } — subdivisions (2/3/4) per beat
    notes: null,             // { [sectionId]: { [rowId]: number[][] } } — [beat][sub] note values
    tool: 'hit',
    swing: 0,
    metronome: false,
    tempo: 120,
    playing: false,
    playheadPos: -1,
    muted: { cymbal: false, snare: false, tenor: false, bass: false },
    painting: null,          // { value } while a drag-paint is in progress
    rendering: false,        // WAV export in progress
    projectStatus: 'Autosaves in this browser as you edit',
  };

  constructor(props) {
    super(props);
    const notes = {}, beatSubs = {};
    for (const s of this.state.sections) { notes[s.id] = makeSectionNotes(s); beatSubs[s.id] = makeBeatSubs(s); }
    this.state = { ...this.state, notes, beatSubs };
  }

  componentDidMount() {
    if (window.innerWidth < 820) this.setState({ viewport: 'mobile' });
    this._mouseUpHandler = () => this.cellUp();
    window.addEventListener('mouseup', this._mouseUpHandler);
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) this._applyProject(JSON.parse(saved));
    } catch (e) { /* keep defaults */ }
  }
  componentWillUnmount() {
    window.removeEventListener('mouseup', this._mouseUpHandler);
    clearTimeout(this._saveT);
    this._scheduler?.stop();
  }

  _persist() {
    clearTimeout(this._saveT);
    this._saveT = setTimeout(() => {
      try { localStorage.setItem(STORAGE_KEY, this._serializeProject()); } catch (e) { /* storage full/blocked */ }
    }, 400);
  }
  _serializeProject() {
    const { tempo, swing, sections, beatSubs, notes, activeSectionId } = this.state;
    return JSON.stringify({ v: 2, app: 'dut-dut', tempo, swing, sections, beatSubs, notes, activeSectionId });
  }
  _project() {
    const { tempo, swing, sections, beatSubs, notes } = this.state;
    return { tempo, swing, sections, beatSubs, notes };
  }
  _applyProject(p) {
    const norm = normalizeProject(p);
    if (this.state.playing) this._scheduler?.stop();
    this.setState({ ...norm, playing: false, playheadPos: -1 });
    this._persist();
  }

  _activeSection() {
    return this.state.sections.find(s => s.id === this.state.activeSectionId) || this.state.sections[0];
  }
  _subs() { return this.state.beatSubs[this._activeSection().id]; }
  _posCount() { return this._subs().reduce((a, b) => a + b, 0); }
  _resolvePos(pos) {
    const subs = this._subs();
    let acc = 0;
    for (let b = 0; b < subs.length; b++) {
      if (pos < acc + subs[b]) return { beat: b, sub: pos - acc, subCount: subs[b] };
      acc += subs[b];
    }
    return { beat: 0, sub: 0, subCount: subs[0] || 4 };
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
        getPositionCount: () => this._posCount(),
        getDuration: (pos) => (60 / this.state.tempo) / this._resolvePos(pos).subCount,
        onScheduleStep: (pos, time) => this._onStep(mod, pos, time),
      });
    }
    return mod;
  }

  _onStep(mod, pos, time) {
    const section = this._activeSection();
    const notes = this.state.notes[section.id];
    const { beat, sub, subCount } = this._resolvePos(pos);
    const dur = (60 / this.state.tempo) / subCount;
    let t = time;
    if (subCount % 2 === 0 && sub % 2 === 1) t += dur * (this.state.swing / 100) * 0.5;
    if (this.state.metronome && sub === 0) {
      mod.playMetronome(this._audioCtx, t, this._audioCtx.destination, beat % 4 === 0);
    }
    const dest = this._audioCtx.destination;
    for (const row of ALL_ROWS) {
      if (this.state.muted[row.groupId]) continue;
      const v = notes[row.id][beat][sub];
      if (!v) continue;
      const play = this._voicePlayers[row.id];
      if (v === 1) play(this._audioCtx, t, dest, 1);
      else if (v === 2) play(this._audioCtx, t, dest, 2);
      else if (v === 3) { play(this._audioCtx, t - 0.028, dest, 0); play(this._audioCtx, t, dest, 1); }
      else if (v === 4) { play(this._audioCtx, t, dest, 1); play(this._audioCtx, t + dur / 2, dest, 1); }
      else if (v === 5) { for (let i = 0; i < 4; i++) play(this._audioCtx, t + i * dur / 4, dest, i === 0 ? 1 : 0); }
    }
    requestAnimationFrame(() => this.setState({ playheadPos: pos }));
  }

  togglePlay = async () => {
    if (this.state.playing) {
      this._scheduler?.stop();
      this.setState({ playing: false, playheadPos: -1 });
      return;
    }
    await this._ensureAudio();
    this._scheduler.start();
    this.setState({ playing: true });
  };

  setTempo = (v) => { this.setState({ tempo: Math.max(40, Math.min(240, Math.round(Number(v) || 120))) }); this._persist(); };

  selectSection = (id) => {
    if (this.state.playing) { this._scheduler?.stop(); this.setState({ playing: false, playheadPos: -1 }); }
    this.setState({ activeSectionId: id });
    this._persist();
  };
  addSection = () => {
    const id = 'section' + Date.now();
    const section = { id, name: 'Section ' + (this.state.sections.length + 1), measures: 4 };
    this.setState({
      sections: [...this.state.sections, section],
      notes: { ...this.state.notes, [id]: makeSectionNotes(section) },
      beatSubs: { ...this.state.beatSubs, [id]: makeBeatSubs(section) },
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
    const rows = {};
    for (const row of ALL_ROWS) rows[row.id] = resizeBeatArray(this.state.notes[id][row.id], count, (i) => new Array(subs[i]).fill(0));
    this.setState({ sections, beatSubs: { ...this.state.beatSubs, [id]: subs }, notes: { ...this.state.notes, [id]: rows } });
    this._persist();
  };
  deleteSection = (id) => {
    if (this.state.sections.length <= 1) return;
    const sections = this.state.sections.filter(s => s.id !== id);
    const notes = { ...this.state.notes }; delete notes[id];
    const beatSubs = { ...this.state.beatSubs }; delete beatSubs[id];
    const activeSectionId = this.state.activeSectionId === id ? sections[0].id : this.state.activeSectionId;
    this.setState({ sections, notes, beatSubs, activeSectionId });
    this._persist();
  };

  cycleBeatSub = (beatIdx) => {
    const section = this._activeSection();
    const subs = this.state.beatSubs[section.id].slice();
    const next = subs[beatIdx] === 4 ? 3 : subs[beatIdx] === 3 ? 2 : 4;
    subs[beatIdx] = next;
    const rows = {};
    for (const row of ALL_ROWS) {
      const beats = this.state.notes[section.id][row.id].slice();
      const old = beats[beatIdx];
      const na = new Array(next).fill(0);
      for (let i = 0; i < Math.min(next, old.length); i++) na[i] = old[i];
      beats[beatIdx] = na;
      rows[row.id] = beats;
    }
    this.setState({
      beatSubs: { ...this.state.beatSubs, [section.id]: subs },
      notes: { ...this.state.notes, [section.id]: rows },
    });
    this._persist();
  };

  setSwing = (v) => { this.setState({ swing: Number(v) }); this._persist(); };
  toggleMetronome = () => this.setState({ metronome: !this.state.metronome });
  toggleMute = (groupId) => this.setState({ muted: { ...this.state.muted, [groupId]: !this.state.muted[groupId] } });
  setTool = (id) => this.setState({ tool: id });

  _paintCell(rowId, beat, sub, value) {
    const section = this._activeSection();
    const beats = this.state.notes[section.id][rowId].slice();
    const na = beats[beat].slice();
    na[sub] = value;
    beats[beat] = na;
    this.setState({ notes: { ...this.state.notes, [section.id]: { ...this.state.notes[section.id], [rowId]: beats } } });
    this._persist();
  }
  cellDown = (rowId, beat, sub) => {
    const section = this._activeSection();
    const cur = this.state.notes[section.id][rowId][beat][sub];
    const toolV = TOOLS.find(tl => tl.id === this.state.tool).v;
    const value = (toolV !== 0 && cur === toolV) ? 0 : toolV;
    this._paintCell(rowId, beat, sub, value);
    this.setState({ painting: { value } });
  };
  cellEnter = (rowId, beat, sub) => {
    if (!this.state.painting) return;
    this._paintCell(rowId, beat, sub, this.state.painting.value);
  };
  cellUp = () => this.state.painting && this.setState({ painting: null });
  clearSection = () => {
    const section = this._activeSection();
    const subs = this.state.beatSubs[section.id];
    const rows = {};
    for (const row of ALL_ROWS) rows[row.id] = subs.map(sc => new Array(sc).fill(0));
    this.setState({ notes: { ...this.state.notes, [section.id]: rows } });
    this._persist();
  };

  setViewport = (v) => this.setState({ viewport: v });
  setScreen = (s) => this.setState({ screen: s });
  setMobileTab = (t) => this.setState({ mobileTab: t });
  toggleSettings = () => this.setState({ settingsOpen: !this.state.settingsOpen });

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
    const render = this.state.sections.map(sec => ({
      name: sec.name,
      groups: GROUPS_META.map(g => ({
        name: g.name, color: g.color,
        shapes: buildStaffShapes(g, g.rowDefs.map(rd => this.state.notes[sec.id][rd.id]), this.state.beatSubs[sec.id], sec.measures, beatW, leftPad),
      })),
    }));
    await u.renderScorePng(render, { title: 'dut dut — cadence', tempo: this.state.tempo });
  };

  render() {
    const { screen, viewport, mobileTab, settingsOpen, sections, tempo, playing, playheadPos } = this.state;
    const section = this._activeSection();
    const subs = this.state.beatSubs[section.id];
    const isMobile = viewport === 'mobile';
    const isEditor = screen === 'editor';
    const isPreview = screen === 'preview';
    const { accent, onAccent, text, mutedText, border } = COLORS;

    const tabStyle = (active) => ({ background: active ? accent : 'transparent', color: active ? onAccent : mutedText });

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
              </div>
            )}
          </div>

          <div className="main-area" style={{ flexDirection: isEditor && !isMobile ? 'row' : 'column' }}>
            <BlocksPanel
              style={{
                display: isEditor && (!isMobile || mobileTab === 'blocks') ? 'flex' : 'none',
                flex: !isMobile ? '1.35 1 0%' : '1 1 auto',
              }}
              isMobile={isMobile}
              section={section}
              subs={subs}
              sectionNotes={this.state.notes[section.id]}
              tool={this.state.tool}
              setTool={this.setTool}
              tempo={tempo}
              muted={this.state.muted}
              toggleMute={this.toggleMute}
              cycleBeatSub={this.cycleBeatSub}
              cellDown={this.cellDown}
              cellEnter={this.cellEnter}
              playheadPos={playheadPos}
            />
            <StaffPanel
              style={{
                display: isPreview || (isEditor && (!isMobile || mobileTab === 'staff')) ? 'flex' : 'none',
                flex: !isMobile && isEditor ? '1 1 0%' : '1 1 auto',
              }}
              isMobile={isMobile}
              isPreview={isPreview}
              section={section}
              subs={subs}
              sectionNotes={this.state.notes[section.id]}
              tempo={tempo}
              playing={playing}
              onTogglePlay={this.togglePlay}
              playheadPos={playheadPos}
              resolvePos={(pos) => this._resolvePos(pos)}
            />
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
        </div>
      </div>
    );
  }
}

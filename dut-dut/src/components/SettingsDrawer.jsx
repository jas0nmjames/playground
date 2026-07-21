import { GROUPS_META, COLORS } from '../constants.js';

export default function SettingsDrawer({
  open, onClose, isMobile,
  tempo, setTempo, metronome, toggleMetronome, setViewport, clearSection,
  swing, setSwing, muted, toggleMute,
  sections, addSection, renameSection, setSectionMeasures, deleteSection,
  onSaveProject, onLoadFile, onExportMidi, onExportWav, onExportPng, projectStatus, rendering,
}) {
  const { accent, onAccent, mutedText, text } = COLORS;
  const canDelete = sections.length > 1;

  return (
    <div
      className="settings-drawer"
      style={{ width: isMobile ? '100%' : '360px', transform: open ? 'translateX(0)' : 'translateX(100%)' }}
    >
      <div className="drawer-header">
        <div className="drawer-title">Settings</div>
        <button className="drawer-close" onClick={onClose}>×</button>
      </div>
      <div className="drawer-body">

        <div>
          <div className="drawer-section-title">Playback</div>
          <div className="tempo-row">
            <button className="stepper-btn" onClick={() => setTempo(tempo - 5)}>−</button>
            <input
              type="number"
              className="tempo-input"
              key={tempo}
              defaultValue={tempo}
              onBlur={e => setTempo(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') e.target.blur(); }}
            />
            <span className="unit-label">BPM</span>
            <button className="stepper-btn" onClick={() => setTempo(tempo + 5)}>+</button>
          </div>
          <div className="toggle-row">
            <span>Metronome click</span>
            <button
              className="pill-toggle"
              onClick={toggleMetronome}
              style={{ background: metronome ? accent : 'transparent', color: metronome ? onAccent : mutedText }}
            >
              {metronome ? 'On' : 'Off'}
            </button>
          </div>
          <div className="toggle-row">
            <span>Preview as</span>
            <div className="mini-track">
              <button onClick={() => setViewport('desktop')} style={{ background: !isMobile ? accent : 'transparent', color: !isMobile ? onAccent : mutedText }}>Desktop</button>
              <button onClick={() => setViewport('mobile')} style={{ background: isMobile ? accent : 'transparent', color: isMobile ? onAccent : mutedText }}>Mobile</button>
            </div>
          </div>
          <button className="danger-btn" onClick={clearSection}>Clear active section</button>
        </div>

        <div>
          <div className="drawer-section-title">Feel</div>
          <div className="swing-row">
            <span className="swing-label">Swing</span>
            <span className="swing-value">{swing}%</span>
          </div>
          <input type="range" min={0} max={100} value={swing} className="swing-slider" onChange={e => setSwing(e.target.value)} />
          <div className="small-note" style={{ marginTop: 4 }}>Applies to straight (even) beats only</div>
        </div>

        <div>
          <div className="drawer-section-title">Mute</div>
          <div className="mute-chip-row">
            {GROUPS_META.map(g => (
              <button
                key={g.id}
                className="mute-chip"
                onClick={() => toggleMute(g.id)}
                style={{ background: muted[g.id] ? 'oklch(72% 0.12 25)' : 'transparent', color: muted[g.id] ? text : mutedText }}
              >
                <span className="mute-chip-dot" style={{ background: g.color }} />
                {g.name}
              </button>
            ))}
          </div>
        </div>

        <div>
          <div className="drawer-section-header">
            <div className="drawer-section-title">Sections</div>
            <button className="add-btn" onClick={addSection}>+ Add</button>
          </div>
          <div className="section-list">
            {sections.map(sd => (
              <div key={sd.id} className="section-row">
                <input className="section-name-input" value={sd.name} onChange={e => renameSection(sd.id, e.target.value)} />
                <button className="stepper-btn small" onClick={() => setSectionMeasures(sd.id, sd.measures - 1)}>−</button>
                <span className="measures-label">{sd.measures}m</span>
                <button className="stepper-btn small" onClick={() => setSectionMeasures(sd.id, sd.measures + 1)}>+</button>
                <button
                  className="del-btn"
                  disabled={!canDelete}
                  style={{ opacity: canDelete ? 1 : 0.35 }}
                  onClick={() => deleteSection(sd.id)}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div className="drawer-section-title">Project</div>
          <div className="file-row">
            <button className="file-btn" onClick={onSaveProject}>Save file ↓</button>
            <label className="file-btn">
              Load file ↑
              <input type="file" accept=".json,application/json" onChange={onLoadFile} style={{ display: 'none' }} />
            </label>
          </div>
          <div className="small-note">{projectStatus}</div>
        </div>

        <div>
          <div className="drawer-section-title">Export</div>
          <div className="export-col">
            <button className="file-btn" onClick={onExportMidi}>MIDI file (.mid)</button>
            <button className="file-btn" onClick={onExportWav}>{rendering ? 'Rendering audio…' : 'Audio file (.wav)'}</button>
            <button className="file-btn" onClick={onExportPng}>Score image (.png)</button>
          </div>
          <div className="small-note" style={{ marginTop: 6 }}>Exports include every section in order</div>
        </div>

      </div>
    </div>
  );
}

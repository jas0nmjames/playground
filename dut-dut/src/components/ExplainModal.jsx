import { useState } from 'react';
import { DESTINATIONS, sendTo, copyText, downloadMarkdown, fitsInUrl, encodedLength, URL_LIMIT } from '../handoff.js';
import { COLORS } from '../constants.js';

// `levels` is passed in rather than imported so that insights-engine.js stays a
// lazily-loaded chunk instead of being pulled into the initial bundle.
export default function ExplainModal({
  open, onClose, text, levels = [], level, setLevel, scopeLabel, showDisclosure, onDismissDisclosure,
}) {
  const [status, setStatus] = useState('');
  if (!open) return null;

  const { accent, onAccent, mutedText } = COLORS;
  const fits = fitsInUrl(text);

  const handleSend = (dest) => {
    const r = sendTo(dest, text);
    setStatus(r.fellBack
      ? `Too long to prefill — copied to your clipboard instead. Paste it into the ${dest.label} tab that just opened.`
      : `Opened ${dest.label} with the pattern prefilled.`);
  };
  const handleCopy = () => {
    copyText(text)
      .then(() => setStatus('Copied to your clipboard — paste it into any assistant.'))
      .catch(() => setStatus('Could not reach the clipboard — select the text above and copy manually.'));
  };
  const handleDownload = () => {
    downloadMarkdown(text);
    setStatus('Saved dut-dut-cadence.md.');
  };

  return (
    <>
      <div className="settings-backdrop" style={{ zIndex: 20 }} onClick={onClose} />
      <div className="explain-modal" role="dialog" aria-label="Explain this pattern">
        <div className="drawer-header">
          <div className="drawer-title">Explain this pattern</div>
          <button className="drawer-close" onClick={onClose}>×</button>
        </div>

        <div className="explain-body">
          {showDisclosure && (
            <div className="explain-disclosure">
              <div className="explain-disclosure-title">Before you send this somewhere</div>
              <ul>
                <li><strong>What gets shared:</strong> the pattern you drew, your section names, and your tempo — shown in full below. Nothing about you, no account details.</li>
                <li><strong>What it costs:</strong> this opens an assistant you already use and spends <em>your</em> credits or plan usage, not the app's. dut dut never calls an AI itself.</li>
                <li><strong>Age requirements:</strong> assistants set their own minimums — claude.ai requires 18+, most others 13+ or parental consent. Check the service's terms before using it.</li>
              </ul>
              <button className="file-btn" style={{ flex: '0 0 auto', alignSelf: 'flex-start' }} onClick={onDismissDisclosure}>Got it</button>
            </div>
          )}

          <div className="explain-controls">
            <div className="explain-control">
              <div className="drawer-section-title" style={{ marginBottom: 6 }}>Explain it for</div>
              <div className="mini-track">
                {levels.map(l => (
                  <button
                    key={l.id}
                    onClick={() => setLevel(l.id)}
                    style={{ background: level === l.id ? accent : 'transparent', color: level === l.id ? onAccent : mutedText }}
                  >
                    {l.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="explain-control">
              <div className="drawer-section-title" style={{ marginBottom: 6 }}>Covering</div>
              <div className="small-note" style={{ fontSize: 11 }}>{scopeLabel}</div>
            </div>
          </div>

          <div className="drawer-section-title" style={{ marginBottom: 6 }}>Exactly what will be sent</div>
          <pre className="explain-preview">{text}</pre>
          <div className="small-note">
            {text.length.toLocaleString()} characters.{' '}
            {fits
              ? 'Short enough to open prefilled in a chat.'
              : `Too long to fit in a link (${encodedLength(text).toLocaleString()} encoded, limit ~${URL_LIMIT.toLocaleString()}) — sending will copy it and open an empty chat for you to paste into.`}
          </div>

          <div className="drawer-section-title" style={{ margin: '16px 0 6px' }}>Send it to</div>
          <div className="explain-dests">
            {DESTINATIONS.map(d => (
              <button key={d.id} className="file-btn" onClick={() => handleSend(d)}>{d.label} ↗</button>
            ))}
          </div>
          <div className="explain-dests" style={{ marginTop: 6 }}>
            <button className="file-btn" onClick={handleCopy}>Copy for any tool</button>
            <button className="file-btn" onClick={handleDownload}>Download .md</button>
          </div>
          <div className="small-note" style={{ marginTop: 8 }}>
            Opens in a new tab and uses your own account and credits. Works with any assistant — including a local model — via copy.
          </div>

          {status && <div className="explain-status">{status}</div>}
        </div>
      </div>
    </>
  );
}

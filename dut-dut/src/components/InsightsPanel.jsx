import { COLORS } from '../constants.js';

function ScopeToggle({ scope, setScope }) {
  const { accent, onAccent, mutedText } = COLORS;
  const style = (active) => ({ background: active ? accent : 'transparent', color: active ? onAccent : mutedText });
  return (
    <div className="scope-track">
      <button onClick={() => setScope('section')} style={style(scope === 'section')}>Section</button>
      <button onClick={() => setScope('cadence')} style={style(scope === 'cadence')}>Cadence</button>
    </div>
  );
}

function InsightCard({ card, variant }) {
  return (
    <div
      className={variant === 'bottom' ? 'insight-card insight-card--bottom' : 'insight-card'}
      onMouseEnter={card.enter}
      onMouseLeave={card.leave}
      onClick={card.pin}
      style={{ borderColor: card.border, background: card.bg }}
    >
      {variant === 'bottom' && card.showSectionLabel && (
        <div className="insight-section-label" style={{ marginBottom: 3 }}>{card.sectionLabel}</div>
      )}
      <div className="insight-card-head">
        <span className="insight-dot" style={{ background: card.color }} />
        <span className="insight-title">{card.title}</span>
      </div>
      <div className="insight-body">{card.body}</div>
      {card.hasTerms && (
        <div className="insight-terms">
          {card.terms.map(tm => (
            <a key={tm.url} href={tm.url} target="_blank" rel="noopener noreferrer">{tm.label} ↗</a>
          ))}
        </div>
      )}
    </div>
  );
}

function LlmBits({ llmAvailable, onAskClaude, askClaudeLabel, llmText, llmLabel, variant }) {
  return (
    <>
      {llmAvailable && (
        <button
          className="ask-claude-btn"
          style={variant === 'bottom' ? { flex: '0 0 190px' } : undefined}
          onClick={onAskClaude}
        >
          {askClaudeLabel}
        </button>
      )}
      {!!llmText && (
        <div className="llm-card" style={variant === 'bottom' ? { flex: '0 0 320px', overflow: 'auto' } : undefined}>
          <div className="llm-label">{llmLabel}</div>
          <div className="llm-text">{llmText}</div>
          <div className="llm-note">AI-generated — verify anything surprising</div>
        </div>
      )}
    </>
  );
}

// variant 'sidebar': right column (also fills the main area as the mobile Learn tab).
// variant 'bottom': horizontal strip under the main area.
export default function InsightsPanel({ variant, style, cards, scope, setScope, onClose, showClose, ...llm }) {
  if (variant === 'bottom') {
    return (
      <div className="insights-panel insights-panel--bottom" style={style}>
        <div className="insights-header">
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
            <div className="panel-title">Insights</div>
            <div className="small-note">Hover a card to light up the score · click to pin</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <ScopeToggle scope={scope} setScope={setScope} />
            <button className="insights-close" onClick={onClose}>×</button>
          </div>
        </div>
        <div className="insights-row">
          {cards.map(card => <InsightCard key={card.key} card={card} variant="bottom" />)}
          <LlmBits {...llm} variant="bottom" />
        </div>
      </div>
    );
  }

  return (
    <div className="insights-panel insights-panel--sidebar" style={style}>
      <div className="insights-header">
        <div className="panel-title">Insights</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <ScopeToggle scope={scope} setScope={setScope} />
          {showClose && <button className="insights-close" onClick={onClose}>×</button>}
        </div>
      </div>
      <div className="small-note" style={{ padding: '0 14px 8px' }}>Hover a card to light up the score · click to pin</div>
      <div className="insights-scroll">
        {cards.map(card => (
          <div key={card.key} style={{ display: 'contents' }}>
            {card.showSectionLabel && <div className="insight-section-label" style={{ marginTop: 4 }}>{card.sectionLabel}</div>}
            <InsightCard card={card} variant="sidebar" />
          </div>
        ))}
        <LlmBits {...llm} variant="sidebar" />
      </div>
    </div>
  );
}

export function InsightTooltip({ tip, tipKeep, tipLeave }) {
  if (!tip) return null;
  return (
    <div
      className="insight-tooltip"
      onMouseEnter={tipKeep}
      onMouseLeave={tipLeave}
      style={{ left: tip.x, top: tip.y, borderColor: tip.color }}
    >
      <div className="insight-card-head">
        <span className="insight-dot" style={{ background: tip.color }} />
        <span className="insight-title">{tip.title}</span>
      </div>
      <div className="insight-body">{tip.body}</div>
      <div className="insight-terms">
        {tip.terms.map(tm => (
          <a key={tm.url} href={tm.url} target="_blank" rel="noopener noreferrer">{tm.label} ↗</a>
        ))}
      </div>
    </div>
  );
}

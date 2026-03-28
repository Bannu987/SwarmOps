import { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';

// ─────────────────────────────────────────────────────────────
// CONSTANTS
// ─────────────────────────────────────────────────────────────
const API_URL = 'https://marketingos2-0.onrender.com';

const AGENTS_CFG = {
  nexus:    { name: 'Nexus',    role: 'CMO Orchestrator',    color: '#818cf8', icon: '⬡' },
  seo:      { name: 'SEO',      role: 'Search Optimization', color: '#22d3ee', icon: '◎' },
  content:  { name: 'Content',  role: 'Content Strategy',    color: '#f59e0b', icon: '✦' },
  ppc:      { name: 'PPC',      role: 'Paid Advertising',    color: '#f87171', icon: '◈' },
  analytics:{ name: 'Analytics',role: 'Data & Metrics',      color: '#4ade80', icon: '◉' },
  crm:      { name: 'CRM',      role: 'Email & Lifecycle',   color: '#a78bfa', icon: '◫' },
  smm:      { name: 'Social',   role: 'Social Media',        color: '#fb923c', icon: '◐' },
  brand:    { name: 'Brand',    role: 'Brand Identity',      color: '#f472b6', icon: '◆' },
  cro:      { name: 'CRO',      role: 'Conversion Opt.',     color: '#34d399', icon: '◑' },
  web_ux:   { name: 'Web/UX',   role: 'UX & Design',        color: '#60a5fa', icon: '◇' },
  research: { name: 'Research', role: 'Market Research',     color: '#c084fc', icon: '◌' },
  aeo:      { name: 'AEO',      role: 'AI Search Opt.',      color: '#2dd4bf', icon: '◯' },
};

const SLASH_COMMANDS = [
  { cmd: '/seo',       desc: 'SEO analysis & keyword research',  icon: '◎', shortcut: 'S' },
  { cmd: '/content',   desc: 'Content strategy & copywriting',   icon: '✦', shortcut: 'C' },
  { cmd: '/ppc',       desc: 'Paid advertising & campaigns',     icon: '◈', shortcut: 'P' },
  { cmd: '/analytics', desc: 'Data analysis & reporting',        icon: '◉', shortcut: 'A' },
  { cmd: '/crm',       desc: 'Email flows & lifecycle',          icon: '◫', shortcut: 'E' },
  { cmd: '/smm',       desc: 'Social media strategy',            icon: '◐', shortcut: 'M' },
  { cmd: '/aeo',       desc: 'AI search optimization',           icon: '◯', shortcut: 'O' },
  { cmd: '/cro',       desc: 'Conversion rate optimization',     icon: '◑', shortcut: 'V' },
  { cmd: '/publish',   desc: 'Create & publish blog post',       icon: '✦', shortcut: 'B' },
  { cmd: '/campaign',  desc: 'Launch ad campaign',               icon: '◆', shortcut: 'G' },
  { cmd: '/schema',    desc: 'Generate JSON-LD markup',          icon: '◇', shortcut: 'J' },
  { cmd: '/audit',     desc: 'Full marketing audit',             icon: '⬡', shortcut: 'U' },
  { cmd: '/tools',     desc: 'Manage data integrations',         icon: '◌', shortcut: 'T' },
  { cmd: '/approve',   desc: 'Approve a pending artifact',       icon: '✓', shortcut: 'R' },
];

const QUICK_ACTIONS = [
  { icon: '✦', label: 'Content Strategy',  text: 'Create a content strategy for Q1 2026 based on my brand', tag: 'Content' },
  { icon: '◎', label: 'SEO Opportunities', text: 'Find top SEO keyword opportunities for my business',       tag: 'SEO'     },
  { icon: '⬡', label: '90-Day Growth Plan',text: 'Build a 90-day growth plan with budget breakdown',         tag: 'Growth'  },
  { icon: '◉', label: 'Marketing Audit',   text: 'Run a complete marketing audit on https://',               tag: 'Audit'   },
];

const DATA_SOURCES = [
  { id: 'ga4',     name: 'Google Analytics 4',    icon: '◉', desc: 'Traffic, conversions, user behavior',  status: 'disconnected', freshness: null },
  { id: 'gsc',     name: 'Search Console',         icon: '◎', desc: 'Keyword rankings, impressions, CTR',  status: 'disconnected', freshness: null },
  { id: 'hubspot', name: 'HubSpot CRM',            icon: '◫', desc: 'Contacts, leads, deal pipeline',      status: 'disconnected', freshness: null },
  { id: 'gads',    name: 'Google Ads',             icon: '◈', desc: 'Campaign spend, ROAS, conversions',   status: 'disconnected', freshness: null },
];

const MEMORY_LAYERS = [
  { id: 'brand',        label: 'Brand DNA',         icon: '◆', desc: 'Core brand identity & positioning' },
  { id: 'competitive',  label: 'Competitive Intel', icon: '◎', desc: 'Competitor profiles & analysis'   },
  { id: 'conversation', label: 'Conversation',      icon: '◉', desc: 'Session context & preferences'    },
  { id: 'data',         label: 'Data Memory',       icon: '◫', desc: 'Metrics, benchmarks & KPIs'       },
  { id: 'learning',     label: 'Learning',          icon: '⬡', desc: 'Personalized agent behavior'      },
];

// ─────────────────────────────────────────────────────────────
// MARKDOWN
// ─────────────────────────────────────────────────────────────
function md(text) {
  if (!text) return '';
  let t = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  const blocks = [];
  t = t.replace(/```[\w]*\n?([\s\S]*?)```/g,(_,c)=>{const i=blocks.length;blocks.push(`<pre class="md-pre"><code>${c.trim()}</code></pre>`);return `\x00B${i}\x00`;});
  t = t.replace(/`([^`\n]+)`/g,'<code class="md-code">$1</code>');
  t = t.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>');
  t = t.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g,'<em>$1</em>');
  t = t.replace(/^### (.+)$/gm,'<h3 class="md-h3">$1</h3>');
  t = t.replace(/^## (.+)$/gm,'<h2 class="md-h2">$1</h2>');
  t = t.replace(/^# (.+)$/gm,'<h1 class="md-h1">$1</h1>');
  t = t.replace(/^&gt; (.+)$/gm,'<blockquote class="md-bq">$1</blockquote>');
  t = t.replace(/^---+$/gm,'<hr class="md-hr"/>');
  const lines=t.split('\n');const out=[];let ul=false,ol=false;
  for(const l of lines){const um=l.match(/^[ \t]*[-*+] (.+)$/);const om=l.match(/^\d+\. (.+)$/);
    if(um){if(ol){out.push('</ol>');ol=false;}if(!ul){out.push('<ul class="md-ul">');ul=true;}out.push(`<li>${um[1]}</li>`);}
    else if(om){if(ul){out.push('</ul>');ul=false;}if(!ol){out.push('<ol class="md-ol">');ol=true;}out.push(`<li>${om[1]}</li>`);}
    else{if(ul){out.push('</ul>');ul=false;}if(ol){out.push('</ol>');ol=false;}out.push(l);}
  }
  if(ul)out.push('</ul>');if(ol)out.push('</ol>');
  t=out.join('\n').replace(/\n/g,'<br/>');
  t=t.replace(/(<(?:ul|ol|pre|h[1-3]|blockquote)[^>]*>)(<br\/>)+/gi,'$1');
  t=t.replace(/(<br\/>)+(<\/(?:ul|ol|pre|h[1-3]|blockquote)>)/gi,'$2');
  blocks.forEach((b,i)=>{t=t.replace(`\x00B${i}\x00`,b);});
  return t;
}

// ─────────────────────────────────────────────────────────────
// SMALL COMPONENTS
// ─────────────────────────────────────────────────────────────
function ConfBadge({ score }) {
  if (!score) return null;
  const pct = Math.round(score * 100);
  const cls = pct >= 80 ? 'conf-high' : pct >= 55 ? 'conf-mid' : 'conf-low';
  return <span className={`conf-badge ${cls}`}>{pct}%</span>;
}

function AgentPill({ id }) {
  const cfg = AGENTS_CFG[id] || { name: id, icon: '◈', color: '#6366f1' };
  return (
    <span className="agent-pill" style={{ '--pc': cfg.color }}>
      <span className="ap-icon">{cfg.icon}</span>
      {cfg.name}
    </span>
  );
}

function StatusDot({ status }) {
  return <span className={`status-dot sd-${status}`} />;
}

// ─────────────────────────────────────────────────────────────
// ARTIFACT CARD  (response card — not a chat bubble)
// ─────────────────────────────────────────────────────────────
function ArtifactCard({ msg, onApprove, onClick, isSelected }) {
  const primaryId = msg.agents_used?.[0] || 'nexus';
  const cfg = AGENTS_CFG[primaryId] || AGENTS_CFG.nexus;

  const copy = () => navigator.clipboard?.writeText(msg.content);

  return (
    <div
      className={`artifact-card ${isSelected ? 'artifact-selected' : ''}`}
      style={{ '--agent-color': cfg.color }}
      onClick={onClick}
    >
      {/* Header */}
      <div className="ac-header">
        <div className="ac-agent">
          <span className="ac-icon" style={{ color: cfg.color }}>{cfg.icon}</span>
          <span className="ac-name">{cfg.name}</span>
          {msg.multi_agent && msg.agents_used?.length > 1 && (
            <span className="ac-multi">+{msg.agents_used.length - 1} agents</span>
          )}
        </div>
        <div className="ac-meta">
          {msg.confidence && <ConfBadge score={msg.confidence} />}
          {msg.latency_ms && (
            <span className="ac-latency">{(msg.latency_ms / 1000).toFixed(1)}s</span>
          )}
          <span className="ac-time">
            {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>

      {/* Agent pills (multi-agent) */}
      {msg.agents_used?.length > 1 && (
        <div className="ac-agents">
          {msg.agents_used.slice(0, 6).map((a, i) => <AgentPill key={i} id={a} />)}
          {msg.agents_used.length > 6 && (
            <span className="ac-agents-more">+{msg.agents_used.length - 6}</span>
          )}
        </div>
      )}

      {/* Body */}
      <div className="ac-body" dangerouslySetInnerHTML={{ __html: md(msg.content) }} />

      {/* Footer */}
      <div className="ac-footer">
        <div className="ac-actions">
          {msg.artifact_id ? (
            <>
              <button className="ac-btn ac-approve" onClick={e => { e.stopPropagation(); onApprove(msg.artifact_id); }}>
                <span>✓</span> Approve
              </button>
              <button className="ac-btn ac-edit" onClick={e => e.stopPropagation()}>
                <span>✎</span> Edit
              </button>
              <button className="ac-btn ac-regen" onClick={e => e.stopPropagation()}>
                <span>↺</span> Regenerate
              </button>
              <button className="ac-btn ac-reject" onClick={e => e.stopPropagation()}>
                <span>✕</span> Reject
              </button>
            </>
          ) : (
            <button className="ac-btn ac-copy" onClick={e => { e.stopPropagation(); copy(); }}>
              <span>⧉</span> Copy
            </button>
          )}
        </div>
        {msg.workflow && (
          <span className="ac-workflow">{msg.workflow.replace(/_/g, ' ')}</span>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// EMPTY STATE
// ─────────────────────────────────────────────────────────────
function EmptyState({ onPrompt }) {
  return (
    <div className="empty-state">
      <div className="es-logo">
        <span className="es-icon">⬡</span>
        <span className="es-name">SwarmOps</span>
      </div>
      <p className="es-sub">AI Marketing Operating System · 12 Specialized Agents</p>
      <div className="es-grid">
        {QUICK_ACTIONS.map((a, i) => (
          <button key={i} className="es-card" onClick={() => onPrompt(a.text)}>
            <span className="es-tag">{a.tag}</span>
            <span className="es-card-icon">{a.icon}</span>
            <span className="es-card-label">{a.label}</span>
            <span className="es-card-text">{a.text}</span>
          </button>
        ))}
      </div>
      <p className="es-hint">
        Type <kbd>/</kbd> for commands &nbsp;·&nbsp; <kbd>⏎</kbd> to send &nbsp;·&nbsp; <kbd>⇧⏎</kbd> new line
      </p>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// SLASH POPUP
// ─────────────────────────────────────────────────────────────
function SlashPopup({ filter, activeIdx, onPick }) {
  const filtered = SLASH_COMMANDS.filter(c =>
    filter === '' || c.cmd.slice(1).startsWith(filter) || c.desc.toLowerCase().includes(filter)
  );
  if (!filtered.length) return null;
  return (
    <div className="slash-popup">
      <div className="sp-header">Commands</div>
      <div className="sp-list">
        {filtered.map((cmd, i) => (
          <div
            key={cmd.cmd}
            className={`sp-item ${i === activeIdx ? 'sp-active' : ''}`}
            onMouseDown={e => { e.preventDefault(); onPick(cmd); }}
          >
            <span className="sp-icon">{cmd.icon}</span>
            <span className="sp-cmd">{cmd.cmd}</span>
            <span className="sp-desc">{cmd.desc}</span>
            <kbd className="sp-key">⌘{cmd.shortcut}</kbd>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// COMMAND CENTER
// ─────────────────────────────────────────────────────────────
function CommandCenter({ messages, loading, input, setInput, sendMessage, onApprove, selectedMsg, setSelectedMsg }) {
  const [showSlash, setShowSlash]   = useState(false);
  const [slashFilter, setSlashFilter] = useState('');
  const [slashIdx, setSlashIdx]     = useState(0);
  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading]);

  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  }, [input]);

  const filteredCmds = SLASH_COMMANDS.filter(c =>
    slashFilter === '' || c.cmd.slice(1).startsWith(slashFilter) || c.desc.toLowerCase().includes(slashFilter)
  );

  const handleChange = (e) => {
    const val = e.target.value;
    setInput(val);
    if (val.startsWith('/')) {
      setSlashFilter(val.slice(1).toLowerCase());
      setShowSlash(true);
      setSlashIdx(0);
    } else {
      setShowSlash(false);
    }
  };

  const pickSlash = (cmd) => {
    setInput(cmd.cmd + ' ');
    setShowSlash(false);
    inputRef.current?.focus();
  };

  const handleKey = (e) => {
    if (showSlash) {
      if (e.key === 'ArrowDown')  { e.preventDefault(); setSlashIdx(p => Math.min(p + 1, filteredCmds.length - 1)); return; }
      if (e.key === 'ArrowUp')    { e.preventDefault(); setSlashIdx(p => Math.max(p - 1, 0)); return; }
      if ((e.key === 'Tab' || e.key === 'Enter') && filteredCmds.length > 0) { e.preventDefault(); pickSlash(filteredCmds[slashIdx]); return; }
      if (e.key === 'Escape')     { setShowSlash(false); return; }
    }
    if (e.key === 'Enter' && !e.shiftKey && !showSlash) { e.preventDefault(); sendMessage(); }
  };

  return (
    <div className="cmd-center">
      {/* Messages */}
      <div className="cmd-messages">
        {messages.length === 0 ? (
          <EmptyState onPrompt={(text) => { setInput(text); setTimeout(() => inputRef.current?.focus(), 0); }} />
        ) : (
          messages.map((msg, i) => (
            <div key={i} className={`msg-row msg-${msg.role}`}>
              {msg.role === 'user' ? (
                <div className="user-msg">
                  <div className="user-avatar">U</div>
                  <div className="user-bubble">{msg.content}</div>
                </div>
              ) : (
                <ArtifactCard
                  msg={msg}
                  onApprove={onApprove}
                  onClick={() => setSelectedMsg(selectedMsg?.timestamp === msg.timestamp ? null : msg)}
                  isSelected={selectedMsg?.timestamp === msg.timestamp}
                />
              )}
            </div>
          ))
        )}

        {loading && (
          <div className="msg-row msg-assistant">
            <div className="artifact-card loading-card">
              <div className="ac-header">
                <div className="ac-agent">
                  <span className="ac-icon" style={{ color: '#818cf8' }}>⬡</span>
                  <span className="ac-name">SwarmOps</span>
                  <span className="ac-multi thinking">thinking…</span>
                </div>
              </div>
              <div className="sk-lines">
                <div className="sk-line" style={{ width: '82%' }} />
                <div className="sk-line" style={{ width: '67%' }} />
                <div className="sk-line" style={{ width: '74%' }} />
                <div className="sk-line" style={{ width: '45%' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="cmd-input-area">
        <div className="cmd-input-wrap">
          {showSlash && (
            <SlashPopup filter={slashFilter} activeIdx={slashIdx} onPick={pickSlash} />
          )}
          <textarea
            ref={inputRef}
            className="cmd-textarea"
            value={input}
            onChange={handleChange}
            onKeyDown={handleKey}
            placeholder="Ask SwarmOps anything… or type / for commands"
            rows={1}
            disabled={loading}
          />
          <button
            className={`cmd-send${(!input.trim() || loading) ? ' cmd-send-disabled' : ''}`}
            onClick={sendMessage}
            disabled={!input.trim() || loading}
          >↑</button>
        </div>
        <div className="cmd-hints">
          <span><kbd>⏎</kbd> send</span>
          <span><kbd>⇧⏎</kbd> new line</span>
          <span><kbd>/</kbd> commands</span>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// SIDEBAR
// ─────────────────────────────────────────────────────────────
const NAV_ITEMS = [
  { id: 'chat',    icon: '◉', label: 'Command Center' },
  { id: 'agents',  icon: '⬡', label: 'Agents'         },
  { id: 'queue',   icon: '◫', label: 'Approval Queue'  },
  { id: 'memory',  icon: '◆', label: 'Memory'          },
  { id: 'data',    icon: '◎', label: 'Data Sources'    },
];

function Sidebar({ view, setView, pendingCount, open, setOpen, onNewChat }) {
  return (
    <aside className={`sidebar${open ? '' : ' sb-collapsed'}`}>
      {/* Logo */}
      <div className="sb-logo">
        <div className="sb-logo-mark">
          <span className="sb-logo-icon">⬡</span>
          {open && <span className="sb-logo-text">SwarmOps</span>}
        </div>
        <button className="sb-toggle" onClick={() => setOpen(v => !v)} title={open ? 'Collapse' : 'Expand'}>
          {open ? '‹' : '›'}
        </button>
      </div>

      {/* New session */}
      <button className="sb-new" onClick={onNewChat} title="New Session">
        <span className="sb-new-icon">+</span>
        {open && <span>New Session</span>}
      </button>

      {/* Nav */}
      <nav className="sb-nav">
        {NAV_ITEMS.map(item => (
          <button
            key={item.id}
            className={`sb-item${view === item.id ? ' sb-active' : ''}`}
            onClick={() => setView(item.id)}
            title={!open ? item.label : undefined}
          >
            <span className="sb-item-icon">{item.icon}</span>
            {open && <span className="sb-item-label">{item.label}</span>}
            {item.id === 'queue' && pendingCount > 0 && (
              <span className="sb-badge">{pendingCount}</span>
            )}
          </button>
        ))}
      </nav>

      {/* Footer */}
      {open && (
        <div className="sb-footer">
          <div className="sb-footer-row">
            <StatusDot status="active" />
            <span>12 agents · 13 workflows</span>
          </div>
          <span className="sb-version">v3.0</span>
        </div>
      )}
    </aside>
  );
}

// ─────────────────────────────────────────────────────────────
// CONTEXT PANEL (right side — shows artifact details)
// ─────────────────────────────────────────────────────────────
function ContextPanel({ msg, onClose }) {
  if (!msg) return null;
  const primaryId = msg.agents_used?.[0] || 'nexus';
  const cfg = AGENTS_CFG[primaryId] || AGENTS_CFG.nexus;

  return (
    <aside className="ctx-panel">
      <div className="ctx-header">
        <span className="ctx-title">Artifact</span>
        <button className="ctx-close" onClick={onClose}>✕</button>
      </div>
      <div className="ctx-body">
        <Section label="Source Agent">
          <div className="ctx-agent" style={{ color: cfg.color }}>
            <span>{cfg.icon}</span> {cfg.name}
            <span className="ctx-agent-role">{cfg.role}</span>
          </div>
        </Section>
        {msg.agents_used?.length > 1 && (
          <Section label={`All Agents (${msg.agents_used.length})`}>
            <div className="ctx-pills">{msg.agents_used.map((a, i) => <AgentPill key={i} id={a} />)}</div>
          </Section>
        )}
        {msg.latency_ms && (
          <Section label="Response Time">
            <span className="ctx-value">{(msg.latency_ms / 1000).toFixed(1)}s</span>
          </Section>
        )}
        {msg.workflow && (
          <Section label="Workflow">
            <span className="ctx-value">{msg.workflow.replace(/_/g, ' ')}</span>
          </Section>
        )}
        <Section label="Status">
          <span className={`ctx-status ${msg.artifact_id ? 'ctx-pending' : 'ctx-done'}`}>
            {msg.artifact_id ? '● Pending Approval' : '● Delivered'}
          </span>
        </Section>
        {msg.artifact_id && (
          <Section label="Artifact ID">
            <span className="ctx-mono">{msg.artifact_id}</span>
          </Section>
        )}
      </div>
    </aside>
  );
}

function Section({ label, children }) {
  return (
    <div className="ctx-section">
      <div className="ctx-label">{label}</div>
      <div className="ctx-content">{children}</div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// APPROVAL QUEUE VIEW
// ─────────────────────────────────────────────────────────────
function ApprovalQueueView({ queue, onApprove, onReject }) {
  const pending  = queue.filter(a => a.status === 'pending');
  const approved = queue.filter(a => a.status === 'approved');
  const rejected = queue.filter(a => a.status === 'rejected');

  return (
    <div className="view-panel">
      <div className="view-header">
        <h2 className="view-title">Approval Queue</h2>
        <p className="view-sub">Review and deploy agent-generated artifacts</p>
      </div>

      <div className="stats-row">
        {[
          { label: 'Pending',  count: pending.length,  color: '#f59e0b' },
          { label: 'Approved', count: approved.length, color: '#22c55e' },
          { label: 'Rejected', count: rejected.length, color: '#ef4444' },
        ].map(s => (
          <div key={s.label} className="stat-chip">
            <span className="stat-num" style={{ color: s.color }}>{s.count}</span>
            <span className="stat-label">{s.label}</span>
          </div>
        ))}
      </div>

      {pending.length === 0 ? (
        <div className="view-empty">
          <span className="ve-icon">◫</span>
          <p className="ve-title">No pending approvals</p>
          <p className="ve-sub">Use /publish or /campaign to create artifacts for review</p>
        </div>
      ) : (
        <div className="queue-list">
          {pending.map(item => (
            <div key={item.id} className="q-card">
              <div className="qc-top">
                <span className="qc-type">{(item.type || 'content').replace(/_/g, ' ')}</span>
                <span className="qc-status">● PENDING</span>
              </div>
              <div className="qc-title">{item.title}</div>
              <div className="qc-meta">ID: {item.id} · {item.created}</div>
              <div className="qc-actions">
                <button className="qc-btn qc-approve" onClick={() => onApprove(item.id)}>✓ Approve & Deploy</button>
                <button className="qc-btn qc-feedback">✎ Send Feedback</button>
                <button className="qc-btn qc-reject" onClick={() => onReject(item.id)}>✕ Reject</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// MEMORY VIEW
// ─────────────────────────────────────────────────────────────
function MemField({ label, placeholder }) {
  const [editing, setEditing] = useState(false);
  const [val, setVal] = useState('');
  return (
    <div className="mem-field">
      <label className="mem-label">{label}</label>
      {editing ? (
        <div className="mem-edit-row">
          <input className="mem-input" value={val} onChange={e => setVal(e.target.value)} placeholder={placeholder} autoFocus />
          <button className="mem-save" onClick={() => setEditing(false)}>Save</button>
          <button className="mem-cancel" onClick={() => setEditing(false)}>Cancel</button>
        </div>
      ) : (
        <div className="mem-display" onClick={() => setEditing(true)}>
          <span className={val ? 'mem-val' : 'mem-ph'}>{val || placeholder}</span>
          <span className="mem-edit-icon">✎</span>
        </div>
      )}
    </div>
  );
}

function MemoryView() {
  const [activeTab, setActiveTab] = useState('brand');
  const active = MEMORY_LAYERS.find(l => l.id === activeTab);

  return (
    <div className="view-panel">
      <div className="view-header">
        <h2 className="view-title">Memory System</h2>
        <p className="view-sub">Layered context powering every agent decision</p>
      </div>
      <div className="mem-tabs">
        {MEMORY_LAYERS.map(l => (
          <button key={l.id} className={`mem-tab${activeTab === l.id ? ' mem-tab-active' : ''}`} onClick={() => setActiveTab(l.id)}>
            <span>{l.icon}</span> {l.label}
          </button>
        ))}
      </div>
      {active && <p className="mem-desc">{active.desc}</p>}
      <div className="mem-body">
        {activeTab === 'brand' ? (
          <div className="mem-fields">
            <MemField label="Brand Name"        placeholder="e.g. Acme Corp" />
            <MemField label="Industry"          placeholder="e.g. B2B SaaS" />
            <MemField label="Website URL"       placeholder="https://yoursite.com" />
            <MemField label="Target Audience"   placeholder="e.g. Marketing leaders at Series A startups" />
            <MemField label="Value Proposition" placeholder="What makes you uniquely different?" />
            <MemField label="Tone of Voice"     placeholder="e.g. Professional, direct, data-driven" />
          </div>
        ) : (
          <div className="view-empty">
            <span className="ve-icon">{active.icon}</span>
            <p className="ve-title">{active.label} memory builds automatically</p>
            <p className="ve-sub">Interact with SwarmOps to populate this layer</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// DATA SOURCES VIEW
// ─────────────────────────────────────────────────────────────
function DataSourcesView() {
  return (
    <div className="view-panel">
      <div className="view-header">
        <h2 className="view-title">Data Sources</h2>
        <p className="view-sub">Connect your marketing stack for real-data analysis</p>
      </div>
      <div className="ds-grid">
        {DATA_SOURCES.map(src => (
          <div key={src.id} className={`ds-card ds-${src.status}`}>
            <div className="ds-top">
              <span className="ds-icon">{src.icon}</span>
              <span className={`ds-badge ds-badge-${src.status}`}>
                {src.status === 'connected' ? '● Connected' : '○ Not connected'}
              </span>
            </div>
            <div className="ds-name">{src.name}</div>
            <div className="ds-desc">{src.desc}</div>
            {src.freshness && <div className="ds-freshness">Updated {src.freshness}</div>}
            <button className={`ds-btn ${src.status === 'connected' ? 'ds-btn-manage' : 'ds-btn-connect'}`}>
              {src.status === 'connected' ? 'Manage' : 'Connect'}
            </button>
          </div>
        ))}
      </div>
      <div className="ds-note">
        <span>⬡</span>
        Without connected sources, SwarmOps uses industry benchmarks. Connect GA4 for real traffic data.
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// AGENTS VIEW
// ─────────────────────────────────────────────────────────────
function AgentsView() {
  return (
    <div className="view-panel">
      <div className="view-header">
        <h2 className="view-title">Agent Network</h2>
        <p className="view-sub">12 specialized agents orchestrated by Nexus CMO</p>
      </div>
      <div className="agents-grid">
        {Object.entries(AGENTS_CFG).map(([id, cfg]) => (
          <div key={id} className="ag-card" style={{ '--ag-color': cfg.color }}>
            <div className="ag-header">
              <span className="ag-icon" style={{ color: cfg.color }}>{cfg.icon}</span>
              <StatusDot status="idle" />
            </div>
            <div className="ag-name">{cfg.name}</div>
            <div className="ag-role">{cfg.role}</div>
            <div className="ag-footer">
              <span className="ag-status-text">Idle · Ready</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// MAIN APP
// ─────────────────────────────────────────────────────────────
export default function App() {
  const [view,        setView]        = useState('chat');
  const [messages,    setMessages]    = useState([]);
  const [input,       setInput]       = useState('');
  const [loading,     setLoading]     = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [queue,       setQueue]       = useState([]);
  const [selectedMsg, setSelectedMsg] = useState(null);

  const pending = queue.filter(a => a.status === 'pending').length;

  const sendMessage = useCallback(async (override) => {
    const text = (override !== undefined ? override : input).trim();
    if (!text || loading) return;

    setMessages(prev => [...prev, { role: 'user', content: text, timestamp: Date.now() }]);
    setInput('');
    setLoading(true);
    if (view !== 'chat') setView('chat');

    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, agent: 'nexus' }),
      });
      if (!res.ok) throw new Error(`${res.status}: ${(await res.text()).slice(0, 200)}`);

      const data = await res.json();
      const content = data.result || data.response || data.message || 'No response received.';

      const msg = {
        role:        'assistant',
        content:     typeof content === 'object' ? JSON.stringify(content, null, 2) : content,
        agents_used: data.agents_used || [],
        workflow:    data.workflow    || null,
        latency_ms:  data.latency_ms  || null,
        multi_agent: data.multi_agent || false,
        artifact_id: data.artifact_id || null,
        confidence:  data.confidence  || null,
        timestamp:   Date.now(),
      };
      setMessages(prev => [...prev, msg]);

      if (data.artifact_id) {
        setQueue(prev => [...prev, {
          id:      data.artifact_id,
          type:    data.workflow || 'content',
          title:   text.substring(0, 60),
          created: new Date().toLocaleTimeString(),
          status:  'pending',
        }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role:      'assistant',
        content:   `Connection error: ${err.message}. The backend may be waking up (cold start). Try again in 30 seconds.`,
        timestamp: Date.now(),
      }]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, view]);

  const approveArtifact = (id) => {
    setQueue(prev => prev.map(a => a.id === id ? { ...a, status: 'approved' } : a));
    sendMessage(`/approve ${id}`);
  };
  const rejectArtifact = (id) => {
    setQueue(prev => prev.map(a => a.id === id ? { ...a, status: 'rejected' } : a));
  };
  const newChat = () => { setMessages([]); setInput(''); setQueue([]); setSelectedMsg(null); };

  const showCtx = selectedMsg && view === 'chat';

  return (
    <div className={`app-root${sidebarOpen ? '' : ' sb-is-collapsed'}${showCtx ? ' has-ctx' : ''}`}>
      <Sidebar
        view={view} setView={setView}
        pendingCount={pending}
        open={sidebarOpen} setOpen={setSidebarOpen}
        onNewChat={newChat}
      />

      <main className="app-main">
        {view === 'chat' && (
          <CommandCenter
            messages={messages} loading={loading}
            input={input} setInput={setInput}
            sendMessage={sendMessage}
            onApprove={approveArtifact}
            selectedMsg={selectedMsg} setSelectedMsg={setSelectedMsg}
          />
        )}
        {view === 'agents' && <AgentsView />}
        {view === 'queue'  && <ApprovalQueueView queue={queue} onApprove={approveArtifact} onReject={rejectArtifact} />}
        {view === 'memory' && <MemoryView />}
        {view === 'data'   && <DataSourcesView />}
      </main>

      {showCtx && <ContextPanel msg={selectedMsg} onClose={() => setSelectedMsg(null)} />}
    </div>
  );
}

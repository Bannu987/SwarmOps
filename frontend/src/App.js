import React, { useState, useEffect, useRef } from 'react';
import './App.css';

// ============================================================
// CONSTANTS
// ============================================================
const API_URL = 'https://marketingos2-0.onrender.com';

const SLASH_COMMANDS = [
  { cmd: '/seo',      desc: 'Direct SEO analysis',        icon: '🔍' },
  { cmd: '/content',  desc: 'Content strategy',            icon: '✍️' },
  { cmd: '/ppc',      desc: 'Paid advertising',            icon: '💰' },
  { cmd: '/analytics',desc: 'Data & metrics',              icon: '📊' },
  { cmd: '/crm',      desc: 'Email & lifecycle',           icon: '📧' },
  { cmd: '/smm',      desc: 'Social media',                icon: '📱' },
  { cmd: '/aeo',      desc: 'AI search optimization',      icon: '🤖' },
  { cmd: '/cro',      desc: 'Conversion optimization',     icon: '🎯' },
  { cmd: '/publish',  desc: 'Create & publish blog post',  icon: '📝' },
  { cmd: '/campaign', desc: 'Create ad campaign',          icon: '🚀' },
  { cmd: '/schema',   desc: 'Generate JSON-LD markup',     icon: '🏗️' },
  { cmd: '/tools',    desc: 'View data integrations',      icon: '🔌' },
  { cmd: '/approve',  desc: 'Approve pending artifact',    icon: '✅' },
  { cmd: '/queue',    desc: 'View approval queue',         icon: '📋' },
];

const QUICK_PROMPTS = [
  { icon: '📝', text: 'Create a content strategy for Q1 2026' },
  { icon: '🔍', text: 'Find SEO keyword opportunities for my business' },
  { icon: '🚀', text: 'Create a 3-month growth plan with budget breakdown' },
  { icon: '📊', text: 'Run a marketing audit on https://' },
];

// ============================================================
// MARKDOWN FORMATTER
// ============================================================
function formatContent(text) {
  if (!text) return '';
  // Escape HTML
  let t = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Code blocks first (protect from other replacements)
  const codeBlocks = [];
  t = t.replace(/```[\w]*\n?([\s\S]*?)```/g, (_, code) => {
    const idx = codeBlocks.length;
    codeBlocks.push(`<pre><code>${code.trim()}</code></pre>`);
    return `\x00CODE${idx}\x00`;
  });

  // Inline code
  t = t.replace(/`([^`\n]+)`/g, '<code>$1</code>');
  // Bold
  t = t.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  // Italic
  t = t.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>');
  // Headers
  t = t.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  t = t.replace(/^## (.+)$/gm,  '<h2>$1</h2>');
  t = t.replace(/^# (.+)$/gm,   '<h1>$1</h1>');
  // Blockquote
  t = t.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');
  // Horizontal rule
  t = t.replace(/^---+$/gm, '<hr/>');
  // List items → wrap in <ul>/<ol> groups
  const lines = t.split('\n');
  const out = [];
  let inUl = false, inOl = false;
  for (const line of lines) {
    const ulMatch = line.match(/^[ \t]*[-*+] (.+)$/);
    const olMatch = line.match(/^\d+\. (.+)$/);
    if (ulMatch) {
      if (inOl) { out.push('</ol>'); inOl = false; }
      if (!inUl) { out.push('<ul>'); inUl = true; }
      out.push(`<li>${ulMatch[1]}</li>`);
    } else if (olMatch) {
      if (inUl) { out.push('</ul>'); inUl = false; }
      if (!inOl) { out.push('<ol>'); inOl = true; }
      out.push(`<li>${olMatch[1]}</li>`);
    } else {
      if (inUl) { out.push('</ul>'); inUl = false; }
      if (inOl) { out.push('</ol>'); inOl = false; }
      out.push(line);
    }
  }
  if (inUl) out.push('</ul>');
  if (inOl) out.push('</ol>');
  t = out.join('\n');

  // Newlines → <br/> (skip inside block elements)
  t = t.replace(/\n/g, '<br/>');
  // Clean up <br/> inside block tags
  t = t.replace(/(<(?:ul|ol|pre|h[1-3]|blockquote)[^>]*>)(<br\/>)+/gi, '$1');
  t = t.replace(/(<br\/>)+(<\/(?:ul|ol|pre|h[1-3]|blockquote)>)/gi, '$2');

  // Restore code blocks
  codeBlocks.forEach((block, idx) => {
    t = t.replace(`\x00CODE${idx}\x00`, block);
  });

  return t;
}

// ============================================================
// APP
// ============================================================
function App() {
  const [messages,          setMessages]          = useState([]);
  const [input,             setInput]             = useState('');
  const [loading,           setLoading]           = useState(false);
  const [sidebarOpen,       setSidebarOpen]       = useState(true);
  const [showSlashPopup,    setShowSlashPopup]    = useState(false);
  const [slashFilter,       setSlashFilter]       = useState('');
  const [selectedSlashIdx,  setSelectedSlashIdx]  = useState(0);
  const [showApprovalPanel, setShowApprovalPanel] = useState(false);
  const [approvalQueue,     setApprovalQueue]     = useState([]);

  const messagesEndRef = useRef(null);
  const inputRef       = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 180) + 'px';
  }, [input]);

  // ============================================================
  // SEND MESSAGE
  // ============================================================
  const sendMessage = async (overrideText) => {
    const text = (overrideText !== undefined ? overrideText : input).trim();
    if (!text || loading) return;

    setMessages(prev => [...prev, { role: 'user', content: text, timestamp: Date.now() }]);
    setInput('');
    setShowSlashPopup(false);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, agent: 'nexus' }),
      });

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`${res.status}: ${errText.slice(0, 200)}`);
      }

      const data = await res.json();
      const content = data.result || data.response || data.message || 'No response received.';

      setMessages(prev => [...prev, {
        role:        'assistant',
        content:     typeof content === 'object' ? JSON.stringify(content, null, 2) : content,
        agents_used: data.agents_used  || [],
        workflow:    data.workflow     || null,
        latency_ms:  data.latency_ms   || null,
        multi_agent: data.multi_agent  || false,
        artifact_id: data.artifact_id  || null,
        timestamp:   Date.now(),
      }]);

      if (data.artifact_id) {
        setApprovalQueue(prev => [...prev, {
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
        content:   `Connection error: ${err.message}. The backend may be waking up (free tier). Try again in 30 seconds.`,
        timestamp: Date.now(),
      }]);
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // INPUT CONTROLS
  // ============================================================
  const handleInputChange = (e) => {
    const val = e.target.value;
    setInput(val);
    if (val.startsWith('/')) {
      setSlashFilter(val.slice(1).toLowerCase());
      setShowSlashPopup(true);
      setSelectedSlashIdx(0);
    } else {
      setShowSlashPopup(false);
    }
  };

  const getFiltered = () =>
    SLASH_COMMANDS.filter(c =>
      c.cmd.slice(1).startsWith(slashFilter) ||
      c.desc.toLowerCase().includes(slashFilter)
    );

  const handleKeyDown = (e) => {
    if (showSlashPopup) {
      const f = getFiltered();
      if (e.key === 'ArrowDown')  { e.preventDefault(); setSelectedSlashIdx(p => Math.min(p + 1, f.length - 1)); return; }
      if (e.key === 'ArrowUp')    { e.preventDefault(); setSelectedSlashIdx(p => Math.max(p - 1, 0)); return; }
      if ((e.key === 'Tab' || e.key === 'Enter') && f.length > 0) {
        e.preventDefault();
        pickSlash(f[selectedSlashIdx]);
        return;
      }
      if (e.key === 'Escape') { setShowSlashPopup(false); return; }
    }
    if (e.key === 'Enter' && !e.shiftKey && !showSlashPopup) {
      e.preventDefault();
      sendMessage();
    }
  };

  const pickSlash = (cmd) => {
    setInput(cmd.cmd + ' ');
    setShowSlashPopup(false);
    inputRef.current?.focus();
  };

  // ============================================================
  // APPROVALS
  // ============================================================
  const newChat = () => { setMessages([]); setInput(''); setApprovalQueue([]); };

  const approveArtifact = (id) => {
    setApprovalQueue(prev => prev.map(a => a.id === id ? { ...a, status: 'approved' } : a));
    setShowApprovalPanel(false);
    sendMessage(`/approve ${id}`);
  };

  const rejectArtifact = (id) =>
    setApprovalQueue(prev => prev.map(a => a.id === id ? { ...a, status: 'rejected' } : a));

  const pendingCount = approvalQueue.filter(a => a.status === 'pending').length;

  // ============================================================
  // RENDER
  // ============================================================
  return (
    <div className="app">

      {/* ── SIDEBAR ── */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <span className="logo">Swarm<span className="logo-accent">Ops</span></span>
          <button className="icon-btn" onClick={() => setSidebarOpen(false)}>◀</button>
        </div>

        <button className="new-chat-btn" onClick={newChat}>+ New Chat</button>

        <div className="sidebar-label">TOOLS</div>

        {[
          { icon: '🧬', label: 'Brand DNA',       query: 'what do you know about my brand?' },
          { icon: '🔍', label: 'Competitors',     query: 'analyze my competitors' },
          { icon: '📊', label: 'Marketing Audit', query: 'run a marketing audit on https://' },
          { icon: '🔌', label: 'Integrations',    query: '/tools' },
        ].map(item => (
          <button key={item.label} className="sidebar-item" onClick={() => {
            setInput(item.query);
            inputRef.current?.focus();
          }}>
            <span className="sidebar-icon">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}

        <button className="sidebar-item" onClick={() => setShowApprovalPanel(v => !v)} style={{ position: 'relative' }}>
          <span className="sidebar-icon">✅</span>
          <span>Approval Queue</span>
          {pendingCount > 0 && <span className="badge">{pendingCount}</span>}
        </button>

        <div className="sidebar-footer">v3 · 12 agents · 13 workflows</div>
      </aside>

      {/* ── MAIN CHAT ── */}
      <main className="chat-main">
        <header className="chat-header">
          {!sidebarOpen && (
            <button className="icon-btn" onClick={() => setSidebarOpen(true)} title="Open sidebar">☰</button>
          )}
          <span className="chat-title">SwarmOps</span>
          <span className="chat-subtitle">AI Marketing Intelligence</span>
        </header>

        <div className="messages-area">
          {messages.length === 0 && (
            <div className="empty-state">
              <div className="empty-logo">SwarmOps</div>
              <p className="empty-sub">Multi-Agent AI Marketing Intelligence</p>
              <div className="quick-grid">
                {QUICK_PROMPTS.map((p, i) => (
                  <button key={i} className="quick-btn" onClick={() => {
                    setInput(p.text);
                    inputRef.current?.focus();
                  }}>
                    <span className="quick-icon">{p.icon}</span>
                    <span>{p.text}</span>
                  </button>
                ))}
              </div>
              <p className="empty-hint">Type / for commands · Shift+Enter for new line</p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`msg-wrap ${msg.role}`}>
              {msg.role === 'user' ? (
                <div className="user-bubble">{msg.content}</div>
              ) : (
                <div className="agent-bubble">
                  <div className="agent-label">SwarmOps</div>

                  {msg.agents_used && msg.agents_used.length > 1 && (
                    <div className="agent-bar">
                      <span className="agent-bar-label">Consulted {msg.agents_used.length} specialists</span>
                      {msg.agents_used.map((ag, j) => (
                        <span key={j} className="agent-chip">
                          <span className="chip-check">✓</span>
                          {ag.charAt(0).toUpperCase() + ag.slice(1).replace('_', ' ')}
                        </span>
                      ))}
                      {msg.latency_ms && (
                        <span className="agent-bar-time">{(msg.latency_ms / 1000).toFixed(1)}s</span>
                      )}
                    </div>
                  )}

                  <div
                    className="response-text"
                    dangerouslySetInnerHTML={{ __html: formatContent(msg.content) }}
                  />

                  {msg.artifact_id && (
                    <div className="artifact-notice">
                      <span>📦 Artifact ready · ID: {msg.artifact_id}</span>
                      <button className="btn-approve-inline" onClick={() => approveArtifact(msg.artifact_id)}>
                        Approve &amp; Deploy
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="msg-wrap assistant">
              <div className="agent-bubble">
                <div className="agent-label">SwarmOps</div>
                <div className="loading-dots"><span /><span /><span /></div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="input-area">
          <div className="input-wrap">
            {showSlashPopup && (() => {
              const filtered = getFiltered();
              return filtered.length > 0 ? (
                <div className="slash-popup">
                  <div className="slash-header">Commands</div>
                  {filtered.map((cmd, i) => (
                    <div
                      key={cmd.cmd}
                      className={`slash-item ${i === selectedSlashIdx ? 'active' : ''}`}
                      onMouseDown={e => { e.preventDefault(); pickSlash(cmd); }}
                    >
                      <span className="slash-icon">{cmd.icon}</span>
                      <span className="slash-cmd">{cmd.cmd}</span>
                      <span className="slash-desc">{cmd.desc}</span>
                    </div>
                  ))}
                </div>
              ) : null;
            })()}

            <textarea
              ref={inputRef}
              className="chat-input"
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask SwarmOps anything… (type / for commands)"
              rows={1}
              disabled={loading}
            />
            <button
              className="send-btn"
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
            >↑</button>
          </div>
          <p className="input-hint">Enter to send · Shift+Enter new line · / for commands</p>
        </div>
      </main>

      {/* ── APPROVAL PANEL ── */}
      <div className={`approval-panel ${showApprovalPanel ? 'open' : ''}`}>
        <div className="approval-header">
          <h3>Approval Queue</h3>
          <button className="icon-btn" onClick={() => setShowApprovalPanel(false)}>✕</button>
        </div>
        <div className="approval-body">
          {approvalQueue.filter(a => a.status === 'pending').length === 0 ? (
            <div className="approval-empty">
              No pending approvals.<br />
              Use /publish or /campaign to create artifacts.
            </div>
          ) : (
            approvalQueue.filter(a => a.status === 'pending').map(artifact => (
              <div key={artifact.id} className="approval-card">
                <div className="approval-type">{(artifact.type || '').replace(/_/g, ' ')}</div>
                <div className="approval-title">{artifact.title}</div>
                <div className="approval-meta">ID: {artifact.id} · {artifact.created}</div>
                <div className="approval-actions">
                  <button className="btn-approve" onClick={() => approveArtifact(artifact.id)}>Approve</button>
                  <button className="btn-reject"  onClick={() => rejectArtifact(artifact.id)}>Reject</button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

    </div>
  );
}

export default App;

import React, { useState, useRef, useEffect } from 'react';

const API_URL = process.env.REACT_APP_API_URL || 'https://marketingos2-0.onrender.com';

const SLASH_COMMANDS = [
  { cmd: '/seo', desc: 'SEO analysis & keyword research', icon: '◎' },
  { cmd: '/content', desc: 'Content strategy & copywriting', icon: '✦' },
  { cmd: '/ppc', desc: 'Paid advertising & campaigns', icon: '◉' },
  { cmd: '/analytics', desc: 'Data analysis & reporting', icon: '◉' },
  { cmd: '/crm', desc: 'Email flows & lifecycle', icon: '◐' },
  { cmd: '/smm', desc: 'Social media strategy', icon: '◌' },
  { cmd: '/aeo', desc: 'AI search optimization', icon: '◯' },
  { cmd: '/cro', desc: 'Conversion rate optimization', icon: '◑' },
  { cmd: '/publish', desc: 'Create & publish content', icon: '↗' },
  { cmd: '/campaign', desc: 'Build ad campaign', icon: '⚡' },
  { cmd: '/schema', desc: 'Generate JSON-LD markup', icon: '◊' },
  { cmd: '/tools', desc: 'View integrations', icon: '⚙' },
  { cmd: '/approve', desc: 'Approve pending artifact', icon: '✓' },
  { cmd: '/queue', desc: 'View approval queue', icon: '▤' },
];

const AGENT_COLORS = {
  nexus: '#6366f1',
  seo: '#22d3ee',
  content: '#a855f7',
  ppc: '#f97316',
  analytics: '#10b981',
  crm: '#3b82f6',
  smm: '#ec4899',
  brand: '#ef4444',
  cro: '#22c55e',
  web_ux: '#06b6d4',
  research: '#84cc16',
  aeo: '#fbbf24',
};

const QUICK_ACTIONS = [
  { text: 'Run a marketing audit on my site', icon: '◎' },
  { text: 'Create a content strategy for Q1 2026', icon: '✦' },
  { text: 'Find SEO keyword opportunities', icon: '◯' },
  { text: 'Analyze my conversion funnel', icon: '◐' },
];

export default function CommandCenter({ onArtifactCreated }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showSlash, setShowSlash] = useState(false);
  const [slashFilter, setSlashFilter] = useState('');
  const [slashIdx, setSlashIdx] = useState(0);
  const [uploading, setUploading] = useState(false);

  const inputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const filteredCommands = SLASH_COMMANDS.filter(
    (c) =>
      c.cmd.slice(1).toLowerCase().includes(slashFilter) ||
      c.desc.toLowerCase().includes(slashFilter)
  );

  const sendMessage = async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;

    setMessages((prev) => [...prev, { role: 'user', content: msg, ts: Date.now() }]);
    setInput('');
    setShowSlash(false);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, agent: 'nexus' }),
      });

      const data = await res.json();

      const assistantMsg = {
        role: 'assistant',
        content: data.response || data.message || 'No response.',
        agents_used: data.agents_used || [],
        workflow: data.workflow,
        latency_ms: data.latency_ms,
        artifact_id: data.artifact_id,
        confidence: data.confidence,
        ts: Date.now(),
      };

      setMessages((prev) => [...prev, assistantMsg]);

      if (data.artifact_id && onArtifactCreated) {
        onArtifactCreated({
          id: data.artifact_id,
          type: data.workflow || 'content',
          title: msg.substring(0, 60),
          created: new Date().toLocaleTimeString(),
          content: data.response,
          status: 'pending',
        });
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            'Connection error. The backend may be waking up (free tier sleeps after 15 min). Try again in 30 seconds.',
          ts: Date.now(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
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

  const handleKeyDown = (e) => {
    if (showSlash) {
      // Only intercept navigation keys when popup is visible
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSlashIdx((prev) => Math.min(prev + 1, filteredCommands.length - 1));
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSlashIdx((prev) => Math.max(prev - 1, 0));
        return;
      }
      if (e.key === 'Escape') {
        setShowSlash(false);
        return;
      }
      // Tab always selects from popup
      if (e.key === 'Tab' && filteredCommands.length > 0) {
        e.preventDefault();
        const selected = filteredCommands[slashIdx];
        setInput(selected.cmd + ' ');
        setShowSlash(false);
        return;
      }
      // Enter selects from popup ONLY if no space (no args typed yet)
      const hasArguments = input.trim().includes(' ');
      if (e.key === 'Enter' && !hasArguments && filteredCommands.length > 0) {
        e.preventDefault();
        const selected = filteredCommands[slashIdx];
        setInput(selected.cmd + ' ');
        setShowSlash(false);
        return;
      }
      // If args typed, hide popup and let Enter send below
      if (e.key === 'Enter' && hasArguments) {
        setShowSlash(false);
      }
    }

    if (e.key === 'Enter' && !e.shiftKey && !showSlash) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_URL}/api/upload`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();

      if (data.success) {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: `**${data.filename}** uploaded (${(data.file_size / 1024).toFixed(1)}KB)\n\n${data.summary}\n\nAsk me anything about this file.`,
            ts: Date.now(),
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `Upload failed: ${data.error || 'Unknown error'}`, ts: Date.now() },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Upload failed: ${err.message}`, ts: Date.now() },
      ]);
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const formatContent = (text) => {
    if (!text) return '';
    let html = text;
    html = html.replace(
      /```(\w*)\n([\s\S]*?)```/g,
      '<pre class="bg-bg-tertiary border border-border rounded-lg p-3 my-2 overflow-x-auto"><code class="text-sm text-text-primary">$2</code></pre>'
    );
    html = html.replace(
      /`([^`]+)`/g,
      '<code class="bg-bg-tertiary px-1.5 py-0.5 rounded text-sm">$1</code>'
    );
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong class="text-text-primary">$1</strong>');
    html = html.replace(
      /^### (.+)$/gm,
      '<h3 class="text-base font-semibold mt-3 mb-1 text-text-primary">$1</h3>'
    );
    html = html.replace(
      /^## (.+)$/gm,
      '<h2 class="text-lg font-semibold mt-3 mb-1.5 text-text-primary">$1</h2>'
    );
    html = html.replace(/^\* (.+)$/gm, '<li class="ml-4 list-disc">$1</li>');
    html = html.replace(/^\d+\. (.+)$/gm, '<li class="ml-4 list-decimal">$1</li>');
    html = html.replace(/(<li.+<\/li>\s*)+/g, (m) => `<ul class="my-2 space-y-1">${m}</ul>`);
    html = html.replace(/\n\n/g, '</p><p class="mb-2">');
    html = html.replace(/\n/g, '<br/>');
    return `<p class="mb-2">${html}</p>`;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-3 border-b border-border flex items-center justify-between">
        <div>
          <h1 className="text-text-primary font-semibold">Command Center</h1>
          <p className="text-xs text-text-secondary">Orchestrated by Nexus CMO</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-text-muted">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
          Online
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 ? (
          <div className="max-w-2xl mx-auto pt-16 text-center">
            <div className="w-12 h-12 mx-auto rounded-xl bg-gradient-to-br from-accent to-accent-cyan flex items-center justify-center text-white text-xl font-bold mb-4">
              S
            </div>
            <h2 className="text-2xl font-semibold text-text-primary mb-2">
              How can your AI marketing team help?
            </h2>
            <p className="text-sm text-text-secondary mb-8">
              12 specialist agents · 13 workflows · Ready to execute
            </p>
            <div className="grid grid-cols-2 gap-2 max-w-xl mx-auto">
              {QUICK_ACTIONS.map((action, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(action.text)}
                  className="text-left px-4 py-3 bg-bg-secondary hover:bg-bg-tertiary border border-border hover:border-border-hover rounded-lg transition group"
                >
                  <div className="text-accent mb-1">{action.icon}</div>
                  <div className="text-sm text-text-secondary group-hover:text-text-primary">
                    {action.text}
                  </div>
                </button>
              ))}
            </div>
            <p className="text-xs text-text-muted mt-8">
              Type{' '}
              <kbd className="px-1.5 py-0.5 bg-bg-tertiary border border-border rounded text-[10px]">
                /
              </kbd>{' '}
              for commands · Click{' '}
              <kbd className="px-1.5 py-0.5 bg-bg-tertiary border border-border rounded text-[10px]">
                📎
              </kbd>{' '}
              to upload files
            </p>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-5">
            {messages.map((msg, i) => (
              <MessageCard
                key={i}
                message={msg}
                formatContent={formatContent}
                agentColors={AGENT_COLORS}
              />
            ))}
            {loading && (
              <div className="bg-bg-secondary border border-border rounded-2xl p-5 animate-fade-in">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-accent to-accent-cyan flex items-center justify-center text-white text-xs font-bold">
                    S
                  </div>
                  <span className="text-sm font-medium text-text-primary">Nexus</span>
                  <span className="text-xs text-text-muted">thinking...</span>
                </div>
                <div className="space-y-2">
                  <div className="h-3 bg-bg-tertiary rounded animate-pulse w-3/4"></div>
                  <div className="h-3 bg-bg-tertiary rounded animate-pulse w-1/2"></div>
                  <div className="h-3 bg-bg-tertiary rounded animate-pulse w-2/3"></div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-t border-border">
        <div className="max-w-3xl mx-auto relative">
          {/* Slash popup */}
          {showSlash && filteredCommands.length > 0 && (
            <div className="absolute bottom-full left-0 right-0 mb-2 bg-bg-secondary border border-border-hover rounded-xl shadow-2xl overflow-hidden max-h-80 overflow-y-auto animate-slide-up z-10">
              <div className="px-3 py-2 text-[10px] font-semibold text-text-muted uppercase tracking-wider border-b border-border">
                Commands · {filteredCommands.length}
              </div>
              {filteredCommands.map((cmd, i) => (
                <button
                  key={cmd.cmd}
                  onClick={() => {
                    setInput(cmd.cmd + ' ');
                    setShowSlash(false);
                    inputRef.current?.focus();
                  }}
                  className={`w-full px-3 py-2 flex items-center gap-3 text-left transition ${
                    i === slashIdx ? 'bg-accent/10' : 'hover:bg-bg-hover'
                  }`}
                >
                  <span className="text-accent text-sm w-5 text-center">{cmd.icon}</span>
                  <span className="font-mono text-sm text-accent min-w-[80px]">{cmd.cmd}</span>
                  <span className="text-sm text-text-secondary">{cmd.desc}</span>
                </button>
              ))}
            </div>
          )}

          {/* Input container */}
          <div className="flex items-end gap-2 bg-bg-secondary border border-border rounded-xl p-2 focus-within:border-accent transition">
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="w-9 h-9 flex items-center justify-center text-text-muted hover:text-text-primary hover:bg-bg-hover rounded-lg transition disabled:opacity-50"
              title="Upload file (any type)"
            >
              {uploading ? '⏳' : '📎'}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="*/*"
              onChange={handleFileUpload}
              className="hidden"
            />

            <textarea
              ref={inputRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask SwarmOps anything..."
              rows={1}
              disabled={loading}
              className="flex-1 bg-transparent text-text-primary placeholder-text-muted text-sm py-2 px-2 outline-none resize-none disabled:opacity-50 min-h-[36px] max-h-32"
            />

            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
              className="w-9 h-9 flex items-center justify-center bg-accent hover:bg-accent-hover text-white rounded-lg transition disabled:opacity-30 disabled:cursor-not-allowed"
            >
              ↑
            </button>
          </div>

          <div className="mt-2 text-[11px] text-text-muted text-center">
            Press{' '}
            <kbd className="px-1 bg-bg-tertiary rounded">Enter</kbd> to send ·{' '}
            <kbd className="px-1 bg-bg-tertiary rounded ml-1">Shift+Enter</kbd> for new line ·{' '}
            <kbd className="px-1 bg-bg-tertiary rounded ml-1">/</kbd> for commands
          </div>
        </div>
      </div>
    </div>
  );
}

function MessageCard({ message, formatContent, agentColors }) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end animate-fade-in">
        <div className="max-w-[80%] bg-accent text-white rounded-2xl rounded-br-md px-4 py-2.5 text-sm">
          {message.content}
        </div>
      </div>
    );
  }

  const primaryAgent = message.agents_used?.[0] || 'nexus';
  const agentColor = agentColors[primaryAgent] || agentColors.nexus;

  return (
    <div
      className="bg-bg-secondary border border-border rounded-2xl overflow-hidden animate-slide-up"
      style={{ borderTopColor: agentColor, borderTopWidth: 2 }}
    >
      {/* Header */}
      <div className="px-5 py-3 flex items-center justify-between border-b border-border">
        <div className="flex items-center gap-2.5">
          <div
            className="w-6 h-6 rounded-md flex items-center justify-center text-white text-xs font-bold"
            style={{ background: `linear-gradient(135deg, ${agentColor}, ${agentColor}99)` }}
          >
            {primaryAgent.charAt(0).toUpperCase()}
          </div>
          <span className="text-sm font-medium text-text-primary capitalize">{primaryAgent}</span>
          {message.agents_used && message.agents_used.length > 1 && (
            <span className="text-xs text-text-muted">+{message.agents_used.length - 1} agents</span>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs">
          {message.confidence && (
            <span className="text-green-400">{Math.round(message.confidence * 100)}%</span>
          )}
          {message.latency_ms && (
            <span className="text-text-muted">{(message.latency_ms / 1000).toFixed(1)}s</span>
          )}
        </div>
      </div>

      {/* Multi-agent chips */}
      {message.agents_used && message.agents_used.length > 1 && (
        <div className="px-5 py-2 flex flex-wrap gap-1.5 border-b border-border bg-bg-primary/30">
          {message.agents_used.map((agent, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1 px-2 py-0.5 bg-bg-tertiary rounded-full text-[11px] text-text-secondary"
              style={{ borderLeft: `2px solid ${agentColors[agent] || '#666'}` }}
            >
              <span className="text-green-400 text-[9px]">✓</span>
              <span className="capitalize">{agent}</span>
            </span>
          ))}
        </div>
      )}

      {/* Content */}
      <div
        className="px-5 py-4 text-sm text-text-primary leading-relaxed"
        dangerouslySetInnerHTML={{ __html: formatContent(message.content) }}
      />

      {/* Artifact action */}
      {message.artifact_id && (
        <div className="px-5 py-3 bg-accent/5 border-t border-accent/20 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm">
            <span>📦</span>
            <span className="text-accent font-medium">Artifact ready</span>
            <span className="text-text-muted text-xs">{message.artifact_id}</span>
          </div>
          <button className="px-3 py-1 bg-accent hover:bg-accent-hover text-white text-xs font-medium rounded-lg transition">
            Review →
          </button>
        </div>
      )}
    </div>
  );
}

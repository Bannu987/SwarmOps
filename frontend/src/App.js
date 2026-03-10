import React, { useState, useRef, useEffect } from 'react';
import api from './api';
import { useChatStore } from './stores/chatStore';
import {
  Send, Plus, Copy, ThumbsUp, ThumbsDown, Loader2, Moon, Sun,
  Settings, Activity, X, Check, ChevronDown, Clock, AlertCircle,
  Zap, ArrowRight, Bell, Menu, Download, RotateCcw, CheckCircle2,
  Layers, BarChart3, Target, RefreshCw, Shield, MessageSquare,
  Lightbulb, Palette, Layout
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from 'recharts';
import './App.css';
import LandingPage from './LandingPage';
import './LandingPage.css';

/* ─────────────────────────────────────────────────────────────
   CUSTOM MARKDOWN PARSER
───────────────────────────────────────────────────────────── */
function parseInline(text) {
  if (!text) return null;
  // Clean bad data patterns
  text = text
    .replace(/VALUE:\s*UNKNOWN/gi, '')
    .replace(/STATUS:\s*INSUFFICIENT_DATA/gi, '')
    .replace(/\bUNKNOWN\b/g, '—')
    .trim();

  const parts = [];
  let remaining = text;
  let key = 0;

  while (remaining.length > 0) {
    // Code inline
    const codeMatch = remaining.match(/^(.*?)`([^`]+)`(.*)/s);
    // Bold
    const boldMatch = remaining.match(/^(.*?)\*\*(.+?)\*\*(.*)/s);
    // Italic
    const italicMatch = remaining.match(/^(.*?)(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)(.*)/s);
    // Link
    const linkMatch = remaining.match(/^(.*?)\[([^\]]+)\]\(([^)]+)\)(.*)/s);

    const firstCode = codeMatch ? (remaining.indexOf('`')) : Infinity;
    const firstBold = boldMatch ? remaining.indexOf('**') : Infinity;
    const firstLink = linkMatch ? remaining.indexOf('[') : Infinity;
    // eslint-disable-next-line no-loop-func
    const firstItalic = italicMatch ? (() => {
      const idx = remaining.search(/(?<!\*)\*(?!\*)/);
      return idx >= 0 ? idx : Infinity;
    })() : Infinity;

    const minIdx = Math.min(firstCode, firstBold, firstLink, firstItalic);

    if (minIdx === Infinity) {
      parts.push(<span key={key++}>{remaining}</span>);
      break;
    }

    if (minIdx === firstBold && boldMatch) {
      if (boldMatch[1]) parts.push(<span key={key++}>{boldMatch[1]}</span>);
      parts.push(<strong key={key++}>{boldMatch[2]}</strong>);
      remaining = boldMatch[3];
    } else if (minIdx === firstCode && codeMatch) {
      if (codeMatch[1]) parts.push(<span key={key++}>{codeMatch[1]}</span>);
      parts.push(<code key={key++} className="inline-code">{codeMatch[2]}</code>);
      remaining = codeMatch[3];
    } else if (minIdx === firstLink && linkMatch) {
      if (linkMatch[1]) parts.push(<span key={key++}>{linkMatch[1]}</span>);
      parts.push(<a key={key++} href={linkMatch[3]} target="_blank" rel="noopener noreferrer">{linkMatch[2]}</a>);
      remaining = linkMatch[4];
    } else if (minIdx === firstItalic && italicMatch) {
      if (italicMatch[1]) parts.push(<span key={key++}>{italicMatch[1]}</span>);
      parts.push(<em key={key++}>{italicMatch[2]}</em>);
      remaining = italicMatch[3];
    } else {
      parts.push(<span key={key++}>{remaining}</span>);
      break;
    }
  }
  return parts;
}

function parseMarkdown(text) {
  if (!text) return null;

  // Clean bad data
  text = text
    .replace(/VALUE:\s*UNKNOWN/gi, '')
    .replace(/STATUS:\s*INSUFFICIENT_DATA/gi, '');

  const lines = text.split('\n');
  const elements = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Code block
    if (line.trimStart().startsWith('```')) {
      const lang = line.trim().slice(3).trim();
      const codeLines = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      elements.push(
        <pre key={key++} className="md-code-block">
          <code className={'language-' + (lang || 'text')}>{codeLines.join('\n')}</code>
        </pre>
      );
      i++;
      continue;
    }

    // Horizontal rule
    if (/^---+$/.test(line.trim())) {
      elements.push(<hr key={key++} className="md-hr" />);
      i++;
      continue;
    }

    // Headers
    const headerMatch = line.match(/^(#{1,6})\s+(.+)/);
    if (headerMatch) {
      const level = headerMatch[1].length;
      const Tag = 'h' + level;
      elements.push(<Tag key={key++} className={'md-h' + level}>{parseInline(headerMatch[2])}</Tag>);
      i++;
      continue;
    }

    // Blockquote
    if (line.startsWith('>')) {
      const quoteLines = [];
      while (i < lines.length && lines[i].startsWith('>')) {
        quoteLines.push(lines[i].slice(1).trim());
        i++;
      }
      elements.push(
        <blockquote key={key++} className="md-blockquote">
          {parseInline(quoteLines.join(' '))}
        </blockquote>
      );
      continue;
    }

    // Table
    if (line.includes('|') && lines[i + 1] && lines[i + 1].match(/^\|?[\s\-|:]+\|?$/)) {
      const tableLines = [];
      while (i < lines.length && lines[i].includes('|')) {
        tableLines.push(lines[i]);
        i++;
      }
      const rows = tableLines.filter(l => !l.match(/^\|?[\s\-|:]+\|?$/));
      if (rows.length > 0) {
        const headers = rows[0].split('|').map(c => c.trim()).filter(c => c);
        const bodyRows = rows.slice(1);
        elements.push(
          <div key={key++} className="md-table-wrap">
            <table className="md-table">
              <thead>
                <tr>{headers.map((h, hi) => <th key={hi}>{parseInline(h)}</th>)}</tr>
              </thead>
              <tbody>
                {bodyRows.map((row, ri) => (
                  <tr key={ri}>
                    {row.split('|').map(c => c.trim()).filter(c => c).map((cell, ci) => (
                      <td key={ci}>{parseInline(cell)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      }
      continue;
    }

    // Unordered list
    if (/^(\s*)[-*+]\s/.test(line)) {
      const listItems = [];
      while (i < lines.length && /^(\s*)[-*+]\s/.test(lines[i])) {
        const content = lines[i].replace(/^\s*[-*+]\s/, '').trim();
        listItems.push(<li key={i}>{parseInline(content)}</li>);
        i++;
      }
      elements.push(<ul key={key++} className="md-ul">{listItems}</ul>);
      continue;
    }

    // Ordered list
    if (/^\d+\.\s/.test(line)) {
      const listItems = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i])) {
        const content = lines[i].replace(/^\d+\.\s/, '').trim();
        listItems.push(<li key={i}>{parseInline(content)}</li>);
        i++;
      }
      elements.push(<ol key={key++} className="md-ol">{listItems}</ol>);
      continue;
    }

    // Empty line → paragraph break
    if (line.trim() === '') {
      i++;
      continue;
    }

    // Regular paragraph
    const paraLines = [];
    while (i < lines.length && lines[i].trim() !== '' && !lines[i].startsWith('#') && !lines[i].startsWith('>') && !lines[i].startsWith('```') && !/^[-*+]\s/.test(lines[i]) && !/^\d+\.\s/.test(lines[i]) && !lines[i].includes('|')) {
      paraLines.push(lines[i]);
      i++;
    }
    if (paraLines.length > 0) {
      const combined = paraLines.join(' ');
      if (combined.trim()) {
        elements.push(<p key={key++} className="md-p">{parseInline(combined)}</p>);
      }
    } else {
      i++; // Safety: advance past unhandled line (e.g. lone | character) to prevent infinite loop
    }
  }

  return elements;
}

/* ─────────────────────────────────────────────────────────────
   AGENTS
───────────────────────────────────────────────────────────── */
const AGENTS = [
  { id: 'nexus',        emoji: '🧠', name: 'Nexus',          shortName: 'Nexus',     desc: 'AI orchestrator — routes to best agent', model: 'Smart Routing',  color: '#818CF8' },
  { id: 'seo',          emoji: '📊', name: 'SEO Agent',       shortName: 'SEO',       desc: 'Rankings, keywords & SERP analysis',      model: 'Gemini 1.5 Pro', color: '#2DD4BF' },
  { id: 'content',      emoji: '✍️', name: 'Content Agent',   shortName: 'Content',   desc: 'Blog posts, copy & WordPress publish',    model: 'Llama 3.3 70B', color: '#818CF8' },
  { id: 'ppc',          emoji: '💰', name: 'PPC Agent',        shortName: 'PPC',       desc: 'Google Ads campaigns & budget',           model: 'Gemini Flash',   color: '#FBBF24' },
  { id: 'analytics',    emoji: '📈', name: 'Analytics',        shortName: 'Analytics', desc: 'GA4 dashboard & anomaly detection',       model: 'Gemini 1.5 Pro', color: '#FB923C' },
  { id: 'crm',          emoji: '📧', name: 'CRM Agent',        shortName: 'CRM',       desc: 'HubSpot contacts & email sequences',      model: 'Llama 3.3 70B', color: '#34D399' },
  { id: 'smm',          emoji: '📱', name: 'SMM Agent',        shortName: 'Social',    desc: 'Social calendar, trends & viral hooks',   model: 'Llama 3.3 70B', color: '#E879F9' },
  { id: 'brand',        emoji: '🎨', name: 'Brand Agent',      shortName: 'Brand',     desc: 'Brand voice, positioning & guidelines',   model: 'Qwen 3 32B',    color: '#C084FC' },
  { id: 'webux',        emoji: '🌐', name: 'Web/UX Agent',    shortName: 'Web/UX',    desc: 'Landing pages, UX flows & wireframes',    model: 'Qwen 3 32B',    color: '#F472B6' },
  { id: 'cro',          emoji: '🔥', name: 'CRO Agent',        shortName: 'CRO',       desc: 'Conversion funnels & A/B testing',        model: 'Qwen 3 32B',    color: '#A78BFA' },
  { id: 'research',     emoji: '🔍', name: 'Research Agent',   shortName: 'Research',  desc: 'Web research with Brave Search',          model: 'Gemini 1.5 Pro', color: '#22D3EE' },
  { id: 'deep_research',emoji: '🔬', name: 'Deep Research',    shortName: 'Deep',      desc: 'Multi-step research with Kimi K2.5',      model: 'Kimi K2.5',     color: '#A78BFA' },
];

const AGENT_MAP = Object.fromEntries(AGENTS.map(a => [a.id, a]));

/* ─────────────────────────────────────────────────────────────
   CHART DATA
───────────────────────────────────────────────────────────── */
const trafficData = [
  { day: 'Mon', organic: 4000, paid: 2400, social: 2400 },
  { day: 'Tue', organic: 3000, paid: 1398, social: 2210 },
  { day: 'Wed', organic: 12000, paid: 9800, social: 2290 },
  { day: 'Thu', organic: 6000, paid: 3908, social: 2000 },
  { day: 'Fri', organic: 8900, paid: 4800, social: 2181 },
  { day: 'Sat', organic: 9500, paid: 3800, social: 2500 },
  { day: 'Sun', organic: 10300, paid: 4300, social: 2100 }
];


/* ─────────────────────────────────────────────────────────────
   CONVERSATION HELPERS
───────────────────────────────────────────────────────────── */
const CONVO_KEY = 'swarmops-conversations';
const DARK_KEY = 'swarmops-darkmode';
const LAUNCH_KEY = 'swarmops-launched';

/* Never block the UI — every API call gets a hard timeout */
const fetchWithTimeout = async (apiFn, timeoutMs = 10000) => {
  try {
    return await Promise.race([
      apiFn(),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('timeout')), timeoutMs)
      )
    ]);
  } catch (e) {
    console.log('API call skipped:', e.message);
    return null;
  }
};

function loadConvos() {
  try { return JSON.parse(localStorage.getItem(CONVO_KEY) || '[]'); } catch { return []; }
}
function saveConvos(convos) {
  try { localStorage.setItem(CONVO_KEY, JSON.stringify(convos.slice(0, 50))); } catch {}
}
function getConfidenceLevel(c) {
  if (c >= 0.7) return 'high';
  if (c >= 0.5) return 'medium';
  return 'low';
}

/* ─────────────────────────────────────────────────────────────
   MAIN APP
───────────────────────────────────────────────────────────── */
function App() {
  const {
    messages, selectedAgentId, addMessage, setSelectedAgent,
    setStreaming, clearMessages
  } = useChatStore();

  const [showLanding, setShowLanding] = useState(() => !localStorage.getItem(LAUNCH_KEY));
  const [darkMode, setDarkMode] = useState(() => {
    const s = localStorage.getItem(DARK_KEY);
    return s !== null ? JSON.parse(s) : true;
  });
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [rightPanelOpen, setRightPanelOpen] = useState(false);
  const [rightPanelTab, setRightPanelTab] = useState('insights');
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [agentDropdownOpen, setAgentDropdownOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [conversations, setConversations] = useState(loadConvos);
  const [currentConvoId, setCurrentConvoId] = useState(() => `convo-${Date.now()}`);
  const [notifOpen, setNotifOpen] = useState(false);
  const [smartMode, setSmartMode] = useState(false);

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const selectedAgent = AGENT_MAP[selectedAgentId] || AGENTS[0];

  // Apply theme to body
  useEffect(() => {
    document.body.className = darkMode ? 'dark' : 'light';
    localStorage.setItem(DARK_KEY, JSON.stringify(darkMode));
  }, [darkMode]);

  // Clear mock/stale messages on first load of new UI version
  useEffect(() => {
    if (!localStorage.getItem('swarmops-ui-v3')) {
      clearMessages();
      localStorage.setItem('swarmops-ui-v3', '1');
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 160) + 'px';
    }
  }, [input]);

  // Save conversation to localStorage when messages change
  useEffect(() => {
    if (messages.length === 0) return;
    const firstUser = messages.find(m => m.role === 'user');
    const title = firstUser ? firstUser.content.slice(0, 45) + (firstUser.content.length > 45 ? '…' : '') : 'New chat';
    setConversations(prev => {
      const existing = prev.findIndex(c => c.id === currentConvoId);
      const updated = {
        id: currentConvoId,
        title,
        messages,
        createdAt: existing >= 0 ? prev[existing].createdAt : new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      const next = existing >= 0
        ? prev.map(c => c.id === currentConvoId ? updated : c)
        : [updated, ...prev];
      saveConvos(next);
      return next;
    });
  }, [messages, currentConvoId]);

  // Keyboard shortcuts
  useEffect(() => {
    const h = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'b') { e.preventDefault(); setSidebarCollapsed(v => !v); }
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); textareaRef.current?.focus(); }
      if (e.key === 'Escape') { setAgentDropdownOpen(false); setNotifOpen(false); setSettingsOpen(false); setRightPanelOpen(false); }
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, []);


  const formatDeepResearchResult = (result) => {
    if (!result || typeof result !== 'object') return String(result);
    let f = '';
    if (result.summary) f += `## Summary\n\n${result.summary}\n\n`;
    if (result.key_findings?.length) {
      f += `## Key Findings\n\n`;
      result.key_findings.forEach((x, i) => { f += `${i + 1}. ${x}\n`; });
      f += '\n';
    }
    if (result.sources?.length) {
      f += `## Sources\n\n`;
      result.sources.slice(0, 8).forEach((s, i) => { f += `${i + 1}. [${s.title}](${s.url})\n`; });
      f += '\n';
    }
    if (result.recommendations?.length) {
      f += `## Recommendations\n\n`;
      result.recommendations.forEach((r, i) => { f += `${i + 1}. ${r}\n`; });
      f += '\n';
    }
    if (result.confidence !== undefined) f += `\n**Confidence:** ${(result.confidence * 100).toFixed(0)}%\n`;
    return f;
  };

  const handleSubmit = async (e) => {
    e?.preventDefault();
    const txt = input.trim();
    if (!txt || loading) return;
    addMessage({ id: Date.now(), role: 'user', content: txt, timestamp: new Date().toISOString() });
    setInput('');
    setLoading(true);
    setStreaming(true);

    const agentId = smartMode ? 'nexus' : selectedAgentId;
    const agentCfg = AGENT_MAP[agentId] || AGENTS[0];

    try {
      let data;
      if (agentId === 'deep_research') {
        data = await api.deepResearch(txt);
      } else {
        data = await api.chat(txt, agentId);
      }

      let content;
      if (agentId === 'deep_research' && data?.result && typeof data.result === 'object') {
        content = formatDeepResearchResult(data.result);
      } else {
        content = data?.result || data?.response || 'Response received.';
        if (typeof content === 'object') content = JSON.stringify(content, null, 2);
      }

      addMessage({
        id: Date.now() + Math.random(),
        role: 'agent',
        content,
        agentId: data?.agent || agentId,
        agentName: agentCfg.name,
        agentEmoji: agentCfg.emoji,
        agentColor: agentCfg.color,
        model: data?.model || agentCfg.model,
        provider: data?.provider,
        latency_ms: data?.latency_ms,
        quality: data?.quality,
        pipeline: data?.pipeline,
        result: data?.result,
        timestamp: new Date().toISOString()
      });
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : err.message || 'Service unavailable.';
      addMessage({
        id: Date.now() + Math.random(),
        role: 'system',
        content: `⚠️ ${agentCfg.name}: ${msg}`,
        timestamp: new Date().toISOString()
      });
    }
    setLoading(false);
    setStreaming(false);
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(); }
  };

  const newChat = () => {
    clearMessages();
    setCurrentConvoId('convo-' + Date.now());
  };

  const loadConversation = (convo) => {
    clearMessages();
    convo.messages.forEach(m => addMessage(m));
    setCurrentConvoId(convo.id);
  };

  const suggestedPrompts = [
    { emoji: '✍️', text: 'Create a content strategy for Q1 2026', agent: 'content' },
    { emoji: '📊', text: 'Find SEO keyword opportunities for my site', agent: 'seo' },
    { emoji: '💰', text: 'Analyze and optimize my PPC campaigns', agent: 'ppc' },
    { emoji: '🔥', text: 'Identify conversion funnel leaks', agent: 'cro' }
  ];

  if (showLanding) {
    return <LandingPage onEnter={() => { localStorage.setItem(LAUNCH_KEY, '1'); setShowLanding(false); }} />;
  }

  return (
    <div className={'app-root' + (darkMode ? ' dark' : ' light')}>
      {/* TOP NAV */}
      <nav className="top-nav">
        <div className="top-nav-left">
          <button className="nav-hamburger" onClick={() => setSidebarCollapsed(v => !v)}>
            <Menu size={18} />
          </button>
          <div className="nav-logo">
            <span className="nav-logo-text">SwarmOps</span>
            <span className="nav-logo-badge">AI</span>
          </div>
        </div>
        <div className="nav-convo-title">
          {messages.length > 0
            ? (messages.find(m => m.role === 'user')?.content.slice(0, 40) || 'Chat')
            : 'New Chat'}
        </div>
        <div className="top-nav-right">
          <button className="nav-icon-btn" onClick={() => setDarkMode(v => !v)} title={darkMode ? 'Light mode' : 'Dark mode'}>
            {darkMode ? <Sun size={16} /> : <Moon size={16} />}
          </button>
          <button className={'nav-icon-btn' + (notifOpen ? ' active' : '')} onClick={() => setNotifOpen(v => !v)} title="Notifications">
            <Bell size={16} />
          </button>
          <button className={'nav-icon-btn' + (rightPanelOpen ? ' active' : '')} onClick={() => setRightPanelOpen(v => !v)} title="Insights panel">
            <Layout size={16} />
          </button>
          <button className="nav-icon-btn" onClick={() => setSettingsOpen(true)} title="Settings">
            <Settings size={16} />
          </button>
        </div>
      </nav>

      <div className="app-body">
        {/* LEFT SIDEBAR */}
        <aside className={'sidebar' + (sidebarCollapsed ? ' collapsed' : '')}>
          <div className="sidebar-top">
            <button className="new-chat-btn" onClick={newChat}>
              <Plus size={16} />
              {!sidebarCollapsed && <span>New Chat</span>}
            </button>
          </div>

          <div className="sidebar-section">
            {!sidebarCollapsed && <div className="sidebar-section-label">Agents</div>}
            <div className="agent-list">
              {AGENTS.map(agent => (
                <button
                  key={agent.id}
                  className={'agent-item' + (selectedAgentId === agent.id ? ' active' : '')}
                  onClick={() => setSelectedAgent(agent.id)}
                  title={agent.name}
                >
                  <span className="agent-item-emoji">{agent.emoji}</span>
                  {!sidebarCollapsed && (
                    <div className="agent-item-info">
                      <span className="agent-item-name">{agent.shortName}</span>
                      <span className="agent-item-model">{agent.model}</span>
                    </div>
                  )}
                  {!sidebarCollapsed && selectedAgentId === agent.id && (
                    <div className="agent-item-dot" style={{ background: agent.color }} />
                  )}
                </button>
              ))}
            </div>
          </div>

          {!sidebarCollapsed && conversations.length > 0 && (
            <div className="sidebar-section sidebar-history">
              <div className="sidebar-section-label">Recent</div>
              <div className="history-list">
                {conversations.slice(0, 15).map(convo => (
                  <button
                    key={convo.id}
                    className={'history-item' + (convo.id === currentConvoId ? ' active' : '')}
                    onClick={() => loadConversation(convo)}
                    title={convo.title}
                  >
                    <MessageSquare size={12} />
                    <span className="history-title">{convo.title}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="sidebar-footer">
            <button className="sidebar-footer-btn" onClick={() => setSettingsOpen(true)} title="Settings">
              <Settings size={16} />
              {!sidebarCollapsed && <span>Settings</span>}
            </button>
          </div>
        </aside>

        {/* MAIN AREA */}
        <main className="main-area">
          {/* CHAT AREA */}
          <div className="chat-area">
            {messages.length === 0 ? (
              <EmptyState
                suggestedPrompts={suggestedPrompts}
                setInput={setInput}
                setSelectedAgent={setSelectedAgent}
                agentEmoji={selectedAgent.emoji}
                agentColor={selectedAgent.color}
                smartMode={smartMode}
              />
            ) : (
              <div className="messages-list">
                {messages.map((msg, idx) => (
                  <MessageBubble key={msg.id || idx} message={msg} isLatest={idx === messages.length - 1} />
                ))}
                {loading && <LoadingDots agent={selectedAgent} />}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* INPUT BAR */}
          <div className="input-bar">
            <div className="input-bar-inner">
              {agentDropdownOpen && (
                <>
                  <div className="dropdown-backdrop" onClick={() => setAgentDropdownOpen(false)} />
                  <div className="agent-dropdown">
                    <div className="agent-dropdown-header">Select Agent</div>
                    {AGENTS.map(agent => (
                      <button
                        key={agent.id}
                        className={'agent-dropdown-item' + (selectedAgentId === agent.id ? ' selected' : '')}
                        onClick={() => { setSelectedAgent(agent.id); setAgentDropdownOpen(false); setSmartMode(false); }}
                      >
                        <span className="dropdown-emoji">{agent.emoji}</span>
                        <div className="dropdown-info">
                          <span className="dropdown-name">{agent.name}</span>
                          <span className="dropdown-model">{agent.model}</span>
                        </div>
                        {selectedAgentId === agent.id && !smartMode && <Check size={13} />}
                      </button>
                    ))}
                    <button
                      className={'agent-dropdown-item smart-mode-item' + (smartMode ? ' selected' : '')}
                      onClick={() => { setSmartMode(true); setAgentDropdownOpen(false); }}
                    >
                      <span className="dropdown-emoji">⚡</span>
                      <div className="dropdown-info">
                        <span className="dropdown-name">Auto Route</span>
                        <span className="dropdown-model">Nexus picks best agent</span>
                      </div>
                      {smartMode && <Check size={13} />}
                    </button>
                  </div>
                </>
              )}

              <div className="input-box">
                <button className="agent-pill" onClick={() => setAgentDropdownOpen(v => !v)}>
                  <span>{smartMode ? '⚡' : selectedAgent.emoji}</span>
                  <span>{smartMode ? 'Auto' : selectedAgent.shortName}</span>
                  <ChevronDown size={11} />
                </button>
                <textarea
                  ref={textareaRef}
                  className="input-textarea"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKey}
                  placeholder={smartMode ? 'Ask anything — Nexus routes automatically…' : 'Ask ' + selectedAgent.name + ' anything…'}
                  rows={1}
                  disabled={loading}
                />
                <button
                  type="button"
                  className={'send-btn' + (input.trim() && !loading ? ' active' : '')}
                  onClick={handleSubmit}
                  disabled={!input.trim() || loading}
                >
                  {loading ? <Loader2 size={15} className="spin" /> : <Send size={15} />}
                </button>
              </div>
              <p className="input-hint">Enter to send · Shift+Enter new line · Ctrl+B toggle sidebar · Ctrl+K focus</p>
            </div>
          </div>
        </main>

        {/* RIGHT PANEL */}
        {rightPanelOpen && (
          <aside className="right-panel">
            <div className="right-panel-header">
              <div className="right-panel-tabs">
                {[
                  { id: 'insights', icon: Lightbulb, label: 'Insights' },
                  { id: 'analytics', icon: BarChart3, label: 'Analytics' },
                  { id: 'competitors', icon: Target, label: 'Compete' },
                  { id: 'brand', icon: Palette, label: 'Brand' },
                  { id: 'settings', icon: Settings, label: 'Settings' },
                ].map(tab => (
                  <button
                    key={tab.id}
                    className={'rp-tab' + (rightPanelTab === tab.id ? ' active' : '')}
                    onClick={() => setRightPanelTab(tab.id)}
                    title={tab.label}
                  >
                    <tab.icon size={13} />
                    <span>{tab.label}</span>
                  </button>
                ))}
              </div>
              <button className="rp-close" onClick={() => setRightPanelOpen(false)}><X size={15} /></button>
            </div>
            <div className="right-panel-content">
              {rightPanelTab === 'insights' && <InsightsTab />}
              {rightPanelTab === 'analytics' && <AnalyticsTab />}
              {rightPanelTab === 'competitors' && <CompetitorsTab />}
              {rightPanelTab === 'brand' && <BrandDnaTab />}
              {rightPanelTab === 'settings' && (
                <SettingsTab darkMode={darkMode} setDarkMode={setDarkMode} clearMessages={() => { clearMessages(); setCurrentConvoId('convo-' + Date.now()); }} />
              )}
            </div>
          </aside>
        )}
      </div>

      {/* SETTINGS MODAL */}
      {settingsOpen && (
        <SettingsModal
          darkMode={darkMode}
          setDarkMode={setDarkMode}
          onClose={() => setSettingsOpen(false)}
          clearMessages={() => { clearMessages(); setCurrentConvoId('convo-' + Date.now()); setSettingsOpen(false); }}
        />
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   EMPTY STATE
───────────────────────────────────────────────────────────── */
function EmptyState({ suggestedPrompts, setInput, setSelectedAgent, agentEmoji, agentColor, smartMode }) {
  return (
    <div className="empty-state">
      <div className="empty-hero">
        <div className="empty-logo" style={{ borderColor: agentColor + '40' }}>
          <span className="empty-logo-emoji">{smartMode ? '⚡' : agentEmoji}</span>
        </div>
        <h1 className="empty-title">SwarmOps</h1>
        <p className="empty-subtitle">Multi-Agent AI Marketing Intelligence</p>
      </div>
      <div className="suggestion-grid">
        {suggestedPrompts.map((p, i) => (
          <button
            key={i}
            className="suggestion-card"
            onClick={() => { setSelectedAgent(p.agent); setInput(p.text); }}
          >
            <span className="suggestion-emoji">{p.emoji}</span>
            <span className="suggestion-text">{p.text}</span>
            <ArrowRight size={14} className="suggestion-arrow" />
          </button>
        ))}
      </div>
      <p className="empty-hint">Select an agent from the sidebar · Type a message · Press Enter</p>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   MESSAGE BUBBLE
───────────────────────────────────────────────────────────── */
function MessageBubble({ message, isLatest }) {
  const [copied, setCopied] = useState(false);
  const [liked, setLiked] = useState(null);
  const [expandedSteps, setExpandedSteps] = useState({});

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFeedback = async (quality) => {
    const newVal = liked === quality ? null : quality;
    setLiked(newVal);
    if (newVal !== null && message.agentId) {
      try {
        await api.learning.feedback(message.agentId, message.content?.slice(0, 100) || '', newVal, '');
      } catch {}
    }
  };

  if (message.role === 'user') {
    return (
      <div className="msg msg-user">
        <div className="user-bubble">
          <p className="user-label">You</p>
          <div className="user-text">{message.content}</div>
        </div>
      </div>
    );
  }

  if (message.role === 'system') {
    return (
      <div className="msg msg-system">
        <AlertCircle size={14} />
        <span>{message.content}</span>
      </div>
    );
  }

  // Onboarding message
  if (message.provider === 'system') {
    return (
      <div className="msg msg-agent">
        <div className="agent-avatar onboarding-avatar">🧠</div>
        <div className="agent-body">
          <div className="agent-label">
            <span className="agent-label-name">SwarmOps</span>
            <span className="agent-label-badge">Setup</span>
          </div>
          <div className="agent-content onboarding-content">
            {parseMarkdown(message.content)}
          </div>
        </div>
      </div>
    );
  }

  const isPipeline = message.pipeline || (message.result && typeof message.result === 'object' && message.result.pipeline);
  const agentColor = message.agentColor || '#818CF8';
  const providerKey = message.provider?.toLowerCase().split(' ')[0] || '';

  return (
    <div className="msg msg-agent">
      <div className="agent-avatar" style={{ background: agentColor + '20', borderColor: agentColor + '40' }}>
        <span>{message.agentEmoji || '🤖'}</span>
      </div>
      <div className="agent-body">
        <div className="agent-label">
          <span className="agent-label-name">{message.agentName}</span>
          {message.model && <span className="agent-label-model">{message.model}</span>}
        </div>

        {isPipeline && message.result?.steps ? (
          <PipelineViz
            steps={message.result.steps}
            totalLatency={message.result.total_latency_ms}
            expandedSteps={expandedSteps}
            toggleStep={(idx) => setExpandedSteps(p => ({ ...p, [idx]: !p[idx] }))}
          />
        ) : (
          <div className="agent-content">
            {parseMarkdown(message.content)}
          </div>
        )}

        {message.provider && message.provider !== 'system' && (
          <div className="msg-meta">
            {message.provider && <span className={'meta-pill provider-' + providerKey}>{message.provider}</span>}
            {message.latency_ms && <span className="meta-pill">{(message.latency_ms / 1000).toFixed(1)}s</span>}
            {message.quality?.confidence != null && (
              <span className={'meta-pill conf-' + getConfidenceLevel(message.quality.confidence)}>
                {(message.quality.confidence * 100).toFixed(0)}% conf
              </span>
            )}
            {message.quality?.revised && <span className="meta-pill revised">✨ Revised</span>}
          </div>
        )}

        <div className="msg-actions">
          <button className={'msg-btn' + (copied ? ' success' : '')} onClick={handleCopy}>
            {copied ? <Check size={12} /> : <Copy size={12} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
          <button className={'msg-btn' + (liked === true ? ' liked' : '')} onClick={() => handleFeedback(true)}>
            <ThumbsUp size={12} />
          </button>
          <button className={'msg-btn' + (liked === false ? ' disliked' : '')} onClick={() => handleFeedback(false)}>
            <ThumbsDown size={12} />
          </button>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   PIPELINE VISUALIZATION
───────────────────────────────────────────────────────────── */
function PipelineViz({ steps, totalLatency, expandedSteps, toggleStep }) {
  if (!steps?.length) return null;
  const avgConf = steps.reduce((s, x) => s + (x.confidence || 0), 0) / steps.length;

  return (
    <div className="pipeline-viz">
      <div className="pipeline-flow">
        {steps.map((step, i) => (
          <React.Fragment key={i}>
            {i > 0 && <div className="pipeline-arrow">→</div>}
            <div className="pipeline-node">
              <div className="pipeline-node-name">{step.department?.toUpperCase()}</div>
              <div className="pipeline-node-meta">
                <span className={'conf-' + getConfidenceLevel(step.confidence)}>{(step.confidence * 100).toFixed(0)}%</span>
                <span>{(step.latency_ms / 1000).toFixed(1)}s</span>
              </div>
            </div>
          </React.Fragment>
        ))}
      </div>
      <div className="pipeline-stats">
        <span><Layers size={12} /> {steps.length} agents</span>
        {totalLatency && <span><Clock size={12} /> {(totalLatency / 1000).toFixed(1)}s</span>}
        <span><Target size={12} /> {(avgConf * 100).toFixed(0)}% avg</span>
      </div>
      <div className="pipeline-accordion">
        {steps.map((step, i) => (
          <div key={i} className={'pipeline-card' + (expandedSteps[i] ? ' expanded' : '')}>
            <button className="pipeline-card-header" onClick={() => toggleStep(i)}>
              <div className="pipeline-card-left">
                <CheckCircle2 size={13} className={'conf-' + getConfidenceLevel(step.confidence)} />
                <span>{step.department?.toUpperCase()}</span>
                <span className={'conf-' + getConfidenceLevel(step.confidence)}>{(step.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="pipeline-card-right">
                <span>{step.latency_ms}ms</span>
                <ChevronDown size={14} className={'chevron' + (expandedSteps[i] ? ' open' : '')} />
              </div>
            </button>
            {expandedSteps[i] && (
              <div className="pipeline-card-body">
                {parseMarkdown(step.full_result || step.result)}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   LOADING DOTS
───────────────────────────────────────────────────────────── */
function LoadingDots({ agent }) {
  return (
    <div className="msg msg-agent">
      <div className="agent-avatar" style={{ background: (agent.color || '#818CF8') + '20' }}>
        <span>{agent.emoji}</span>
      </div>
      <div className="agent-body">
        <div className="agent-label">
          <span className="agent-label-name">{agent.name}</span>
        </div>
        <div className="loading-dots">
          <div className="loading-dot" />
          <div className="loading-dot" />
          <div className="loading-dot" />
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   RIGHT PANEL TABS
───────────────────────────────────────────────────────────── */
const STATIC_INSIGHTS = [
  { title: 'Content Gap', desc: 'Competitors rank for "AI marketing automation" — no content from you.', priority: 'high', impact: '+2,400 visits/mo' },
  { title: 'PPC Opportunity', desc: 'High-intent keywords underutilized in current campaigns.', priority: 'medium', impact: '340 more conversions' },
  { title: 'A/B Test Ready', desc: 'Homepage CTA has enough traffic for a 2-week test.', priority: 'low', impact: '+18% CVR potential' },
];

function InsightsTab() {
  const [insights, setInsights] = useState(STATIC_INSIGHTS); // show instantly
  const [refreshing, setRefreshing] = useState(false);

  const refresh = async () => {
    setRefreshing(true);
    const d = await fetchWithTimeout(() => api.learning.insights('nexus'));
    if (d) {
      const list = d.insights || (Array.isArray(d) ? d : []);
      if (list.length > 0) setInsights(list);
    }
    setRefreshing(false);
  };

  return (
    <div className="rp-tab-content">
      <div className="rp-section-head">
        <h3 className="rp-section-title">AI Insights</h3>
        <button className="rp-add-btn" onClick={refresh} disabled={refreshing} title="Refresh from AI">
          {refreshing ? <Loader2 size={13} className="spin" /> : <RefreshCw size={13} />}
        </button>
      </div>
      <div className="insights-list">
        {insights.map((ins, i) => (
          <div key={i} className={'insight-card priority-' + (ins.priority || 'low')}>
            <div className="insight-priority-bar" />
            <div className="insight-body">
              <div className="insight-head">
                <span className="insight-title">{ins.title}</span>
                <span className={'priority-chip ' + (ins.priority || 'low')}>{ins.priority || 'info'}</span>
              </div>
              <p className="insight-desc">{ins.desc || ins.description || ins.content}</p>
              {ins.impact && (
                <div className="insight-impact"><Zap size={12} /><span>{ins.impact}</span></div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function AnalyticsTab() {
  const [stats, setStats] = useState(null);
  const [rateLimits, setRateLimits] = useState(null);

  useEffect(() => {
    fetchWithTimeout(() => api.stats()).then(d => { if (d) setStats(d); });
    fetchWithTimeout(() => api.rateLimits()).then(d => { if (d) setRateLimits(d); });
  }, []);

  return (
    <div className="rp-tab-content">
      <h3 className="rp-section-title">Analytics</h3>
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Total Tasks</div>
            <div className="stat-value">{stats.total_tasks || 0}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Today</div>
            <div className="stat-value">{stats.tasks_today || 0}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Avg Confidence</div>
            <div className={'stat-value conf-' + getConfidenceLevel(stats.avg_confidence || 0)}>
              {((stats.avg_confidence || 0) * 100).toFixed(0)}%
            </div>
          </div>
        </div>
      )}

      <div className="chart-card">
        <div className="chart-title">Traffic Sources</div>
        <ResponsiveContainer width="100%" height={160}>
          <AreaChart data={trafficData}>
            <defs>
              <linearGradient id="gOrg" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#818CF8" stopOpacity={0.4} />
                <stop offset="100%" stopColor="#818CF8" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gPaid" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#FBBF24" stopOpacity={0.4} />
                <stop offset="100%" stopColor="#FBBF24" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis dataKey="day" stroke="rgba(255,255,255,0.3)" fontSize={10} tickLine={false} axisLine={false} />
            <YAxis stroke="rgba(255,255,255,0.3)" fontSize={10} tickLine={false} axisLine={false} tickFormatter={v => v / 1000 + 'k'} />
            <Tooltip contentStyle={{ background: 'var(--bg-2)', border: '1px solid var(--border)', borderRadius: 8 }} />
            <Area type="monotone" dataKey="organic" stroke="#818CF8" strokeWidth={2} fill="url(#gOrg)" />
            <Area type="monotone" dataKey="paid" stroke="#FBBF24" strokeWidth={2} fill="url(#gPaid)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {rateLimits?.status && (
        <div className="rate-limits">
          <div className="rp-section-title">API Rate Limits</div>
          {Object.entries(rateLimits.status).map(([provider, info]) => {
            const pct = Math.min((info.used / (info.limit || 1)) * 100, 100);
            const cls = pct >= 80 ? 'critical' : pct >= 50 ? 'warning' : 'good';
            return (
              <div key={provider} className="rate-bar-item">
                <div className="rate-bar-label">
                  <span>{provider}</span>
                  <span>{info.used}/{info.limit}</span>
                </div>
                <div className="rate-bar-bg">
                  <div className={'rate-bar-fill ' + cls} style={{ width: pct + '%' }} />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function CompetitorsTab() {
  const [competitors, setCompetitors] = useState([]);
  const [loading, setLoading] = useState(false); // don't block on mount
  const [adding, setAdding] = useState(false);
  const [newName, setNewName] = useState('');
  const [newUrl, setNewUrl] = useState('');
  const [analyzing, setAnalyzing] = useState(null);
  const [battleCard, setBattleCard] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetchWithTimeout(() => api.competitors.list()).then(d => {
      if (d) setCompetitors(d.competitors || d || []);
      setLoading(false);
    });
  }, []);

  const addCompetitor = async () => {
    if (!newName.trim() || !newUrl.trim()) return;
    try {
      await api.competitors.add(newName.trim(), newUrl.trim());
      const fresh = await api.competitors.list();
      setCompetitors(fresh.competitors || fresh || []);
      setNewName(''); setNewUrl(''); setAdding(false);
    } catch (err) {
      alert('Failed to add: ' + err.message);
    }
  };

  const runAnalysis = async (id) => {
    setAnalyzing(id);
    try {
      await api.competitors.analyze(id);
      const fresh = await api.competitors.list();
      setCompetitors(fresh.competitors || fresh || []);
    } catch {}
    setAnalyzing(null);
  };

  const viewBattleCard = async (id) => {
    try {
      const res = await api.competitors.battleCard(id);
      setBattleCard(res.battle_card || res.content || '');
    } catch {}
  };

  if (battleCard) {
    return (
      <div className="rp-tab-content">
        <button className="back-btn" onClick={() => setBattleCard(null)}><ChevronDown size={14} className="rotate-90" /> Back</button>
        <div className="battle-card">{parseMarkdown(battleCard)}</div>
      </div>
    );
  }

  return (
    <div className="rp-tab-content">
      <div className="rp-section-head">
        <h3 className="rp-section-title">Competitors</h3>
        <button className="rp-add-btn" onClick={() => setAdding(v => !v)}>
          {adding ? <X size={14} /> : <Plus size={14} />}
        </button>
      </div>

      {adding && (
        <div className="add-competitor-form">
          <input className="rp-input" placeholder="Company name" value={newName} onChange={e => setNewName(e.target.value)} />
          <input className="rp-input" placeholder="Website URL" value={newUrl} onChange={e => setNewUrl(e.target.value)} />
          <button className="rp-submit-btn" onClick={addCompetitor}>Add &amp; Analyze</button>
        </div>
      )}

      {loading ? (
        <div className="rp-loading"><Loader2 size={20} className="spin" /><span>Loading…</span></div>
      ) : competitors.length === 0 ? (
        <div className="rp-empty">
          <Target size={32} />
          <p>No competitors tracked yet</p>
          <button className="rp-add-btn-lg" onClick={() => setAdding(true)}>Add First Competitor</button>
        </div>
      ) : (
        <div className="competitors-list">
          {competitors.map(comp => (
            <div key={comp.id} className="competitor-card">
              <div className="competitor-head">
                <div>
                  <div className="competitor-name">{comp.name}</div>
                  <div className="competitor-url">{comp.website_url}</div>
                  {comp.industry && <div className="competitor-industry">{comp.industry}</div>}
                </div>
                <div className="competitor-actions">
                  <button
                    className="comp-btn"
                    onClick={() => runAnalysis(comp.id)}
                    disabled={analyzing === comp.id}
                    title="Run analysis"
                  >
                    {analyzing === comp.id ? <Loader2 size={12} className="spin" /> : <RefreshCw size={12} />}
                  </button>
                  <button className="comp-btn" onClick={() => viewBattleCard(comp.id)} title="Battle card">
                    <Shield size={12} />
                  </button>
                </div>
              </div>
              {comp.last_analyzed && (
                <div className="competitor-meta">Last analyzed {new Date(comp.last_analyzed).toLocaleDateString()}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function BrandDnaTab() {
  const [brandDna, setBrandDna] = useState(null);
  const [loading, setLoading] = useState(false); // don't block on mount
  const [extracting, setExtracting] = useState(false);
  const [url, setUrl] = useState('');

  useEffect(() => {
    setLoading(true);
    fetchWithTimeout(() => api.brandDna.get()).then(d => {
      if (d) setBrandDna(d.brand_dna || d || null);
      setLoading(false);
    });
  }, []);

  const extract = async () => {
    if (!url.trim()) return;
    setExtracting(true);
    try {
      const res = await api.brandDna.extract(url.trim());
      setBrandDna(res.brand_dna || res || null);
    } catch (err) {
      alert('Extraction failed: ' + err.message);
    }
    setExtracting(false);
  };

  return (
    <div className="rp-tab-content">
      <h3 className="rp-section-title">Brand DNA</h3>

      {loading ? (
        <div className="rp-loading"><Loader2 size={20} className="spin" /><span>Loading…</span></div>
      ) : brandDna ? (
        <div className="brand-dna">
          {brandDna.brand_name && <div className="dna-field"><span className="dna-label">Brand</span><span className="dna-value">{brandDna.brand_name}</span></div>}
          {brandDna.industry && <div className="dna-field"><span className="dna-label">Industry</span><span className="dna-value">{brandDna.industry}</span></div>}
          {brandDna.tone_of_voice && <div className="dna-field"><span className="dna-label">Tone</span><span className="dna-value">{brandDna.tone_of_voice}</span></div>}
          {brandDna.target_audience && <div className="dna-field"><span className="dna-label">Audience</span><span className="dna-value">{brandDna.target_audience}</span></div>}
          {brandDna.value_proposition && (
            <div className="dna-field-block">
              <span className="dna-label">Value Prop</span>
              <p className="dna-value">{brandDna.value_proposition}</p>
            </div>
          )}
          {brandDna.key_differentiators && (
            <div className="dna-field-block">
              <span className="dna-label">Differentiators</span>
              <ul className="dna-list">
                {(Array.isArray(brandDna.key_differentiators)
                  ? brandDna.key_differentiators
                  : brandDna.key_differentiators.split(',')
                ).map((d, i) => <li key={i}>{d.trim()}</li>)}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <div className="rp-empty">
          <Palette size={32} />
          <p>No brand DNA extracted yet</p>
        </div>
      )}

      <div className="extract-form">
        <div className="rp-section-title" style={{ marginTop: 16 }}>Extract from Website</div>
        <input className="rp-input" placeholder="https://yoursite.com" value={url} onChange={e => setUrl(e.target.value)} />
        <button className="rp-submit-btn" onClick={extract} disabled={extracting}>
          {extracting ? <><Loader2 size={14} className="spin" /> Extracting…</> : 'Extract Brand DNA'}
        </button>
      </div>
    </div>
  );
}

function SettingsTab({ darkMode, setDarkMode, clearMessages }) {
  const [healthStatus, setHealthStatus] = useState(null);
  const [checkingHealth, setCheckingHealth] = useState(false);

  const checkHealth = async () => {
    setCheckingHealth(true);
    try {
      const res = await api.health();
      setHealthStatus(res);
    } catch (err) {
      setHealthStatus({ status: 'error', message: err.message });
    }
    setCheckingHealth(false);
  };

  const exportData = async () => {
    try {
      const res = await api.database.export();
      const blob = new Blob([JSON.stringify(res, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = 'swarmops-export.json'; a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert('Export failed: ' + err.message);
    }
  };

  const resetLearning = async () => {
    if (!window.confirm('Reset all learning preferences?')) return;
    try {
      await api.learning.reset();
      alert('Learning engine reset.');
    } catch (err) {
      alert('Reset failed: ' + err.message);
    }
  };

  return (
    <div className="rp-tab-content">
      <h3 className="rp-section-title">Settings</h3>

      <div className="settings-group">
        <div className="settings-group-label">Theme</div>
        <div className="theme-toggle-row">
          <button className={'theme-btn' + (!darkMode ? ' active' : '')} onClick={() => setDarkMode(false)}>
            <Sun size={14} /> Light
          </button>
          <button className={'theme-btn' + (darkMode ? ' active' : '')} onClick={() => setDarkMode(true)}>
            <Moon size={14} /> Dark
          </button>
        </div>
      </div>

      <div className="settings-group">
        <div className="settings-group-label">Data</div>
        <button className="settings-action-btn" onClick={exportData}>
          <Download size={14} /> Export All Data
        </button>
        <button className="settings-action-btn" onClick={resetLearning}>
          <RotateCcw size={14} /> Reset Learning Engine
        </button>
        <button className="settings-action-btn danger" onClick={clearMessages}>
          <X size={14} /> Clear Conversations
        </button>
      </div>

      <div className="settings-group">
        <div className="settings-group-label">API Health</div>
        <button className="settings-action-btn" onClick={checkHealth} disabled={checkingHealth}>
          {checkingHealth ? <Loader2 size={14} className="spin" /> : <Activity size={14} />}
          Check API Status
        </button>
        {healthStatus && (
          <div className={'health-status ' + (healthStatus.status === 'healthy' ? 'healthy' : 'error')}>
            <pre>{JSON.stringify(healthStatus, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   SETTINGS MODAL
───────────────────────────────────────────────────────────── */
function SettingsModal({ darkMode, setDarkMode, onClose, clearMessages }) {
  const exportData = async () => {
    try {
      const res = await api.database.export();
      const blob = new Blob([JSON.stringify(res, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = 'swarmops-export.json'; a.click();
      URL.revokeObjectURL(url);
    } catch (err) { alert('Export failed: ' + err.message); }
  };

  return (
    <>
      <div className="modal-backdrop" onClick={onClose} />
      <div className="modal">
        <div className="modal-header">
          <div>
            <h3 className="modal-title">Settings</h3>
            <p className="modal-subtitle">Customize your SwarmOps experience</p>
          </div>
          <button className="modal-close" onClick={onClose}><X size={18} /></button>
        </div>

        <div className="modal-body">
          <div className="settings-section">
            <h4 className="settings-label">Appearance</h4>
            <div className="theme-cards">
              <button className={'theme-card' + (!darkMode ? ' active' : '')} onClick={() => setDarkMode(false)}>
                <div className="theme-preview-light">
                  <div className="tp-bar" /><div className="tp-content" />
                </div>
                <span><Sun size={13} /> Light</span>
              </button>
              <button className={'theme-card' + (darkMode ? ' active' : '')} onClick={() => setDarkMode(true)}>
                <div className="theme-preview-dark">
                  <div className="tp-bar" /><div className="tp-content" />
                </div>
                <span><Moon size={13} /> Dark</span>
              </button>
            </div>
          </div>

          <div className="settings-section">
            <h4 className="settings-label">Data Management</h4>
            <button className="modal-action-btn" onClick={exportData}><Download size={15} /> Export Data</button>
            <button className="modal-action-btn danger" onClick={() => { clearMessages(); onClose(); }}>
              <RotateCcw size={15} /> Clear All Conversations
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

export default App;

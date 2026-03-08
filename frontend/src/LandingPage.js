import React, { useState, useEffect, useRef } from 'react';
import './LandingPage.css';
import api from './api';

/* ── Fade-in hook ─────────────────────────────────────────── */
function useFadeIn() {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { el.classList.add('lp-fade--in'); obs.unobserve(el); } },
      { threshold: 0.08 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return ref;
}

/* ── Demo card (isolated so hooks don't violate rules) ──── */
function DemoCard({ label, prompt, agent }) {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [meta, setMeta] = useState(null);
  const [expanded, setExpanded] = useState(false);
  const TRUNCATE = 500;

  const run = async () => {
    setRunning(true);
    setResult(null);
    setMeta(null);
    try {
      const data = await api.chat(prompt, agent);
      const text = typeof data.result === 'string'
        ? data.result
        : typeof data.result === 'object'
          ? JSON.stringify(data.result, null, 2)
          : data.response || data.message || 'Done.';
      setResult(text);
      setMeta({
        model: data.model,
        provider: data.provider,
        latency: data.latency_ms,
        confidence: data.quality?.confidence,
      });
    } catch (err) {
      setResult(`Error: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  const display = result && !expanded && result.length > TRUNCATE
    ? result.slice(0, TRUNCATE) + '…'
    : result;

  const providerClass = meta?.provider
    ? meta.provider.toLowerCase().includes('groq') ? 'groq'
      : meta.provider.toLowerCase().includes('google') ? 'google'
      : meta.provider.toLowerCase().includes('nvidia') ? 'nvidia'
      : ''
    : '';

  const confClass = meta?.confidence != null
    ? meta.confidence >= 0.7 ? 'confidence-high'
      : meta.confidence >= 0.5 ? 'confidence-medium' : ''
    : '';

  return (
    <div className="lp-demo-card">
      <span className="lp-demo-label">{label}</span>
      <p className="lp-demo-prompt">"{prompt}"</p>
      <button
        className={`lp-demo-run-btn${running ? ' running' : ''}`}
        onClick={run}
        disabled={running}
      >
        {running ? (
          <><div className="lp-demo-spinner" /><span>Running…</span></>
        ) : (
          <span>Run →</span>
        )}
      </button>
      {result && (
        <div className="lp-demo-result">
          <pre className="lp-demo-result-text">{display}</pre>
          {result.length > TRUNCATE && (
            <button className="lp-demo-show-more" onClick={() => setExpanded(!expanded)}>
              {expanded ? 'Show less ▴' : 'Show more ▾'}
            </button>
          )}
          {meta && (
            <div className="lp-demo-meta">
              {meta.model && <span className="lp-meta-pill">{meta.model}</span>}
              {meta.provider && <span className={`lp-meta-pill ${providerClass}`}>{meta.provider}</span>}
              {meta.latency && <span className="lp-meta-pill">{(meta.latency / 1000).toFixed(1)}s</span>}
              {meta.confidence != null && (
                <span className={`lp-meta-pill ${confClass}`}>{(meta.confidence * 100).toFixed(0)}% conf</span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Main LandingPage ─────────────────────────────────────── */
export default function LandingPage({ onEnter }) {
  const [menuOpen, setMenuOpen] = useState(false);

  const refHowitworks = useFadeIn();
  const refAgents     = useFadeIn();
  const refDemo       = useFadeIn();
  const refFeatures   = useFadeIn();
  const refStack      = useFadeIn();

  const scrollTo = (id) => {
    setMenuOpen(false);
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  const AGENTS = [
    { emoji: '🔍', name: 'SEO Agent',       model: 'Gemini 1.5 Pro' },
    { emoji: '✍️', name: 'Content Agent',   model: 'Groq · Llama 3.3' },
    { emoji: '📢', name: 'PPC Agent',        model: 'Gemini 1.5 Flash' },
    { emoji: '📊', name: 'Analytics Agent',  model: 'Gemini 1.5 Pro' },
    { emoji: '🤝', name: 'CRM Agent',        model: 'Groq · Llama 3.3' },
    { emoji: '📱', name: 'SMM Agent',        model: 'Groq · Llama 3.3' },
    { emoji: '🎨', name: 'Brand Agent',      model: 'Groq · Qwen 3' },
    { emoji: '🖥️', name: 'Web/UX Agent',    model: 'OpenRouter' },
    { emoji: '🧪', name: 'CRO Agent',        model: 'Groq · Qwen 3' },
    { emoji: '🔬', name: 'Research Agent',   model: 'Brave + Groq' },
    { emoji: '🧠', name: 'Deep Research',    model: 'NVIDIA Kimi K2.5' },
  ];

  const FEATURES = [
    { emoji: '🧠', title: 'Smart Routing',        desc: 'Nexus auto-picks the optimal agent and model for every task. Zero config required.' },
    { emoji: '🔄', title: '5 AI Providers',        desc: 'Groq → OpenRouter → Gemini → NVIDIA with automatic failover when rate limits hit.' },
    { emoji: '🛡️', title: 'The Skeptic',          desc: 'QA agent scores every output for accuracy, relevance, depth, and actionability before delivery.' },
    { emoji: '💾', title: 'Agent Memory',          desc: 'Persistent SQLite. Agents learn your brand voice and campaigns across every session.' },
    { emoji: '⚡', title: 'Parallel Pipelines',    desc: 'Up to 5 agents execute in parallel. Full marketing campaigns in under 10 seconds.' },
    { emoji: '🔬', title: 'Deep Research',         desc: 'Brave web search + NVIDIA Kimi K2.5 multi-step reasoning for comprehensive analysis.' },
  ];

  return (
    <div className="lp">
      {/* ── Nav ─────────────────────────────────────────── */}
      <nav className="lp-nav">
        <span className="lp-nav-logo" style={{ background: 'linear-gradient(135deg, #4F8CFF, #A78BFA)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>SwarmOps</span>
        <div className="lp-nav-links">
          <button className="lp-nav-link" onClick={() => scrollTo('how')}>How It Works</button>
          <button className="lp-nav-link" onClick={() => scrollTo('agents')}>Agents</button>
          <button className="lp-nav-link" onClick={() => scrollTo('demo')}>Demo</button>
          <button className="lp-nav-link" onClick={() => scrollTo('stack')}>Stack</button>
        </div>
        <button className="lp-nav-cta" onClick={onEnter}>Launch App →</button>
        <button className="lp-hamburger" onClick={() => setMenuOpen(!menuOpen)} aria-label="Menu">
          {menuOpen ? '✕' : '☰'}
        </button>
      </nav>

      {/* Mobile menu */}
      <div className={`lp-mobile-menu${menuOpen ? ' open' : ''}`}>
        <button className="lp-mobile-link" onClick={() => scrollTo('how')}>How It Works</button>
        <button className="lp-mobile-link" onClick={() => scrollTo('agents')}>Agents</button>
        <button className="lp-mobile-link" onClick={() => scrollTo('demo')}>Demo</button>
        <button className="lp-mobile-link" onClick={() => scrollTo('stack')}>Stack</button>
        <button className="lp-mobile-cta" onClick={onEnter}>Launch App →</button>
      </div>

      {/* ── Hero ────────────────────────────────────────── */}
      <section className="lp-hero">
        <div className="lp-hero-inner">
          <div className="lp-hero-badge">
            <span className="lp-hero-badge-dot" />
            ✨ Open Source · 11 Agents · $0/month
          </div>
          <h1 className="lp-hero-title">SwarmOps</h1>
          <p className="lp-hero-subtitle">Multi-Agent AI Marketing Intelligence</p>
          <p className="lp-hero-body">
            One command. 11 specialized agents collaborate to research, create, and execute
            complete marketing campaigns in seconds.
          </p>
          <div className="lp-hero-btns">
            <button className="lp-btn-primary" onClick={onEnter}>Launch Dashboard →</button>
            <a
              className="lp-btn-secondary"
              href="https://github.com/Bannu987/MarketingOS2.0"
              target="_blank"
              rel="noopener noreferrer"
            >
              GitHub ↗
            </a>
          </div>
          <div className="lp-hero-stats">
            <div className="lp-stat"><span className="lp-stat-num">11</span><span className="lp-stat-label">Agents</span></div>
            <div className="lp-stat"><span className="lp-stat-num">6</span><span className="lp-stat-label">APIs</span></div>
            <div className="lp-stat"><span className="lp-stat-num">5</span><span className="lp-stat-label">Models</span></div>
            <div className="lp-stat"><span className="lp-stat-num">$0</span><span className="lp-stat-label">Monthly</span></div>
          </div>
        </div>
      </section>

      {/* ── How It Works ────────────────────────────────── */}
      <section id="how" className="lp-section">
        <div ref={refHowitworks} className="lp-fade">
          <h2 className="lp-section-title">How It Works</h2>
          <p className="lp-section-sub">Three steps from instruction to executed campaign.</p>
          <div className="lp-steps">
            <div className="lp-step-card">
              <span className="lp-step-num">01</span>
              <h3 className="lp-step-title">You Speak</h3>
              <p className="lp-step-desc">Give any marketing instruction in natural language. No templates, no config, no dropdowns.</p>
            </div>
            <div className="lp-step-card">
              <span className="lp-step-num">02</span>
              <h3 className="lp-step-title">Nexus Routes</h3>
              <p className="lp-step-desc">AI orchestrator analyzes intent and builds an execution plan across agents in milliseconds.</p>
            </div>
            <div className="lp-step-card">
              <span className="lp-step-num">03</span>
              <h3 className="lp-step-title">Swarm Executes</h3>
              <p className="lp-step-desc">Agents work in parallel. The Skeptic QA agent scores every output before delivery.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Agents ──────────────────────────────────────── */}
      <section id="agents" className="lp-section">
        <div ref={refAgents} className="lp-fade">
          <h2 className="lp-section-title">11 Specialized Agents</h2>
          <p className="lp-section-sub">Each agent is tuned for its domain, with the right model, prompt, and integrations.</p>
          <div className="lp-agents-grid-wrap">
            <div className="lp-agents-grid">
              {AGENTS.map((a, i) => (
                <div key={i} className="lp-agent-cell">
                  <span className="lp-agent-emoji">{a.emoji}</span>
                  <div className="lp-agent-info">
                    <span className="lp-agent-name">{a.name}</span>
                    <span className="lp-agent-model">{a.model}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Live Demo ───────────────────────────────────── */}
      <section id="demo" className="lp-section">
        <div ref={refDemo} className="lp-fade">
          <div className="lp-demo-header">
            <h2 className="lp-section-title">Try It Live</h2>
            <div className="lp-live-badge">
              <span className="lp-live-dot" />
              LIVE
            </div>
          </div>
          <p className="lp-demo-note">Real API calls to production agents. Not mocked.</p>
          <div className="lp-demo-cards">
            <DemoCard
              label="SEO"
              prompt="Find keywords for organic dog food"
              agent="seo"
            />
            <DemoCard
              label="Content"
              prompt="Write a tagline for an AI marketing tool"
              agent="content"
            />
            <DemoCard
              label="Pipeline"
              prompt="Create a complete marketing campaign for a new coffee shop"
              agent="nexus"
            />
          </div>
        </div>
      </section>

      {/* ── Features ────────────────────────────────────── */}
      <section className="lp-section">
        <div ref={refFeatures} className="lp-fade">
          <h2 className="lp-section-title">Built Different</h2>
          <p className="lp-section-sub">Not another chatbot wrapper. A real multi-agent system with integrations.</p>
          <div className="lp-features-grid">
            {FEATURES.map((f, i) => (
              <div key={i} className="lp-feature-card">
                <span className="lp-feature-emoji">{f.emoji}</span>
                <h3 className="lp-feature-title">{f.title}</h3>
                <p className="lp-feature-desc">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Tech Stack ──────────────────────────────────── */}
      <section id="stack" className="lp-section">
        <div ref={refStack} className="lp-fade">
          <h2 className="lp-section-title">Tech Stack</h2>
          <div className="lp-stack-rows">
            <div className="lp-stack-row">
              <span className="lp-stack-cat">Core</span>
              <div className="lp-stack-pills">
                {['Python', 'FastAPI', 'React', 'SQLite', 'Zustand'].map(t => (
                  <span key={t} className="lp-stack-pill">{t}</span>
                ))}
              </div>
            </div>
            <div className="lp-stack-row">
              <span className="lp-stack-cat">AI</span>
              <div className="lp-stack-pills">
                {['Groq', 'Gemini', 'OpenRouter', 'NVIDIA NIMs', 'Brave Search', 'Serper'].map(t => (
                  <span key={t} className="lp-stack-pill">{t}</span>
                ))}
              </div>
            </div>
            <div className="lp-stack-row">
              <span className="lp-stack-cat">Integrations</span>
              <div className="lp-stack-pills">
                {['HubSpot', 'WordPress', 'Google Analytics', 'Google Ads', 'DataForSEO'].map(t => (
                  <span key={t} className="lp-stack-pill">{t}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────── */}
      <footer className="lp-footer">
        <span className="lp-footer-logo" style={{ background: 'linear-gradient(135deg, #4F8CFF, #A78BFA)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>SwarmOps</span>
        <p className="lp-footer-by">
          Built by{' '}
          <a href="https://github.com/Bannu987/MarketingOS2.0" target="_blank" rel="noopener noreferrer">
            Shravan Payyavula
          </a>
        </p>
        <p className="lp-footer-powered">Powered by Groq · Gemini · OpenRouter · NVIDIA NIMs</p>
        <p className="lp-footer-copy">© 2026 SwarmOps. Open source.</p>
      </footer>
    </div>
  );
}

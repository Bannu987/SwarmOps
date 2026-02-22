import React, { useState, useEffect, useRef } from 'react';
import './LandingPage.css';

const BACKEND_URL = 'https://marketingos20-production.up.railway.app';

const AGENTS = [
  { id: 'content',    name: 'Content Writer',    specialty: 'Blog posts, copy, long-form articles',    emoji: '✍️',  color: '#3B82F6' },
  { id: 'ads',        name: 'Ad Strategist',      specialty: 'PPC, paid media, ROI optimization',       emoji: '📊',  color: '#8B5CF6' },
  { id: 'social',     name: 'Social Media',       specialty: 'Posts, trends, community growth',         emoji: '📱',  color: '#EC4899' },
  { id: 'email',      name: 'Email Marketer',     specialty: 'Campaigns, sequences, drip flows',        emoji: '📧',  color: '#F59E0B' },
  { id: 'analytics',  name: 'Data Analyst',       specialty: 'KPI insights, dashboards, reporting',     emoji: '📈',  color: '#10B981' },
  { id: 'seo',        name: 'SEO Specialist',     specialty: 'Keywords, rankings, technical SEO',       emoji: '🔍',  color: '#06B6D4' },
  { id: 'brand',      name: 'Brand Strategist',   specialty: 'Identity, voice, market positioning',     emoji: '🎨',  color: '#F97316' },
  { id: 'competitor', name: 'Competitor Intel',   specialty: 'Market gaps, SWOT, competitive analysis', emoji: '🕵️', color: '#EF4444' },
  { id: 'abtesting',  name: 'A/B Testing',        specialty: 'Experiments, CRO, variant analysis',      emoji: '🧪',  color: '#84CC16' },
  { id: 'research',   name: 'Deep Research',      specialty: 'In-depth reports, citations, analysis',   emoji: '🔬',  color: '#A78BFA' },
  { id: 'nexus',      name: 'Nexus Router',       specialty: 'Smart multi-agent auto-routing',          emoji: '⚡',  color: '#FCD34D' },
];

const DEMO_PROMPTS = [
  { label: 'Write a viral LinkedIn post about AI in marketing', icon: '✍️' },
  { label: "Analyze top SaaS competitors' positioning strategies", icon: '🕵️' },
  { label: 'Create a 5-email B2B onboarding sequence', icon: '📧' },
];

const FEATURES = [
  { icon: '⚡', title: 'Smart Auto-Routing',      desc: 'Nexus analyzes intent and routes to the best agent + AI model automatically. Zero configuration.' },
  { icon: '🧠', title: 'Persistent Memory',       desc: 'Agents remember your brand voice, past campaigns, and preferences across every session.' },
  { icon: '🔀', title: 'Multi-Agent Pipelines',   desc: 'Chain agents together — research → write → optimize — for complex multi-step workflows.' },
  { icon: '📊', title: 'Real-time Analytics',     desc: 'Track costs, latency, confidence scores, and model usage across all agents live.' },
  { icon: '🌐', title: 'Live Web Research',        desc: 'Agents search the web, pull live data, and cite sources directly in their output.' },
  { icon: '🔒', title: 'Provider Failover',        desc: 'Auto-fallback across Claude, GPT-4o, and Gemini if any provider hits rate limits.' },
];

// ── Intersection Observer fade-in hook ─────────────────────────────────────
function useFadeIn(delay = 0) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setVisible(true); observer.disconnect(); } },
      { threshold: 0.08 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return {
    ref,
    style: { transitionDelay: `${delay}ms` },
    animClass: `lp-fade${visible ? ' lp-fade--in' : ''}`,
  };
}

// ── Main Landing Page ───────────────────────────────────────────────────────
export default function LandingPage({ onEnter }) {
  const [demoInput, setDemoInput]     = useState('');
  const [demoResult, setDemoResult]   = useState(null);
  const [demoLoading, setDemoLoading] = useState(false);
  const [demoMeta, setDemoMeta]       = useState(null);
  const [menuOpen, setMenuOpen]       = useState(false);
  const [navScrolled, setNavScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setNavScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const runDemo = async (prompt) => {
    const query = (prompt || demoInput).trim();
    if (!query) return;
    setDemoInput(query);
    setDemoLoading(true);
    setDemoResult(null);
    setDemoMeta(null);
    try {
      const res = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: query, agent: 'content', use_smart_routing: true }),
        signal: AbortSignal.timeout(25000),
      });
      const data = await res.json();
      setDemoResult(data.response || data.message || 'Task completed successfully.');
      setDemoMeta({ agent: data.agent || 'nexus', model: data.model, latency: data.latency_ms });
    } catch {
      setDemoResult('Deploy the backend to see live AI responses from all 11 agents in real time.');
      setDemoMeta({ agent: 'nexus', model: 'claude-3-5-sonnet' });
    }
    setDemoLoading(false);
  };

  // Hero fade animations
  const heroA = useFadeIn(0);
  const heroB = useFadeIn(180);

  return (
    <div className="lp">

      {/* ══════════════════════════ NAV ════════════════════════════ */}
      <nav className={`lp-nav${navScrolled ? ' lp-nav--scrolled' : ''}`}>
        <div className="lp-nav-inner">
          <div className="lp-logo">
            <div className="lp-logo-mark">⚡</div>
            <span className="lp-logo-name">SwarmOps</span>
            <span className="lp-logo-beta">BETA</span>
          </div>

          <div className={`lp-nav-links${menuOpen ? ' open' : ''}`}>
            <a href="#agents"   onClick={() => setMenuOpen(false)}>Agents</a>
            <a href="#features" onClick={() => setMenuOpen(false)}>Features</a>
            <a href="#demo"     onClick={() => setMenuOpen(false)}>Demo</a>
            <a href="#tech"     onClick={() => setMenuOpen(false)}>Stack</a>
          </div>

          <div className="lp-nav-right">
            <a
              href="https://github.com/Bannu987/MarketingOS2.0"
              target="_blank"
              rel="noopener noreferrer"
              className="lp-nav-ghost"
            >GitHub</a>
            <button className="lp-nav-cta" onClick={onEnter}>Launch App →</button>
            <button
              className={`lp-hamburger${menuOpen ? ' open' : ''}`}
              onClick={() => setMenuOpen(!menuOpen)}
              aria-label="Toggle menu"
            >
              <span /><span /><span />
            </button>
          </div>
        </div>
      </nav>

      {/* ══════════════════════════ HERO ═══════════════════════════ */}
      <section className="lp-hero">
        <div className="lp-hero-bg" aria-hidden="true">
          <div className="lp-orb lp-orb-1" />
          <div className="lp-orb lp-orb-2" />
          <div className="lp-orb lp-orb-3" />
          <div className="lp-grid-overlay" />
        </div>

        <div className="lp-hero-inner">
          {/* Copy */}
          <div ref={heroA.ref} className={`lp-hero-copy ${heroA.animClass}`} style={heroA.style}>
            <div className="lp-hero-badge">
              <span className="lp-badge-pulse" />
              11 AI Agents · Live Now
            </div>

            <h1 className="lp-hero-h1">
              The AI Agent Platform<br />
              <span className="lp-gradient-text">Built for Growth Teams</span>
            </h1>

            <p className="lp-hero-sub">
              Orchestrate 11 specialized AI agents — content, ads, SEO, email, research, and more.
              One command. Expert results. At scale.
            </p>

            <div className="lp-hero-btns">
              <button className="lp-btn-primary" onClick={onEnter}>
                Start for Free
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </button>
              <a href="#demo" className="lp-btn-ghost">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <polygon points="10 8 16 12 10 16 10 8" />
                </svg>
                Watch Demo
              </a>
            </div>

            <div className="lp-hero-stats">
              {[
                { num: '11',    label: 'AI Agents'    },
                { num: '3',     label: 'AI Providers' },
                { num: '< 3s',  label: 'Avg Response' },
                { num: '∞',     label: 'Scale'        },
              ].map((s, i) => (
                <React.Fragment key={i}>
                  {i > 0 && <div className="lp-stat-sep" />}
                  <div className="lp-hero-stat">
                    <span className="lp-hero-stat-num">{s.num}</span>
                    <span className="lp-hero-stat-label">{s.label}</span>
                  </div>
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Terminal visual */}
          <div ref={heroB.ref} className={`lp-hero-visual ${heroB.animClass}`} style={heroB.style}>
            <div className="lp-terminal">
              <div className="lp-terminal-bar">
                <span className="lp-tl lp-tl--red" />
                <span className="lp-tl lp-tl--yellow" />
                <span className="lp-tl lp-tl--green" />
                <span className="lp-terminal-title">SwarmOps Terminal</span>
              </div>
              <div className="lp-terminal-body">
                <p className="lp-tline">
                  <span className="lp-prompt">$</span>
                  <span className="lp-tcmd"> nexus "Write viral post on AI marketing"</span>
                </p>
                <p className="lp-tline lp-tdim">✓ Routing → Content Writer</p>
                <p className="lp-tline lp-tdim">✓ Model: claude-3-5-sonnet · Confidence: 97%</p>
                <p className="lp-tline lp-tdim">✓ Latency: 1.8s · Tokens: 412</p>
                <div className="lp-toutput">
                  🚀 <strong>"AI isn't coming for your marketing budget —</strong><br />
                  it already took it. Here's how top CMOs are<br />
                  turning that into their biggest competitive advantage..."
                </div>
                <span className="lp-tcursor">▋</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════════ HOW IT WORKS ═══════════════════════ */}
      <section className="lp-section lp-how" id="how">
        <div className="lp-container">
          <SectionHeader
            label="HOW IT WORKS"
            title="Three steps to AI-powered growth"
            sub="No configuration. No training data. Just describe what you need."
          />
          <StepsList />
        </div>
      </section>

      {/* ══════════════════════ AGENTS GRID ════════════════════════ */}
      <section className="lp-section lp-agents" id="agents">
        <div className="lp-container">
          <SectionHeader
            label="THE SWARM"
            title="11 Specialized AI Agents"
            sub="Each agent is purpose-built and uses the best AI model for its marketing domain."
          />
          <AgentsGrid onEnter={onEnter} />
        </div>
      </section>

      {/* ════════════════════════ LIVE DEMO ════════════════════════ */}
      <section className="lp-section lp-demo" id="demo">
        <div className="lp-container">
          <SectionHeader
            label="LIVE DEMO"
            title="Try the agents right now"
            sub="Real agents. Real AI. No account required."
          />
          <DemoBox
            demoInput={demoInput}
            setDemoInput={setDemoInput}
            demoLoading={demoLoading}
            demoResult={demoResult}
            demoMeta={demoMeta}
            runDemo={runDemo}
            onEnter={onEnter}
          />
        </div>
      </section>

      {/* ════════════════════════ FEATURES ═════════════════════════ */}
      <section className="lp-section lp-features" id="features">
        <div className="lp-container">
          <SectionHeader
            label="FEATURES"
            title="Everything you need to scale"
            sub="Built for growth teams that move fast and need reliable AI output."
          />
          <FeaturesGrid />
        </div>
      </section>

      {/* ══════════════════════ TECH STACK ═════════════════════════ */}
      <section className="lp-section lp-tech" id="tech">
        <div className="lp-container">
          <SectionHeader
            label="TECH STACK"
            title="Best-in-class infrastructure"
            sub="Modern, battle-tested tools from frontend to AI runtime."
          />
          <TechGrid />
        </div>
      </section>

      {/* ═══════════════════════════ CTA ═══════════════════════════ */}
      <section className="lp-section lp-cta-wrap">
        <div className="lp-container">
          <CtaBox onEnter={onEnter} />
        </div>
      </section>

      {/* ════════════════════════ FOOTER ═══════════════════════════ */}
      <footer className="lp-footer">
        <div className="lp-container">
          <div className="lp-footer-top">
            <div className="lp-footer-brand">
              <div className="lp-logo">
                <div className="lp-logo-mark">⚡</div>
                <span className="lp-logo-name">SwarmOps</span>
              </div>
              <p className="lp-footer-tagline">The AI agent platform for modern growth teams.</p>
            </div>
            <div className="lp-footer-cols">
              <div className="lp-footer-col">
                <span className="lp-footer-col-title">Product</span>
                <button onClick={onEnter}>Launch App</button>
                <a href="#agents">Agents</a>
                <a href="#features">Features</a>
                <a href="#demo">Live Demo</a>
              </div>
              <div className="lp-footer-col">
                <span className="lp-footer-col-title">Developers</span>
                <a href="https://github.com/Bannu987/MarketingOS2.0" target="_blank" rel="noopener noreferrer">GitHub</a>
                <a href="#tech">Tech Stack</a>
              </div>
            </div>
          </div>
          <div className="lp-footer-bottom">
            <span>© 2025 SwarmOps. Built with AI, for AI.</span>
            <span className="lp-footer-powered">Powered by Claude · GPT-4o · Gemini</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

// ── Reusable section header ─────────────────────────────────────────────────
function SectionHeader({ label, title, sub }) {
  const f = useFadeIn();
  return (
    <div ref={f.ref} className={`lp-section-hd ${f.animClass}`} style={f.style}>
      <span className="lp-section-label">{label}</span>
      <h2 className="lp-section-title">{title}</h2>
      {sub && <p className="lp-section-sub">{sub}</p>}
    </div>
  );
}

// ── Steps list ──────────────────────────────────────────────────────────────
function StepItem({ step, delay }) {
  const f = useFadeIn(delay);
  return (
    <div ref={f.ref} className={`lp-step ${f.animClass}`} style={f.style}>
      <div className="lp-step-num">{step.num}</div>
      <div className="lp-step-line" />
      <h3 className="lp-step-title">{step.title}</h3>
      <p className="lp-step-desc">{step.desc}</p>
    </div>
  );
}

function StepsList() {
  const steps = [
    { num: '01', title: 'Describe your task',          desc: 'Type in plain English. Nexus automatically picks the best agent and AI model for the job.' },
    { num: '02', title: 'Agent executes in seconds',   desc: 'Each agent uses the optimal model — Claude, GPT-4o, or Gemini — tuned for its domain.' },
    { num: '03', title: 'Get expert results instantly', desc: 'Professional-quality output in seconds. Refine, export, or chain to the next agent.' },
  ];
  return (
    <div className="lp-steps">
      {steps.map((s, i) => <StepItem key={i} step={s} delay={i * 120} />)}
    </div>
  );
}

// ── Agent card ──────────────────────────────────────────────────────────────
function AgentCard({ agent, delay, onEnter }) {
  const f = useFadeIn(delay);
  return (
    <button
      ref={f.ref}
      className={`lp-agent-card ${f.animClass}`}
      style={f.style}
      onClick={onEnter}
    >
      <div
        className="lp-agent-avatar"
        style={{ background: `${agent.color}18`, border: `1px solid ${agent.color}30` }}
      >
        {agent.emoji}
      </div>
      <div className="lp-agent-body">
        <span className="lp-agent-name">{agent.name}</span>
        <span className="lp-agent-spec">{agent.specialty}</span>
      </div>
      <span className="lp-agent-tag" style={{ color: agent.color, background: `${agent.color}12` }}>
        Active
      </span>
    </button>
  );
}

function AgentsGrid({ onEnter }) {
  return (
    <div className="lp-agents-grid">
      {AGENTS.map((agent, i) => (
        <AgentCard key={agent.id} agent={agent} delay={i * 40} onEnter={onEnter} />
      ))}
    </div>
  );
}

// ── Demo box ────────────────────────────────────────────────────────────────
function DemoBox({ demoInput, setDemoInput, demoLoading, demoResult, demoMeta, runDemo, onEnter }) {
  const f = useFadeIn(100);
  return (
    <div ref={f.ref} className={`lp-demo-box ${f.animClass}`} style={f.style}>
      {/* Bar */}
      <div className="lp-demo-bar">
        <div className="lp-tl-group">
          <span className="lp-tl lp-tl--red" />
          <span className="lp-tl lp-tl--yellow" />
          <span className="lp-tl lp-tl--green" />
        </div>
        <span className="lp-demo-bar-title">SwarmOps · Live</span>
        <span className="lp-demo-live-ind">
          <span className="lp-live-dot" />LIVE
        </span>
      </div>

      {/* Prompt chips */}
      <div className="lp-demo-chips">
        {DEMO_PROMPTS.map((p, i) => (
          <button key={i} className="lp-demo-chip" onClick={() => runDemo(p.label)}>
            <span>{p.icon}</span>{p.label}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="lp-demo-input-row">
        <input
          className="lp-demo-input"
          value={demoInput}
          onChange={(e) => setDemoInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && runDemo()}
          placeholder="Ask anything — ads, SEO, content, email, research..."
        />
        <button
          className="lp-demo-send"
          onClick={() => runDemo()}
          disabled={demoLoading || !demoInput.trim()}
          aria-label="Send"
        >
          {demoLoading
            ? <span className="lp-spin" />
            : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z" />
              </svg>
            )}
        </button>
      </div>

      {/* Thinking */}
      {demoLoading && (
        <div className="lp-demo-thinking">
          <span className="lp-thinking-dots"><span /><span /><span /></span>
          Nexus is routing your task to the best agent…
        </div>
      )}

      {/* Result */}
      {demoResult && !demoLoading && (
        <div className="lp-demo-result">
          <div className="lp-demo-result-meta">
            <span className="lp-demo-agent-pill">⚡ {demoMeta?.agent || 'SwarmOps'}</span>
            {demoMeta?.model && <span className="lp-demo-model-pill">{demoMeta.model}</span>}
            {demoMeta?.latency && <span className="lp-demo-latency">{(demoMeta.latency / 1000).toFixed(1)}s</span>}
          </div>
          <div className="lp-demo-result-text">{demoResult}</div>
          <button className="lp-demo-upgrade" onClick={onEnter}>
            Use the full app for richer results →
          </button>
        </div>
      )}
    </div>
  );
}

// ── Feature card ────────────────────────────────────────────────────────────
function FeatureCard({ feature, delay }) {
  const f = useFadeIn(delay);
  return (
    <div ref={f.ref} className={`lp-feature-card ${f.animClass}`} style={f.style}>
      <div className="lp-feature-icon">{feature.icon}</div>
      <h3 className="lp-feature-title">{feature.title}</h3>
      <p className="lp-feature-desc">{feature.desc}</p>
    </div>
  );
}

function FeaturesGrid() {
  return (
    <div className="lp-features-grid">
      {FEATURES.map((f, i) => <FeatureCard key={i} feature={f} delay={i * 70} />)}
    </div>
  );
}

// ── Tech item ───────────────────────────────────────────────────────────────
function TechItem({ item, delay }) {
  const f = useFadeIn(delay);
  return (
    <div ref={f.ref} className={`lp-tech-item ${f.animClass}`} style={f.style}>
      <span className="lp-tech-name">{item.name}</span>
      <span className="lp-tech-cat">{item.cat}</span>
    </div>
  );
}

function TechGrid() {
  const items = [
    { name: 'React 18',    cat: 'Frontend UI'    },
    { name: 'FastAPI',     cat: 'Backend API'    },
    { name: 'Claude 3.5',  cat: 'Anthropic AI'   },
    { name: 'GPT-4o',      cat: 'OpenAI'         },
    { name: 'Gemini Pro',  cat: 'Google AI'      },
    { name: 'Python 3.11', cat: 'Agent Runtime'  },
    { name: 'Railway',     cat: 'Backend Infra'  },
    { name: 'Vercel',      cat: 'Frontend CDN'   },
  ];
  return (
    <div className="lp-tech-grid">
      {items.map((t, i) => <TechItem key={i} item={t} delay={i * 50} />)}
    </div>
  );
}

// ── CTA box ─────────────────────────────────────────────────────────────────
function CtaBox({ onEnter }) {
  const f = useFadeIn();
  return (
    <div ref={f.ref} className={`lp-cta-box ${f.animClass}`} style={f.style}>
      <div className="lp-cta-glow" aria-hidden="true" />
      <span className="lp-section-label">GET STARTED</span>
      <h2 className="lp-cta-title">Ready to 10× your marketing output?</h2>
      <p className="lp-cta-sub">
        Join growth teams using SwarmOps to automate their entire marketing stack with AI.
      </p>
      <button className="lp-btn-primary lp-btn-lg" onClick={onEnter}>
        Launch SwarmOps Free →
      </button>
    </div>
  );
}

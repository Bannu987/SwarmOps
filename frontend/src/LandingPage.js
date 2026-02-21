import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const BACKEND_URL = 'https://marketingos20-production.up.railway.app';

// Animated counter hook
function useCounter(end, duration = 2000, start = 0, trigger = true) {
  const [count, setCount] = useState(start);
  useEffect(() => {
    if (!trigger) return;
    let startTime = null;
    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      setCount(Math.floor(progress * (end - start) + start));
      if (progress < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [end, duration, start, trigger]);
  return count;
}

// Intersection Observer hook for fade-in
function useFadeIn() {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) { setVisible(true); obs.unobserve(el); }
    }, { threshold: 0.15 });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return [ref, visible];
}

function Section({ children, className = '' }) {
  const [ref, visible] = useFadeIn();
  return (
    <section ref={ref} className={`lp-section ${className} ${visible ? 'lp-visible' : ''}`}>
      {children}
    </section>
  );
}

const AGENTS = [
  { emoji: '\u{1F50D}', name: 'SEO Agent', desc: 'Keywords, rankings, search strategy' },
  { emoji: '\u{270D}\u{FE0F}', name: 'Content Agent', desc: 'Blog posts, articles, copy' },
  { emoji: '\u{1F4E2}', name: 'PPC Agent', desc: 'Ad campaigns, budgets, ROAS' },
  { emoji: '\u{1F4CA}', name: 'Analytics Agent', desc: 'Traffic analysis, dashboards' },
  { emoji: '\u{1F91D}', name: 'CRM Agent', desc: 'Email sequences, lead nurturing' },
  { emoji: '\u{1F4F1}', name: 'SMM Agent', desc: 'Social media, trends, calendars' },
  { emoji: '\u{1F3A8}', name: 'Brand Agent', desc: 'Positioning, voice, identity' },
  { emoji: '\u{1F5A5}\u{FE0F}', name: 'Web/UX Agent', desc: 'Landing pages, UX audits' },
  { emoji: '\u{1F9EA}', name: 'CRO Agent', desc: 'A/B tests, conversion optimization' },
  { emoji: '\u{1F52C}', name: 'Research Agent', desc: 'Market research, competitor analysis' },
  { emoji: '\u{1F9E0}', name: 'Deep Research', desc: 'Intensive analysis with Kimi K2.5' },
];

const DEMOS = [
  { label: '\u{1F50D} Find Keywords', body: { message: 'Find SEO keywords for organic dog food', agent: 'seo' } },
  { label: '\u{270D}\u{FE0F} Write Content', body: { message: 'Write a tagline for an AI marketing tool', agent: 'content' } },
  { label: '\u{1F680} Full Campaign', body: { message: 'Create a marketing campaign for organic dog food', agent: 'nexus' } },
];

const FEATURES = [
  { emoji: '\u{1F9E0}', title: 'Smart Routing', desc: 'Nexus auto-picks the best agent for any task' },
  { emoji: '\u{1F504}', title: '5 AI Providers', desc: 'Groq, Gemini, OpenRouter, NVIDIA, Serper with auto-fallback' },
  { emoji: '\u{1F6E1}\u{FE0F}', title: 'Quality Control', desc: 'The Skeptic reviews every output with confidence scoring' },
  { emoji: '\u{1F4BE}', title: 'Agent Memory', desc: 'Agents learn from past decisions via persistent SQLite' },
  { emoji: '\u{26A1}', title: 'Parallel Pipelines', desc: 'Multi-agent workflows with serial + parallel execution' },
  { emoji: '\u{1F52C}', title: 'Deep Research', desc: 'Web search + Kimi K2.5 reasoning for market analysis' },
];

export default function LandingPage({ onLaunch }) {
  const [demoResults, setDemoResults] = useState({});
  const [demoLoading, setDemoLoading] = useState({});
  const [heroVisible, setHeroVisible] = useState(false);

  useEffect(() => { setTimeout(() => setHeroVisible(true), 100); }, []);

  const runDemo = async (idx) => {
    const demo = DEMOS[idx];
    setDemoLoading(p => ({ ...p, [idx]: true }));
    setDemoResults(p => ({ ...p, [idx]: null }));
    try {
      const res = await axios.post(`${BACKEND_URL}/api/chat`, demo.body, { timeout: 60000 });
      setDemoResults(p => ({ ...p, [idx]: res.data }));
    } catch (e) {
      setDemoResults(p => ({ ...p, [idx]: { error: true, message: 'Backend warming up, try again in a moment.' } }));
    }
    setDemoLoading(p => ({ ...p, [idx]: false }));
  };

  const agents11 = useCounter(11, 1500, 0, heroVisible);
  const apis6 = useCounter(6, 1500, 0, heroVisible);
  const models5 = useCounter(5, 1500, 0, heroVisible);

  return (
    <div className="lp-root">
      {/* Animated BG */}
      <div className="lp-bg">
        <div className="lp-orb lp-orb-1" />
        <div className="lp-orb lp-orb-2" />
        <div className="lp-orb lp-orb-3" />
      </div>

      {/* HERO */}
      <section className={`lp-section lp-hero ${heroVisible ? 'lp-visible' : ''}`}>
        <h1 className="lp-title">SwarmOps</h1>
        <p className="lp-subtitle">Multi-Agent AI Marketing Intelligence</p>
        <p className="lp-subtext">
          11 AI agents. 6 real integrations. One command.<br/>
          Complete marketing campaigns in under 10 seconds.
        </p>
        <button className="lp-cta" onClick={onLaunch}>
          Launch Dashboard <span className="lp-arrow">&rarr;</span>
        </button>
        <div className="lp-stats">
          <div className="lp-stat"><span className="lp-stat-num">{agents11}</span><span className="lp-stat-label">Agents</span></div>
          <div className="lp-stat"><span className="lp-stat-num">{apis6}</span><span className="lp-stat-label">APIs</span></div>
          <div className="lp-stat"><span className="lp-stat-num">{models5}</span><span className="lp-stat-label">AI Models</span></div>
          <div className="lp-stat"><span className="lp-stat-num">$0</span><span className="lp-stat-label">/month</span></div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <Section>
        <h2 className="lp-h2">How It Works</h2>
        <div className="lp-steps">
          <div className="lp-step">
            <div className="lp-step-icon">{'\u{1F4AC}'}</div>
            <h3>You Speak</h3>
            <p>Give a natural language instruction</p>
          </div>
          <div className="lp-step-line" />
          <div className="lp-step">
            <div className="lp-step-icon">{'\u{1F9E0}'}</div>
            <h3>Nexus Routes</h3>
            <p>AI brain classifies and routes to the right agents</p>
          </div>
          <div className="lp-step-line" />
          <div className="lp-step">
            <div className="lp-step-icon">{'\u{26A1}'}</div>
            <h3>Swarm Executes</h3>
            <p>Agents work in parallel, Skeptic reviews quality</p>
          </div>
        </div>
      </Section>

      {/* AGENTS */}
      <Section>
        <h2 className="lp-h2">11 Specialized AI Agents</h2>
        <div className="lp-agents-grid">
          {AGENTS.map((a, i) => (
            <div key={i} className="lp-agent-card">
              <span className="lp-agent-emoji">{a.emoji}</span>
              <h3>{a.name}</h3>
              <p>{a.desc}</p>
            </div>
          ))}
        </div>
      </Section>

      {/* LIVE DEMO */}
      <Section>
        <h2 className="lp-h2">Try It Live</h2>
        <div className="lp-demo-buttons">
          {DEMOS.map((d, i) => (
            <button key={i} className="lp-demo-btn" onClick={() => runDemo(i)} disabled={demoLoading[i]}>
              {demoLoading[i] ? '\u{26A1} Agents working...' : d.label}
            </button>
          ))}
        </div>
        {Object.keys(demoResults).map(idx => {
          const r = demoResults[idx];
          if (!r) return null;
          return (
            <div key={idx} className="lp-demo-result">
              {r.error ? (
                <p className="lp-demo-error">{r.message}</p>
              ) : (
                <>
                  <pre className="lp-demo-text">{typeof r.result === 'string' ? r.result : JSON.stringify(r.result, null, 2)}</pre>
                  <div className="lp-demo-badges">
                    {r.model && <span className="lp-badge lp-badge-blue">{r.model}</span>}
                    {r.provider && <span className="lp-badge lp-badge-purple">{r.provider}</span>}
                    {r.latency_ms > 0 && <span className="lp-badge lp-badge-green">{r.latency_ms}ms</span>}
                    {r.quality && <span className="lp-badge lp-badge-yellow">{Math.round(r.quality.confidence * 100)}% confidence</span>}
                  </div>
                </>
              )}
            </div>
          );
        })}
      </Section>

      {/* TECH STACK */}
      <Section>
        <h2 className="lp-h2">Built With</h2>
        <div className="lp-tech-rows">
          <div className="lp-tech-row">
            <span className="lp-tech lp-tech-core">Python</span>
            <span className="lp-tech lp-tech-core">FastAPI</span>
            <span className="lp-tech lp-tech-core">React</span>
            <span className="lp-tech lp-tech-core">SQLite</span>
          </div>
          <div className="lp-tech-row">
            <span className="lp-tech lp-tech-ai">Groq</span>
            <span className="lp-tech lp-tech-ai">Gemini</span>
            <span className="lp-tech lp-tech-ai">OpenRouter</span>
            <span className="lp-tech lp-tech-ai">NVIDIA NIMs</span>
            <span className="lp-tech lp-tech-ai">Brave</span>
            <span className="lp-tech lp-tech-ai">Serper</span>
          </div>
          <div className="lp-tech-row">
            <span className="lp-tech lp-tech-int">HubSpot</span>
            <span className="lp-tech lp-tech-int">WordPress</span>
            <span className="lp-tech lp-tech-int">Google Analytics</span>
            <span className="lp-tech lp-tech-int">Google Ads</span>
            <span className="lp-tech lp-tech-int">DataForSEO</span>
          </div>
        </div>
      </Section>

      {/* FEATURES */}
      <Section>
        <h2 className="lp-h2">Features</h2>
        <div className="lp-features-grid">
          {FEATURES.map((f, i) => (
            <div key={i} className="lp-feature-card">
              <span className="lp-feature-emoji">{f.emoji}</span>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </Section>

      {/* ARCHITECTURE */}
      <Section>
        <h2 className="lp-h2">System Architecture</h2>
        <div className="lp-arch">
          <div className="lp-arch-row">
            <div className="lp-arch-box">
              <strong>User</strong>
              <span>Natural language input</span>
            </div>
            <div className="lp-arch-arrow">&rarr;</div>
            <div className="lp-arch-box lp-arch-highlight">
              <strong>Nexus</strong>
              <span>Smart router + orchestrator</span>
            </div>
            <div className="lp-arch-arrow">&rarr;</div>
            <div className="lp-arch-box">
              <strong>Model Router</strong>
              <span>5 providers with fallback</span>
            </div>
          </div>
          <div className="lp-arch-down">&darr;</div>
          <div className="lp-arch-row">
            <div className="lp-arch-box">
              <strong>11 Agents</strong>
              <span>Specialized AI workers</span>
            </div>
            <div className="lp-arch-arrow">&rarr;</div>
            <div className="lp-arch-box lp-arch-highlight">
              <strong>The Skeptic</strong>
              <span>Quality control layer</span>
            </div>
            <div className="lp-arch-arrow">&rarr;</div>
            <div className="lp-arch-box">
              <strong>Memory</strong>
              <span>Persistent SQLite store</span>
            </div>
            <div className="lp-arch-arrow">&rarr;</div>
            <div className="lp-arch-box">
              <strong>Response</strong>
              <span>Reviewed + enriched output</span>
            </div>
          </div>
        </div>
      </Section>

      {/* FOOTER */}
      <footer className="lp-footer">
        <p>Built by <strong>Shravan</strong></p>
        <a href="https://github.com/Bannu987/MarketingOS2.0" target="_blank" rel="noopener noreferrer">GitHub</a>
        <p className="lp-footer-tech">Powered by Groq &bull; Gemini &bull; OpenRouter &bull; NVIDIA NIMs &bull; Brave &bull; Serper</p>
        <p className="lp-footer-copy">&copy; 2026 SwarmOps</p>
      </footer>
    </div>
  );
}

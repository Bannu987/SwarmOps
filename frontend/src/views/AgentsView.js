import React from 'react';

const AGENTS = [
  { id: 'nexus', name: 'Nexus', role: 'CMO Orchestrator', color: '#6366f1', icon: '◉' },
  { id: 'seo', name: 'SEO', role: 'Search Optimization', color: '#22d3ee', icon: '◎' },
  { id: 'content', name: 'Content', role: 'Content Strategy', color: '#a855f7', icon: '✦' },
  { id: 'ppc', name: 'PPC', role: 'Paid Advertising', color: '#f97316', icon: '◇' },
  { id: 'analytics', name: 'Analytics', role: 'Data & Metrics', color: '#10b981', icon: '◉' },
  { id: 'crm', name: 'CRM', role: 'Email & Lifecycle', color: '#3b82f6', icon: '◐' },
  { id: 'smm', name: 'Social', role: 'Social Media', color: '#ec4899', icon: '◌' },
  { id: 'brand', name: 'Brand', role: 'Brand Identity', color: '#ef4444', icon: '◆' },
  { id: 'cro', name: 'CRO', role: 'Conversion Opt.', color: '#22c55e', icon: '◑' },
  { id: 'web_ux', name: 'Web/UX', role: 'UX & Design', color: '#06b6d4', icon: '◊' },
  { id: 'research', name: 'Research', role: 'Market Research', color: '#84cc16', icon: '◯' },
  { id: 'aeo', name: 'AEO', role: 'AI Search Opt.', color: '#fbbf24', icon: '◯' },
];

export default function AgentsView() {
  return (
    <div className="flex-1 overflow-y-auto px-8 py-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-text-primary mb-1">Agent Network</h1>
          <p className="text-sm text-text-secondary">12 specialized agents orchestrated by Nexus CMO</p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {AGENTS.map((agent) => (
            <div
              key={agent.id}
              className="bg-bg-secondary border border-border rounded-xl p-5 hover:border-border-hover transition-all hover:scale-[1.02] cursor-pointer group"
              style={{
                background: `linear-gradient(180deg, ${agent.color}08 0%, transparent 100%)`,
              }}
            >
              <div className="flex items-start justify-between mb-3">
                <div
                  className="w-9 h-9 rounded-lg flex items-center justify-center text-white text-lg font-bold transition-transform group-hover:scale-110"
                  style={{ background: `linear-gradient(135deg, ${agent.color}, ${agent.color}99)` }}
                >
                  {agent.icon}
                </div>
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
              </div>
              <h3 className="text-text-primary font-semibold mb-0.5">{agent.name}</h3>
              <p className="text-xs text-text-secondary mb-3">{agent.role}</p>
              <div className="text-[11px] text-text-muted">
                <span className="text-green-400">●</span> Idle · Ready
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

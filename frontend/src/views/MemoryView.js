import React, { useState } from 'react';

const TABS = [
  { id: 'brand', label: 'Brand DNA', icon: '◆' },
  { id: 'competitive', label: 'Competitive Intel', icon: '◉' },
  { id: 'conversation', label: 'Conversation', icon: '◎' },
  { id: 'data', label: 'Data Memory', icon: '▤' },
  { id: 'learning', label: 'Learning', icon: '◯' },
];

const BRAND_FIELDS = [
  { key: 'name', label: 'Brand Name', placeholder: 'e.g. Acme Corp' },
  { key: 'industry', label: 'Industry', placeholder: 'e.g. B2B SaaS' },
  { key: 'website', label: 'Website URL', placeholder: 'https://yoursite.com' },
  { key: 'audience', label: 'Target Audience', placeholder: 'e.g. Marketing leaders at Series A startups' },
  { key: 'value_prop', label: 'Value Proposition', placeholder: 'What makes you uniquely different?' },
  { key: 'tone', label: 'Tone of Voice', placeholder: 'e.g. Professional, direct, data-driven' },
];

export default function MemoryView() {
  const [activeTab, setActiveTab] = useState('brand');
  const [brandData, setBrandData] = useState({});

  return (
    <div className="flex-1 overflow-y-auto px-8 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-text-primary mb-1">Memory System</h1>
          <p className="text-sm text-text-secondary">Layered context powering every agent decision</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-border overflow-x-auto">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition whitespace-nowrap ${
                activeTab === tab.id
                  ? 'text-accent border-accent'
                  : 'text-text-secondary border-transparent hover:text-text-primary'
              }`}
            >
              <span className="mr-1.5">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Brand DNA tab */}
        {activeTab === 'brand' && (
          <div className="space-y-4">
            <p className="text-sm text-text-secondary">Core brand identity & positioning</p>
            {BRAND_FIELDS.map((field) => (
              <div key={field.key} className="bg-bg-secondary border border-border rounded-lg p-4">
                <label className="block text-xs font-medium text-text-muted uppercase tracking-wider mb-2">
                  {field.label}
                </label>
                <input
                  type="text"
                  value={brandData[field.key] || ''}
                  onChange={(e) =>
                    setBrandData((prev) => ({ ...prev, [field.key]: e.target.value }))
                  }
                  placeholder={field.placeholder}
                  className="w-full bg-transparent text-text-primary placeholder-text-muted text-sm outline-none"
                />
              </div>
            ))}
          </div>
        )}

        {/* Placeholder for other tabs */}
        {activeTab !== 'brand' && (
          <div className="bg-bg-secondary border border-border rounded-xl p-12 text-center text-text-muted">
            <div className="text-4xl mb-3">{TABS.find((t) => t.id === activeTab)?.icon}</div>
            <p className="text-sm">{TABS.find((t) => t.id === activeTab)?.label} coming in Phase D</p>
          </div>
        )}
      </div>
    </div>
  );
}

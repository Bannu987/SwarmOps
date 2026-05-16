import React, { useState } from 'react';

const API_URL = process.env.REACT_APP_API_URL || 'https://marketingos2-0.onrender.com';

const SOURCES = [
  {
    id: 'ga4',
    name: 'Google Analytics 4',
    desc: 'Traffic, conversions, user behavior',
    icon: '◉',
    color: '#f59e0b',
    fields: [
      { key: 'property_id', label: 'GA4 Property ID', placeholder: '123456789' },
      {
        key: 'credentials_json',
        label: 'Service Account JSON',
        placeholder: 'Paste your service account JSON',
        textarea: true,
      },
    ],
  },
  {
    id: 'gsc',
    name: 'Search Console',
    desc: 'Keyword rankings, impressions, CTR',
    icon: '◎',
    color: '#06b6d4',
    fields: [
      { key: 'site_url', label: 'Site URL', placeholder: 'https://yoursite.com' },
      {
        key: 'credentials_json',
        label: 'Service Account JSON',
        placeholder: 'Paste your service account JSON',
        textarea: true,
      },
    ],
  },
  {
    id: 'hubspot',
    name: 'HubSpot CRM',
    desc: 'Contacts, leads, deal pipeline',
    icon: '◐',
    color: '#f97316',
    fields: [
      { key: 'api_key', label: 'HubSpot Private App Token', placeholder: 'pat-na1-...' },
    ],
  },
  {
    id: 'google_ads',
    name: 'Google Ads',
    desc: 'Campaign spend, ROAS, conversions',
    icon: '◇',
    color: '#22c55e',
    fields: [
      {
        key: 'developer_token',
        label: 'Developer Token',
        placeholder: 'Developer token from Google Ads',
      },
      { key: 'customer_id', label: 'Customer ID', placeholder: '123-456-7890' },
    ],
  },
];

export default function DataSourcesView() {
  const [openModal, setOpenModal] = useState(null);
  const [credentials, setCredentials] = useState({});
  const [status, setStatus] = useState({});
  const [saving, setSaving] = useState(false);

  const handleConnect = async (sourceId) => {
    setSaving(true);
    try {
      const res = await fetch(`${API_URL}/api/credentials/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ service: sourceId, credentials: credentials[sourceId] || {} }),
      });
      const data = await res.json();
      if (data.success) {
        setStatus((prev) => ({ ...prev, [sourceId]: 'connected' }));
        setOpenModal(null);
      } else {
        alert(`Failed: ${data.error}`);
      }
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const updateField = (sourceId, key, value) => {
    setCredentials((prev) => ({
      ...prev,
      [sourceId]: { ...(prev[sourceId] || {}), [key]: value },
    }));
  };

  const activeSource = SOURCES.find((s) => s.id === openModal);

  return (
    <div className="flex-1 overflow-y-auto px-8 py-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-text-primary mb-1">Data Sources</h1>
          <p className="text-sm text-text-secondary">
            Connect your marketing stack for real-data analysis
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {SOURCES.map((source) => {
            const isConnected = status[source.id] === 'connected';
            return (
              <div
                key={source.id}
                className="bg-bg-secondary border border-border rounded-xl p-5 transition hover:border-border-hover"
              >
                <div className="flex items-start justify-between mb-3">
                  <div
                    className="w-9 h-9 rounded-lg flex items-center justify-center text-white text-lg"
                    style={{
                      background: `linear-gradient(135deg, ${source.color}, ${source.color}99)`,
                    }}
                  >
                    {source.icon}
                  </div>
                  <span
                    className={`px-2 py-0.5 text-[10px] font-medium rounded uppercase tracking-wider ${
                      isConnected
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-bg-tertiary text-text-muted'
                    }`}
                  >
                    {isConnected ? '● Connected' : '○ Not connected'}
                  </span>
                </div>
                <h3 className="text-text-primary font-semibold mb-1">{source.name}</h3>
                <p className="text-xs text-text-secondary mb-4">{source.desc}</p>
                <button
                  onClick={() => setOpenModal(source.id)}
                  className={`w-full py-2 text-sm font-medium rounded-lg transition ${
                    isConnected
                      ? 'bg-bg-tertiary text-text-secondary hover:bg-bg-hover'
                      : 'bg-accent hover:bg-accent-hover text-white'
                  }`}
                >
                  {isConnected ? 'Reconfigure' : 'Connect'}
                </button>
              </div>
            );
          })}
        </div>

        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 flex items-start gap-3">
          <span className="text-amber-400">◯</span>
          <div className="text-sm text-amber-200">
            Without connected sources, SwarmOps uses industry benchmarks. Connect GA4 for real
            traffic data and personalized recommendations.
          </div>
        </div>
      </div>

      {/* Connect Modal */}
      {openModal && activeSource && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-bg-secondary border border-border rounded-2xl max-w-lg w-full p-6 animate-slide-up">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">
                Connect {activeSource.name}
              </h3>
              <button
                onClick={() => setOpenModal(null)}
                className="text-text-muted hover:text-text-primary"
              >
                ✕
              </button>
            </div>
            <p className="text-sm text-text-secondary mb-5">{activeSource.desc}</p>
            <div className="space-y-3 mb-5">
              {activeSource.fields.map((field) => (
                <div key={field.key}>
                  <label className="block text-xs font-medium text-text-secondary mb-1.5">
                    {field.label}
                  </label>
                  {field.textarea ? (
                    <textarea
                      value={(credentials[activeSource.id] || {})[field.key] || ''}
                      onChange={(e) => updateField(activeSource.id, field.key, e.target.value)}
                      placeholder={field.placeholder}
                      rows={4}
                      className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary text-sm font-mono outline-none focus:border-accent"
                    />
                  ) : (
                    <input
                      type="text"
                      value={(credentials[activeSource.id] || {})[field.key] || ''}
                      onChange={(e) => updateField(activeSource.id, field.key, e.target.value)}
                      placeholder={field.placeholder}
                      className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary text-sm outline-none focus:border-accent"
                    />
                  )}
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleConnect(activeSource.id)}
                disabled={saving}
                className="flex-1 py-2 bg-accent hover:bg-accent-hover text-white text-sm font-medium rounded-lg transition disabled:opacity-50"
              >
                {saving ? 'Connecting...' : 'Connect'}
              </button>
              <button
                onClick={() => setOpenModal(null)}
                className="px-4 py-2 bg-bg-tertiary text-text-secondary text-sm rounded-lg hover:bg-bg-hover transition"
              >
                Cancel
              </button>
            </div>
            <p className="mt-4 text-xs text-text-muted">
              🔒 Credentials are encrypted and stored per-user. Only you can see your data.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

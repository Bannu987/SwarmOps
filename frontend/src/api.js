import axios from 'axios';

const API_BASE = 'https://marketingos20-production.up.railway.app';

// Intercept HTML responses (Vercel SPA fallback when URL is wrong)
axios.interceptors.response.use(
  response => {
    if (typeof response.data === 'string' && response.data.startsWith('<!')) {
      return Promise.reject(new Error('Received HTML instead of JSON — wrong URL'));
    }
    return response;
  },
  error => Promise.reject(error)
);

export const api = {
  // Main chat — ALL agents use this single endpoint
  chat: async (message, agent) => {
    const response = await axios.post(`${API_BASE}/api/chat`, {
      message,
      agent
    }, {
      timeout: 300000,
      headers: { 'Content-Type': 'application/json' }
    });
    return response.data;
  },

  // Deep research — separate endpoint
  deepResearch: async (topic) => {
    const response = await axios.post(`${API_BASE}/api/deep-research`, {
      topic
    }, {
      timeout: 300000,
      headers: { 'Content-Type': 'application/json' }
    });
    return response.data;
  },

  // Health check
  health: async () => {
    const response = await axios.get(`${API_BASE}/health`);
    return response.data;
  },

  // Stats
  stats: async () => {
    const response = await axios.get(`${API_BASE}/api/stats`);
    return response.data;
  },

  // History
  history: async (filters = {}) => {
    const response = await axios.get(`${API_BASE}/api/history`, { params: filters });
    return response.data;
  },

  // Memory
  getMemory: async (department) => {
    const response = await axios.get(`${API_BASE}/api/memory/${department}`);
    return response.data;
  },

  // Backend has DELETE /api/memory (no department param)
  clearMemory: async () => {
    const response = await axios.delete(`${API_BASE}/api/memory`);
    return response.data;
  },

  // Rate limits
  rateLimits: async () => {
    const response = await axios.get(`${API_BASE}/api/rate-limits`);
    return response.data;
  },

  // Providers
  testProviders: async () => {
    const response = await axios.get(`${API_BASE}/api/test-providers`);
    return response.data;
  },

  // Business profile
  getProfile: async () => {
    const response = await axios.get(`${API_BASE}/api/business-profile`);
    return response.data;
  },

  saveProfile: async (data) => {
    const response = await axios.post(`${API_BASE}/api/business-profile`, data, {
      headers: { 'Content-Type': 'application/json' }
    });
    return response.data;
  },

  // Integrations status
  integrations: async () => {
    const response = await axios.get(`${API_BASE}/api/integrations/status`);
    return response.data;
  },

  // Insights
  insights: async (department) => {
    const response = await axios.get(`${API_BASE}/api/insights/${department}`);
    return response.data;
  },

  // Memory export/import
  exportMemory: async () => {
    const response = await axios.post(`${API_BASE}/api/memory/export`);
    return response.data;
  },

  importMemory: async (data) => {
    const response = await axios.post(`${API_BASE}/api/memory/import`, data, {
      headers: { 'Content-Type': 'application/json' }
    });
    return response.data;
  },

  // Feedback loop
  feedbackLoop: async (payload) => {
    const response = await axios.post(`${API_BASE}/api/feedback-loop`, payload, {
      headers: { 'Content-Type': 'application/json' }
    });
    return response.data;
  },

  // Competitive Intelligence
  competitors: {
    list: async () => {
      const r = await axios.get(`${API_BASE}/api/competitors`);
      return r.data;
    },
    add: async (name, url) => {
      const r = await axios.post(`${API_BASE}/api/competitors`, { name, url }, {
        headers: { 'Content-Type': 'application/json' },
        timeout: 90000
      });
      return r.data;
    },
    remove: async (id) => {
      const r = await axios.delete(`${API_BASE}/api/competitors/${id}`);
      return r.data;
    },
    analyze: async (id) => {
      const r = await axios.post(`${API_BASE}/api/competitors/${id}/analyze`, {}, {
        timeout: 90000
      });
      return r.data;
    },
    compare: async () => {
      const r = await axios.get(`${API_BASE}/api/competitors/compare`, {
        timeout: 90000
      });
      return r.data;
    },
    alerts: async () => {
      const r = await axios.get(`${API_BASE}/api/competitors/alerts`);
      return r.data;
    },
    acknowledgeAlert: async (id) => {
      const r = await axios.post(`${API_BASE}/api/competitors/alerts/${id}/acknowledge`);
      return r.data;
    },
    battleCard: async (id) => {
      const r = await axios.get(`${API_BASE}/api/competitors/${id}/battle-card`, {
        timeout: 90000
      });
      return r.data;
    },
    snapshots: async (id) => {
      const r = await axios.get(`${API_BASE}/api/competitors/${id}/snapshots`);
      return r.data;
    }
  },

  // Brand DNA
  brandDna: {
    get: async () => {
      const r = await axios.get(`${API_BASE}/api/brand-dna`);
      return r.data;
    },
    extract: async (url) => {
      const r = await axios.post(`${API_BASE}/api/brand-dna/extract`, { url }, {
        timeout: 60000,
        headers: { 'Content-Type': 'application/json' }
      });
      return r.data;
    },
    update: async (data) => {
      const r = await axios.put(`${API_BASE}/api/brand-dna`, data, {
        headers: { 'Content-Type': 'application/json' }
      });
      return r.data;
    }
  },

  // Learning Engine
  learning: {
    preferences: async () => {
      const r = await axios.get(`${API_BASE}/api/learning/preferences`);
      return r.data;
    },
    insights: async (agent) => {
      const r = await axios.get(`${API_BASE}/api/learning/insights/${agent}`);
      return r.data;
    },
    feedback: async (agent, query, quality, notes) => {
      const r = await axios.post(`${API_BASE}/api/learning/feedback`, {
        agent, query, response_quality: quality, notes
      }, { headers: { 'Content-Type': 'application/json' } });
      return r.data;
    },
    reset: async () => {
      const r = await axios.delete(`${API_BASE}/api/learning/reset`);
      return r.data;
    }
  },

  // Revenue Tracker
  recommendations: {
    list: async (agent) => {
      const url = agent
        ? `${API_BASE}/api/recommendations/${agent}`
        : `${API_BASE}/api/recommendations`;
      const r = await axios.get(url);
      return r.data;
    },
    recordOutcome: async (id, actualImpact) => {
      const r = await axios.post(`${API_BASE}/api/recommendations/${id}/outcome`, {
        actual_impact: actualImpact
      }, { headers: { 'Content-Type': 'application/json' } });
      return r.data;
    },
    performance: async () => {
      const r = await axios.get(`${API_BASE}/api/agent-performance`);
      return r.data;
    }
  },

  // Database
  database: {
    export: async () => {
      const r = await axios.post(`${API_BASE}/api/database/export`);
      return r.data;
    },
    import: async (data) => {
      const r = await axios.post(`${API_BASE}/api/database/import`, data, {
        headers: { 'Content-Type': 'application/json' }
      });
      return r.data;
    }
  }
};

export default api;

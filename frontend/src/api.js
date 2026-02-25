import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

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
      timeout: 60000,
      headers: { 'Content-Type': 'application/json' }
    });
    return response.data;
  },

  // Deep research — separate endpoint
  deepResearch: async (topic) => {
    const response = await axios.post(`${API_BASE}/api/deep-research`, {
      topic
    }, {
      timeout: 120000,
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
  }
};

export default api;

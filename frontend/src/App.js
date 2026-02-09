import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { useChatStore } from './stores/chatStore';
import { 
  Send, Paperclip, Mic, Plus, Sparkles, Copy, Share2,
  ThumbsUp, ThumbsDown, RotateCcw, Loader2, Moon, Sun,
  Bell, User, Search, ChevronDown, X, Settings, BarChart3,
  Lightbulb, Cpu, HardDrive, Activity, AlertCircle, Users,
  TrendingUp, TrendingDown, Eye, MousePointer, Target, Zap,
  PenTool, DollarSign, Palette, Globe, Layout as LayoutIcon,
  ArrowRight, Check, Clock, Filter,
  Maximize2, Minimize2, RefreshCw, ExternalLink,
  AtSign, Smile, CheckCircle2, Info,
  Layers, Bookmark, Volume2
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  Cell
} from 'recharts';
import './App.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Agent configurations - 10 agents with real integration endpoints
const AGENTS = [
  {
    id: 'content',
    name: 'Content Agent',
    shortName: 'Content',
    icon: PenTool,
    iconEmoji: '✍️',
    description: 'Creates and publishes content to WordPress',
    capabilities: ['Blog Posts', 'Auto-Publish', 'SEO Content', 'Social Media'],
    model: 'Llama 3.3 70B',
    provider: 'Groq',
    color: '#818CF8',
    gradientFrom: '#6366F1',
    gradientTo: '#8B5CF6',
    bgColor: 'rgba(99, 102, 241, 0.15)',
    endpoint: '/api/content/generate',
    integration: 'wordpress',
    tasks: 47,
    successRate: 98.5,
    avgResponseTime: '1.2s',
    status: 'online'
  },
  {
    id: 'ppc',
    name: 'PPC Agent',
    shortName: 'PPC',
    icon: DollarSign,
    iconEmoji: '💰',
    description: 'Creates real Google Ads campaigns',
    capabilities: ['Google Ads', 'Campaign Creation', 'Budget Optimization', 'Auto-Optimize'],
    model: 'Gemini 1.5 Flash',
    provider: 'Google',
    color: '#FBBF24',
    gradientFrom: '#F59E0B',
    gradientTo: '#FBBF24',
    bgColor: 'rgba(251, 191, 36, 0.15)',
    endpoint: '/api/ppc/campaigns',
    integration: 'google_ads',
    tasks: 23,
    successRate: 96.2,
    avgResponseTime: '0.8s',
    status: 'online'
  },
  {
    id: 'brand',
    name: 'Brand Strategist',
    shortName: 'Brand',
    icon: Palette,
    iconEmoji: '🎨',
    description: 'Develops brand identity and positioning',
    capabilities: ['Brand Voice', 'Positioning', 'Visual Identity', 'Guidelines'],
    model: 'Llama 3.3 70B',
    provider: 'Groq',
    color: '#C084FC',
    gradientFrom: '#A855F7',
    gradientTo: '#C084FC',
    bgColor: 'rgba(168, 85, 247, 0.15)',
    endpoint: '/api/brand/strategy',
    tasks: 8,
    successRate: 99.1,
    avgResponseTime: '1.5s',
    status: 'online'
  },
  {
    id: 'research',
    name: 'Research Agent',
    shortName: 'Research',
    icon: Search,
    iconEmoji: '🔍',
    description: 'Web research with Brave Search',
    capabilities: ['Market Analysis', 'Competitor Research', 'Trend Reports', 'Insights'],
    model: 'Gemini 1.5 Pro',
    provider: 'Google',
    color: '#22D3EE',
    gradientFrom: '#06B6D4',
    gradientTo: '#22D3EE',
    bgColor: 'rgba(6, 182, 212, 0.15)',
    endpoint: '/api/research/topic',
    tasks: 156,
    successRate: 97.8,
    avgResponseTime: '2.1s',
    status: 'online'
  },
  {
    id: 'crm',
    name: 'CRM Agent',
    shortName: 'CRM',
    icon: Users,
    iconEmoji: '📧',
    description: 'HubSpot CRM integration for contacts & emails',
    capabilities: ['HubSpot Contacts', 'Email Sequences', 'Lead Scoring', 'Automation'],
    model: 'Llama 3.3 70B',
    provider: 'Groq',
    color: '#34D399',
    gradientFrom: '#10B981',
    gradientTo: '#34D399',
    bgColor: 'rgba(16, 185, 129, 0.15)',
    endpoint: '/api/crm/email-sequence',
    integration: 'hubspot',
    tasks: 89,
    successRate: 98.9,
    avgResponseTime: '1.0s',
    status: 'online'
  },
  {
    id: 'webux',
    name: 'Web/UX Agent',
    shortName: 'Web/UX',
    icon: Globe,
    iconEmoji: '🌐',
    description: 'Designs and optimizes user experiences',
    capabilities: ['Landing Pages', 'User Flows', 'Wireframes', 'UX Audit'],
    model: 'Qwen 3 32B',
    provider: 'Groq',
    color: '#F472B6',
    gradientFrom: '#EC4899',
    gradientTo: '#F472B6',
    bgColor: 'rgba(236, 72, 153, 0.15)',
    endpoint: '/api/webux/landing-page',
    tasks: 15,
    successRate: 97.5,
    avgResponseTime: '1.8s',
    status: 'online'
  },
  {
    id: 'seo',
    name: 'SEO Agent',
    shortName: 'SEO',
    icon: TrendingUp,
    iconEmoji: '📊',
    description: 'Real rankings from Search Console + DataForSEO',
    capabilities: ['Real Rankings', 'Keyword Data', 'Opportunities', 'SERP Analysis'],
    model: 'Gemini 1.5 Pro',
    provider: 'Google',
    color: '#2DD4BF',
    gradientFrom: '#14B8A6',
    gradientTo: '#2DD4BF',
    bgColor: 'rgba(20, 184, 166, 0.15)',
    endpoint: '/api/seo/rankings',
    integration: 'search_console',
    tasks: 234,
    successRate: 96.8,
    avgResponseTime: '1.4s',
    status: 'online'
  },
  {
    id: 'analytics',
    name: 'Analytics Agent',
    shortName: 'Analytics',
    icon: BarChart3,
    iconEmoji: '📈',
    description: 'Live GA4 data + anomaly detection',
    capabilities: ['GA4 Dashboard', 'Anomaly Detection', 'Live Traffic', 'Conversions'],
    model: 'Gemini 1.5 Pro',
    provider: 'Google',
    color: '#FB923C',
    gradientFrom: '#F97316',
    gradientTo: '#FB923C',
    bgColor: 'rgba(249, 115, 22, 0.15)',
    endpoint: '/api/analytics/dashboard',
    integration: 'ga4',
    tasks: 500,
    successRate: 99.2,
    avgResponseTime: '0.9s',
    status: 'online'
  },
  {
    id: 'cro',
    name: 'CRO Agent',
    shortName: 'CRO',
    icon: Zap,
    iconEmoji: '⚡',
    description: 'Conversion optimization triggered by feedback loop',
    capabilities: ['Funnel Analysis', 'A/B Testing', 'Friction Points', 'Auto-Trigger'],
    model: 'Qwen 3 32B',
    provider: 'Groq',
    color: '#A78BFA',
    gradientFrom: '#8B5CF6',
    gradientTo: '#A78BFA',
    bgColor: 'rgba(139, 92, 246, 0.15)',
    endpoint: '/api/cro/analyze-funnel',
    tasks: 67,
    successRate: 97.3,
    avgResponseTime: '1.6s',
    status: 'online'
  },
  {
    id: 'smm',
    name: 'SMM Agent',
    shortName: 'Social',
    icon: Share2,
    iconEmoji: '📱',
    description: 'Social media calendar, trends, viral hooks',
    capabilities: ['Content Calendar', 'Trend Analysis', 'Platform Posts', 'Viral Hooks'],
    model: 'Llama 3.3 70B',
    provider: 'Groq',
    color: '#E879F9',
    gradientFrom: '#D946EF',
    gradientTo: '#E879F9',
    bgColor: 'rgba(217, 70, 239, 0.15)',
    endpoint: '/api/smm/post',
    tasks: 34,
    successRate: 97.8,
    avgResponseTime: '1.3s',
    status: 'online'
  }
];

// Mock data for charts
const trafficData = [
  { day: 'Mon', organic: 4000, paid: 2400, social: 2400 },
  { day: 'Tue', organic: 3000, paid: 1398, social: 2210 },
  { day: 'Wed', organic: 12000, paid: 9800, social: 2290 },
  { day: 'Thu', organic: 6000, paid: 3908, social: 2000 },
  { day: 'Fri', organic: 8900, paid: 4800, social: 2181 },
  { day: 'Sat', organic: 9500, paid: 3800, social: 2500 },
  { day: 'Sun', organic: 10300, paid: 4300, social: 2100 }
];

const conversionData = [
  { page: 'Homepage', conversions: 4.2 },
  { page: 'Pricing', conversions: 7.8 },
  { page: 'Blog', conversions: 2.1 },
  { page: 'Demo', conversions: 12.5 },
  { page: 'Contact', conversions: 8.9 }
];

// Main App Component
function App() {
  const {
    messages,
    selectedAgentId,
    isStreaming,
    rightPanelOpen,
    addMessage,
    setSelectedAgent,
    setStreaming,
    toggleRightPanel,
    setRightPanelOpen,
    clearMessages
  } = useChatStore();

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('marketingos-darkmode');
    return saved !== null ? JSON.parse(saved) : true;
  });
  const [agentDropdownOpen, setAgentDropdownOpen] = useState(false);
  const [selectAgentsModal, setSelectAgentsModal] = useState(false);
  const [rightPanelTab, setRightPanelTab] = useState('analytics');
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [multiAgentMode, setMultiAgentMode] = useState(false);
  const [selectedAgents, setSelectedAgents] = useState([selectedAgentId]);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [notifications, setNotifications] = useState([
    { id: 1, title: 'Campaign Completed', message: 'PPC Agent finished optimizing your Google Ads campaign', time: '2 min ago', read: false, type: 'success' },
    { id: 2, title: 'New Insight Available', message: 'SEO Agent found 12 new keyword opportunities', time: '15 min ago', read: false, type: 'info' },
    { id: 3, title: 'A/B Test Winner', message: 'Variant B increased conversions by 23%', time: '1 hour ago', read: true, type: 'success' }
  ]);
  const [integrationStatus, setIntegrationStatus] = useState(null);
  const [smartRoutingMode, setSmartRoutingMode] = useState(false);
  const [realTimeAnalytics, setRealTimeAnalytics] = useState(null);
  const [feedbackLoopRunning, setFeedbackLoopRunning] = useState(false);

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const selectedAgent = AGENTS.find(a => a.id === selectedAgentId) || AGENTS[0];
  const activeAgents = AGENTS.filter(a => a.status === 'online').length;
  const totalTasks = AGENTS.reduce((sum, a) => sum + a.tasks, 0);

  // Persist dark mode
  useEffect(() => {
    localStorage.setItem('marketingos-darkmode', JSON.stringify(darkMode));
  }, [darkMode]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  }, [input]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(true);
      }
      if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
        e.preventDefault();
        toggleRightPanel();
      }
      if (e.key === 'Escape') {
        setCommandPaletteOpen(false);
        setSettingsOpen(false);
        setNotificationsOpen(false);
        setUserMenuOpen(false);
        setSelectAgentsModal(false);
        setAgentDropdownOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toggleRightPanel]);

  // Sync selectedAgents when selectedAgentId changes
  useEffect(() => {
    if (!multiAgentMode) {
      setSelectedAgents([selectedAgentId]);
    }
  }, [selectedAgentId, multiAgentMode]);

  // Fetch integration status on mount and periodically
  useEffect(() => {
    const fetchIntegrationStatus = async () => {
      try {
        const response = await axios.get(`${API_BASE}/api/integrations/status`);
        setIntegrationStatus(response.data);
      } catch (err) {
        console.log('Integration status unavailable');
      }
    };
    fetchIntegrationStatus();
    const interval = setInterval(fetchIntegrationStatus, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  // Fetch real-time analytics
  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await axios.get(`${API_BASE}/api/analytics/dashboard`);
        if (response.data) {
          setRealTimeAnalytics(response.data);
        }
      } catch (err) {
        console.log('Analytics unavailable');
      }
    };
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  // Trigger feedback loop
  const triggerFeedbackLoop = async () => {
    if (feedbackLoopRunning) return;
    setFeedbackLoopRunning(true);
    try {
      const response = await axios.post(`${API_BASE}/api/feedback-loop`, {
        trigger: 'manual',
        metrics: { conversion_rate: 2.5, bounce_rate: 45, avg_session: 120 }
      });
      const feedbackMessage = {
        id: Date.now(),
        role: 'agent',
        content: response.data?.result || 'Feedback loop completed',
        agentId: 'nexus',
        agentName: 'Nexus Orchestrator',
        agentIcon: '🧠',
        agentColor: '#818CF8',
        agentGradientFrom: '#6366F1',
        agentGradientTo: '#8B5CF6',
        model: 'Smart Routing',
        timestamp: new Date().toISOString()
      };
      addMessage(feedbackMessage);
      // Add notification
      setNotifications(prev => [{
        id: Date.now(),
        title: 'Feedback Loop Complete',
        message: 'CRO Agent analyzed your funnel and generated optimization recommendations',
        time: 'Just now',
        read: false,
        type: 'success'
      }, ...prev]);
    } catch (err) {
      console.error('Feedback loop error:', err);
    } finally {
      setFeedbackLoopRunning(false);
    }
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString()
    };

    addMessage(userMessage);
    const currentInput = input.trim();
    setInput('');
    setLoading(true);
    setStreaming(true);

    try {
      // Smart Routing Mode - Let Nexus decide which agent to use
      if (smartRoutingMode) {
        try {
          const response = await axios.post(`${API_BASE}/api/task`, {
            goal: currentInput
          });
          const agentMessage = {
            id: Date.now() + Math.random(),
            role: 'agent',
            content: response?.data?.result || 'Task completed',
            agentId: 'nexus',
            agentName: 'Nexus Orchestrator',
            agentIcon: '🧠',
            agentColor: '#818CF8',
            agentGradientFrom: '#6366F1',
            agentGradientTo: '#8B5CF6',
            model: 'Smart Routing',
            timestamp: new Date().toISOString(),
            metadata: {
              selectedAgent: response?.data?.agent,
              confidence: response?.data?.confidence
            }
          };
          addMessage(agentMessage);
        } catch (err) {
          throw err;
        }
      } else {
        // Manual agent selection mode
        const agentsToQuery = multiAgentMode && selectedAgents.length > 0 ? selectedAgents : [selectedAgentId];

        for (const agentId of agentsToQuery) {
          const agent = AGENTS.find(a => a.id === agentId);
          if (!agent) continue;

          let response;

          try {
            if (agent.id === 'content') {
              response = await axios.post(`${API_BASE}${agent.endpoint}`, {
                prompt: currentInput,
                max_length: 2000
              });
            } else if (agent.id === 'crm') {
              response = await axios.post(`${API_BASE}/api/crm/email-sequence`, {
                topic: currentInput,
                num_emails: 3
              });
            } else if (agent.id === 'brand') {
              response = await axios.post(`${API_BASE}${agent.endpoint}`, {
                company_name: "Your Company",
                industry: "Technology",
                target_audience: "Target audience",
                unique_value: currentInput
              });
            } else if (agent.id === 'webux') {
              response = await axios.post(`${API_BASE}${agent.endpoint}`, {
                product: "Your Product",
                target_audience: "Target users",
                goal: "Conversions",
                style: "modern",
                key_benefits: currentInput
              });
            } else if (agent.id === 'cro') {
              response = await axios.post(`${API_BASE}${agent.endpoint}`, {
                funnel_steps: currentInput,
                conversion_data: "",
                goal: "Increase conversions"
              });
            } else if (agent.id === 'ppc') {
              response = await axios.post(`${API_BASE}/api/task`, {
                goal: "PPC campaign help: " + currentInput
              });
            } else if (agent.id === 'research') {
              response = await axios.post(`${API_BASE}${agent.endpoint}`, {
                topic: currentInput,
                depth: "comprehensive"
              });
            } else if (agent.id === 'seo') {
              response = await axios.get(`${API_BASE}/api/seo/opportunities?topic=${encodeURIComponent(currentInput)}`);
            } else if (agent.id === 'analytics') {
              response = await axios.get(`${API_BASE}/api/analytics/dashboard`);
            } else if (agent.id === 'smm') {
              response = await axios.post(`${API_BASE}/api/smm/post`, {
                platform: "linkedin",
                topic: currentInput,
                brand_voice: "Professional and engaging",
                goal: "Increase engagement",
                brand_name: "Brand"
              });
            }

            const agentMessage = {
              id: Date.now() + Math.random(),
              role: 'agent',
              content: response?.data?.result || response?.data?.data?.analysis || response?.data?.post || (typeof response?.data === 'object' ? JSON.stringify(response?.data, null, 2) : String(response?.data)) || 'Response received',
              agentId: agent.id,
              agentName: agent.name,
              agentIcon: agent.iconEmoji,
              agentColor: agent.color,
              agentGradientFrom: agent.gradientFrom,
              agentGradientTo: agent.gradientTo,
              model: agent.model,
              timestamp: new Date().toISOString()
            };

            addMessage(agentMessage);
          } catch (agentErr) {
            console.error(`Error with agent ${agent.name}:`, agentErr);
            const errorMsg = {
              id: Date.now() + Math.random(),
              role: 'agent',
              content: `⚠️ ${agent.name} encountered an issue: ${typeof agentErr.response?.data?.detail === 'string' ? agentErr.response.data.detail : agentErr.message || 'Service temporarily unavailable. Please try again.'}`,
              agentId: agent.id,
              agentName: agent.name,
              agentIcon: agent.iconEmoji,
              agentColor: agent.color,
              agentGradientFrom: agent.gradientFrom,
              agentGradientTo: agent.gradientTo,
              model: agent.model,
              timestamp: new Date().toISOString()
            };
            addMessage(errorMsg);
          }
        }
      }
    } catch (err) {
      const errorMessage = {
        id: Date.now(),
        role: 'system',
        content: `Error: ${typeof err.response?.data?.detail === 'string' ? err.response.data.detail : err.message || 'Failed to connect to API. Make sure backend is running.'}`,
        timestamp: new Date().toISOString()
      };
      addMessage(errorMessage);
    } finally {
      setLoading(false);
      setStreaming(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Add agent to selection (for multi-agent mode)
  const addAgentToSelection = (agentId) => {
    if (!selectedAgents.includes(agentId)) {
      setSelectedAgents(prev => [...prev, agentId]);
    }
    setSelectAgentsModal(false);
  };

  // Remove agent from selection
  const removeAgentFromSelection = (agentId) => {
    if (selectedAgents.length > 1) {
      setSelectedAgents(prev => prev.filter(id => id !== agentId));
      if (selectedAgentId === agentId) {
        const remaining = selectedAgents.filter(id => id !== agentId);
        setSelectedAgent(remaining[0]);
      }
    }
  };

  // Toggle agent selection
  const toggleAgentInSelection = (agentId) => {
    if (selectedAgents.includes(agentId)) {
      if (selectedAgents.length > 1) {
        removeAgentFromSelection(agentId);
      }
    } else {
      addAgentToSelection(agentId);
    }
  };

  const suggestedPrompts = [
    { icon: PenTool, text: 'Create a content strategy for Q1', agent: 'content' },
    { icon: DollarSign, text: 'Analyze my PPC campaign performance', agent: 'ppc' },
    { icon: TrendingUp, text: 'Find SEO keyword opportunities', agent: 'seo' },
    { icon: Zap, text: 'Optimize my conversion funnel', agent: 'cro' }
  ];

  return (
    <div className={`maestro-app ${darkMode ? 'dark' : 'light'}`}>
      {/* Ambient Background */}
      <div className="ambient-background">
        <div className="gradient-orb orb-1"></div>
        <div className="gradient-orb orb-2"></div>
        <div className="gradient-orb orb-3"></div>
        <div className="noise-overlay"></div>
      </div>

      {/* Header */}
      <Header
        selectedAgent={selectedAgent}
        agentDropdownOpen={agentDropdownOpen}
        setAgentDropdownOpen={setAgentDropdownOpen}
        agents={AGENTS}
        setSelectedAgent={(id) => {
          setSelectedAgent(id);
          if (!multiAgentMode) {
            setSelectedAgents([id]);
          }
        }}
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        notificationsOpen={notificationsOpen}
        setNotificationsOpen={setNotificationsOpen}
        notifications={notifications}
        setNotifications={setNotifications}
        userMenuOpen={userMenuOpen}
        setUserMenuOpen={setUserMenuOpen}
        setSettingsOpen={setSettingsOpen}
        setCommandPaletteOpen={setCommandPaletteOpen}
        multiAgentMode={multiAgentMode}
        setMultiAgentMode={(mode) => {
          setMultiAgentMode(mode);
          if (!mode) {
            setSelectedAgents([selectedAgentId]);
          }
        }}
        isFullscreen={isFullscreen}
        setIsFullscreen={setIsFullscreen}
        smartRoutingMode={smartRoutingMode}
        setSmartRoutingMode={setSmartRoutingMode}
        feedbackLoopRunning={feedbackLoopRunning}
        triggerFeedbackLoop={triggerFeedbackLoop}
      />

      {/* Main Layout Container */}
      <div className="main-layout">
        {/* Left: Messages Area */}
        <div className="chat-area">
          {/* Messages */}
          <div className="messages-container">
            {messages.length === 0 ? (
              <EmptyState 
                suggestedPrompts={suggestedPrompts}
                setInput={setInput}
                setSelectedAgent={(id) => {
                  setSelectedAgent(id);
                  setSelectedAgents([id]);
                }}
                agents={AGENTS}
              />
            ) : (
              <div className="messages-list">
                {messages.map((message, index) => (
                  <MessageBubble 
                    key={message.id || index} 
                    message={message}
                    isLatest={index === messages.length - 1}
                  />
                ))}
                {loading && <LoadingMessage agent={selectedAgent} />}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="input-area">
            <div className="input-context">
              <div className="active-agents">
                <span className="context-label">Talking to:</span>
                {selectedAgents.map(agentId => {
                  const agent = AGENTS.find(a => a.id === agentId);
                  if (!agent) return null;
                  const AgentIcon = agent.icon;
                  return (
                    <div
                      key={agentId}
                      className="agent-chip"
                      style={{ 
                        '--chip-color': agent.color,
                        '--chip-bg': agent.bgColor
                      }}
                    >
                      <AgentIcon size={14} />
                      <span>{agent.shortName}</span>
                      {selectedAgents.length > 1 && (
                        <button 
                          className="chip-remove"
                          onClick={() => removeAgentFromSelection(agentId)}
                        >
                          <X size={12} />
                        </button>
                      )}
                    </div>
                  );
                })}
                <button 
                  className="add-agent-chip"
                  onClick={() => setSelectAgentsModal(true)}
                >
                  <Plus size={14} />
                  <span>Add</span>
                </button>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="input-form">
              <div className={`input-container ${loading ? 'disabled' : ''}`}>
                <div className="input-actions-left">
                  <button type="button" className="input-action-btn" title="Attach file">
                    <Paperclip size={18} />
                  </button>
                  <button type="button" className="input-action-btn" title="Mention agent">
                    <AtSign size={18} />
                  </button>
                  <button type="button" className="input-action-btn" title="Add emoji">
                    <Smile size={18} />
                  </button>
                </div>
                
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={`Ask ${selectedAgent.name} anything...`}
                  rows={1}
                  disabled={loading}
                />
                
                <div className="input-actions-right">
                  <button type="button" className="input-action-btn" title="Voice input">
                    <Mic size={18} />
                  </button>
                  <button 
                    type="submit" 
                    className={`send-btn ${input.trim() ? 'active' : ''}`}
                    disabled={!input.trim() || loading}
                  >
                    {loading ? (
                      <Loader2 size={18} className="spinner" />
                    ) : (
                      <Send size={18} />
                    )}
                  </button>
                </div>
              </div>
            </form>

            <div className="input-hints">
              <span><kbd>Enter</kbd> to send</span>
              <span><kbd>Shift + Enter</kbd> new line</span>
              <span><kbd>⌘K</kbd> commands</span>
            </div>
          </div>
        </div>

        {/* Right Panel */}
        {rightPanelOpen && (
          <div className="right-panel">
            <div className="panel-header">
              <div className="panel-tabs">
                <button 
                  className={`panel-tab ${rightPanelTab === 'analytics' ? 'active' : ''}`}
                  onClick={() => setRightPanelTab('analytics')}
                >
                  <BarChart3 size={16} />
                  <span>Analytics</span>
                </button>
                <button 
                  className={`panel-tab ${rightPanelTab === 'activity' ? 'active' : ''}`}
                  onClick={() => setRightPanelTab('activity')}
                >
                  <Activity size={16} />
                  <span>Activity</span>
                </button>
                <button 
                  className={`panel-tab ${rightPanelTab === 'insights' ? 'active' : ''}`}
                  onClick={() => setRightPanelTab('insights')}
                >
                  <Lightbulb size={16} />
                  <span>Insights</span>
                </button>
              </div>
              <button className="panel-close-btn" onClick={() => setRightPanelOpen(false)}>
                <X size={18} />
              </button>
            </div>

            <div className="panel-content">
              {rightPanelTab === 'analytics' && (
                <AnalyticsPanel trafficData={trafficData} conversionData={conversionData} realTimeData={realTimeAnalytics} />
              )}
              {rightPanelTab === 'activity' && <ActivityPanel agents={AGENTS} />}
              {rightPanelTab === 'insights' && <InsightsPanel agents={AGENTS} />}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <Footer
        activeAgents={activeAgents}
        totalTasks={totalTasks}
        toggleRightPanel={toggleRightPanel}
        rightPanelOpen={rightPanelOpen}
        setSettingsOpen={setSettingsOpen}
        setRightPanelTab={setRightPanelTab}
        integrationStatus={integrationStatus}
      />

      {/* Modals */}
      {selectAgentsModal && (
        <SelectAgentsModal
          agents={AGENTS}
          selectedAgents={selectedAgents}
          onSelectAgent={addAgentToSelection}
          onClose={() => setSelectAgentsModal(false)}
        />
      )}

      {commandPaletteOpen && (
        <CommandPalette
          agents={AGENTS}
          onClose={() => setCommandPaletteOpen(false)}
          setSelectedAgent={(id) => {
            setSelectedAgent(id);
            setSelectedAgents([id]);
          }}
          setSettingsOpen={setSettingsOpen}
          toggleRightPanel={toggleRightPanel}
          setRightPanelTab={setRightPanelTab}
          clearMessages={clearMessages}
        />
      )}

      {settingsOpen && (
        <SettingsModal
          darkMode={darkMode}
          setDarkMode={setDarkMode}
          soundEnabled={soundEnabled}
          setSoundEnabled={setSoundEnabled}
          onClose={() => setSettingsOpen(false)}
          clearMessages={clearMessages}
        />
      )}
    </div>
  );
}

// Header Component
function Header({
  selectedAgent, agentDropdownOpen, setAgentDropdownOpen, agents, setSelectedAgent,
  darkMode, setDarkMode, notificationsOpen, setNotificationsOpen, notifications,
  setNotifications, userMenuOpen, setUserMenuOpen, setSettingsOpen,
  setCommandPaletteOpen, multiAgentMode, setMultiAgentMode,
  isFullscreen, setIsFullscreen, smartRoutingMode, setSmartRoutingMode,
  feedbackLoopRunning, triggerFeedbackLoop
}) {
  const unreadCount = notifications.filter(n => !n.read).length;

  const markAllRead = () => {
    setNotifications(notifications.map(n => ({ ...n, read: true })));
  };

  return (
    <header className="header">
      <div className="header-left">
        <div className="logo">
          <div className="logo-icon">
            <Sparkles size={20} />
          </div>
          <div className="logo-text">
            <span className="logo-name">MarketingOS</span>
            <span className="logo-badge">PRO</span>
          </div>
        </div>

        <div className="header-divider" />

        {/* Agent Selector */}
        <div className="agent-dropdown-wrapper">
          <button 
            className="agent-selector-btn"
            onClick={() => setAgentDropdownOpen(!agentDropdownOpen)}
          >
            <div 
              className="agent-icon-btn" 
              style={{ background: `linear-gradient(135deg, ${selectedAgent.gradientFrom}, ${selectedAgent.gradientTo})` }}
            >
              <selectedAgent.icon size={16} />
            </div>
            <div className="agent-selector-info">
              <span className="agent-selector-name">{selectedAgent.name}</span>
              <span className="agent-selector-model">{selectedAgent.model}</span>
            </div>
            <ChevronDown size={16} className={`chevron ${agentDropdownOpen ? 'open' : ''}`} />
          </button>

          {agentDropdownOpen && (
            <>
              <div className="dropdown-backdrop" onClick={() => setAgentDropdownOpen(false)} />
              <div className="agent-dropdown-menu">
                <div className="dropdown-header">
                  <span className="dropdown-title">AI Agents</span>
                  <span className="agents-online">{agents.filter(a => a.status === 'online').length} online</span>
                </div>
                <div className="agents-list-dropdown">
                  {agents.map(agent => {
                    const AgentIcon = agent.icon;
                    return (
                      <button
                        key={agent.id}
                        className={`agent-dropdown-item ${selectedAgent.id === agent.id ? 'active' : ''}`}
                        onClick={() => {
                          setSelectedAgent(agent.id);
                          setAgentDropdownOpen(false);
                        }}
                      >
                        <div 
                          className="agent-icon-dropdown" 
                          style={{ background: `linear-gradient(135deg, ${agent.gradientFrom}, ${agent.gradientTo})` }}
                        >
                          <AgentIcon size={18} />
                        </div>
                        <div className="agent-dropdown-info">
                          <span className="agent-dropdown-name">{agent.name}</span>
                          <span className="agent-dropdown-model">{agent.model}</span>
                        </div>
                        {selectedAgent.id === agent.id && <Check size={16} className="check-icon" />}
                      </button>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Multi-agent toggle */}
        <button
          className={`multi-agent-toggle ${multiAgentMode ? 'active' : ''}`}
          onClick={() => setMultiAgentMode(!multiAgentMode)}
          title="Multi-Agent Mode"
        >
          <Layers size={16} />
          <span>Multi</span>
        </button>

        {/* Smart Routing toggle */}
        <button
          className={`smart-routing-toggle ${smartRoutingMode ? 'active' : ''}`}
          onClick={() => setSmartRoutingMode(!smartRoutingMode)}
          title="Smart Routing - Let Nexus choose the best agent"
        >
          <Cpu size={16} />
          <span>Smart</span>
        </button>

        {/* Feedback Loop trigger */}
        <button
          className={`feedback-loop-btn ${feedbackLoopRunning ? 'running' : ''}`}
          onClick={triggerFeedbackLoop}
          disabled={feedbackLoopRunning}
          title="Run Feedback Loop - Analyze and optimize"
        >
          {feedbackLoopRunning ? <Loader2 size={16} className="spinner" /> : <RefreshCw size={16} />}
          <span>Loop</span>
        </button>
      </div>

      <div className="header-center">
        <button className="search-bar" onClick={() => setCommandPaletteOpen(true)}>
          <Search size={16} />
          <span>Search or run command...</span>
          <div className="search-shortcut">
            <kbd>⌘</kbd>
            <kbd>K</kbd>
          </div>
        </button>
      </div>

      <div className="header-right">
        <button className="header-icon-btn" onClick={() => setDarkMode(!darkMode)} title={darkMode ? 'Light Mode' : 'Dark Mode'}>
          {darkMode ? <Sun size={18} /> : <Moon size={18} />}
        </button>
        
        <button className="header-icon-btn" onClick={() => setIsFullscreen(!isFullscreen)} title="Fullscreen">
          {isFullscreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
        </button>

        {/* Notifications */}
        <div className="notifications-wrapper">
          <button 
            className={`header-icon-btn ${unreadCount > 0 ? 'has-badge' : ''}`}
            onClick={() => setNotificationsOpen(!notificationsOpen)}
          >
            <Bell size={18} />
            {unreadCount > 0 && <span className="notification-badge">{unreadCount}</span>}
          </button>

          {notificationsOpen && (
            <>
              <div className="dropdown-backdrop" onClick={() => setNotificationsOpen(false)} />
              <div className="notifications-dropdown">
                <div className="notifications-header">
                  <span>Notifications</span>
                  {unreadCount > 0 && (
                    <button className="mark-read-btn" onClick={markAllRead}>Mark all read</button>
                  )}
                </div>
                <div className="notifications-list">
                  {notifications.map(n => (
                    <div key={n.id} className={`notification-item ${n.read ? '' : 'unread'} ${n.type}`}>
                      <div className="notification-icon">
                        {n.type === 'success' ? <CheckCircle2 size={18} /> : <Info size={18} />}
                      </div>
                      <div className="notification-content">
                        <span className="notification-title">{n.title}</span>
                        <span className="notification-message">{n.message}</span>
                        <span className="notification-time">{n.time}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>

        {/* User Menu */}
        <div className="user-menu-wrapper">
          <button className="user-btn" onClick={() => setUserMenuOpen(!userMenuOpen)}>
            <div className="user-avatar">M</div>
            <ChevronDown size={14} className={`chevron ${userMenuOpen ? 'open' : ''}`} />
          </button>

          {userMenuOpen && (
            <>
              <div className="dropdown-backdrop" onClick={() => setUserMenuOpen(false)} />
              <div className="user-dropdown">
                <div className="user-dropdown-header">
                  <div className="user-dropdown-avatar">M</div>
                  <div className="user-dropdown-info">
                    <span className="user-dropdown-name">Marketing Pro</span>
                    <span className="user-dropdown-email">pro@marketingos.ai</span>
                  </div>
                </div>
                <div className="dropdown-divider" />
                <button className="dropdown-menu-item"><User size={16} /><span>Profile</span></button>
                <button className="dropdown-menu-item"><BarChart3 size={16} /><span>Billing</span></button>
                <button className="dropdown-menu-item"><Users size={16} /><span>Team</span></button>
                <button className="dropdown-menu-item" onClick={() => { setUserMenuOpen(false); setSettingsOpen(true); }}>
                  <Settings size={16} /><span>Settings</span>
                </button>
                <div className="dropdown-divider" />
                <button className="dropdown-menu-item danger"><ExternalLink size={16} /><span>Sign out</span></button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

// Empty State
function EmptyState({ suggestedPrompts, setInput, setSelectedAgent, agents }) {
  return (
    <div className="empty-state">
      <div className="empty-state-content">
        <div className="empty-icon-wrapper">
          <div className="empty-icon-glow"></div>
          <div className="empty-icon">
            <Sparkles size={40} />
          </div>
        </div>
        
        <h1 className="empty-title">How can I help you today?</h1>
        <p className="empty-description">
          Your AI-powered marketing command center. Choose an agent or describe what you need.
        </p>

        <div className="suggested-prompts">
          {suggestedPrompts.map((prompt, i) => {
            const Icon = prompt.icon;
            const agent = agents.find(a => a.id === prompt.agent);
            return (
              <button
                key={i}
                className="suggested-prompt"
                onClick={() => {
                  setSelectedAgent(prompt.agent);
                  setInput(prompt.text);
                }}
                style={{ '--accent-color': agent?.color }}
              >
                <div className="prompt-icon" style={{ background: agent?.bgColor, color: agent?.color }}>
                  <Icon size={18} />
                </div>
                <span className="prompt-text">{prompt.text}</span>
                <ArrowRight size={16} className="prompt-arrow" />
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// Message Bubble
function MessageBubble({ message, isLatest }) {
  const [copied, setCopied] = useState(false);
  const [liked, setLiked] = useState(null);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (message.role === 'user') {
    return (
      <div className="message user-message">
        <div className="message-wrapper">
          <div className="user-message-bubble">
            <div className="user-message-text">{message.content}</div>
          </div>
          <div className="message-meta">
            <span className="message-time">
              {new Date(message.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (message.role === 'system') {
    return (
      <div className="message system-message">
        <div className="system-message-content">
          <AlertCircle size={18} />
          <span>{message.content}</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`message agent-message ${isLatest ? 'latest' : ''}`}>
      <div 
        className="agent-avatar"
        style={{ background: `linear-gradient(135deg, ${message.agentGradientFrom}, ${message.agentGradientTo})` }}
      >
        <span>{message.agentIcon}</span>
      </div>
      <div className="message-wrapper">
        <div className="message-header">
          <span className="agent-name">{message.agentName}</span>
          <span className="agent-model-tag">{message.model}</span>
        </div>
        <div className="agent-message-bubble">
          <div className="agent-message-text">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </div>
        </div>
        <div className="message-actions">
          <button className={`action-btn ${copied ? 'success' : ''}`} onClick={handleCopy}>
            {copied ? <Check size={14} /> : <Copy size={14} />}
            <span>{copied ? 'Copied!' : 'Copy'}</span>
          </button>
          <button className="action-btn"><Share2 size={14} /><span>Share</span></button>
          <button className="action-btn"><Bookmark size={14} /><span>Save</span></button>
          <div className="action-divider" />
          <button className={`action-btn icon-only ${liked === true ? 'liked' : ''}`} onClick={() => setLiked(liked === true ? null : true)}>
            <ThumbsUp size={14} />
          </button>
          <button className={`action-btn icon-only ${liked === false ? 'disliked' : ''}`} onClick={() => setLiked(liked === false ? null : false)}>
            <ThumbsDown size={14} />
          </button>
          <button className="action-btn icon-only"><RotateCcw size={14} /></button>
        </div>
      </div>
    </div>
  );
}

// Loading Message
function LoadingMessage({ agent }) {
  return (
    <div className="message agent-message loading">
      <div className="agent-avatar" style={{ background: `linear-gradient(135deg, ${agent.gradientFrom}, ${agent.gradientTo})` }}>
        <span>{agent.iconEmoji}</span>
      </div>
      <div className="message-wrapper">
        <div className="message-header">
          <span className="agent-name">{agent.name}</span>
        </div>
        <div className="agent-message-bubble loading-bubble">
          <div className="typing-indicator">
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
          </div>
          <span className="typing-text">Thinking...</span>
        </div>
      </div>
    </div>
  );
}

// Analytics Panel
function AnalyticsPanel({ trafficData, conversionData, realTimeData }) {
  // Use real-time data if available, otherwise use mock data
  const metrics = realTimeData?.metrics || {
    users: { value: '45,234', change: '+12.5%', positive: true },
    pageviews: { value: '128,847', change: '+8.2%', positive: true },
    avgSession: { value: '4m 32s', change: '-2.1%', positive: false },
    conversion: { value: '3.8%', change: '+0.5%', positive: true }
  };

  return (
    <div className="analytics-panel">
      {realTimeData && (
        <div className="live-indicator">
          <span className="live-dot" />
          <span>Live Data</span>
          <span className="last-updated">Updated {new Date().toLocaleTimeString()}</span>
        </div>
      )}
      <div className="metrics-grid">
        <MetricCard icon={Users} label="Total Visitors" value={metrics.users?.value || '45,234'} change={metrics.users?.change || '+12.5%'} positive={metrics.users?.positive !== false} />
        <MetricCard icon={Eye} label="Page Views" value={metrics.pageviews?.value || '128,847'} change={metrics.pageviews?.change || '+8.2%'} positive={metrics.pageviews?.positive !== false} />
        <MetricCard icon={MousePointer} label="Avg. Session" value={metrics.avgSession?.value || '4m 32s'} change={metrics.avgSession?.change || '-2.1%'} positive={metrics.avgSession?.positive === true} />
        <MetricCard icon={Target} label="Conversion" value={metrics.conversion?.value || '3.8%'} change={metrics.conversion?.change || '+0.5%'} positive={metrics.conversion?.positive !== false} />
      </div>

      <div className="chart-card">
        <div className="chart-header">
          <h4>Traffic Sources</h4>
          <select className="chart-select">
            <option>Last 7 days</option>
            <option>Last 30 days</option>
          </select>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={trafficData}>
            <defs>
              <linearGradient id="gradientOrganic" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#818CF8" stopOpacity={0.4}/>
                <stop offset="100%" stopColor="#818CF8" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="gradientPaid" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#FBBF24" stopOpacity={0.4}/>
                <stop offset="100%" stopColor="#FBBF24" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="gradientSocial" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#F472B6" stopOpacity={0.4}/>
                <stop offset="100%" stopColor="#F472B6" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis dataKey="day" stroke="rgba(255,255,255,0.4)" fontSize={11} tickLine={false} axisLine={false} />
            <YAxis stroke="rgba(255,255,255,0.4)" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v) => `${v/1000}k`} />
            <Tooltip contentStyle={{ background: 'rgba(15, 23, 42, 0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }} />
            <Area type="monotone" dataKey="organic" stroke="#818CF8" strokeWidth={2} fill="url(#gradientOrganic)" />
            <Area type="monotone" dataKey="paid" stroke="#FBBF24" strokeWidth={2} fill="url(#gradientPaid)" />
            <Area type="monotone" dataKey="social" stroke="#F472B6" strokeWidth={2} fill="url(#gradientSocial)" />
          </AreaChart>
        </ResponsiveContainer>
        <div className="chart-legend">
          <div className="legend-item"><span className="legend-dot" style={{ background: '#818CF8' }} /><span>Organic</span></div>
          <div className="legend-item"><span className="legend-dot" style={{ background: '#FBBF24' }} /><span>Paid</span></div>
          <div className="legend-item"><span className="legend-dot" style={{ background: '#F472B6' }} /><span>Social</span></div>
        </div>
      </div>

      <div className="chart-card">
        <div className="chart-header"><h4>Conversion by Page</h4></div>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={conversionData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" horizontal={false} />
            <XAxis type="number" stroke="rgba(255,255,255,0.4)" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}%`} />
            <YAxis dataKey="page" type="category" stroke="rgba(255,255,255,0.4)" fontSize={11} tickLine={false} axisLine={false} width={70} />
            <Tooltip contentStyle={{ background: 'rgba(15, 23, 42, 0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }} formatter={(v) => [`${v}%`, 'Conversion']} />
            <Bar dataKey="conversions" radius={[0, 6, 6, 0]}>
              {conversionData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={['#34D399', '#22D3EE', '#818CF8', '#FBBF24', '#F472B6'][index % 5]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// Metric Card
function MetricCard({ icon: Icon, label, value, change, positive }) {
  return (
    <div className="metric-card">
      <div className="metric-header">
        <div className={`metric-icon ${positive ? 'positive' : 'negative'}`}>
          <Icon size={18} />
        </div>
        <div className={`metric-change ${positive ? 'positive' : 'negative'}`}>
          {positive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          <span>{change}</span>
        </div>
      </div>
      <div className="metric-value">{value}</div>
      <div className="metric-label">{label}</div>
    </div>
  );
}

// Activity Panel
function ActivityPanel({ agents }) {
  const activities = [
    { agent: agents[0], action: 'Generated blog post', target: '"10 AI Marketing Trends"', time: '2 min ago', status: 'completed' },
    { agent: agents[8], action: 'Completed A/B test', target: 'Landing page variant B', time: '5 min ago', status: 'completed' },
    { agent: agents[6], action: 'Found keywords', target: '12 new opportunities', time: '12 min ago', status: 'completed' },
    { agent: agents[1], action: 'Optimizing campaign', target: 'Google Ads - Q1', time: '18 min ago', status: 'in-progress' },
  ];

  return (
    <div className="activity-panel">
      <div className="activity-list">
        {activities.map((activity, i) => {
          const AgentIcon = activity.agent.icon;
          return (
            <div key={i} className="activity-item">
              <div className="activity-avatar" style={{ background: `linear-gradient(135deg, ${activity.agent.gradientFrom}, ${activity.agent.gradientTo})` }}>
                <AgentIcon size={16} />
              </div>
              <div className="activity-content">
                <div className="activity-main">
                  <span className="activity-agent">{activity.agent.shortName}</span>
                  <span className="activity-action">{activity.action}</span>
                </div>
                <div className="activity-target">{activity.target}</div>
                <div className="activity-meta">
                  <span className={`activity-status ${activity.status}`}>
                    {activity.status === 'completed' ? <><CheckCircle2 size={12} /> Done</> : <><Loader2 size={12} className="spinner" /> Running</>}
                  </span>
                  <span className="activity-time">{activity.time}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Insights Panel
function InsightsPanel({ agents }) {
  const insights = [
    { title: 'Content Gap Detected', description: 'Competitors ranking for "AI marketing automation" - you have no content.', agent: agents[6], priority: 'high', impact: '+2,400 visits/mo', action: 'Create content strategy' },
    { title: 'PPC Budget Underutilized', description: '$2,400 remaining with only 5 days left.', agent: agents[1], priority: 'medium', impact: '340 more conversions', action: 'Increase bids' },
    { title: 'Email Campaign Outperforming', description: '28% open rate - 5% above industry average.', agent: agents[4], priority: 'low', impact: 'Keep strategy, test variations', action: 'View report' },
    { title: 'A/B Test Winner Found', description: 'Variant B has 23% higher conversion rate.', agent: agents[8], priority: 'high', impact: '+$12,000 revenue', action: 'Deploy winner' },
  ];

  return (
    <div className="insights-panel">
      <div className="insights-list">
        {insights.map((insight, i) => {
          const AgentIcon = insight.agent.icon;
          return (
            <div key={i} className={`insight-card priority-${insight.priority}`}>
              <div className="insight-priority-bar" />
              <div className="insight-content">
                <div className="insight-header">
                  <h4 className="insight-title">{insight.title}</h4>
                  <span className={`priority-badge ${insight.priority}`}>{insight.priority}</span>
                </div>
                <p className="insight-description">{insight.description}</p>
                <div className="insight-impact"><Zap size={14} /><span>{insight.impact}</span></div>
                <div className="insight-footer">
                  <div className="insight-agent">
                    <div className="insight-agent-icon" style={{ background: `linear-gradient(135deg, ${insight.agent.gradientFrom}, ${insight.agent.gradientTo})` }}>
                      <AgentIcon size={12} />
                    </div>
                    <span>{insight.agent.shortName}</span>
                  </div>
                  <button className="insight-action-btn">{insight.action}<ArrowRight size={14} /></button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Footer
function Footer({ activeAgents, totalTasks, toggleRightPanel, rightPanelOpen, setSettingsOpen, setRightPanelTab, integrationStatus }) {
  const connectedCount = integrationStatus?.connected || 0;
  const totalIntegrations = integrationStatus?.total || 6;

  return (
    <footer className="footer">
      <div className="footer-left">
        <div className="system-stat">
          <Cpu size={14} />
          <span>CPU</span>
          <div className="stat-bar"><div className="stat-fill cpu" style={{ width: '42%' }} /></div>
          <span className="stat-value">42%</span>
        </div>
        <div className="system-stat">
          <HardDrive size={14} />
          <span>Memory</span>
          <div className="stat-bar"><div className="stat-fill memory" style={{ width: '68%' }} /></div>
          <span className="stat-value">68%</span>
        </div>
        <div className="footer-divider" />
        <div className="footer-info"><Activity size={14} /><span>{activeAgents} agents online</span></div>
        <div className="footer-info"><CheckCircle2 size={14} /><span>{totalTasks.toLocaleString()} tasks</span></div>
        <div className="footer-divider" />
        {/* Integration Status */}
        <div className={`integration-status ${connectedCount > 0 ? 'connected' : 'disconnected'}`}>
          <Globe size={14} />
          <span>{connectedCount}/{totalIntegrations} integrations</span>
          {integrationStatus && (
            <div className="integration-tooltip">
              {Object.entries(integrationStatus.integrations || {}).map(([name, status]) => (
                <div key={name} className={`integration-item ${status ? 'active' : 'inactive'}`}>
                  <span className={`status-dot ${status ? 'online' : 'offline'}`} />
                  <span>{name.replace('_', ' ')}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      <div className="footer-right">
        <button className={`footer-btn ${rightPanelOpen ? 'active' : ''}`} onClick={() => { setRightPanelTab('analytics'); toggleRightPanel(); }}>
          <BarChart3 size={16} /><span>Analytics</span>
        </button>
        <button className="footer-btn" onClick={() => { setRightPanelTab('insights'); toggleRightPanel(); }}>
          <Lightbulb size={16} /><span>Insights</span>
        </button>
        <button className="footer-btn" onClick={() => setSettingsOpen(true)}>
          <Settings size={16} />
        </button>
        <div className="footer-divider" />
        <div className="system-status"><span className="status-dot online" /><span>All systems operational</span></div>
      </div>
    </footer>
  );
}

// Select Agents Modal - Fixed for adding agents one by one
function SelectAgentsModal({ agents, selectedAgents, onSelectAgent, onClose }) {
  return (
    <>
      <div className="modal-backdrop" onClick={onClose} />
      <div className="modal select-agents-modal">
        <div className="modal-header">
          <div>
            <h3>Add Agent</h3>
            <p className="modal-subtitle">Select an agent to add to your conversation</p>
          </div>
          <button className="modal-close-btn" onClick={onClose}><X size={20} /></button>
        </div>
        <div className="agents-list-modal">
          {agents.map(agent => {
            const AgentIcon = agent.icon;
            const isAlreadySelected = selectedAgents.includes(agent.id);
            return (
              <button
                key={agent.id}
                className={`agent-list-item ${isAlreadySelected ? 'already-selected' : ''}`}
                onClick={() => !isAlreadySelected && onSelectAgent(agent.id)}
                disabled={isAlreadySelected}
              >
                <div className="agent-list-icon" style={{ background: `linear-gradient(135deg, ${agent.gradientFrom}, ${agent.gradientTo})` }}>
                  <AgentIcon size={20} />
                </div>
                <div className="agent-list-info">
                  <span className="agent-list-name">{agent.name}</span>
                  <span className="agent-list-desc">{agent.description}</span>
                </div>
                {isAlreadySelected ? (
                  <span className="already-added-badge">Added</span>
                ) : (
                  <Plus size={18} className="add-icon" />
                )}
              </button>
            );
          })}
        </div>
      </div>
    </>
  );
}

// Command Palette
function CommandPalette({ agents, onClose, setSelectedAgent, setSettingsOpen, toggleRightPanel, setRightPanelTab, clearMessages }) {
  const [search, setSearch] = useState('');
  const inputRef = useRef(null);

  useEffect(() => { inputRef.current?.focus(); }, []);

  const commands = [
    ...agents.map(agent => ({ id: agent.id, type: 'agent', icon: agent.icon, label: agent.name, color: agent.color, action: () => setSelectedAgent(agent.id) })),
    { id: 'analytics', type: 'action', icon: BarChart3, label: 'Open Analytics', action: () => { setRightPanelTab('analytics'); toggleRightPanel(); } },
    { id: 'insights', type: 'action', icon: Lightbulb, label: 'View Insights', action: () => { setRightPanelTab('insights'); toggleRightPanel(); } },
    { id: 'settings', type: 'action', icon: Settings, label: 'Settings', action: () => setSettingsOpen(true) },
    { id: 'clear', type: 'action', icon: RefreshCw, label: 'Clear Chat', action: () => clearMessages() },
  ];

  const filtered = commands.filter(c => c.label.toLowerCase().includes(search.toLowerCase()));

  return (
    <>
      <div className="modal-backdrop" onClick={onClose} />
      <div className="modal command-palette">
        <div className="command-search">
          <Search size={20} />
          <input ref={inputRef} type="text" placeholder="Search commands..." value={search} onChange={(e) => setSearch(e.target.value)} />
          <kbd>ESC</kbd>
        </div>
        <div className="command-list">
          {filtered.map(cmd => {
            const Icon = cmd.icon;
            return (
              <button key={cmd.id} className="command-item" onClick={() => { cmd.action(); onClose(); }}>
                <div className="command-icon" style={cmd.color ? { background: `${cmd.color}20`, color: cmd.color } : {}}>
                  <Icon size={18} />
                </div>
                <span className="command-label">{cmd.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </>
  );
}

// Settings Modal
function SettingsModal({ darkMode, setDarkMode, soundEnabled, setSoundEnabled, onClose, clearMessages }) {
  const [pushNotifications, setPushNotifications] = useState(true);

  return (
    <>
      <div className="modal-backdrop" onClick={onClose} />
      <div className="modal settings-modal">
        <div className="modal-header">
          <div><h3>Settings</h3><p className="modal-subtitle">Customize your experience</p></div>
          <button className="modal-close-btn" onClick={onClose}><X size={20} /></button>
        </div>
        <div className="settings-content">
          <div className="settings-section">
            <h4 className="settings-section-title">Appearance</h4>
            <div className="theme-selector">
              <button className={`theme-option ${!darkMode ? 'active' : ''}`} onClick={() => setDarkMode(false)}>
                <div className="theme-preview light"><div className="preview-header" /><div className="preview-content"><div className="preview-line" /><div className="preview-line short" /></div></div>
                <div className="theme-info"><Sun size={16} /><span>Light</span></div>
              </button>
              <button className={`theme-option ${darkMode ? 'active' : ''}`} onClick={() => setDarkMode(true)}>
                <div className="theme-preview dark"><div className="preview-header" /><div className="preview-content"><div className="preview-line" /><div className="preview-line short" /></div></div>
                <div className="theme-info"><Moon size={16} /><span>Dark</span></div>
              </button>
            </div>
          </div>
          <div className="settings-section">
            <h4 className="settings-section-title">Notifications</h4>
            <SettingsToggle icon={Bell} label="Push Notifications" description="Get notified about agent updates" checked={pushNotifications} onChange={setPushNotifications} />
            <SettingsToggle icon={Volume2} label="Sound Effects" description="Play sounds for actions" checked={soundEnabled} onChange={setSoundEnabled} />
          </div>
          <div className="settings-section">
            <h4 className="settings-section-title">Data</h4>
            <button className="danger-btn" onClick={() => { clearMessages(); onClose(); }}>
              <RefreshCw size={16} /><span>Clear All Conversations</span>
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

function SettingsToggle({ icon: Icon, label, description, checked, onChange }) {
  return (
    <div className="settings-toggle">
      <div className="settings-toggle-icon"><Icon size={20} /></div>
      <div className="settings-toggle-content">
        <span className="settings-toggle-label">{label}</span>
        <span className="settings-toggle-description">{description}</span>
      </div>
      <label className="toggle-switch">
        <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
        <span className="toggle-slider" />
      </label>
    </div>
  );
}

export default App;
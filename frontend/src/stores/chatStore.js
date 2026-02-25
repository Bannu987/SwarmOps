import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useChatStore = create(
  persist(
    (set, get) => ({
      // State
      messages: [{
        id: 'mock-1',
        role: 'agent',
        agentId: 'content',
        agentName: 'System Verification',
        agentIcon: '⚙️',
        content: `Here is the analysis you requested.

## PRIORITY_ACTIONS
- Review Google Ads budget allocation
- Approve the new Q1 Content Strategy draft
- Fix the broken links on the Pricing page

## CONFIDENCE_SCORE
85%

## CROSS_IMPACT_SIGNALS
- SEO Agent noted the pricing page links are affecting crawl budget.
- PPC Agent suggests pausing ads to the broken pricing page.`,
        quality: { confidence: 0.85 }
      }],
      selectedAgentId: 'content',
      isStreaming: false,
      rightPanelOpen: false,
      conversations: [],
      currentConversationId: null,
      settings: {
        darkMode: true,
        soundEnabled: true,
        pushNotifications: true,
        compactMode: false,
        autoSave: true
      },

      // Message Actions
      addMessage: (message) => set((state) => ({
        messages: [
          ...state.messages,
          {
            ...message,
            id: message.id || Date.now(),
            timestamp: message.timestamp || new Date().toISOString()
          }
        ]
      })),

      updateMessage: (id, updates) => set((state) => ({
        messages: state.messages.map(msg =>
          msg.id === id ? { ...msg, ...updates } : msg
        )
      })),

      deleteMessage: (id) => set((state) => ({
        messages: state.messages.filter(msg => msg.id !== id)
      })),

      clearMessages: () => set({ messages: [] }),

      // Agent Actions
      setSelectedAgent: (agentId) => set({ selectedAgentId: agentId }),

      // UI State Actions
      setStreaming: (isStreaming) => set({ isStreaming }),

      toggleRightPanel: () => set((state) => ({
        rightPanelOpen: !state.rightPanelOpen
      })),

      setRightPanelOpen: (open) => set({ rightPanelOpen: open }),

      // Conversation Management
      createConversation: (title = 'New Conversation') => {
        const id = Date.now().toString();
        set((state) => ({
          conversations: [
            ...state.conversations,
            {
              id,
              title,
              createdAt: new Date().toISOString(),
              messages: [],
              agentId: state.selectedAgentId
            }
          ],
          currentConversationId: id,
          messages: []
        }));
        return id;
      },

      loadConversation: (id) => {
        const state = get();
        const conversation = state.conversations.find(c => c.id === id);
        if (conversation) {
          set({
            currentConversationId: id,
            messages: conversation.messages || [],
            selectedAgentId: conversation.agentId || 'content'
          });
        }
      },

      saveCurrentConversation: () => set((state) => {
        if (!state.currentConversationId) return state;

        return {
          conversations: state.conversations.map(conv =>
            conv.id === state.currentConversationId
              ? { ...conv, messages: state.messages, updatedAt: new Date().toISOString() }
              : conv
          )
        };
      }),

      deleteConversation: (id) => set((state) => ({
        conversations: state.conversations.filter(c => c.id !== id),
        currentConversationId: state.currentConversationId === id ? null : state.currentConversationId,
        messages: state.currentConversationId === id ? [] : state.messages
      })),

      renameConversation: (id, title) => set((state) => ({
        conversations: state.conversations.map(c =>
          c.id === id ? { ...c, title } : c
        )
      })),

      // Settings Actions
      updateSettings: (updates) => set((state) => ({
        settings: { ...state.settings, ...updates }
      })),

      resetSettings: () => set({
        settings: {
          darkMode: true,
          soundEnabled: true,
          pushNotifications: true,
          compactMode: false,
          autoSave: true
        }
      }),

      // Bulk Actions
      resetAll: () => set({
        messages: [],
        selectedAgentId: 'content',
        isStreaming: false,
        rightPanelOpen: false,
        conversations: [],
        currentConversationId: null
      })
    }),
    {
      name: 'swarmops-storage',
      version: 1,
      partialize: (state) => ({
        messages: state.messages.slice(-100),
        selectedAgentId: state.selectedAgentId,
        rightPanelOpen: state.rightPanelOpen,
        conversations: state.conversations.slice(-20),
        currentConversationId: state.currentConversationId,
        settings: state.settings
      })
    }
  )
);
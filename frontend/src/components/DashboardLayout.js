import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const SIDEBAR_ITEMS = [
  { id: 'command', label: 'Command Center', icon: '◉' },
  { id: 'agents', label: 'Agents', icon: '◯' },
  { id: 'approval', label: 'Approval Queue', icon: '◐', hasBadge: true },
  { id: 'memory', label: 'Memory', icon: '◆' },
  { id: 'sources', label: 'Data Sources', icon: '◎' },
];

export default function DashboardLayout({
  children,
  activeView,
  onViewChange,
  pendingApprovals = 0,
  onNewChat,
}) {
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleSignOut = async () => {
    await signOut();
    navigate('/login');
  };

  const getInitials = (email) => {
    if (!email) return '?';
    return email.charAt(0).toUpperCase();
  };

  return (
    <div className="flex h-screen bg-bg-primary overflow-hidden">
      {/* Sidebar */}
      <aside
        className={`flex flex-col bg-bg-secondary border-r border-border transition-all duration-200 ${
          sidebarOpen ? 'w-60' : 'w-0'
        }`}
      >
        {sidebarOpen && (
          <>
            {/* Logo */}
            <div className="px-4 py-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded bg-gradient-to-br from-accent to-accent-cyan flex items-center justify-center text-white text-sm font-bold">
                  S
                </div>
                <span className="text-text-primary font-semibold">
                  Swarm<span className="text-accent">Ops</span>
                </span>
              </div>
              <button
                onClick={() => setSidebarOpen(false)}
                className="text-text-muted hover:text-text-primary text-xs"
              >
                ◀
              </button>
            </div>

            {/* New chat */}
            <div className="px-3 pb-3">
              <button
                onClick={onNewChat}
                className="w-full py-2 px-3 bg-bg-tertiary hover:bg-bg-hover border border-border rounded-lg text-text-primary text-sm font-medium transition flex items-center gap-2"
              >
                <span className="text-accent">+</span> New Chat
              </button>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-2 py-2 space-y-0.5 overflow-y-auto">
              <div className="text-[10px] font-semibold text-text-muted uppercase tracking-wider px-2 py-2">
                Workspace
              </div>
              {SIDEBAR_ITEMS.map((item) => {
                const isActive = activeView === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => onViewChange(item.id)}
                    className={`w-full px-2 py-2 rounded-md text-sm flex items-center gap-2.5 transition relative ${
                      isActive
                        ? 'bg-accent/10 text-accent'
                        : 'text-text-secondary hover:text-text-primary hover:bg-bg-hover'
                    }`}
                  >
                    <span className={isActive ? 'text-accent' : 'text-text-muted'}>
                      {item.icon}
                    </span>
                    <span>{item.label}</span>
                    {item.hasBadge && pendingApprovals > 0 && (
                      <span className="ml-auto bg-accent text-white text-[10px] font-semibold px-1.5 py-0.5 rounded-full">
                        {pendingApprovals}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>

            {/* User menu */}
            <div className="px-2 py-3 border-t border-border relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="w-full px-2 py-2 hover:bg-bg-hover rounded-md flex items-center gap-2.5 transition"
              >
                <div className="w-7 h-7 rounded-full bg-accent/20 flex items-center justify-center text-accent text-sm font-semibold">
                  {getInitials(user?.email)}
                </div>
                <div className="flex-1 text-left overflow-hidden">
                  <div className="text-sm text-text-primary truncate">
                    {user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'User'}
                  </div>
                  <div className="text-[11px] text-text-muted truncate">
                    {user?.email || 'Not signed in'}
                  </div>
                </div>
                <span className="text-text-muted text-xs">⋯</span>
              </button>

              {userMenuOpen && (
                <div className="absolute bottom-full left-2 right-2 mb-2 bg-bg-tertiary border border-border-hover rounded-lg shadow-2xl py-1 animate-fade-in z-50">
                  <button
                    onClick={() => {
                      setUserMenuOpen(false);
                      onViewChange('settings');
                    }}
                    className="w-full px-3 py-2 text-left text-sm text-text-secondary hover:bg-bg-hover hover:text-text-primary transition flex items-center gap-2"
                  >
                    <span>⚙</span> Settings
                  </button>
                  <button
                    onClick={() => {
                      setUserMenuOpen(false);
                      onViewChange('profile');
                    }}
                    className="w-full px-3 py-2 text-left text-sm text-text-secondary hover:bg-bg-hover hover:text-text-primary transition flex items-center gap-2"
                  >
                    <span>◔</span> Profile
                  </button>
                  <div className="h-px bg-border my-1"></div>
                  <button
                    onClick={handleSignOut}
                    className="w-full px-3 py-2 text-left text-sm text-red-400 hover:bg-red-500/10 transition flex items-center gap-2"
                  >
                    <span>→</span> Sign out
                  </button>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-3 py-2 border-t border-border">
              <div className="text-[10px] text-text-muted">
                v3.0 · 12 agents · 13 workflows
              </div>
            </div>
          </>
        )}
      </aside>

      {/* Collapsed sidebar toggle */}
      {!sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(true)}
          className="fixed top-4 left-4 z-30 w-8 h-8 bg-bg-tertiary border border-border rounded-md text-text-secondary hover:text-text-primary transition flex items-center justify-center"
        >
          ☰
        </button>
      )}

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">{children}</main>
    </div>
  );
}

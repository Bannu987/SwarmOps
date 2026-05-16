import React, { useState } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import CommandCenter from '../views/CommandCenter';
import AgentsView from '../views/AgentsView';
import ApprovalQueueView from '../views/ApprovalQueueView';
import MemoryView from '../views/MemoryView';
import DataSourcesView from '../views/DataSourcesView';

export default function Dashboard() {
  const [activeView, setActiveView] = useState('command');
  const [artifacts, setArtifacts] = useState([]);
  const [chatKey, setChatKey] = useState(0);

  const handleArtifactCreated = (artifact) => {
    setArtifacts((prev) => [...prev, artifact]);
  };

  const handleApprove = (id) => {
    setArtifacts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status: 'approved' } : a))
    );
  };

  const handleReject = (id) => {
    setArtifacts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status: 'rejected' } : a))
    );
  };

  const handleNewChat = () => {
    setChatKey((k) => k + 1);
    setActiveView('command');
  };

  const pendingApprovals = artifacts.filter((a) => a.status === 'pending').length;

  return (
    <DashboardLayout
      activeView={activeView}
      onViewChange={setActiveView}
      pendingApprovals={pendingApprovals}
      onNewChat={handleNewChat}
    >
      {activeView === 'command' && (
        <CommandCenter key={chatKey} onArtifactCreated={handleArtifactCreated} />
      )}
      {activeView === 'agents' && <AgentsView />}
      {activeView === 'approval' && (
        <ApprovalQueueView
          artifacts={artifacts}
          onApprove={handleApprove}
          onReject={handleReject}
        />
      )}
      {activeView === 'memory' && <MemoryView />}
      {activeView === 'sources' && <DataSourcesView />}
    </DashboardLayout>
  );
}

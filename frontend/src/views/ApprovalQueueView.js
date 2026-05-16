import React from 'react';

export default function ApprovalQueueView({ artifacts = [], onApprove, onReject }) {
  const pending = artifacts.filter((a) => a.status === 'pending');
  const approved = artifacts.filter((a) => a.status === 'approved');
  const rejected = artifacts.filter((a) => a.status === 'rejected');

  return (
    <div className="flex-1 overflow-y-auto px-8 py-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-text-primary mb-1">Approval Queue</h1>
          <p className="text-sm text-text-secondary">Review and deploy agent-generated artifacts</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 mb-8">
          <div className="bg-bg-secondary border border-border rounded-xl p-4">
            <div className="text-2xl font-semibold text-amber-400">{pending.length}</div>
            <div className="text-xs text-text-secondary uppercase tracking-wider">Pending</div>
          </div>
          <div className="bg-bg-secondary border border-border rounded-xl p-4">
            <div className="text-2xl font-semibold text-green-400">{approved.length}</div>
            <div className="text-xs text-text-secondary uppercase tracking-wider">Approved</div>
          </div>
          <div className="bg-bg-secondary border border-border rounded-xl p-4">
            <div className="text-2xl font-semibold text-red-400">{rejected.length}</div>
            <div className="text-xs text-text-secondary uppercase tracking-wider">Rejected</div>
          </div>
        </div>

        {/* Pending list */}
        {pending.length === 0 ? (
          <div className="text-center py-16 text-text-muted">
            <div className="text-4xl mb-3">▤</div>
            <p className="text-sm mb-1">No pending approvals</p>
            <p className="text-xs">Use /publish or /campaign to create artifacts for review</p>
          </div>
        ) : (
          <div className="space-y-3">
            {pending.map((artifact) => (
              <div
                key={artifact.id}
                className="bg-bg-secondary border border-border rounded-xl overflow-hidden"
              >
                <div className="px-5 py-4 border-b border-border flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="px-2 py-0.5 bg-amber-500/20 text-amber-400 text-xs font-medium rounded uppercase tracking-wider">
                      {artifact.type?.replace(/_/g, ' ')}
                    </div>
                    <span className="text-text-primary font-medium text-sm">{artifact.title}</span>
                  </div>
                  <span className="text-xs text-text-muted">{artifact.created}</span>
                </div>
                {artifact.content && (
                  <div className="px-5 py-3 text-sm text-text-secondary line-clamp-3">
                    {artifact.content.substring(0, 200)}...
                  </div>
                )}
                <div className="px-5 py-3 bg-bg-primary/30 flex gap-2">
                  <button
                    onClick={() => onApprove(artifact.id)}
                    className="flex-1 py-2 bg-green-500 hover:bg-green-600 text-white text-sm font-medium rounded-lg transition"
                  >
                    ✓ Approve
                  </button>
                  <button
                    onClick={() => onReject(artifact.id)}
                    className="px-4 py-2 bg-bg-tertiary hover:bg-bg-hover border border-border text-text-secondary text-sm rounded-lg transition"
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

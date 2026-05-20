export default function ApprovalPage() {
  return (
    <div className="flex-1 overflow-y-auto px-8 py-8">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-2xl font-semibold mb-1">Approval Queue</h1>
        <p className="text-sm text-muted-foreground mb-8">
          Review and deploy agent-generated artifacts
        </p>
        <div className="text-center py-16 text-muted-foreground">
          <p className="text-sm">No pending approvals</p>
          <p className="text-xs mt-1">Use /blog or /audit to generate artifacts for review</p>
        </div>
      </div>
    </div>
  )
}

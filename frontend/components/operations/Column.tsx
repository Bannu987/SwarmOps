"use client"

interface ColumnProps {
  title: string
  badge?: string | number
  badgeColor?: string
  status?: { dot: string; label: string }
  children: React.ReactNode
  className?: string
}

export function Column({ title, badge, badgeColor, status, children, className = "" }: ColumnProps) {
  return (
    <div className={`flex flex-col h-full ${className}`}>
      <div className="px-4 py-3 flex items-center justify-between border-b border-border">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">
            {title}
          </span>
          {badge !== undefined && (
            <span
              className="text-[10px] font-mono"
              style={{ color: badgeColor || undefined }}
            >
              {badge}
            </span>
          )}
        </div>
        {status && (
          <div className="flex items-center gap-1.5">
            <div
              className="w-1.5 h-1.5 rounded-full animate-pulse"
              style={{ background: status.dot }}
            />
            <span className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
              {status.label}
            </span>
          </div>
        )}
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {children}
      </div>
    </div>
  )
}

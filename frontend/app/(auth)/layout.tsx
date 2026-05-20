import Link from "next/link"

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex">
      {/* Left side — form */}
      <div className="flex-1 flex flex-col px-6 py-8 lg:px-16">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary to-swarm-cyan flex items-center justify-center text-white text-sm font-bold">
            S
          </div>
          <span className="font-semibold">SwarmOps</span>
        </Link>

        <div className="flex-1 flex items-center justify-center">
          <div className="w-full max-w-sm">{children}</div>
        </div>
      </div>

      {/* Right side — brand */}
      <div className="hidden lg:flex flex-1 bg-gradient-to-br from-primary/20 via-background to-swarm-cyan/10 border-l border-border items-center justify-center p-16">
        <div className="max-w-md">
          <div className="text-xs font-semibold text-primary uppercase tracking-wider mb-3">
            What&apos;s inside
          </div>
          <h2 className="text-2xl font-bold mb-6">
            6 specialist agents.<br />
            One strategic mind.
          </h2>
          <div className="space-y-4 text-sm text-muted-foreground">
            <div className="flex gap-3">
              <span className="text-primary">→</span>
              <div>
                <strong className="text-foreground">Nexus orchestrates everything.</strong> One conversation, full marketing team output.
              </div>
            </div>
            <div className="flex gap-3">
              <span className="text-primary">→</span>
              <div>
                <strong className="text-foreground">Real frameworks.</strong> MECLABS, LIFT, RICE, AEO — not generic advice.
              </div>
            </div>
            <div className="flex gap-3">
              <span className="text-primary">→</span>
              <div>
                <strong className="text-foreground">Your data, your tools.</strong> Connect GA4, Search Console, HubSpot, Google Ads.
              </div>
            </div>
            <div className="flex gap-3">
              <span className="text-primary">→</span>
              <div>
                <strong className="text-foreground">Approval gates.</strong> Nothing publishes without your sign-off.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

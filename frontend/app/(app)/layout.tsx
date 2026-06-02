import { createClient } from "@/lib/supabase/server"
import { redirect } from "next/navigation"
import { Sidebar } from "@/components/sidebar/Sidebar"
import { AmbientBackground } from "@/components/shared/MotionPrimitives"

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    redirect("/login")
  }

  return (
    <div className="flex h-screen overflow-hidden relative">
      <AmbientBackground />
      <Sidebar user={user} />
      <main className="flex-1 flex flex-col overflow-hidden relative">{children}</main>
    </div>
  )
}

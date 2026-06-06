import { NextResponse } from "next/server"
import { createClient } from "@/lib/supabase/server"

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get("code")
  const next = searchParams.get("next") ?? "/dashboard"

  if (code) {
    const supabase = createClient()
    const { data, error } = await supabase.auth.exchangeCodeForSession(code)
    
    if (!error && data?.user) {
      const user = data.user
      try {
        // Idempotent profile check/upsert
        const { data: existingProfile, error: selectError } = await supabase
          .from("profiles")
          .select("id")
          .eq("id", user.id)
          .maybeSingle()

        if (selectError) {
          console.error("Error checking existing profile:", selectError)
        }

        if (!existingProfile) {
          const fullName = user.user_metadata?.full_name || user.user_metadata?.name || user.email?.split("@")[0] || "User"
          const avatarUrl = user.user_metadata?.avatar_url || null
          
          const { error: insertError } = await supabase.from("profiles").insert({
            id: user.id,
            email: user.email,
            full_name: fullName,
            avatar_url: avatarUrl,
            onboarding_complete: false
          })

          if (insertError) {
            console.error("Error inserting profile in callback:", insertError)
          }
        }
      } catch (profileErr) {
        // Fail-safe: log but do not block redirect
        console.error("Fail-safe profile check/creation error in auth callback:", profileErr)
      }

      return NextResponse.redirect(`${origin}${next}`)
    } else if (error) {
      console.error("Auth callback exchange error:", error)
      return NextResponse.redirect(`${origin}/login?error=${encodeURIComponent(error.message)}`)
    }
  }

  // return the user to an error page with instructions
  return NextResponse.redirect(`${origin}/login?error=Could not authenticate user`)
}

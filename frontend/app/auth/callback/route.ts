import { NextResponse, type NextRequest } from "next/server"
import { createServerClient } from "@supabase/ssr"

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get("code")
  const next = requestUrl.searchParams.get("next") ?? "/dashboard"

  // Construct absolute redirect URL respecting reverse proxies/load balancers (e.g., Vercel)
  const forwardedProto = request.headers.get("x-forwarded-proto") || "https"
  const forwardedHost = request.headers.get("x-forwarded-host") || requestUrl.host
  const origin = `${forwardedProto}://${forwardedHost}`

  if (code) {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

    // Create redirect response object first so we can attach session cookies to it
    const response = NextResponse.redirect(`${origin}${next}`)

    const supabase = createServerClient(
      supabaseUrl,
      supabaseAnonKey,
      {
        cookies: {
          getAll() {
            return request.cookies.getAll()
          },
          setAll(cookiesToSet) {
            cookiesToSet.forEach(({ name, value }) =>
              request.cookies.set(name, value)
            )
            cookiesToSet.forEach(({ name, value, options }) =>
              response.cookies.set(name, value, options)
            )
          },
        },
      }
    )

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

      return response
    } else if (error) {
      console.error("Auth callback exchange error:", error)
      return NextResponse.redirect(`${origin}/login?error=${encodeURIComponent(error.message)}`)
    }
  }

  // return the user to an error page with instructions
  return NextResponse.redirect(`${origin}/login?error=Could not authenticate user`)
}

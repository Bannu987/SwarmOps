import { createBrowserClient } from "@supabase/ssr"

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

if (process.env.NODE_ENV === "development") {
  if (!supabaseUrl) {
    console.error("Missing env variable: NEXT_PUBLIC_SUPABASE_URL")
  }
  if (!supabaseAnonKey) {
    console.error("Missing env variable: NEXT_PUBLIC_SUPABASE_ANON_KEY")
  }
}

export function createClient() {
  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error("Supabase client failed to initialize: Missing environment variables.")
  }
  return createBrowserClient(supabaseUrl, supabaseAnonKey)
}

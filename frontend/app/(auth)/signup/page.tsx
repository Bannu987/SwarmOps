"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/supabase/client"
import { Loader2, CheckCircle2 } from "lucide-react"

export default function SignupPage() {
  const router = useRouter()
  const supabase = createClient()
  const [fullName, setFullName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [resending, setResending] = useState(false)
  const [resendStatus, setResendStatus] = useState<string | null>(null)

  const handleResend = async () => {
    setResending(true)
    setResendStatus(null)
    const { error } = await supabase.auth.resend({
      type: "signup",
      email: email,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    })
    setResending(false)
    if (error) {
      setResendStatus(`Failed to resend: ${error.message}`)
    } else {
      setResendStatus("Confirmation email resent successfully!")
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (password.length < 6) {
      setError("Password must be at least 6 characters")
      return
    }

    setLoading(true)
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { full_name: fullName },
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    })

    if (error) {
      setError(error.message)
      setLoading(false)
      return
    }

    if (data.session) {
      router.push("/dashboard")
      router.refresh()
    } else {
      setSuccess(true)
      setLoading(false)
    }
  }

  const handleGoogle = async () => {
    setLoading(true)
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/dashboard` },
    })
    if (error) {
      setError(error.message)
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="text-center">
        <div className="w-12 h-12 mx-auto bg-primary/20 rounded-full flex items-center justify-center mb-4">
          <CheckCircle2 className="w-6 h-6 text-primary" />
        </div>
        <h2 className="text-xl font-semibold mb-2">Check your email</h2>
        <p className="text-sm text-muted-foreground mb-6">
          We sent a confirmation link to{" "}
          <strong className="text-foreground">{email}</strong>.
          Click it to activate your account.
        </p>
        <Link href="/login" className="text-sm text-primary hover:underline">
          Back to sign in
        </Link>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-1">Create your account</h1>
      <p className="text-sm text-muted-foreground mb-8">
        Get started in less than a minute
      </p>

      {error && (
        <div className="mb-4 p-3 bg-destructive/10 border border-destructive/30 rounded-lg text-sm text-destructive">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Full name</label>
          <input
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Your name"
            className="w-full px-3 py-2 bg-input border border-border rounded-lg text-foreground placeholder:text-muted-foreground text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition"
          />
        </div>

        <div>
          <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            className="w-full px-3 py-2 bg-input border border-border rounded-lg text-foreground placeholder:text-muted-foreground text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition"
          />
        </div>

        <div>
          <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Password</label>
          <input
            type="password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="At least 6 characters"
            className="w-full px-3 py-2 bg-input border border-border rounded-lg text-foreground placeholder:text-muted-foreground text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground font-medium rounded-lg text-sm transition disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Creating...</> : "Create account"}
        </button>
      </form>

      <div className="my-6 flex items-center gap-3">
        <div className="flex-1 h-px bg-border" />
        <span className="text-xs text-muted-foreground">OR</span>
        <div className="flex-1 h-px bg-border" />
      </div>

      <button
        onClick={handleGoogle}
        disabled={loading}
        className="w-full py-2.5 bg-card hover:bg-muted border border-border text-foreground font-medium rounded-lg text-sm transition flex items-center justify-center gap-2 disabled:opacity-50"
      >
        <svg className="w-4 h-4" viewBox="0 0 24 24">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
        </svg>
        Sign up with Google
      </button>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link href="/login" className="text-primary hover:underline font-medium">
          Sign in
        </Link>
      </p>
    </div>
  )
}

import type { Metadata } from "next"
import { Inter, Instrument_Serif } from "next/font/google"
import "./globals.css"

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
})

const instrumentSerif = Instrument_Serif({
  subsets: ["latin"],
  weight: ["400"],
  style: ["normal", "italic"],
  variable: "--font-serif",
  display: "swap",
})

export const metadata: Metadata = {
  title: "SwarmOps — Cinematic Multi-Agent Marketing Command Center",
  description:
    "SwarmOps is a luxury intelligence war room coordinating 6 specialist AI agents collaborating to scan, plan, and execute your brand's growth marketing strategy.",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} ${instrumentSerif.variable} font-sans bg-background text-foreground antialiased`}
      >
        {children}
      </body>
    </html>
  )
}


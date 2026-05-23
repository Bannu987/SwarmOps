export const SEVERITY_CONFIG = {
  critical: { color: "#EF4444", bg: "rgba(239,68,68,0.1)", border: "rgba(239,68,68,0.3)", label: "CRITICAL" },
  high:     { color: "#F97316", bg: "rgba(249,115,22,0.1)", border: "rgba(249,115,22,0.3)", label: "HIGH" },
  medium:   { color: "#FBBF24", bg: "rgba(251,191,36,0.1)", border: "rgba(251,191,36,0.3)", label: "MEDIUM" },
  low:      { color: "#71717A", bg: "rgba(113,113,122,0.1)", border: "rgba(113,113,122,0.2)", label: "LOW" },
} as const

export const CATEGORY_CONFIG = {
  risk:        { icon: "⚠", color: "#EF4444", label: "Risk" },
  opportunity: { icon: "↗", color: "#22C55E", label: "Opportunity" },
  market:      { icon: "◉", color: "#A1A1AA", label: "Market" },
  content:     { icon: "✦", color: "#A855F7", label: "Content" },
  seo:         { icon: "◎", color: "#22D3EE", label: "SEO" },
  analytics:   { icon: "▣", color: "#10B981", label: "Analytics" },
  cro:         { icon: "◑", color: "#22C55E", label: "CRO" },
  aeo:         { icon: "◯", color: "#FBBF24", label: "AEO" },
  strategic:   { icon: "◆", color: "#7B6EFB", label: "Strategic" },
} as const

export const IMPACT_CONFIG = {
  high:   { color: "#22C55E", label: "HIGH IMPACT" },
  medium: { color: "#FBBF24", label: "MED IMPACT" },
  low:    { color: "#71717A", label: "LOW IMPACT" },
} as const

export const EFFORT_CONFIG = {
  low:    { color: "#22C55E", label: "Low effort" },
  medium: { color: "#FBBF24", label: "Medium effort" },
  high:   { color: "#F97316", label: "High effort" },
} as const

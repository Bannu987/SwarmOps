export const SEVERITY_CONFIG = {
  critical: { color: "#d76f57", bg: "rgba(215,111,87,0.1)", border: "rgba(215,111,87,0.3)", label: "CRITICAL" },
  high:     { color: "#e8927d", bg: "rgba(232,146,125,0.08)", border: "rgba(232,146,125,0.25)", label: "HIGH" },
  medium:   { color: "#c5a880", bg: "rgba(197,168,128,0.1)", border: "rgba(197,168,128,0.25)", label: "MEDIUM" },
  low:      { color: "#8a857b", bg: "rgba(138,133,123,0.08)", border: "rgba(138,133,123,0.18)", label: "LOW" },
} as const

export const CATEGORY_CONFIG = {
  risk:        { icon: "⚠", color: "#d76f57", label: "Risk" },
  opportunity: { icon: "↗", color: "#c5a880", label: "Opportunity" },
  market:      { icon: "◉", color: "#8a857b", label: "Market" },
  content:     { icon: "✦", color: "#c5a880", label: "Content" },
  seo:         { icon: "◎", color: "#dfdacf", label: "SEO" },
  analytics:   { icon: "▣", color: "#8a857b", label: "Analytics" },
  cro:         { icon: "◑", color: "#c5a880", label: "CRO" },
  aeo:         { icon: "◯", color: "#dfdacf", label: "AEO" },
  strategic:   { icon: "◆", color: "#4a0c10", label: "Strategic" },
} as const

export const IMPACT_CONFIG = {
  high:   { color: "#c5a880", label: "HIGH IMPACT" },
  medium: { color: "#dfdacf", label: "MED IMPACT" },
  low:    { color: "#8a857b", label: "LOW IMPACT" },
} as const

export const EFFORT_CONFIG = {
  low:    { color: "#a3b899", label: "Low effort" },
  medium: { color: "#dfdacf", label: "Medium effort" },
  high:   { color: "#d76f57", label: "High effort" },
} as const


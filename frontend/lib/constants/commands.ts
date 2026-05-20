import type { SlashCommand } from "@/types"

export const SLASH_COMMANDS: SlashCommand[] = [
  { cmd: "/seo", desc: "Direct SEO analysis & keyword research", icon: "◎", category: "agent" },
  { cmd: "/content", desc: "Content strategy & copywriting", icon: "✦", category: "agent" },
  { cmd: "/analytics", desc: "Data analysis & metrics", icon: "▣", category: "agent" },
  { cmd: "/cro", desc: "Conversion optimization & A/B testing", icon: "◑", category: "agent" },
  { cmd: "/aeo", desc: "AI search optimization (ChatGPT, Perplexity)", icon: "◯", category: "agent" },
  { cmd: "/audit", desc: "Full marketing audit (all 5 agents)", icon: "◐", category: "action" },
  { cmd: "/keywords", desc: "Keyword research workflow", icon: "🔍", category: "action" },
  { cmd: "/blog", desc: "Generate blog post", icon: "📝", category: "action" },
  { cmd: "/funnel", desc: "Conversion funnel analysis", icon: "📊", category: "action" },
  { cmd: "/growth", desc: "Growth strategy roadmap", icon: "🚀", category: "action" },
]

export function filterCommands(query: string): SlashCommand[] {
  const q = query.toLowerCase().replace("/", "")
  if (!q) return SLASH_COMMANDS
  return SLASH_COMMANDS.filter(
    (c) =>
      c.cmd.slice(1).toLowerCase().includes(q) ||
      c.desc.toLowerCase().includes(q)
  )
}

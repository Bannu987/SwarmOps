"use client"

import React from "react"

// 1. Ambient Backgroundpersistent cinematic overlay
export function AmbientBackground() {
  return (
    <div className="fixed inset-0 pointer-events-none z-[-1] overflow-hidden bg-[#050305]">
      {/* Subtle Grain Overlay */}
      <div className="absolute inset-0 opacity-[0.015] bg-[radial-gradient(ellipse_at_center,rgba(255,255,255,0.15)_0,transparent_100%)]" />
      {/* Slow-pulsing Rich Oxblood Glow */}
      <div className="absolute top-[-10%] left-[20%] w-[60%] h-[50%] rounded-full bg-[radial-gradient(circle,rgba(74,12,16,0.15)_0,transparent_70%)] blur-[80px]" />
      {/* Slow-pulsing Warm Brass Glow */}
      <div className="absolute bottom-[-15%] right-[10%] w-[50%] h-[60%] rounded-full bg-[radial-gradient(circle,rgba(197,168,128,0.06)_0,transparent_75%)] blur-[100px]" />
      {/* Telemetry horizontal lines */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.18)_50%)] bg-[size:100%_4px] opacity-25" />
    </div>
  )
}

// 2. Reusable Animated Segmented Tabs
interface Tab {
  id: string
  label: string
}

interface AnimatedTabsProps {
  tabs: Tab[]
  activeTab: string
  onChange: (id: string) => void
  className?: string
  buttonClassName?: string
}

export function AnimatedTabs({ tabs, activeTab, onChange, className = "", buttonClassName = "" }: AnimatedTabsProps) {
  return (
    <div className={`flex bg-card/45 border border-border/40 p-1 rounded-lg gap-1 relative ${className}`}>
      {tabs.map((tab) => {
        const isActive = tab.id === activeTab
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={`relative rounded transition-all duration-300 z-10 ${
              buttonClassName || "px-4 py-1.5 text-[10px] font-mono uppercase tracking-wider"
            } ${
              isActive 
                ? "bg-primary text-primary-foreground shadow-sm font-semibold border border-primary/25" 
                : "text-muted-foreground hover:text-foreground hover:bg-card/50"
            }`}
          >
            {tab.label}
          </button>
        )
      })}
    </div>
  )
}

// 3. Right-Side Progressive Detail Rail Container
interface RevealPanelProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
  widthClass?: string
}

export function RevealPanel({ isOpen, onClose, title, children, widthClass = "w-96" }: RevealPanelProps) {
  if (!isOpen) return null
  return (
    <div className={`border-l border-border/50 bg-card/75 backdrop-blur-[5px] flex flex-col h-full flex-shrink-0 animate-slide-up shadow-xl ${widthClass}`}>
      <div className="p-4 border-b border-border/40 flex items-center justify-between bg-card/25">
        <h3 className="font-serif font-normal text-sm text-foreground">{title}</h3>
        <button
          onClick={onClose}
          className="text-muted-foreground hover:text-foreground text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 border border-border/60 rounded bg-card/65 transition hover:bg-card"
        >
          Close
        </button>
      </div>
      <div className="flex-grow overflow-y-auto p-5 space-y-4">
        {children}
      </div>
    </div>
  )
}

// 4. Cyber Scanline skeletons
export function ScanlineSkeleton() {
  return (
    <div className="w-full space-y-3.5 p-4.5 bg-card/45 border border-border/30 rounded-xl relative overflow-hidden">
      {/* Animated laser line */}
      <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-primary/50 to-transparent animate-[scan_2s_infinite_linear]" />
      <div className="h-3 w-1/3 bg-muted/40 rounded animate-pulse" />
      <div className="h-7 w-full bg-muted/30 rounded animate-pulse" />
      <div className="h-4 w-5/6 bg-muted/30 rounded animate-pulse" />
      
      <style jsx global>{`
        @keyframes scan {
          0% { transform: translateY(0); }
          100% { transform: translateY(120px); }
        }
      `}</style>
    </div>
  )
}

// 5. Breathing Status Pulse
interface StatusPulseProps {
  type: "success" | "warning" | "error" | "info"
  label?: string
}

export function StatusPulse({ type, label }: StatusPulseProps) {
  const colors = {
    success: { bg: "bg-[#a3b899]", text: "text-[#a3b899]", border: "border-[#a3b899]/20" },
    warning: { bg: "bg-[#c5a880]", text: "text-[#c5a880]", border: "border-[#c5a880]/20" },
    error: { bg: "bg-[#d76f57]", text: "text-[#d76f57]", border: "border-[#d76f57]/20" },
    info: { bg: "bg-[#dfdacf]", text: "text-[#dfdacf]", border: "border-[#dfdacf]/20" },
  }
  const c = colors[type]
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded border ${c.border} bg-card/20 text-[9px] font-mono uppercase tracking-wider ${c.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.bg} animate-pulse`} />
      <span>{label}</span>
    </span>
  )
}

// 6. Magnetic Hover Button
interface MagneticButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode
  variant?: "primary" | "secondary" | "outline"
}

export function MagneticButton({ children, variant = "outline", className = "", ...props }: MagneticButtonProps) {
  const classes = {
    primary: "bg-primary hover:bg-primary/95 text-primary-foreground border border-primary/20",
    secondary: "bg-[#a3b899]/10 border border-[#a3b899]/25 text-[#a3b899] hover:bg-[#a3b899]/20",
    outline: "bg-card/85 hover:bg-card border border-border/80 hover:border-primary/45 text-foreground",
  }
  return (
    <button
      className={`px-4 py-1.5 font-mono text-[10px] uppercase tracking-wider rounded transition-all duration-300 shadow-sm hover:scale-[1.01] active:scale-100 ${classes[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}

// 7. Radial circular progress ring
interface ProgressRingProps {
  percentage: number
  size?: number
  strokeWidth?: number
}

export function ProgressRing({ percentage, size = 34, strokeWidth = 3 }: ProgressRingProps) {
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (percentage / 100) * circumference
  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          stroke="rgba(255, 255, 255, 0.05)"
          fill="transparent"
          strokeWidth={strokeWidth}
          r={radius}
          cx={size / 2}
          cy={size / 2}
        />
        <circle
          stroke="var(--primary)"
          fill="transparent"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          r={radius}
          cx={size / 2}
          cy={size / 2}
          className="transition-all duration-500 ease-out"
        />
      </svg>
      <span className="absolute text-[8px] font-mono text-primary">{percentage}%</span>
    </div>
  )
}

// 8. Structured Command Module telemetry wrapper
interface CommandModuleProps {
  title: string
  subtitle?: string
  badge?: string
  children: React.ReactNode
  className?: string
}

export function CommandModule({ title, subtitle, badge, children, className = "" }: CommandModuleProps) {
  return (
    <div className={`bg-card/65 border border-border/40 rounded-xl shadow-sm overflow-hidden flex flex-col justify-between transition-all duration-300 ${className}`}>
      <div className="px-4 py-3 flex items-center justify-between border-b border-border/30 bg-card/15">
        <div>
          <span className="text-[10px] font-mono text-primary uppercase tracking-widest block leading-none">
            {title}
          </span>
          {subtitle && (
            <span className="text-[9px] text-muted-foreground/60 font-sans block mt-0.5 leading-none">
              {subtitle}
            </span>
          )}
        </div>
        {badge && (
          <span className="text-[9px] font-mono text-muted-foreground bg-muted/40 px-1.5 py-0.5 rounded border border-border/30">
            {badge}
          </span>
        )}
      </div>
      <div className="p-4 space-y-3 flex-grow">
        {children}
      </div>
    </div>
  )
}

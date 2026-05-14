'use client'

import HelpTooltip from '@/components/ui/help-tooltip'

interface TooltipFieldProps {
  children: React.ReactNode
  help: string
  label?: string
}

export function TooltipField({ children, help, label }: TooltipFieldProps) {
  return (
    <div className="relative group">
      {label && <span className="text-sm font-medium mb-1 block">{label}</span>}
      {children}
      <div className="absolute -right-2 top-0 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
        <HelpTooltip content={help} variant="highlight" />
      </div>
    </div>
  )
}

export function ContextualHelp({ items }: { items: { selector: string; content: string }[] }) {
  return (
    <div className="hidden">
      {items.map((item, idx) => (
        <div key={idx} data-tour-help={item.selector} data-content={item.content} />
      ))}
    </div>
  )
}

export function TourSpotlight({ id, title, description }: { id: string; title: string; description: string }) {
  return (
    <div data-tour-spotlight={id} className="hidden">
      <span data-title>{title}</span>
      <span data-description>{description}</span>
    </div>
  )
}
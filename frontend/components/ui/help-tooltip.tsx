'use client'

import { useState } from 'react'
import { HelpCircle, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface HelpTooltipProps {
  content: string
  title?: string
  variant?: 'default' | 'highlight'
  className?: string
}

export default function HelpTooltip({ content, title, variant = 'default', className }: HelpTooltipProps) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className={cn('relative inline-block', className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'p-1 rounded-lg transition-colors',
          variant === 'highlight' 
            ? 'bg-primary/10 text-primary hover:bg-primary/20' 
            : 'text-muted-foreground hover:text-foreground hover:bg-secondary'
        )}
        aria-label="Help"
      >
        <HelpCircle className="h-4 w-4" />
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute left-0 top-full mt-2 z-50 w-64 animate-scale-in origin-top-left">
            <div className="rounded-lg border border-border bg-card shadow-lg overflow-hidden">
              <div className="flex items-center justify-between p-3 border-b border-border">
                <span className="text-sm font-medium">{title || 'Help'}</span>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 rounded hover:bg-secondary transition-colors"
                >
                  <X className="h-3 w-3 text-muted-foreground" />
                </button>
              </div>
              <div className="p-3">
                <p className="text-sm text-muted-foreground leading-relaxed">{content}</p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
'use client'

import { useState, useRef, useEffect } from 'react'
import { HelpCircle, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface HelpTooltipProps {
  content: string
  title?: string
  variant?: 'default' | 'highlight'
  className?: string
  position?: 'top' | 'bottom' | 'left' | 'right'
}

export default function HelpTooltip({
  content,
  title,
  variant = 'default',
  className,
  position: preferredPosition = 'right',
}: HelpTooltipProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [actualPosition, setActualPosition] = useState<'top' | 'bottom' | 'left' | 'right'>('right')
  const triggerRef = useRef<HTMLButtonElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isOpen && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect()
      const viewportWidth = window.innerWidth
      const viewportHeight = window.innerHeight
      const tooltipWidth = 256
      const tooltipHeight = 150
      const padding = 8

      let pos: 'top' | 'bottom' | 'left' | 'right' = preferredPosition

      if (preferredPosition === 'right' && rect.right + tooltipWidth + padding > viewportWidth) {
        pos = 'left'
      } else if (preferredPosition === 'left' && rect.left - tooltipWidth - padding < 0) {
        pos = 'right'
      } else if (preferredPosition === 'bottom' && rect.bottom + tooltipHeight + padding > viewportHeight) {
        pos = 'top'
      } else if (preferredPosition === 'top' && rect.top - tooltipHeight - padding < 0) {
        pos = 'bottom'
      }

      setActualPosition(pos)
    }
  }, [isOpen, preferredPosition])

  const positionStyles = {
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    bottom: 'left-1/2 -translate-x-1/2 top-full mt-2',
    top: 'left-1/2 -translate-x-1/2 bottom-full mb-2',
  }

  return (
    <div className={cn('relative inline-block', className)}>
      <button
        ref={triggerRef}
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
          <div
            ref={tooltipRef}
            className={cn(
              'absolute z-50 w-64 animate-scale-in',
              positionStyles[actualPosition]
            )}
          >
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
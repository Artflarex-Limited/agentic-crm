'use client'

import { useEffect, useState, useRef, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SpotlightTourProps {
  targetSelector: string
  title: string
  description: string
  onNext?: () => void
  onSkip?: () => void
  nextLabel?: string
  skipLabel?: string
  children?: ReactNode
}

interface TargetRect {
  top: number
  left: number
  width: number
  height: number
}

export default function SpotlightTour({
  targetSelector,
  title,
  description,
  onNext,
  onSkip,
  nextLabel = 'Next',
  skipLabel = 'Skip Tour',
  children,
}: SpotlightTourProps) {
  const [mounted, setMounted] = useState(false)
  const [targetRect, setTargetRect] = useState<TargetRect | null>(null)
  const [tooltipPosition, setTooltipPosition] = useState<'bottom' | 'right' | 'left'>('bottom')
  const tooltipRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!targetSelector) return

    const updateTargetRect = () => {
      const el = document.querySelector(targetSelector) as HTMLElement
      if (el) {
        const rect = el.getBoundingClientRect()
        setTargetRect({
          top: rect.top,
          left: rect.left,
          width: rect.width,
          height: rect.height,
        })

        const viewportWidth = window.innerWidth
        const viewportHeight = window.innerHeight
        const tooltipWidth = 320
        const tooltipHeight = 200

        if (rect.right + tooltipWidth + 20 < viewportWidth) {
          setTooltipPosition('right')
        } else if (rect.left - tooltipWidth - 20 > 0) {
          setTooltipPosition('left')
        } else {
          setTooltipPosition('bottom')
        }
      }
    }

    updateTargetRect()
    window.addEventListener('scroll', updateTargetRect, true)
    window.addEventListener('resize', updateTargetRect)

    return () => {
      window.removeEventListener('scroll', updateTargetRect, true)
      window.removeEventListener('resize', updateTargetRect)
    }
  }, [targetSelector])

  if (!mounted || !targetRect) return null

  const padding = 8
  const spotlightStyle = {
    top: targetRect.top - padding,
    left: targetRect.left - padding,
    width: targetRect.width + padding * 2,
    height: targetRect.height + padding * 2,
  }

  const tooltipStyle = (() => {
    const base = { position: 'fixed' as const, zIndex: 9999 }
    switch (tooltipPosition) {
      case 'right':
        return { ...base, top: targetRect.top, left: targetRect.left + targetRect.width + padding + 8 }
      case 'left':
        return { ...base, top: targetRect.top, left: targetRect.left - 340 }
      case 'bottom':
      default:
        return {
          ...base,
          top: targetRect.top + targetRect.height + padding + 8,
          left: Math.max(16, Math.min(targetRect.left, window.innerWidth - 340)),
        }
    }
  })()

  return createPortal(
    <>
      <div
        className="fixed inset-0 z-[9998] bg-black/60 backdrop-blur-sm animate-fade-in"
        onClick={onSkip}
      />

      <div
        className="fixed z-[9999] rounded-xl border-2 border-primary animate-spotlight transition-all duration-300"
        style={spotlightStyle}
      />

      <div
        ref={tooltipRef}
        className="fixed z-[10000] w-80 animate-scale-in"
        style={tooltipStyle}
      >
        <div className="rounded-xl border border-border bg-card shadow-2xl overflow-hidden">
          <div className="flex items-center justify-between p-4 border-b border-border">
            <h3 className="font-semibold text-base">{title}</h3>
            <button
              onClick={onSkip}
              className="p-1.5 rounded-lg hover:bg-secondary transition-colors"
            >
              <X className="h-4 w-4 text-muted-foreground" />
            </button>
          </div>
          <div className="p-4">
            <p className="text-sm text-muted-foreground leading-relaxed mb-4">
              {description}
            </p>
            {children}
          </div>
          <div className="flex items-center justify-between p-4 border-t border-border bg-secondary/30">
            <button
              onClick={onSkip}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              {skipLabel}
            </button>
            {onNext && (
              <button
                onClick={onNext}
                className={cn(
                  'px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium',
                  'hover:bg-primary/90 transition-colors'
                )}
              >
                {nextLabel}
              </button>
            )}
          </div>
        </div>
      </div>
    </>,
    document.body
  )
}
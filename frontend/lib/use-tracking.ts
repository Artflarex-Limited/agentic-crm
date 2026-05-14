'use client'

import { useEffect, useRef } from 'react'
import { trackBlogEngage, trackSearchAbandon, getStoredUTM, type BlogEngageTrigger } from '@/lib/tracking'

interface UseBlogEngageTrackerOptions {
  enabled?: boolean
}

export function useBlogEngageTracker({ enabled = true }: UseBlogEngageTrackerOptions = {}) {
  const hasTracked = useRef(false)
  const pagePath = typeof window !== 'undefined' ? window.location.pathname : ''

  useEffect(() => {
    if (!enabled || hasTracked.current) return

    let triggered = false

    const track = (trigger: BlogEngageTrigger) => {
      if (triggered) return
      triggered = true
      hasTracked.current = true
      trackBlogEngage(trigger, pagePath, getStoredUTM())
    }

    const scrollHandler = () => {
      const scrollTop = window.scrollY
      const docHeight = document.documentElement.scrollHeight
      const windowHeight = window.innerHeight
      if (scrollTop / (docHeight - windowHeight) > 0.75) {
        track('scroll_75')
      }
    }

    const timeTimer = setTimeout(() => {
      track('time_2min')
    }, 120000)

    const shareHandler = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      if (
        target.closest('a[href*="twitter"]') ||
        target.closest('a[href*="facebook"]') ||
        target.closest('a[href*="linkedin"]') ||
        target.closest('[class*="share"]')
      ) {
        track('social_share')
      }
    }

    window.addEventListener('scroll', scrollHandler, { passive: true })
    window.addEventListener('click', shareHandler)
    return () => {
      clearTimeout(timeTimer)
      window.removeEventListener('scroll', scrollHandler)
      window.removeEventListener('click', shareHandler)
    }
  }, [enabled, pagePath])
}

interface UseSearchAbandonOptions {
  searchQueryGetter: () => string
  enabled?: boolean
}

export function useSearchAbandon({ searchQueryGetter, enabled = true }: UseSearchAbandonOptions) {
  const hasTracked = useRef(false)

  return {
    trackAbandon: () => {
      if (!enabled || hasTracked.current) return
      const query = searchQueryGetter()
      if (!query) return
      hasTracked.current = true
      trackSearchAbandon(query, getStoredUTM())
    },
  }
}
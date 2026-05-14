'use client'

import { useEffect, useState, type ReactNode } from 'react'
import {
  captureUTMParams,
  getStoredUTM,
  initGA4,
  initHubSpot,
  trackPageView,
} from '@/lib/tracking'

interface ProvidersProps {
  children: ReactNode
  ga4MeasurementId?: string
  hubspotPortalId?: string
}

export function Providers({ children, ga4MeasurementId, hubspotPortalId }: ProvidersProps) {
  const [utm, setUtm] = useState<ReturnType<typeof getStoredUTM>>({})

  useEffect(() => {
    const captured = captureUTMParams()
    if (Object.values(captured).some(Boolean)) {
      setUtm(captured)
    } else {
      setUtm(getStoredUTM())
    }

    if (ga4MeasurementId) {
      initGA4(ga4MeasurementId)
    }
    if (hubspotPortalId) {
      initHubSpot(hubspotPortalId)
    }
  }, [ga4MeasurementId, hubspotPortalId])

  useEffect(() => {
    if (typeof window === 'undefined') return

    const handleTrackPageView = () => {
      trackPageView(window.location.pathname, document.title)
    }

    handleTrackPageView()

    window.addEventListener('popstate', handleTrackPageView)
    const originalPushState = history.pushState
    const originalReplaceState = history.replaceState

    history.pushState = function (...args) {
      originalPushState.apply(history, args)
      handleTrackPageView()
    }
    history.replaceState = function (...args) {
      originalReplaceState.apply(history, args)
      handleTrackPageView()
    }

    return () => {
      window.removeEventListener('popstate', handleTrackPageView)
      history.pushState = originalPushState
      history.replaceState = originalReplaceState
    }
  }, [])

  return <>{children}</>
}

export { getStoredUTM }
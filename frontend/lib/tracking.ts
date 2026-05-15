'use client'

declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void
    gtag_report_conversion?: (url?: string) => void
    dataLayer?: unknown[]
    hsConversationsSettings?: {
      loadImmediately: boolean
    }
    ConversationsWidget?: {
      initialize: () => void
    }
    google_track_conversion?: (conversionId: string, conversionLabel?: string) => void
    fbq?: (...args: unknown[]) => void
  }
}

export interface UTMParams {
  utm_source?: string
  utm_medium?: string
  utm_campaign?: string
  utm_term?: string
  utm_content?: string
}

const UTM_STORAGE_KEY = 'agentic_crm_utm'

export function captureUTMParams(): UTMParams {
  if (typeof window === 'undefined') return {}

  const params = new URLSearchParams(window.location.search)
  const utm: UTMParams = {
    utm_source: params.get('utm_source') || undefined,
    utm_medium: params.get('utm_medium') || undefined,
    utm_campaign: params.get('utm_campaign') || undefined,
    utm_term: params.get('utm_term') || undefined,
    utm_content: params.get('utm_content') || undefined,
  }

  if (Object.values(utm).some(Boolean)) {
    try {
      sessionStorage.setItem(UTM_STORAGE_KEY, JSON.stringify(utm))
    } catch {
      // sessionStorage not available
    }
  }

  return utm
}

export function getStoredUTM(): UTMParams {
  if (typeof window === 'undefined') return {}

  try {
    const stored = sessionStorage.getItem(UTM_STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored) as UTMParams
    }
  } catch {
    // ignore parse errors
  }
  return {}
}

export function clearStoredUTM(): void {
  if (typeof window === 'undefined') return
  try {
    sessionStorage.removeItem(UTM_STORAGE_KEY)
  } catch {
    // ignore
  }
}

export function initGA4(measurementId?: string): void {
  if (typeof window === 'undefined' || !measurementId) return

  const gtagScript = document.createElement('script')
  gtagScript.async = true
  gtagScript.src = `https://www.googletagmanager.com/gtag/js?id=${measurementId}`
  document.head.appendChild(gtagScript)

  window.dataLayer = window.dataLayer || []
  window.gtag = function gtag(...args: unknown[]) {
    window.dataLayer!.push(args)
  }
  window.gtag('js', new Date())
  window.gtag('config', measurementId, {
    send_page_view: true,
    page_title: document.title,
    user_id: undefined,
  })
}

export function initMetaPixel(pixelId?: string): void {
  if (typeof window === 'undefined' || !pixelId) return

  window.fbq = window.fbq || function (...args: unknown[]) {
    const c = window.fbq as ((...args: unknown[]) => void) | undefined
    if (typeof c === 'function') {
      c(...args)
    }
  }

  const script = document.createElement('script')
  script.async = true
  script.src = 'https://connect.facebook.net/en_US/fbevents.js'
  document.head.appendChild(script)

  window.fbq('init', pixelId)
  window.fbq('track', 'PageView')
}

export function trackMetaPageView(): void {
  if (typeof window === 'undefined' || !window.fbq) return
  window.fbq('track', 'PageView')
}

export function trackPageView(path: string, title?: string): void {
  if (typeof window === 'undefined' || !window.gtag) return
  window.gtag('event', 'page_view', {
    page_path: path,
    page_title: title || document.title,
    page_location: window.location.href,
  })
}

export function trackEvent(
  action: string,
  category: string,
  label?: string,
  value?: number,
  extra?: Record<string, unknown>
): void {
  if (typeof window === 'undefined' || !window.gtag) return
  window.gtag('event', action, {
    event_category: category,
    event_label: label,
    value: value,
    ...extra,
  })
}

export function trackLeadCreated(leadData: { source: string; stage: string; score: number; utm?: UTMParams }): void {
  trackEvent('lead_created', 'engagement', leadData.source, leadData.score, {
    lead_stage: leadData.stage,
    ...leadData.utm,
  })
}

export function trackDealStageChange(dealId: number, fromStage: string, toStage: string, dealValue?: number): void {
  trackEvent('deal_stage_changed', 'pipeline', `${fromStage} → ${toStage}`, dealValue, {
    deal_id: dealId,
    from_stage: fromStage,
    to_stage: toStage,
  })
}

export function trackAgentAction(agentId: number, agentRole: string, action: string): void {
  trackEvent('agent_action', 'agents', action, undefined, {
    agent_id: agentId,
    agent_role: agentRole,
  })
}

export function trackFormSubmission(formName: string, success: boolean): void {
  trackEvent(success ? 'form_submit_success' : 'form_submit_failure', 'conversion', formName)
}

export function trackRFQGenerated(utm?: UTMParams): void {
  trackEvent('generate_rfq', 'conversion', undefined, undefined, {
    event_category: 'engagement',
    ...utm,
  })

  if (typeof window !== 'undefined' && window.gtag) {
    const conversionId = process.env.NEXT_PUBLIC_GOOGLE_ADS_CONVERSION_ID
    const conversionLabel = process.env.NEXT_PUBLIC_GOOGLE_ADS_CONVERSION_LABEL_RFQ
    if (conversionId && conversionLabel) {
      window.gtag('event', 'conversion', {
        send_to: `${conversionId}/${conversionLabel}`,
      })
      if (window.gtag_report_conversion) {
        window.gtag_report_conversion()
      }
    }
  }
}

export function trackGoogleAdsConversion(conversionId: string, conversionLabel: string): void {
  if (typeof window !== 'undefined' && window.gtag_report_conversion) {
    window.gtag_report_conversion()
  }
}

export function trackSearchAbandon(query: string, utm?: UTMParams): void {
  trackEvent('search_abandon', 'engagement', query, undefined, {
    search_query: query,
    ...utm,
  })
}

export type BlogEngageTrigger = 'scroll_75' | 'time_2min' | 'social_share'

export function trackBlogEngage(trigger: BlogEngageTrigger, pagePath: string, utm?: UTMParams): void {
  trackEvent('blog_engage', 'engagement', trigger, undefined, {
    blog_page_path: pagePath,
    engage_trigger: trigger,
    ...utm,
  })
}

export function initHubSpot(hubspotId?: string): void {
  if (typeof window === 'undefined' || !hubspotId) return

  const script = document.createElement('script')
  script.type = 'text/javascript'
  script.id = 'hs-script-loader'
  script.async = true
  script.defer = true
  script.src = `//js.hs-scripts.com/${hubspotId}.js`
  document.head.appendChild(script)
}

export function loadHubSpotConversations(): void {
  if (typeof window === 'undefined') return

  if (window.ConversationsWidget) {
    window.ConversationsWidget.initialize()
    return
  }

  const checkAndLoad = setInterval(() => {
    if (window.ConversationsWidget) {
      window.ConversationsWidget.initialize()
      clearInterval(checkAndLoad)
    }
  }, 100)

  setTimeout(() => clearInterval(checkAndLoad), 10000)
}

export function identifyHubSpotContact(email: string, properties?: Record<string, string>): void {
  if (typeof window === 'undefined') return
  const w = window as Window & typeof globalThis & { _hsq?: unknown[] }
  if (!w._hsq) w._hsq = []

  w._hsq.push(['identify', {
    email,
    ...properties,
  }])
}
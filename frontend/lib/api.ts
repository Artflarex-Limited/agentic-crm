const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export type AgentRole = 'lead_sourcing' | 'research' | 'outreach' | 'follow_up' | 'qualification' | 'reporting'
export type AgentStatus = 'active' | 'paused' | 'stopped'
export type LeadSource = 'linkedin' | 'email' | 'web' | 'phone' | 'cold_outreach' | 'referral' | 'other'
export type LeadStage = 'new' | 'contacted' | 'qualified' | 'proposal' | 'negotiation' | 'won' | 'lost'
export type DealStage = 'lead' | 'qualified' | 'proposal' | 'negotiation' | 'won' | 'lost'
export type ActivityType = 'email_sent' | 'email_opened' | 'email_replied' | 'linkedin_message' | 'linkedin_connection' | 'call_made' | 'call_received' | 'note_added' | 'meeting_scheduled' | 'stage_changed' | 'agent_action'

export interface Contact {
  id: number
  company_id?: number
  first_name?: string
  last_name?: string
  email?: string
  phone?: string
  title?: string
  linkedin_url?: string
  extra_data: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface Company {
  id: number
  name: string
  domain?: string
  industry?: string
  size?: string
  linkedin_url?: string
  extra_data: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface Lead {
  id: number
  contact_id: number
  source: LeadSource
  stage: LeadStage
  score: number
  tags: string[]
  notes?: string
  assigned_agent_id?: number
  last_contacted_at?: string
  created_at: string
  updated_at: string
  contact?: Contact
}

export interface Deal {
  id: number
  contact_id: number
  company_id?: number
  name: string
  value: number
  stage: DealStage
  expected_close_date?: string
  actual_close_date?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface Agent {
  id: number
  name: string
  role: AgentRole
  status: AgentStatus
  config: Record<string, unknown>
  description?: string
  created_at: string
  updated_at: string
}

export interface Activity {
  id: number
  lead_id?: number
  contact_id?: number
  deal_id?: number
  agent_id?: number
  type: ActivityType
  content?: string
  metadata: Record<string, unknown>
  created_at: string
}

export interface SequenceStep {
  type: string
  subject?: string
  content: string
  delay_days: number
}

export interface Sequence {
  id: number
  name: string
  description?: string
  steps: SequenceStep[]
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface PipelineItem {
  id: number
  name: string
  contact_name: string
  company_name?: string
  value: number
  stage: DealStage
  expected_close_date?: string
}

export interface ConversionMetrics {
  lead_to_contacted_rate: number
  contacted_to_qualified_rate: number
  qualified_to_proposal_rate: number
  proposal_to_negotiation_rate: number
  negotiation_to_won_rate: number
  overall_conversion_rate: number
}

export interface RevenueForecast {
  projected_revenue_30_days: number
  projected_revenue_60_days: number
  projected_revenue_90_days: number
  weighted_pipeline_value: number
  forecast_confidence: number
}

export interface SourceEffectiveness {
  source: string
  total_leads: number
  conversion_rate: number
  avg_deal_value: number
  revenue: number
}

export interface AgentPerformanceMetric {
  agent_id: number
  agent_name: string
  actions_today: number
  actions_this_week: number
  success_rate: number
  avg_response_time_minutes: number
}

export interface MarketIntelligenceDashboard {
  conversion_metrics: ConversionMetrics
  revenue_forecast: RevenueForecast
  source_effectiveness: SourceEffectiveness[]
  agent_performance: AgentPerformanceMetric[]
  period_days: number
}

export interface PricingTrend {
  date: string
  avg_price: number
  min_price: number
  max_price: number
  volume: number
  moving_avg_7d: number | null
  moving_avg_30d: number | null
}

export interface DemandForecast {
  date: string
  predicted_demand: number
  confidence_lower: number
  confidence_upper: number
  trend: 'increasing' | 'decreasing' | 'stable'
}

export interface CompetitorAggregate {
  competitor_name: string
  avg_price: number
  price_range_min: number
  price_range_max: number
  market_share_estimate: number
  last_updated: string
}

export interface PriceAlert {
  alert_id: string
  alert_type: 'price_spike' | 'price_drop' | 'demand_anomaly' | 'competitor_movement'
  severity: 'low' | 'medium' | 'high' | 'critical'
  message: string
  affected_category: string | null
  detected_value: number
  threshold_value: number
  detected_at: string
}

export interface MarketIntelligenceResponse {
  pricing_trends: PricingTrend[]
  demand_forecast: DemandForecast[]
  competitor_aggregates: CompetitorAggregate[]
  active_alerts: PriceAlert[]
  last_refreshed: string
  cache_ttl_seconds: number
}

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export const api = {
  dashboard: {
    stats: () => fetchApi<{ total_leads: number; total_contacts: number; total_deals: number; open_deals_value: number; leads_by_stage: Record<string, number>; deals_by_stage: Record<string, number>; recent_activities: Activity[] }>('/api/dashboard/stats'),
    pipeline: () => fetchApi<{ items: PipelineItem[] }>('/api/dashboard/pipeline'),
    marketIntelligence: (period_days?: number) => fetchApi<MarketIntelligenceDashboard>(`/api/dashboard/market-intelligence${period_days ? `?period_days=${period_days}` : ''}`),
  },
  leads: {
    list: (params?: { stage?: LeadStage; source?: LeadSource; search?: string }) => {
      const searchParams = new URLSearchParams()
      if (params?.stage) searchParams.set('stage', params.stage)
      if (params?.source) searchParams.set('source', params.source)
      if (params?.search) searchParams.set('search', params.search)
      const query = searchParams.toString()
      return fetchApi<Lead[]>(`/api/leads${query ? `?${query}` : ''}`)
    },
    get: (id: number) => fetchApi<Lead>(`/api/leads/${id}`),
    create: (data: Partial<Lead>) => fetchApi<Lead>('/api/leads', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Partial<Lead>) => fetchApi<Lead>(`/api/leads/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
    delete: (id: number) => fetchApi<void>(`/api/leads/${id}`, { method: 'DELETE' }),
  },
  contacts: {
    list: (params?: { search?: string }) => fetchApi<Contact[]>(`/api/contacts${params?.search ? `?search=${params.search}` : ''}`),
    get: (id: number) => fetchApi<Contact>(`/api/contacts/${id}`),
    create: (data: Partial<Contact>) => fetchApi<Contact>('/api/contacts', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Partial<Contact>) => fetchApi<Contact>(`/api/contacts/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  },
  companies: {
    list: () => fetchApi<Company[]>('/api/companies'),
    get: (id: number) => fetchApi<Company>(`/api/companies/${id}`),
    create: (data: Partial<Company>) => fetchApi<Company>('/api/companies', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Partial<Company>) => fetchApi<Company>(`/api/companies/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  },
  deals: {
    list: (params?: { stage?: DealStage }) => {
      const query = params?.stage ? `?stage=${params.stage}` : ''
      return fetchApi<Deal[]>(`/api/deals${query}`)
    },
    get: (id: number) => fetchApi<Deal>(`/api/deals/${id}`),
    create: (data: Partial<Deal>) => fetchApi<Deal>('/api/deals', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Partial<Deal>) => fetchApi<Deal>(`/api/deals/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
    delete: (id: number) => fetchApi<void>(`/api/deals/${id}`, { method: 'DELETE' }),
  },
  agents: {
    list: () => fetchApi<Agent[]>('/api/agents'),
    get: (id: number) => fetchApi<Agent>(`/api/agents/${id}`),
    create: (data: Partial<Agent>) => fetchApi<Agent>('/api/agents', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Partial<Agent>) => fetchApi<Agent>(`/api/agents/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
    setStatus: (id: number, status: AgentStatus) => fetchApi<Agent>(`/api/agents/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) }),
  },
  activities: {
    list: (params?: { lead_id?: number; contact_id?: number; limit?: number }) => {
      const searchParams = new URLSearchParams()
      if (params?.lead_id) searchParams.set('lead_id', String(params.lead_id))
      if (params?.contact_id) searchParams.set('contact_id', String(params.contact_id))
      if (params?.limit) searchParams.set('limit', String(params.limit))
      const query = searchParams.toString()
      return fetchApi<Activity[]>(`/api/activities${query ? `?${query}` : ''}`)
    },
    create: (data: Partial<Activity>) => fetchApi<Activity>('/api/activities', { method: 'POST', body: JSON.stringify(data) }),
  },
  sequences: {
    list: () => fetchApi<Sequence[]>('/api/sequences'),
    get: (id: number) => fetchApi<Sequence>(`/api/sequences/${id}`),
    create: (data: Partial<Sequence>) => fetchApi<Sequence>('/api/sequences', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Partial<Sequence>) => fetchApi<Sequence>(`/api/sequences/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  },
  market: {
    intelligence: (params?: { category?: string; country?: string; include_forecast?: boolean }) => {
      const searchParams = new URLSearchParams()
      if (params?.category) searchParams.set('category', params.category)
      if (params?.country) searchParams.set('country', params.country)
      if (params?.include_forecast !== undefined) searchParams.set('include_forecast', String(params.include_forecast))
      const query = searchParams.toString()
      return fetchApi<MarketIntelligenceResponse>(`/api/market/intelligence${query ? `?${query}` : ''}`)
    },
  },
}
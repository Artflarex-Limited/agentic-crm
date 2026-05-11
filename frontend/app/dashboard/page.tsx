'use client'

import { useEffect, useState } from 'react'
import { api, type Deal, type DealStage, type Activity } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DollarSign, Users, Target, TrendingUp } from 'lucide-react'

const STAGES: { key: DealStage; label: string; color: string }[] = [
  { key: 'lead', label: 'Lead', color: 'bg-blue-100 text-blue-800' },
  { key: 'qualified', label: 'Qualified', color: 'bg-yellow-100 text-yellow-800' },
  { key: 'proposal', label: 'Proposal', color: 'bg-orange-100 text-orange-800' },
  { key: 'negotiation', label: 'Negotiation', color: 'bg-purple-100 text-purple-800' },
  { key: 'won', label: 'Won', color: 'bg-green-100 text-green-800' },
  { key: 'lost', label: 'Lost', color: 'bg-red-100 text-red-800' },
]

interface PipelineData {
  items: Deal[]
}

export default function DashboardPage() {
  const [pipeline, setPipeline] = useState<Deal[]>([])
  const [stats, setStats] = useState({ total_leads: 0, total_contacts: 0, total_deals: 0, open_deals_value: 0, leads_by_stage: {} as Record<string, number>, deals_by_stage: {} as Record<string, number>, recent_activities: [] as Activity[] })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [pipelineData, statsData] = await Promise.all([
          api.dashboard.pipeline(),
          api.dashboard.stats(),
        ])
        setPipeline(pipelineData.items)
        setStats(statsData)
      } catch (e) {
        console.error('Failed to load dashboard', e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const dealsByStage = STAGES.map(stage => ({
    ...stage,
    deals: pipeline.filter(d => d.stage === stage.key),
    total: pipeline.filter(d => d.stage === stage.key).reduce((sum, d) => sum + d.value, 0),
  }))

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Leads</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_leads}</div>
            <p className="text-xs text-muted-foreground">Across all stages</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Contacts</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_contacts}</div>
            <p className="text-xs text-muted-foreground">In database</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Deals</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_deals}</div>
            <p className="text-xs text-muted-foreground">Pipeline deals</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Open Deals Value</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${stats.open_deals_value.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">Potential revenue</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Pipeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-6 gap-4 overflow-x-auto">
            {dealsByStage.map(stage => (
              <div key={stage.key} className="min-w-[180px]">
                <div className="mb-2 flex items-center justify-between">
                  <span className="font-medium text-sm">{stage.label}</span>
                  <Badge variant="secondary" className="text-xs">{stage.deals.length}</Badge>
                </div>
                <div className="space-y-2">
                  {stage.deals.map(deal => (
                    <div key={deal.id} className="rounded-lg border p-3 text-sm">
                      <div className="font-medium truncate">{deal.name}</div>
                      <div className="text-xs text-muted-foreground mt-1">
                        ${deal.value.toLocaleString()}
                      </div>
                      {deal.expected_close_date && (
                        <div className="text-xs text-muted-foreground">
                          Close: {new Date(deal.expected_close_date).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                  ))}
                  {stage.deals.length === 0 && (
                    <div className="text-xs text-muted-foreground text-center py-4">No deals</div>
                  )}
                </div>
                <div className="mt-2 text-xs font-medium text-right">
                  ${stage.total.toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
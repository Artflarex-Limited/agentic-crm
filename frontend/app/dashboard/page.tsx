'use client'

import { useEffect, useState } from 'react'
import { api, type Deal, type DealStage, type Activity, type Agent, type PipelineItem } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { PipelineChart, StatCard, ConversionFunnel, VelocityMetric } from '@/components/analytics'
import { DollarSign, Users, Target, TrendingUp, Activity as ActivityIcon, Bot, ArrowUpRight, ArrowDownRight } from 'lucide-react'

const STAGES: { key: DealStage; label: string; color: string; borderColor: string }[] = [
  { key: 'lead', label: 'Lead', color: 'text-blue-400 bg-blue-400/10', borderColor: 'border-blue-400/30' },
  { key: 'qualified', label: 'Qualified', color: 'text-yellow-400 bg-yellow-400/10', borderColor: 'border-yellow-400/30' },
  { key: 'proposal', label: 'Proposal', color: 'text-orange-400 bg-orange-400/10', borderColor: 'border-orange-400/30' },
  { key: 'negotiation', label: 'Negotiation', color: 'text-purple-400 bg-purple-400/10', borderColor: 'border-purple-400/30' },
  { key: 'won', label: 'Won', color: 'text-emerald-400 bg-emerald-400/10', borderColor: 'border-emerald-400/30' },
  { key: 'lost', label: 'Lost', color: 'text-red-400 bg-red-400/10', borderColor: 'border-red-400/30' },
]

const activityIcons: Record<string, typeof ActivityIcon> = {
  email_sent: ActivityIcon,
  agent_action: Bot,
  stage_changed: ArrowUpRight,
}

interface DashboardStats {
  total_leads: number
  total_contacts: number
  total_deals: number
  open_deals_value: number
  leads_by_stage: Record<string, number>
  deals_by_stage: Record<string, number>
  recent_activities: Activity[]
}

interface PipelineData {
  items: PipelineItem[]
}

export default function DashboardPage() {
  const [pipeline, setPipeline] = useState<PipelineItem[]>([])
  const [stats, setStats] = useState<DashboardStats>({
    total_leads: 0,
    total_contacts: 0,
    total_deals: 0,
    open_deals_value: 0,
    leads_by_stage: {},
    deals_by_stage: {},
    recent_activities: [],
  })
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [pipelineResponse, statsData, agentsData] = await Promise.all([
          api.dashboard.pipeline(),
          api.dashboard.stats(),
          api.agents.list(),
        ])
        setPipeline((pipelineResponse as PipelineData).items)
        setStats(statsData)
        setAgents(agentsData)
      } catch (e) {
        console.error('Failed to load dashboard', e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const dealsByStage: Record<string, number> = {}
  const dealsValueByStage: Record<string, number> = {}

  STAGES.forEach(stage => {
    const stageDeals = pipeline.filter(d => d.stage === stage.key)
    dealsByStage[stage.key] = stageDeals.length
    dealsValueByStage[stage.key] = stageDeals.reduce((sum, d) => sum + d.value, 0)
  })

  const activeAgents = agents.filter(a => a.status === 'active').length

  const conversionStages = [
    { label: 'Lead', count: stats.leads_by_stage['new'] || 0, value: 0 },
    { label: 'Qualified', count: stats.leads_by_stage['qualified'] || 0, value: 0 },
    { label: 'Proposal', count: stats.leads_by_stage['proposal'] || 0, value: 0 },
    { label: 'Negotiation', count: stats.leads_by_stage['negotiation'] || 0, value: 0 },
    { label: 'Won', count: stats.deals_by_stage['won'] || 0, value: 0 },
  ]

  const avgDealValue = stats.total_deals > 0 ? Math.round(stats.open_deals_value / stats.total_deals) : 0
  const conversionRate = stats.total_leads > 0 ? Math.round(((stats.deals_by_stage['won'] || 0) / stats.total_leads) * 100) : 0

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid gap-4 md:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="skeleton h-32" />
          ))}
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="skeleton h-64" />
          <Card className="skeleton h-64" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in" data-tour="dashboard">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground mt-1">Mission control for your AI sales team</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400"></span>
          </span>
          Live updates
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <StatCard
          title="Total Leads"
          value={stats.total_leads}
          icon={Users}
          trend={{ value: 12, label: 'from last month' }}
          colorClass="text-blue-400"
          bgColorClass="bg-blue-500/10"
        />
        <StatCard
          title="Open Deals Value"
          value={`$${stats.open_deals_value.toLocaleString()}`}
          icon={DollarSign}
          trend={{ value: 8, label: 'from last month' }}
          subValue={`${stats.total_deals} total deals`}
          colorClass="text-emerald-400"
          bgColorClass="bg-emerald-500/10"
        />
        <StatCard
          title="Won This Month"
          value={stats.deals_by_stage['won'] || 0}
          icon={Target}
          trend={{ value: 15, label: 'vs last month' }}
          colorClass="text-purple-400"
          bgColorClass="bg-purple-500/10"
        />
        <StatCard
          title="Active Agents"
          value={activeAgents}
          icon={Bot}
          subValue="All systems operational"
          colorClass="text-primary"
          bgColorClass="bg-primary/10"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <PipelineChart dealsByStage={dealsByStage} dealsValueByStage={dealsValueByStage} />

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                Deal Velocity Metrics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 md:grid-cols-2">
                <VelocityMetric
                  label="Avg Deal Value"
                  value={`$${avgDealValue.toLocaleString()}`}
                  subValue="Per won deal"
                  trend={5}
                  icon={DollarSign}
                />
                <VelocityMetric
                  label="Conversion Rate"
                  value={`${conversionRate}%`}
                  subValue="Lead to Won"
                  trend={-2}
                  icon={Target}
                />
                <VelocityMetric
                  label="Pipeline Value"
                  value={`$${stats.open_deals_value.toLocaleString()}`}
                  subValue="Across all open deals"
                  icon={TrendingUp}
                />
                <VelocityMetric
                  label="Active Agents"
                  value={String(activeAgents)}
                  subValue={`${agents.length} total configured`}
                  icon={Bot}
                />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <ConversionFunnel stages={conversionStages} />

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-base">
                <Bot className="h-4 w-4 text-primary" />
                Agent Status
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {agents.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">No agents yet</p>
              ) : (
                agents.slice(0, 4).map(agent => (
                  <div key={agent.id} className="flex items-center justify-between p-3 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors">
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        agent.status === 'active' ? 'bg-emerald-500/20' :
                        agent.status === 'paused' ? 'bg-amber-500/20' : 'bg-red-500/20'
                      }`}>
                        <Bot className={`h-4 w-4 ${
                          agent.status === 'active' ? 'text-emerald-400' :
                          agent.status === 'paused' ? 'text-amber-400' : 'text-red-400'
                        }`} />
                      </div>
                      <div>
                        <p className="text-sm font-medium">{agent.name}</p>
                        <p className="text-xs text-muted-foreground font-mono">{agent.role.replace('_', ' ')}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${
                        agent.status === 'active' ? 'bg-emerald-400 animate-pulse' :
                        agent.status === 'paused' ? 'bg-amber-400' : 'bg-red-400'
                      }`} />
                      <span className="text-xs text-muted-foreground capitalize">{agent.status}</span>
                    </div>
                  </div>
                ))
              )}
              <Button variant="outline" className="w-full mt-2" size="sm" asChild>
                <a href="/agents">View all agents</a>
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-base">
                <ActivityIcon className="h-4 w-4 text-primary" />
                Recent Activity
              </CardTitle>
            </CardHeader>
            <CardContent>
              {stats.recent_activities.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">No recent activity</p>
              ) : (
                <div className="space-y-4">
                  {stats.recent_activities.slice(0, 5).map((activity, idx) => {
                    const Icon = activityIcons[activity.type] || ActivityIcon
                    return (
                      <div key={activity.id} className="flex gap-3 group">
                        <div className="flex flex-col items-center">
                          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                            <Icon className="h-4 w-4 text-primary" />
                          </div>
                          {idx < stats.recent_activities.slice(0, 5).length - 1 && (
                            <div className="w-px h-full bg-border mt-2" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm leading-tight">{activity.content || `${activity.type.replace('_', ' ')} performed`}</p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {new Date(activity.created_at).toLocaleString('en-US', {
                              month: 'short',
                              day: 'numeric',
                              hour: 'numeric',
                              minute: '2-digit'
                            })}
                          </p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
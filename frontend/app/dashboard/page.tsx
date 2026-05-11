'use client'

import { useEffect, useState } from 'react'
import { api, type Deal, type DealStage, type Activity, type Agent } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
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

export default function DashboardPage() {
  const [pipeline, setPipeline] = useState<Deal[]>([])
  const [stats, setStats] = useState({ total_leads: 0, total_contacts: 0, total_deals: 0, open_deals_value: 0, leads_by_stage: {} as Record<string, number>, deals_by_stage: {} as Record<string, number>, recent_activities: [] as Activity[] })
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
        const allDeals = Object.values(pipelineResponse as Record<string, Deal[]>).flat()
        setPipeline(allDeals)
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

  const dealsByStage = STAGES.map(stage => ({
    ...stage,
    deals: pipeline.filter(d => d.stage === stage.key),
    total: pipeline.filter(d => d.stage === stage.key).reduce((sum, d) => sum + d.value, 0),
  }))

  const activeAgents = agents.filter(a => a.status === 'active').length

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid gap-4 md:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="skeleton h-32" />
          ))}
        </div>
        <Card className="skeleton h-96" />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground mt-1">Mission control for your AI sales team</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-success"></span>
          </span>
          Live updates
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card className="group hover:border-primary/50 transition-all duration-300 hover:shadow-lg hover:shadow-primary/5">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Leads</CardTitle>
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center group-hover:bg-blue-500/20 transition-colors">
              <Users className="h-5 w-5 text-blue-400" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats.total_leads}</div>
            <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
              <ArrowUpRight className="h-3 w-3 text-emerald-400" />
              <span className="text-emerald-400">+12%</span> from last month
            </p>
          </CardContent>
        </Card>
        <Card className="group hover:border-primary/50 transition-all duration-300 hover:shadow-lg hover:shadow-primary/5">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Open Deals Value</CardTitle>
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center group-hover:bg-emerald-500/20 transition-colors">
              <DollarSign className="h-5 w-5 text-emerald-400" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">${stats.open_deals_value.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
              <ArrowUpRight className="h-3 w-3 text-emerald-400" />
              <span className="text-emerald-400">+8%</span> from last month
            </p>
          </CardContent>
        </Card>
        <Card className="group hover:border-primary/50 transition-all duration-300 hover:shadow-lg hover:shadow-primary/5">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Deals</CardTitle>
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center group-hover:bg-purple-500/20 transition-colors">
              <Target className="h-5 w-5 text-purple-400" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats.total_deals}</div>
            <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
              <ArrowUpRight className="h-3 w-3 text-emerald-400" />
              <span className="text-emerald-400">+5</span> new this week
            </p>
          </CardContent>
        </Card>
        <Card className="group hover:border-primary/50 transition-all duration-300 hover:shadow-lg hover:shadow-primary/5">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Active Agents</CardTitle>
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
              <Bot className="h-5 w-5 text-primary" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{activeAgents}</div>
            <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-success"></span>
              </span>
              All systems operational
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                Pipeline
              </CardTitle>
              <Badge variant="secondary" className="font-mono text-xs">{pipeline.length} deals</Badge>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-thin">
                {dealsByStage.map((stage, idx) => (
                  <div 
                    key={stage.key} 
                    className={`min-w-[200px] flex-1 rounded-xl border ${stage.borderColor} bg-secondary/30 p-4 transition-all hover:bg-secondary/50 stagger-${idx + 1}`}
                    style={{ animationDelay: `${idx * 50}ms` }}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${stage.color.split(' ')[1]}`} />
                        <span className="font-medium text-sm">{stage.label}</span>
                      </div>
                      <Badge variant="secondary" className="font-mono text-xs">{stage.deals.length}</Badge>
                    </div>
                    <div className="space-y-2 min-h-[200px]">
                      {stage.deals.slice(0, 4).map(deal => (
                        <div 
                          key={deal.id} 
                          className="rounded-lg border border-border bg-card p-3 hover:border-primary/30 transition-all cursor-pointer group"
                        >
                          <div className="font-medium text-sm group-hover:text-primary transition-colors truncate">
                            {deal.name}
                          </div>
                          <div className="flex items-center justify-between mt-2">
                            <span className="text-sm font-mono text-emerald-400">${deal.value.toLocaleString()}</span>
                            {deal.expected_close_date && (
                              <span className="text-xs text-muted-foreground">
                                {new Date(deal.expected_close_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                      {stage.deals.length === 0 && (
                        <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                          <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center mb-2">
                            <span className="text-lg">-</span>
                          </div>
                          <span className="text-xs">No deals</span>
                        </div>
                      )}
                      {stage.deals.length > 4 && (
                        <div className="text-xs text-muted-foreground text-center py-2">
                          +{stage.deals.length - 4} more
                        </div>
                      )}
                    </div>
                    <div className="mt-4 pt-4 border-t border-border flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">Total</span>
                      <span className="text-sm font-mono font-medium text-foreground">${stage.total.toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
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
              <Button variant="outline" className="w-full mt-2" size="sm">
                View all agents
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
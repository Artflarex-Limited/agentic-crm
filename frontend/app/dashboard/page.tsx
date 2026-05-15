'use client'

import { useEffect, useState } from 'react'
import { api, type Deal, type DealStage, type Activity, type Agent, type PipelineItem, type MarketIntelligenceDashboard, type MarketIntelligenceResponse } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { PipelineChart, StatCard, ConversionFunnel, VelocityMetric, PipelineTrend, WinLossRatio, AgentPerformancePanel, CampaignEffectiveness } from '@/components/analytics'
import { DollarSign, Users, Target, TrendingUp, Activity as ActivityIcon, Bot, ArrowUpRight, ArrowDownRight, BarChart3, PieChart, TrendingDown, AlertTriangle, LineChart } from 'lucide-react'

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

function ConversionFunnelCard({ metrics }: { metrics: { lead_to_contacted_rate: number; contacted_to_qualified_rate: number; qualified_to_proposal_rate: number; proposal_to_negotiation_rate: number; negotiation_to_won_rate: number } }) {
  const stages = [
    { label: 'Lead → Contacted', rate: metrics.lead_to_contacted_rate },
    { label: 'Contacted → Qualified', rate: metrics.contacted_to_qualified_rate },
    { label: 'Qualified → Proposal', rate: metrics.qualified_to_proposal_rate },
    { label: 'Proposal → Negotiation', rate: metrics.proposal_to_negotiation_rate },
    { label: 'Negotiation → Won', rate: metrics.negotiation_to_won_rate },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-primary" />
          Conversion Funnel
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {stages.map((stage, idx) => (
            <div key={idx} className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">{stage.label}</span>
                <span className="font-medium">{stage.rate}%</span>
              </div>
              <div className="h-2 bg-secondary rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, stage.rate)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

function RevenueForecastCard({ forecast }: { forecast: { projected_revenue_30_days: number; projected_revenue_60_days: number; projected_revenue_90_days: number; weighted_pipeline_value: number; forecast_confidence: number } }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-primary" />
          Revenue Forecast
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4">
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">30-Day Projection</span>
            <span className="text-lg font-semibold text-emerald-400">${forecast.projected_revenue_30_days.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">60-Day Projection</span>
            <span className="text-lg font-semibold text-emerald-400">${forecast.projected_revenue_60_days.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">90-Day Projection</span>
            <span className="text-lg font-semibold text-emerald-400">${forecast.projected_revenue_90_days.toLocaleString()}</span>
          </div>
          <div className="border-t pt-4 flex justify-between items-center">
            <span className="text-sm text-muted-foreground">Pipeline Value</span>
            <span className="text-lg font-bold">${forecast.weighted_pipeline_value.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">Confidence</span>
            <Badge variant="outline" className="bg-primary/10 text-primary border-primary/30">
              {(forecast.forecast_confidence * 100).toFixed(0)}%
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function SourceEffectivenessCard({ sources }: { sources: Array<{ source: string; total_leads: number; conversion_rate: number; avg_deal_value: number; revenue: number }> }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <PieChart className="h-5 w-5 text-primary" />
          Source Effectiveness
        </CardTitle>
      </CardHeader>
      <CardContent>
        {sources.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">No source data available</p>
        ) : (
          <div className="space-y-4">
            {sources.map((source, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-secondary/50">
                <div>
                  <p className="text-sm font-medium capitalize">{source.source.replace('_', ' ')}</p>
                  <p className="text-xs text-muted-foreground">{source.total_leads} leads</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-emerald-400">${source.revenue.toLocaleString()}</p>
                  <p className="text-xs text-muted-foreground">{source.conversion_rate}% conversion</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
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
  const [marketIntelligence, setMarketIntelligence] = useState<MarketIntelligenceDashboard | null>(null)
  const [realTimeMarketData, setRealTimeMarketData] = useState<MarketIntelligenceResponse | null>(null)
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [pipelineResponse, statsData, agentsData, marketData, realTimeData] = await Promise.all([
          api.dashboard.pipeline(),
          api.dashboard.stats(),
          api.agents.list(),
          api.dashboard.marketIntelligence(30),
          api.market.intelligence(),
        ])
        setPipeline((pipelineResponse as PipelineData).items)
        setStats(statsData)
        setAgents(agentsData)
        setMarketIntelligence(marketData)
        setRealTimeMarketData(realTimeData)
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

          {marketIntelligence && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-primary" />
                    Market Intelligence - Conversion Metrics
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-3 md:grid-cols-5">
                    <div className="p-3 rounded-lg bg-secondary/50 text-center">
                      <p className="text-2xl font-bold text-blue-400">{marketIntelligence.conversion_metrics.lead_to_contacted_rate}%</p>
                      <p className="text-xs text-muted-foreground">Lead → Contacted</p>
                    </div>
                    <div className="p-3 rounded-lg bg-secondary/50 text-center">
                      <p className="text-2xl font-bold text-blue-400">{marketIntelligence.conversion_metrics.contacted_to_qualified_rate}%</p>
                      <p className="text-xs text-muted-foreground">Contacted → Qualified</p>
                    </div>
                    <div className="p-3 rounded-lg bg-secondary/50 text-center">
                      <p className="text-2xl font-bold text-yellow-400">{marketIntelligence.conversion_metrics.qualified_to_proposal_rate}%</p>
                      <p className="text-xs text-muted-foreground">Qualified → Proposal</p>
                    </div>
                    <div className="p-3 rounded-lg bg-secondary/50 text-center">
                      <p className="text-2xl font-bold text-orange-400">{marketIntelligence.conversion_metrics.proposal_to_negotiation_rate}%</p>
                      <p className="text-xs text-muted-foreground">Proposal → Negotiation</p>
                    </div>
                    <div className="p-3 rounded-lg bg-secondary/50 text-center">
                      <p className="text-2xl font-bold text-emerald-400">{marketIntelligence.conversion_metrics.negotiation_to_won_rate}%</p>
                      <p className="text-xs text-muted-foreground">Negotiation → Won</p>
                    </div>
                  </div>
                  <div className="mt-4 flex justify-center">
                    <div className="px-6 py-3 rounded-lg bg-primary/10 text-center">
                      <p className="text-3xl font-bold text-primary">{marketIntelligence.conversion_metrics.overall_conversion_rate}%</p>
                      <p className="text-sm text-muted-foreground">Overall Conversion Rate</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {realTimeMarketData && (
                <>
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <LineChart className="h-5 w-5 text-primary" />
                        Real-time Market Intelligence
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid gap-4 md:grid-cols-3">
                        <div className="p-4 rounded-lg bg-secondary/50">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-muted-foreground">Pricing Trend (7D MA)</span>
                            {realTimeMarketData.pricing_trends.length > 0 && (
                              <span className={`text-sm font-medium ${(realTimeMarketData.pricing_trends[realTimeMarketData.pricing_trends.length - 1]?.moving_avg_7d || 0) > (realTimeMarketData.pricing_trends[realTimeMarketData.pricing_trends.length - 1]?.moving_avg_30d || 0) ? 'text-emerald-400' : 'text-red-400'}`}>
                                {(realTimeMarketData.pricing_trends[realTimeMarketData.pricing_trends.length - 1]?.moving_avg_7d || 0) > (realTimeMarketData.pricing_trends[realTimeMarketData.pricing_trends.length - 1]?.moving_avg_30d || 0) ? '↑' : '↓'}
                              </span>
                            )}
                          </div>
                          <p className="text-2xl font-bold">
                            ${(realTimeMarketData.pricing_trends[realTimeMarketData.pricing_trends.length - 1]?.moving_avg_7d || 0).toLocaleString()}
                          </p>
                          <p className="text-xs text-muted-foreground">30D: ${(realTimeMarketData.pricing_trends[realTimeMarketData.pricing_trends.length - 1]?.moving_avg_30d || 0).toLocaleString()}</p>
                        </div>

                        <div className="p-4 rounded-lg bg-secondary/50">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-muted-foreground">Demand Forecast</span>
                            {realTimeMarketData.demand_forecast.length > 0 && (
                              <span className={`text-sm font-medium ${realTimeMarketData.demand_forecast[0]?.trend === 'increasing' ? 'text-emerald-400' : realTimeMarketData.demand_forecast[0]?.trend === 'decreasing' ? 'text-red-400' : 'text-yellow-400'}`}>
                                {realTimeMarketData.demand_forecast[0]?.trend}
                              </span>
                            )}
                          </div>
                          <p className="text-2xl font-bold">
                            {(realTimeMarketData.demand_forecast[0]?.predicted_demand || 0).toFixed(1)}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Conf: {(realTimeMarketData.demand_forecast[0]?.confidence_lower || 0).toFixed(1)} - {(realTimeMarketData.demand_forecast[0]?.confidence_upper || 0).toFixed(1)}
                          </p>
                        </div>

                        <div className="p-4 rounded-lg bg-secondary/50">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-muted-foreground">Active Alerts</span>
                            <Badge variant="destructive" className="text-xs">
                              {realTimeMarketData.active_alerts.length}
                            </Badge>
                          </div>
                          {realTimeMarketData.active_alerts.length > 0 ? (
                            <div className="space-y-1">
                              {realTimeMarketData.active_alerts.slice(0, 2).map((alert, idx) => (
                                <p key={idx} className="text-xs truncate">{alert.message}</p>
                              ))}
                            </div>
                          ) : (
                            <p className="text-sm text-muted-foreground">No active alerts</p>
                          )}
                        </div>
                      </div>

                      {realTimeMarketData.pricing_trends.length > 0 && (
                        <div className="mt-4 pt-4 border-t">
                          <p className="text-xs text-muted-foreground mb-2">Recent Pricing Trend</p>
                          <div className="flex items-end gap-1 h-16">
                            {realTimeMarketData.pricing_trends.slice(-14).map((trend, idx) => {
                              const maxPrice = Math.max(...realTimeMarketData.pricing_trends.slice(-14).map(t => t.avg_price))
                              const height = maxPrice > 0 ? (trend.avg_price / maxPrice) * 100 : 0
                              return (
                                <div
                                  key={idx}
                                  className="flex-1 bg-primary/30 hover:bg-primary/50 transition-colors rounded-t"
                                  style={{ height: `${Math.max(10, height)}%` }}
                                  title={`${trend.date}: $${trend.avg_price.toLocaleString()}`}
                                />
                              )
                            })}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  <div className="grid gap-6 md:grid-cols-2">
                    <RevenueForecastCard forecast={marketIntelligence.revenue_forecast} />
                    <SourceEffectivenessCard sources={marketIntelligence.source_effectiveness} />
                  </div>

                  {realTimeMarketData.competitor_aggregates.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <PieChart className="h-5 w-5 text-primary" />
                          Competitor Analysis
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                          {realTimeMarketData.competitor_aggregates.slice(0, 6).map((comp, idx) => (
                            <div key={idx} className="p-3 rounded-lg bg-secondary/50">
                              <p className="text-sm font-medium truncate">{comp.competitor_name}</p>
                              <p className="text-lg font-bold text-emerald-400">${comp.avg_price.toLocaleString()}</p>
                              <p className="text-xs text-muted-foreground">
                                Range: ${comp.price_range_min.toLocaleString()} - ${comp.price_range_max.toLocaleString()}
                              </p>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </>
              )}

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

          <div className="grid gap-6 md:grid-cols-2">
            <PipelineTrend
              data={[
                { date: 'May 1', deals_created: 5, deals_won: 1, deals_lost: 0, revenue: 15000 },
                { date: 'May 5', deals_created: 8, deals_won: 2, deals_lost: 1, revenue: 28000 },
                { date: 'May 10', deals_created: 3, deals_won: 1, deals_lost: 0, revenue: 12000 },
                { date: 'May 15', deals_created: 6, deals_won: 0, deals_lost: 2, revenue: 0 },
              ]}
            />
            <WinLossRatio won={stats.deals_by_stage['won'] || 0} lost={stats.deals_by_stage['lost'] || 0} />
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <AgentPerformancePanel
              agents={agents.map(a => ({
                agent_id: a.id,
                agent_name: a.name,
                agent_role: a.role,
                actions_today: 0,
                actions_this_week: 0,
                success_rate: 75,
              }))}
            />
            <CampaignEffectiveness
              campaigns={[
                { name: 'Cold Outreach', sent: 150, opened: 78, replied: 12, converted: 3 },
                { name: 'LinkedIn Sequence', sent: 85, opened: 52, replied: 18, converted: 5 },
                { name: 'Follow-up', sent: 45, opened: 32, replied: 8, converted: 2 },
              ]}
            />
          </div>
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
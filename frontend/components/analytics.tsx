'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LineChart, Line } from 'recharts'
import { TrendingUp, TrendingDown, Minus, DollarSign, Users, Target, Bot, ArrowUpRight, ArrowDownRight, Activity as ActivityIcon } from 'lucide-react'

const STAGE_COLORS: Record<string, string> = {
  lead: '#60a5fa',
  qualified: '#facc15',
  proposal: '#fb923c',
  negotiation: '#a78bfa',
  won: '#34d399',
  lost: '#f87171',
}

interface PipelineChartProps {
  dealsByStage: Record<string, number>
  dealsValueByStage: Record<string, number>
}

export function PipelineChart({ dealsByStage, dealsValueByStage }: PipelineChartProps) {
  const data = Object.entries(dealsByStage).map(([stage, count]) => ({
    stage: stage.charAt(0).toUpperCase() + stage.slice(1),
    count,
    value: dealsValueByStage[stage] || 0,
    color: STAGE_COLORS[stage] || '#6b7280',
  }))

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-primary" />
          Pipeline Overview
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[200px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" margin={{ left: 20, right: 20 }}>
              <XAxis type="number" tickFormatter={(v) => `${v}`} />
              <YAxis dataKey="stage" type="category" width={80} tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={(value: number, name: string) => [
                  name === 'value' ? `$${value.toLocaleString()}` : value,
                  name === 'value' ? 'Value' : 'Deals',
                ]}
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
              />
              <Bar dataKey="count" radius={[4, 4, 4, 4]} maxBarSize={30}>
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}

interface StatCardProps {
  title: string
  value: string | number
  icon: React.ElementType
  trend?: { value: number; label: string }
  subValue?: string
  colorClass: string
  bgColorClass: string
}

export function StatCard({ title, value, icon: Icon, trend, subValue, colorClass, bgColorClass }: StatCardProps) {
  const trendValue = trend?.value ?? 0
  const TrendIcon = trendValue > 0 ? ArrowUpRight : trendValue < 0 ? ArrowDownRight : Minus
  const trendColorClass = trendValue > 0 ? 'text-emerald-400' : trendValue < 0 ? 'text-red-400' : 'text-muted-foreground'

  return (
    <Card className="group hover:border-primary/50 transition-all duration-300 hover:shadow-lg hover:shadow-primary/5">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <div className={`w-10 h-10 rounded-xl ${bgColorClass} flex items-center justify-center group-hover:scale-105 transition-transform`}>
          <Icon className={`h-5 w-5 ${colorClass}`} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold">{value}</div>
        {subValue && (
          <p className="text-xs text-muted-foreground mt-1">{subValue}</p>
        )}
        {trend && (
          <p className={`text-xs mt-1 flex items-center gap-1 ${trendColorClass}`}>
            <TrendIcon className="h-3 w-3" />
            <span>{trendValue > 0 ? '+' : ''}{trendValue}%</span>
            <span className="text-muted-foreground">{trend.label}</span>
          </p>
        )}
      </CardContent>
    </Card>
  )
}

interface ConversionFunnelProps {
  stages: { label: string; count: number; value: number }[]
}

export function ConversionFunnel({ stages }: ConversionFunnelProps) {
  const maxCount = Math.max(...stages.map(s => s.count), 1)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="h-5 w-5 text-primary" />
          Lead Conversion Funnel
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {stages.map((stage, idx) => {
            const widthPercent = (stage.count / maxCount) * 100
            const dropOff = idx > 0 ? Math.round(((stages[idx - 1].count - stage.count) / stages[idx - 1].count) * 100) : 0

            return (
              <div key={stage.label} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">{stage.label}</span>
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-medium">{stage.count}</span>
                    <span className="text-xs text-muted-foreground">${stage.value.toLocaleString()}</span>
                    {dropOff > 0 && (
                      <span className="text-xs text-red-400">-{dropOff}%</span>
                    )}
                  </div>
                </div>
                <div className="h-2 bg-secondary rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${widthPercent}%`,
                      backgroundColor: STAGE_COLORS[stage.label.toLowerCase()] || '#6b7280',
                    }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

interface VelocityMetricProps {
  label: string
  value: string
  subValue?: string
  trend?: number
  icon: React.ElementType
}

export function VelocityMetric({ label, value, subValue, trend, icon: Icon }: VelocityMetricProps) {
  const trendVal = trend ?? 0
  const trendColorClass = trendVal > 0 ? 'text-emerald-400' : trendVal < 0 ? 'text-red-400' : 'text-muted-foreground'
  const TrendIcon = trendVal > 0 ? ArrowUpRight : trendVal < 0 ? ArrowDownRight : Minus

  return (
    <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/30 hover:bg-secondary/50 transition-colors">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
          <Icon className="h-4 w-4 text-primary" />
        </div>
        <div>
          <p className="text-sm font-medium">{label}</p>
          {subValue && <p className="text-xs text-muted-foreground">{subValue}</p>}
        </div>
      </div>
      <div className="text-right">
        <p className="text-lg font-bold font-mono">{value}</p>
        {trend !== undefined && (
          <p className={`text-xs flex items-center justify-end gap-1 ${trendColorClass}`}>
            <TrendIcon className="h-3 w-3" />
            {trend > 0 ? '+' : ''}{trend}%
          </p>
        )}
      </div>
    </div>
  )
}

interface TimeSeriesDataPoint {
  date: string
  deals_created: number
  deals_won: number
  deals_lost: number
  revenue: number
}

interface PipelineTrendProps {
  data: TimeSeriesDataPoint[]
}

export function PipelineTrend({ data }: PipelineTrendProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-primary" />
          Pipeline Trend
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[200px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ left: 20, right: 20 }}>
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(value: number, name: string) => [
                  name === 'revenue' ? `$${value.toLocaleString()}` : value,
                  name === 'revenue' ? 'Revenue' : name.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase()),
                ]}
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
              />
              <Bar dataKey="deals_won" name="deals_won" fill="#34d399" radius={[4, 4, 0, 0]} maxBarSize={20} />
              <Bar dataKey="deals_created" name="deals_created" fill="#60a5fa" radius={[4, 4, 0, 0]} maxBarSize={20} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}

interface WinLossRatioProps {
  won: number
  lost: number
}

export function WinLossRatio({ won, lost }: WinLossRatioProps) {
  const total = won + lost
  const wonPercent = total > 0 ? Math.round((won / total) * 100) : 0
  const lostPercent = total > 0 ? Math.round((lost / total) * 100) : 0

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="h-5 w-5 text-primary" />
          Win/Loss Ratio
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="text-center">
            <p className="text-3xl font-bold text-emerald-400">{won}</p>
            <p className="text-xs text-muted-foreground">Won</p>
          </div>
          <div className="flex-1 mx-4">
            <div className="h-4 bg-secondary rounded-full overflow-hidden flex">
              <div className="bg-emerald-400 transition-all" style={{ width: `${wonPercent}%` }} />
              <div className="bg-red-400 transition-all" style={{ width: `${lostPercent}%` }} />
            </div>
          </div>
          <div className="text-center">
            <p className="text-3xl font-bold text-red-400">{lost}</p>
            <p className="text-xs text-muted-foreground">Lost</p>
          </div>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-emerald-400 font-medium">{wonPercent}% win rate</span>
          <span className="text-red-400 font-medium">{lostPercent}% loss rate</span>
        </div>
      </CardContent>
    </Card>
  )
}

interface AgentPerformance {
  agent_id: number
  agent_name: string
  agent_role: string
  actions_today: number
  actions_this_week: number
  success_rate: number
}

interface AgentPerformancePanelProps {
  agents: AgentPerformance[]
}

export function AgentPerformancePanel({ agents }: AgentPerformancePanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-primary" />
          Agent Performance
        </CardTitle>
      </CardHeader>
      <CardContent>
        {agents.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">No agent data available</p>
        ) : (
          <div className="space-y-3">
            {agents.map(agent => (
              <div key={agent.agent_id} className="flex items-center justify-between p-3 rounded-lg bg-secondary/30 hover:bg-secondary/50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <Bot className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{agent.agent_name}</p>
                    <p className="text-xs text-muted-foreground font-mono">{agent.agent_role.replace('_', ' ')}</p>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-center">
                    <p className="text-lg font-bold font-mono">{agent.actions_today}</p>
                    <p className="text-xs text-muted-foreground">Today</p>
                  </div>
                  <div className="text-center">
                    <p className="text-lg font-bold font-mono">{agent.actions_this_week}</p>
                    <p className="text-xs text-muted-foreground">This Week</p>
                  </div>
                  <div className="text-center">
                    <p className={`text-lg font-bold font-mono ${agent.success_rate >= 80 ? 'text-emerald-400' : agent.success_rate >= 50 ? 'text-yellow-400' : 'text-red-400'}`}>
                      {agent.success_rate}%
                    </p>
                    <p className="text-xs text-muted-foreground">Success</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

interface CampaignMetric {
  name: string
  sent: number
  opened: number
  replied: number
  converted: number
}

interface CampaignEffectivenessProps {
  campaigns: CampaignMetric[]
}

export function CampaignEffectiveness({ campaigns }: CampaignEffectivenessProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ActivityIcon className="h-5 w-5 text-primary" />
          Outreach Effectiveness
        </CardTitle>
      </CardHeader>
      <CardContent>
        {campaigns.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">No campaign data available</p>
        ) : (
          <div className="space-y-3">
            {campaigns.map((campaign, idx) => {
              const openRate = campaign.sent > 0 ? Math.round((campaign.opened / campaign.sent) * 100) : 0
              const replyRate = campaign.sent > 0 ? Math.round((campaign.replied / campaign.sent) * 100) : 0
              const convRate = campaign.sent > 0 ? Math.round((campaign.converted / campaign.sent) * 100) : 0

              return (
                <div key={idx} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{campaign.name}</span>
                    <span className="text-xs text-muted-foreground font-mono">{campaign.sent} sent</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="bg-blue-500/10 rounded p-2 text-center">
                      <p className="text-sm font-bold text-blue-400">{openRate}%</p>
                      <p className="text-xs text-muted-foreground">Open</p>
                    </div>
                    <div className="bg-emerald-500/10 rounded p-2 text-center">
                      <p className="text-sm font-bold text-emerald-400">{replyRate}%</p>
                      <p className="text-xs text-muted-foreground">Reply</p>
                    </div>
                    <div className="bg-purple-500/10 rounded p-2 text-center">
                      <p className="text-sm font-bold text-purple-400">{convRate}%</p>
                      <p className="text-xs text-muted-foreground">Convert</p>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { TrendingUp, TrendingDown, Minus, DollarSign, Users, Target, Bot, ArrowUpRight, ArrowDownRight } from 'lucide-react'

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
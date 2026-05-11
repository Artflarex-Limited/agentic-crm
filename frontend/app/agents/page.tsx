'use client'

import { useEffect, useState } from 'react'
import { api, type Agent, type AgentStatus, type Activity } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Play, Pause, Square, Bot, Clock, CheckCircle, AlertCircle, Activity as ActivityIcon, ChevronDown } from 'lucide-react'

const roleLabels: Record<string, string> = {
  lead_sourcing: 'Lead Sourcing',
  research: 'Research',
  outreach: 'Outreach',
  follow_up: 'Follow-up',
  qualification: 'Qualification',
  reporting: 'Reporting',
}

const roleColors: Record<string, string> = {
  lead_sourcing: 'bg-blue-500/10 text-blue-400',
  research: 'bg-purple-500/10 text-purple-400',
  outreach: 'bg-emerald-500/10 text-emerald-400',
  follow_up: 'bg-amber-500/10 text-amber-400',
  qualification: 'bg-pink-500/10 text-pink-400',
  reporting: 'bg-cyan-500/10 text-cyan-400',
}

const statusConfig: Record<AgentStatus, { color: string; bgColor: string; label: string }> = {
  active: { color: 'text-emerald-400', bgColor: 'bg-emerald-500/10', label: 'Active' },
  paused: { color: 'text-amber-400', bgColor: 'bg-amber-500/10', label: 'Paused' },
  stopped: { color: 'text-red-400', bgColor: 'bg-red-500/10', label: 'Stopped' },
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [activities, setActivities] = useState<Activity[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedAgent, setExpandedAgent] = useState<number | null>(null)
  const [approvalQueue, setApprovalQueue] = useState<{ id: number; message: string; agent: string; timestamp: string }[]>([
    { id: 1, message: 'Approve outreach to John Smith at Acme Corp', agent: 'Outreach Agent', timestamp: new Date().toISOString() },
    { id: 2, message: 'Send follow-up to Jane Doe', agent: 'Follow-up Agent', timestamp: new Date(Date.now() - 3600000).toISOString() },
  ])

  useEffect(() => {
    loadAgents()
    loadActivities()
  }, [])

  async function loadAgents() {
    try {
      const data = await api.agents.list()
      setAgents(data)
    } catch (e) {
      console.error('Failed to load agents', e)
    } finally {
      setLoading(false)
    }
  }

  async function loadActivities() {
    try {
      const data = await api.activities.list({ limit: 20 })
      setActivities(data)
    } catch (e) {
      console.error('Failed to load activities', e)
    }
  }

  async function handleSetStatus(id: number, status: AgentStatus) {
    try {
      await api.agents.setStatus(id, status)
      await loadAgents()
    } catch (e) {
      console.error('Failed to update agent status', e)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="skeleton h-12 w-32" />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Card key={i} className="skeleton h-48" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Agents</h1>
          <p className="text-muted-foreground mt-1">Monitor and control your AI team</p>
        </div>
        <Badge variant="secondary" className="px-3 py-1.5 font-mono text-sm">
          <span className="relative flex h-2 w-2 mr-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400"></span>
          </span>
          {agents.filter(a => a.status === 'active').length} active
        </Badge>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {agents.map(agent => {
              const status = statusConfig[agent.status]
              const isExpanded = expandedAgent === agent.id
              return (
                <Card 
                  key={agent.id} 
                  className={`group transition-all duration-300 hover:border-primary/50 ${isExpanded ? 'ring-1 ring-primary/50' : ''}`}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-12 h-12 rounded-xl ${status.bgColor} flex items-center justify-center group-hover:scale-105 transition-transform`}>
                          <Bot className={`h-6 w-6 ${status.color}`} />
                        </div>
                        <div>
                          <CardTitle className="text-base font-semibold">{agent.name}</CardTitle>
                          <Badge className={`mt-1 font-mono text-xs uppercase ${roleColors[agent.role]}`}>
                            {roleLabels[agent.role]}
                          </Badge>
                        </div>
                      </div>
                      <div className={`flex items-center gap-2 px-2.5 py-1 rounded-full ${status.bgColor}`}>
                        <span className={`w-2 h-2 rounded-full ${
                          agent.status === 'active' ? 'bg-emerald-400 animate-pulse' : 
                          agent.status === 'paused' ? 'bg-amber-400' : 'bg-red-400'
                        }`} />
                        <span className={`text-xs font-medium ${status.color}`}>{status.label}</span>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {agent.description && (
                      <p className="text-sm text-muted-foreground">{agent.description}</p>
                    )}
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      <span>Created {new Date(agent.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="flex gap-2">
                      {agent.status === 'paused' && (
                        <Button size="sm" onClick={() => handleSetStatus(agent.id, 'active')} className="gap-1.5">
                          <Play className="h-3 w-3" />
                          Resume
                        </Button>
                      )}
                      {agent.status === 'active' && (
                        <Button size="sm" variant="outline" onClick={() => handleSetStatus(agent.id, 'paused')} className="gap-1.5">
                          <Pause className="h-3 w-3" />
                          Pause
                        </Button>
                      )}
                      {agent.status !== 'stopped' && (
                        <Button size="sm" variant="destructive" onClick={() => handleSetStatus(agent.id, 'stopped')} className="gap-1.5">
                          <Square className="h-3 w-3" />
                          Stop
                        </Button>
                      )}
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        onClick={() => setExpandedAgent(isExpanded ? null : agent.id)}
                        className="gap-1.5 ml-auto"
                      >
                        <ActivityIcon className="h-3 w-3" />
                        Log
                        <ChevronDown className={`h-3 w-3 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                      </Button>
                    </div>
                    {isExpanded && (
                      <div className="pt-4 border-t border-border">
                        <p className="text-xs text-muted-foreground mb-2">Recent Activity</p>
                        <div className="space-y-2 max-h-32 overflow-y-auto">
                          {activities.filter(a => a.agent_id === agent.id).length > 0 ? (
                            activities.filter(a => a.agent_id === agent.id).slice(0, 5).map(activity => (
                              <div key={activity.id} className="flex items-center gap-2 text-sm">
                                <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                                <span className="text-muted-foreground truncate flex-1">
                                  {activity.content || activity.type.replace('_', ' ')}
                                </span>
                                <span className="text-xs text-muted-foreground">
                                  {new Date(activity.created_at).toLocaleTimeString()}
                                </span>
                              </div>
                            ))
                          ) : (
                            <p className="text-xs text-muted-foreground">No recent activity</p>
                          )}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )
            })}
          </div>

          {agents.length === 0 && (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
                  <Bot className="h-8 w-8 text-primary" />
                </div>
                <p className="text-lg font-medium">No agents configured yet</p>
                <p className="text-muted-foreground mt-1">Agents will appear here once created in the backend</p>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <AlertCircle className="h-4 w-4 text-amber-400" />
                Approval Queue
                <Badge variant="secondary" className="ml-auto">{approvalQueue.length}</Badge>
              </CardTitle>
              <CardDescription>Outreach actions waiting for your approval</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {approvalQueue.length === 0 ? (
                <div className="flex flex-col items-center py-6 text-muted-foreground">
                  <CheckCircle className="h-8 w-8 mb-2 text-emerald-400" />
                  <p className="text-sm">All clear! No pending approvals.</p>
                </div>
              ) : (
                approvalQueue.map(item => (
                  <div key={item.id} className="p-3 rounded-lg bg-secondary/50 border border-border hover:border-amber-500/30 transition-colors">
                    <p className="text-sm font-medium">{item.message}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant="outline" className="font-mono text-xs">{item.agent}</Badge>
                      <span className="text-xs text-muted-foreground">
                        {new Date(item.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex gap-2 mt-3">
                      <Button size="sm" className="flex-1 gap-1.5">
                        <CheckCircle className="h-3 w-3" />
                        Approve
                      </Button>
                      <Button size="sm" variant="outline" className="flex-1 gap-1.5">
                        <Square className="h-3 w-3" />
                        Deny
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <ActivityIcon className="h-4 w-4 text-primary" />
                Activity Feed
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {activities.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">No recent activity</p>
                ) : (
                  activities.slice(0, 10).map((activity, idx) => {
                    const agent = agents.find(a => a.id === activity.agent_id)
                    return (
                      <div key={activity.id} className="flex gap-3 group">
                        <div className="flex flex-col items-center">
                          <div className={`w-7 h-7 rounded-full flex items-center justify-center ${
                            agent ? roleColors[agent.role] : 'bg-secondary'
                          }`}>
                            <Bot className="h-3.5 w-3.5" />
                          </div>
                          {idx < Math.min(activities.length, 10) - 1 && (
                            <div className="w-px flex-1 bg-border mt-2" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0 pb-3">
                          <p className="text-sm leading-tight">{activity.content || `${activity.type.replace('_', ' ')} performed`}</p>
                          <div className="flex items-center gap-2 mt-1">
                            {agent && <span className="text-xs font-mono text-muted-foreground">{agent.name}</span>}
                            <span className="text-xs text-muted-foreground">
                              {new Date(activity.created_at).toLocaleString()}
                            </span>
                          </div>
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
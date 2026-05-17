'use client'

import { useEffect, useState } from 'react'
import { api, type Agent, type AgentStatus, type Activity } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Play, Pause, Square, Bot, Clock, CheckCircle, AlertCircle, Activity as ActivityIcon, ChevronDown, Settings, X, Plus } from 'lucide-react'

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
  const [configAgent, setConfigAgent] = useState<Agent | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
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
          <h1 className="text-3xl font-bold tracking-tight" data-tour="agents">Agents</h1>
          <p className="text-muted-foreground mt-1">Monitor and control your AI team</p>
        </div>
        <Badge variant="secondary" className="px-3 py-1.5 font-mono text-sm">
          <span className="relative flex h-2 w-2 mr-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400"></span>
          </span>
          {agents.filter(a => a.status === 'active').length} active
        </Badge>
        <Button 
          className="gap-2 bg-accent text-background hover:bg-accent-hover"
          onClick={() => setShowCreateModal(true)}
        >
          <Plus className="h-4 w-4" />
          Create Agent
        </Button>
      </div>

      <div className="flex gap-6">
        {/* Left: Agent cards — scrollable, takes remaining width */}
        <div className="flex-1 min-w-0 space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {agents.map(agent => {
              const status = statusConfig[agent.status]
              const isExpanded = expandedAgent === agent.id
              return (
                <Card 
                  key={agent.id} 
                  className={`
                    group relative bg-surface border-border rounded-[var(--radius-lg)] overflow-hidden
                    transition-all duration-200
                    hover:border-border-hover hover:-translate-y-0.5 hover:shadow-card
                    ${isExpanded ? 'ring-1 ring-accent/30' : ''}
                  `}
                >
                  <CardHeader className="pb-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-center gap-4">
                        {/* Agent icon */}
                        <div className={`w-14 h-14 rounded-[var(--radius-md)] ${status.bgColor} flex items-center justify-center group-hover:scale-105 transition-transform duration-200`}>
                          <Bot className={`h-6 w-6 ${status.color}`} />
                        </div>
                        <div>
                          <CardTitle className="text-base font-semibold font-display text-text-primary">
                            {agent.name}
                          </CardTitle>
                          <div className="mt-1">
                            <Badge className={`font-mono text-xs uppercase ${roleColors[agent.role]}`}>
                              {roleLabels[agent.role]}
                            </Badge>
                          </div>
                        </div>
                      </div>
                      
                      {/* Status pill */}
                      <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${status.bgColor} shrink-0`}>
                        <span className={`w-2 h-2 rounded-full ${
                          agent.status === 'active' ? 'bg-emerald-400 animate-pulse' : 
                          agent.status === 'paused' ? 'bg-amber-400' : 'bg-red-400'
                        }`} />
                        <span className={`text-xs font-medium ${status.color}`}>{status.label}</span>
                      </div>
                      
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setConfigAgent(agent)
                        }}
                        className="w-8 h-8 rounded-[var(--radius-md)] bg-surface border border-border flex items-center justify-center text-text-muted hover:text-text-secondary hover:border-border-hover transition-colors shrink-0"
                        title="Configure agent"
                      >
                        <Settings className="h-4 w-4" />
                      </button>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {agent.description && (
                      <p className="text-sm text-text-secondary leading-relaxed">{agent.description}</p>
                    )}
                    
                    <div className="flex items-center gap-2 text-xs text-text-muted">
                      <Clock className="h-3 w-3" />
                      <span>Created {new Date(agent.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                    </div>
                    
                    <div className="flex items-center gap-2 pt-2">
                      {agent.status === 'paused' && (
                        <Button size="sm" className="gap-1.5 bg-accent/10 text-accent border border-accent/20 hover:bg-accent/20">
                          <Play className="h-3 w-3" />
                          Resume
                        </Button>
                      )}
                      {agent.status === 'active' && (
                        <Button size="sm" variant="outline" className="gap-1.5 border-border text-text-secondary hover:bg-surface hover:border-border-hover">
                          <Pause className="h-3 w-3" />
                          Pause
                        </Button>
                      )}
                      {agent.status !== 'stopped' && (
                        <Button size="sm" variant="outline" className="gap-1.5 border-border/60 text-text-muted hover:bg-surface hover:border-border-hover">
                          <Square className="h-3 w-3" />
                          Stop
                        </Button>
                      )}
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        className="gap-1.5 ml-auto text-text-muted hover:text-text-secondary"
                        onClick={() => setExpandedAgent(isExpanded ? null : agent.id)}
                      >
                        <ActivityIcon className="h-3 w-3" />
                        Log
                        <ChevronDown className={`h-3 w-3 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                      </Button>
                    </div>
                    
                    {/* Expanded activity log */}
                    {isExpanded && (
                      <div className="pt-4 border-t border-border/50">
                        <p className="text-xs text-text-muted mb-2 font-medium uppercase tracking-wider">Recent Activity</p>
                        <div className="space-y-2 max-h-40 overflow-y-auto pr-2">
                          {activities.filter(a => a.agent_id === agent.id).length > 0 ? (
                            activities.filter(a => a.agent_id === agent.id).slice(0, 5).map(activity => (
                              <div key={activity.id} className="flex items-center gap-3 text-sm group/item">
                                <div className="w-1.5 h-1.5 rounded-full bg-accent shrink-0" />
                                <span className="text-text-secondary truncate flex-1">
                                  {activity.content || activity.type.replace('_', ' ')}
                                </span>
                                <span className="text-xs text-text-muted font-mono shrink-0">
                                  {new Date(activity.created_at).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
                                </span>
                              </div>
                            ))
                          ) : (
                            <p className="text-xs text-text-muted italic">No recent activity</p>
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

        {/* Right: Sticky Approval Queue + Activity Feed — 280px */}
        <div className="w-[280px] shrink-0 space-y-4">
          <div className="sticky top-6">
            {/* Approval Queue Panel */}
            <Card className="bg-surface border-border rounded-[var(--radius-lg)] overflow-hidden">
              <CardHeader className="pb-3 border-b border-border/50">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-semibold font-display text-text-primary flex items-center gap-2">
                    <div className="w-7 h-7 rounded-[var(--radius-md)] bg-amber-500/10 flex items-center justify-center">
                      <AlertCircle className="h-4 w-4 text-amber-400" />
                    </div>
                    Approval Queue
                  </CardTitle>
                  <Badge variant="secondary" className="text-xs">
                    {approvalQueue.length}
                  </Badge>
                </div>
                <p className="text-xs text-text-muted mt-1">Actions waiting for your approval</p>
              </CardHeader>
              <CardContent className="p-4 space-y-3 max-h-[300px] overflow-y-auto">
                {approvalQueue.length === 0 ? (
                  <div className="flex flex-col items-center py-6 text-center">
                    <CheckCircle className="h-8 w-8 mb-2 text-success" />
                    <p className="text-sm text-text-secondary">All clear!</p>
                    <p className="text-xs text-text-muted">No pending approvals</p>
                  </div>
                ) : (
                  approvalQueue.map(item => (
                    <div key={item.id} className="p-3 rounded-[var(--radius-md)] bg-bg-muted border border-border/50 hover:border-amber-500/30 transition-colors">
                      <p className="text-sm font-medium text-text-primary leading-tight mb-2">{item.message}</p>
                      <div className="flex items-center gap-2 mb-3">
                        <Badge variant="outline" className="font-mono text-xs text-text-muted">{item.agent}</Badge>
                        <span className="text-xs text-text-muted">
                          {new Date(item.timestamp).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}
                        </span>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" className="flex-1 gap-1.5 bg-accent/10 text-accent border border-accent/20 hover:bg-accent/20 h-7 text-xs">
                          <CheckCircle className="h-3 w-3" />
                          Approve
                        </Button>
                        <Button size="sm" variant="outline" className="flex-1 gap-1.5 border-border hover:bg-surface h-7 text-xs">
                          <Square className="h-3 w-3" />
                          Deny
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Activity Feed — below approval queue */}
            <Card className="bg-surface border-border rounded-[var(--radius-lg)] overflow-hidden mt-4">
              <CardHeader className="pb-3 border-b border-border/50">
                <CardTitle className="text-sm font-semibold font-display text-text-primary flex items-center gap-2">
                  <div className="w-7 h-7 rounded-[var(--radius-md)] bg-accent/10 flex items-center justify-center">
                    <ActivityIcon className="h-4 w-4 text-accent" />
                  </div>
                  Activity Feed
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4">
                <div className="space-y-3 max-h-[200px] overflow-y-auto">
                  {activities.length === 0 ? (
                    <p className="text-xs text-text-muted text-center py-4">No recent activity</p>
                  ) : (
                    activities.slice(0, 10).map((activity, idx) => {
                      const agent = agents.find(a => a.id === activity.agent_id)
                      return (
                        <div key={activity.id} className="flex gap-3">
                          <div className="flex flex-col items-center">
                            <div className={`w-6 h-6 rounded-full flex items-center justify-center ${agent ? roleColors[agent.role] : 'bg-secondary'}`}>
                              <Bot className="h-3 w-3" />
                            </div>
                            {idx < Math.min(activities.length, 10) - 1 && (
                              <div className="w-px flex-1 bg-border/50 mt-1" />
                            )}
                          </div>
                          <div className="flex-1 min-w-0 pb-2">
                            <p className="text-xs text-text-secondary leading-tight truncate">
                              {activity.content || activity.type.replace('_', ' ')}
                            </p>
                            <div className="flex items-center gap-1 mt-0.5">
                              {agent && <span className="text-xs font-mono text-text-muted">{agent.name}</span>}
                              <span className="text-xs text-text-muted">
                                {new Date(activity.created_at).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
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

      {configAgent && (
        <Dialog open={!!configAgent} onOpenChange={() => setConfigAgent(null)}>
          <DialogContent className="fixed inset-y-0 right-0 w-[440px] max-w-full border-l border-border bg-bg-base shadow-xl data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right duration-200 p-0 flex flex-col">
            <div className="flex items-center justify-between p-6 border-b border-border">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-[var(--radius-md)] ${statusConfig[configAgent.status].bgColor} flex items-center justify-center`}>
                  <Bot className={`h-5 w-5 ${statusConfig[configAgent.status].color}`} />
                </div>
                <div>
                  <h3 className="text-base font-semibold font-display">{configAgent.name}</h3>
                  <p className="text-xs text-text-muted font-mono">{configAgent.role.replace('_', ' ')}</p>
                </div>
              </div>
              <button
                onClick={() => setConfigAgent(null)}
                className="w-8 h-8 rounded-[var(--radius-md)] bg-surface border border-border flex items-center justify-center text-text-muted hover:text-text-primary transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              <div className="space-y-2">
                <Label className="text-sm font-medium text-text-secondary">Agent Name</Label>
                <Input
                  defaultValue={configAgent.name}
                  className="bg-surface border-border focus:border-accent"
                />
              </div>

              <div className="space-y-2">
                <Label className="text-sm font-medium text-text-secondary">Role</Label>
                <Select defaultValue={configAgent.role}>
                  <SelectTrigger className="bg-surface border-border">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="lead_sourcing">Lead Sourcing</SelectItem>
                    <SelectItem value="research">Research</SelectItem>
                    <SelectItem value="outreach">Outreach</SelectItem>
                    <SelectItem value="follow_up">Follow-up</SelectItem>
                    <SelectItem value="qualification">Qualification</SelectItem>
                    <SelectItem value="reporting">Reporting</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="text-sm font-medium text-text-secondary">Description</Label>
                <textarea
                  defaultValue={configAgent.description || ''}
                  className="w-full h-20 rounded-[var(--radius-md)] border border-border bg-surface p-3 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent resize-none"
                  placeholder="What does this agent do?"
                />
              </div>

              <div className="space-y-2">
                <Label className="text-sm font-medium text-text-secondary">Daily Outreach Limit</Label>
                <Input
                  type="number"
                  defaultValue={50}
                  min={0}
                  max={500}
                  className="bg-surface border-border focus:border-accent"
                />
                <p className="text-xs text-text-muted">Maximum emails/messages per day (0 = unlimited)</p>
              </div>

              <div className="space-y-2">
                <Label className="text-sm font-medium text-text-secondary">Target Criteria</Label>
                <div className="p-4 rounded-[var(--radius-md)] bg-surface border border-border space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">Min lead score</span>
                    <span className="text-sm font-mono text-accent">40</span>
                  </div>
                  <input type="range" min="0" max="100" defaultValue={40} className="w-full accent-accent" />
                  <div className="flex items-center justify-between text-xs text-text-muted">
                    <span>0</span>
                    <span>100</span>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-sm font-medium text-text-secondary">Active Hours</Label>
                <Select defaultValue="all">
                  <SelectTrigger className="bg-surface border-border">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">24/7 (always active)</SelectItem>
                    <SelectItem value="business">Business hours (9–5)</SelectItem>
                    <SelectItem value="custom">Custom schedule</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="p-6 border-t border-border flex gap-3">
              <Button variant="outline" className="flex-1" onClick={() => setConfigAgent(null)}>
                Cancel
              </Button>
              <Button className="flex-1 bg-accent text-background hover:bg-accent-hover">
                Save Changes
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {showCreateModal && (
        <Dialog open={showCreateModal} onOpenChange={() => setShowCreateModal(false)}>
          <DialogContent className="sm:max-w-[480px] bg-surface border-border rounded-[var(--radius-lg)]">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-[var(--radius-md)] bg-accent/10 flex items-center justify-center">
                <Bot className="h-5 w-5 text-accent" />
              </div>
              <h2 className="text-lg font-semibold font-display">Create New Agent</h2>
            </div>
            <p className="text-sm text-text-muted mb-4">
              Define the agent's role and behavior
            </p>
            
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="agent-name">Agent Name</Label>
                <Input 
                  id="agent-name" 
                  placeholder="e.g. Sales Lead Sourcing Agent"
                  className="bg-surface border-border focus:border-accent"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="agent-role">Role</Label>
                <Select>
                  <SelectTrigger className="bg-surface border-border">
                    <SelectValue placeholder="Select a role" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="lead_sourcing">Lead Sourcing</SelectItem>
                    <SelectItem value="research">Research</SelectItem>
                    <SelectItem value="outreach">Outreach</SelectItem>
                    <SelectItem value="follow_up">Follow-up</SelectItem>
                    <SelectItem value="qualification">Qualification</SelectItem>
                    <SelectItem value="reporting">Reporting</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="agent-desc">Description</Label>
                <textarea
                  id="agent-desc"
                  placeholder="What does this agent do? What triggers its actions?"
                  className="w-full h-20 rounded-[var(--radius-md)] border border-border bg-surface p-3 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent resize-none"
                />
              </div>
            </div>
            
            <div className="flex gap-3">
              <Button variant="outline" onClick={() => setShowCreateModal(false)} className="flex-1">
                Cancel
              </Button>
              <Button className="flex-1 bg-accent text-background hover:bg-accent-hover" onClick={() => {
                setShowCreateModal(false)
              }}>
                Create Agent
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  )
}
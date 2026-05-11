'use client'

import { useEffect, useState } from 'react'
import { api, type Agent, type AgentStatus } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Play, Pause, Square, Bot, Clock } from 'lucide-react'

const roleLabels: Record<string, string> = {
  lead_sourcing: 'Lead Sourcing',
  research: 'Research',
  outreach: 'Outreach',
  follow_up: 'Follow-up',
  qualification: 'Qualification',
  reporting: 'Reporting',
}

const statusColors: Record<AgentStatus, string> = {
  active: 'bg-green-100 text-green-800',
  paused: 'bg-yellow-100 text-yellow-800',
  stopped: 'bg-red-100 text-red-800',
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAgents()
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

  async function handleSetStatus(id: number, status: AgentStatus) {
    try {
      await api.agents.setStatus(id, status)
      await loadAgents()
    } catch (e) {
      console.error('Failed to update agent status', e)
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Agents</h2>
        <Badge variant="secondary" className="text-sm">
          {agents.filter(a => a.status === 'active').length} active
        </Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {agents.map(agent => (
          <Card key={agent.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="rounded-full bg-primary/10 p-2">
                    <Bot className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-base">{agent.name}</CardTitle>
                    <CardDescription className="text-xs">{roleLabels[agent.role]}</CardDescription>
                  </div>
                </div>
                <Badge className={statusColors[agent.status]}>
                  {agent.status}
                </Badge>
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
                  <Button size="sm" onClick={() => handleSetStatus(agent.id, 'active')}>
                    <Play className="h-4 w-4 mr-1" />
                    Resume
                  </Button>
                )}
                {agent.status === 'active' && (
                  <Button size="sm" variant="outline" onClick={() => handleSetStatus(agent.id, 'paused')}>
                    <Pause className="h-4 w-4 mr-1" />
                    Pause
                  </Button>
                )}
                <Button size="sm" variant="destructive" onClick={() => handleSetStatus(agent.id, 'stopped')}>
                  <Square className="h-4 w-4 mr-1" />
                  Stop
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {agents.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Bot className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No agents configured yet</p>
            <p className="text-sm text-muted-foreground mt-1">Agents will appear here once created in the backend</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
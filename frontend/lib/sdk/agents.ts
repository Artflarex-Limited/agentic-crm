import type { Agent, AgentStatus } from '../api'
import { AgenticCRM } from './client'

export interface CreateAgentInput {
  name: string
  role: string
  description?: string
  config?: Record<string, unknown>
}

export interface UpdateAgentInput {
  name?: string
  role?: string
  description?: string
  config?: Record<string, unknown>
}

export class AgentsClient {
  constructor(private client: AgenticCRM) {}

  async list(): Promise<Agent[]> {
    return this.client.get<Agent[]>('/api/agents')
  }

  async get(agentId: number): Promise<Agent> {
    return this.client.get<Agent>(`/api/agents/${agentId}`)
  }

  async create(data: CreateAgentInput): Promise<Agent> {
    return this.client.post<Agent>('/api/agents', data)
  }

  async update(agentId: number, data: UpdateAgentInput): Promise<Agent> {
    return this.client.patch<Agent>(`/api/agents/${agentId}`, data)
  }

  async updateStatus(agentId: number, status: AgentStatus): Promise<Agent> {
    return this.client.patch<Agent>(`/api/agents/${agentId}`, { status })
  }

  async pause(agentId: number): Promise<Agent> {
    return this.updateStatus(agentId, 'paused')
  }

  async resume(agentId: number): Promise<Agent> {
    return this.updateStatus(agentId, 'active')
  }
}
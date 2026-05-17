import type { Lead, LeadSource, LeadStage } from '../api'
import { AgenticCRM } from './client'

export interface CreateLeadInput {
  contact_id: number
  source?: LeadSource
  stage?: LeadStage
  score?: number
  tags?: string[]
  notes?: string
  assigned_agent_id?: number
}

export interface UpdateLeadInput {
  source?: LeadSource
  stage?: LeadStage
  score?: number
  tags?: string[]
  notes?: string
  assigned_agent_id?: number
  last_contacted_at?: string
}

export class LeadsClient {
  constructor(private client: AgenticCRM) {}

  async list(params?: { stage?: LeadStage; source?: LeadSource; search?: string }): Promise<Lead[]> {
    return this.client.get<Lead[]>('/api/leads', params as Record<string, string>)
  }

  async get(leadId: number): Promise<Lead> {
    return this.client.get<Lead>(`/api/leads/${leadId}`)
  }

  async create(data: CreateLeadInput): Promise<Lead> {
    return this.client.post<Lead>('/api/leads', data)
  }

  async update(leadId: number, data: UpdateLeadInput): Promise<Lead> {
    return this.client.patch<Lead>(`/api/leads/${leadId}`, data)
  }

  async delete(leadId: number): Promise<void> {
    return this.client.delete<void>(`/api/leads/${leadId}`)
  }

  async activities(leadId: number): Promise<unknown[]> {
    return this.client.get<unknown[]>(`/api/leads/${leadId}/activities`)
  }

  async addNote(leadId: number, content: string): Promise<void> {
    return this.client.post<void>(`/api/leads/${leadId}/notes`, { content })
  }
}
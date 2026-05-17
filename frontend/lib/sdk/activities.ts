import type { Activity, ActivityType } from '../api'
import { AgenticCRM } from './client'

export interface CreateActivityInput {
  lead_id?: number
  contact_id?: number
  deal_id?: number
  agent_id?: number
  type: ActivityType
  content?: string
  metadata?: Record<string, unknown>
}

export class ActivitiesClient {
  constructor(private client: AgenticCRM) {}

  async list(params?: {
    lead_id?: number
    contact_id?: number
    limit?: number
  }): Promise<Activity[]> {
    return this.client.get<Activity[]>('/api/activities', params as Record<string, string>)
  }

  async create(data: CreateActivityInput): Promise<Activity> {
    return this.client.post<Activity>('/api/activities', data)
  }
}
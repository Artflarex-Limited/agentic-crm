import type { Deal, DealStage } from '../api'
import { AgenticCRM } from './client'

export interface CreateDealInput {
  contact_id: number
  company_id?: number
  name: string
  value: number
  stage?: DealStage
  expected_close_date?: string
  notes?: string
}

export interface UpdateDealInput {
  name?: string
  value?: number
  stage?: DealStage
  expected_close_date?: string
  actual_close_date?: string
  notes?: string
}

export class DealsClient {
  constructor(private client: AgenticCRM) {}

  async list(params?: { stage?: DealStage }): Promise<Deal[]> {
    return this.client.get<Deal[]>('/api/deals', params as Record<string, string>)
  }

  async get(dealId: number): Promise<Deal> {
    return this.client.get<Deal>(`/api/deals/${dealId}`)
  }

  async create(data: CreateDealInput): Promise<Deal> {
    return this.client.post<Deal>('/api/deals', data)
  }

  async update(dealId: number, data: UpdateDealInput): Promise<Deal> {
    return this.client.patch<Deal>(`/api/deals/${dealId}`, data)
  }

  async delete(dealId: number): Promise<void> {
    return this.client.delete<void>(`/api/deals/${dealId}`)
  }

  async activities(dealId: number): Promise<unknown[]> {
    return this.client.get<unknown[]>(`/api/deals/${dealId}/activities`)
  }
}
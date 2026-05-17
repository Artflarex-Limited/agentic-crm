import { AgenticCRM } from './client'

export interface SequenceStep {
  type: string
  subject?: string
  content: string
  delay_days: number
}

export interface Sequence {
  id: number
  name: string
  description?: string
  steps: SequenceStep[]
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CreateSequenceInput {
  name: string
  description?: string
  steps: SequenceStep[]
  is_active?: boolean
}

export interface UpdateSequenceInput {
  name?: string
  description?: string
  steps?: SequenceStep[]
  is_active?: boolean
}

export class SequencesClient {
  constructor(private client: AgenticCRM) {}

  async list(): Promise<Sequence[]> {
    return this.client.get<Sequence[]>('/api/sequences')
  }

  async get(sequenceId: number): Promise<Sequence> {
    return this.client.get<Sequence>(`/api/sequences/${sequenceId}`)
  }

  async create(data: CreateSequenceInput): Promise<Sequence> {
    return this.client.post<Sequence>('/api/sequences', data)
  }

  async update(sequenceId: number, data: UpdateSequenceInput): Promise<Sequence> {
    return this.client.patch<Sequence>(`/api/sequences/${sequenceId}`, data)
  }
}
import { AgenticCRM } from './client'

export interface Contact {
  id: number
  company_id?: number
  first_name?: string
  last_name?: string
  email?: string
  phone?: string
  title?: string
  linkedin_url?: string
  extra_data: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface CreateContactInput {
  company_id?: number
  first_name?: string
  last_name?: string
  email?: string
  phone?: string
  title?: string
  linkedin_url?: string
  extra_data?: Record<string, unknown>
}

export interface UpdateContactInput {
  company_id?: number
  first_name?: string
  last_name?: string
  email?: string
  phone?: string
  title?: string
  linkedin_url?: string
  extra_data?: Record<string, unknown>
}

export class ContactsClient {
  constructor(private client: AgenticCRM) {}

  async list(params?: { search?: string }): Promise<Contact[]> {
    return this.client.get<Contact[]>('/api/contacts', params as Record<string, string>)
  }

  async get(contactId: number): Promise<Contact> {
    return this.client.get<Contact>(`/api/contacts/${contactId}`)
  }

  async create(data: CreateContactInput): Promise<Contact> {
    return this.client.post<Contact>('/api/contacts', data)
  }

  async update(contactId: number, data: UpdateContactInput): Promise<Contact> {
    return this.client.patch<Contact>(`/api/contacts/${contactId}`, data)
  }

  async delete(contactId: number): Promise<void> {
    return this.client.delete<void>(`/api/contacts/${contactId}`)
  }
}
import type { SDKConfig } from './config'

export interface ApiError {
  message: string
  status?: number
}

export class AgenticCRMError extends Error {
  status?: number
  constructor(message: string, status?: number) {
    super(message)
    this.name = 'AgenticCRMError'
    this.status = status
  }
}

export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null
  try {
    const keys = ['openclaw_auth_token', 'auth_token', 'jwt_token', 'token']
    for (const key of keys) {
      const token = localStorage.getItem(key)
      if (token) return token
    }
  } catch {
    // localStorage not available
  }
  return null
}

export class AgenticCRM {
  private baseUrl: string
  private timeout: number
  private maxRetries: number
  private apiKey?: string

  constructor(config: SDKConfig | Partial<SDKConfig> = {}) {
    const baseConfig = {
      baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      timeout: 30000,
      maxRetries: 3,
      ...config,
    }
    this.baseUrl = baseConfig.baseUrl.replace(/\/$/, '')
    this.timeout = baseConfig.timeout
    this.maxRetries = baseConfig.maxRetries
    this.apiKey = baseConfig.apiKey
  }

  private buildHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'User-Agent': 'agentic-crm-sdk/0.1.0',
    }
    const token = this.apiKey || getAuthToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    return headers
  }

  private async request<T>(
    method: string,
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`
    const headers = this.buildHeaders()

    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), this.timeout)

        const response = await fetch(url, {
          ...options,
          method,
          headers: { ...headers, ...options.headers },
          signal: controller.signal,
        })

        clearTimeout(timeoutId)

        if (response.status < 400) {
          return response.json()
        }

        if (response.status >= 500) {
          if (attempt < this.maxRetries - 1) continue
          throw new AgenticCRMError(`Server error: ${response.status}`, response.status)
        }

        if (response.status === 429) {
          if (attempt < this.maxRetries - 1) continue
          throw new AgenticCRMError(`Rate limited: ${response.status}`, response.status)
        }

        if (response.status === 401) {
          if (typeof window !== 'undefined') {
            const keys = ['openclaw_auth_token', 'auth_token', 'jwt_token', 'token']
            keys.forEach(key => localStorage.removeItem(key))
          }
        }

        throw new AgenticCRMError(`Client error: ${response.status}`, response.status)
      } catch (e) {
        if (e instanceof AgenticCRMError) throw e
        if (e instanceof Error && e.name === 'AbortError') {
          if (attempt < this.maxRetries - 1) continue
          throw new AgenticCRMError('Request timeout')
        }
        if (e instanceof Error && e.message.includes('fetch')) {
          if (attempt < this.maxRetries - 1) continue
          throw new AgenticCRMError('Connection failed')
        }
        throw e
      }
    }

    throw new AgenticCRMError('Max retries exceeded')
  }

  async get<T>(path: string, params?: Record<string, string | number>): Promise<T> {
    const query = params
      ? '?' + new URLSearchParams(params as Record<string, string>).toString()
      : ''
    return this.request<T>('GET', `${path}${query}`)
  }

  async post<T>(path: string, data?: unknown): Promise<T> {
    return this.request<T>('POST', path, {
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async put<T>(path: string, data?: unknown): Promise<T> {
    return this.request<T>('PUT', path, {
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async patch<T>(path: string, data?: unknown): Promise<T> {
    return this.request<T>('PATCH', path, {
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async delete<T>(path: string): Promise<T> {
    return this.request<T>('DELETE', path)
  }
}
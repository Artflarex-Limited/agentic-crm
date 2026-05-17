export interface SDKConfig {
  baseUrl: string
  apiKey?: string
  timeout: number
  maxRetries: number
}

export const defaultConfig: SDKConfig = {
  baseUrl: 'http://localhost:8000',
  timeout: 30000,
  maxRetries: 3,
}
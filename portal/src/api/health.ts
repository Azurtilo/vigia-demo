import { API_URL } from '../config'

export interface HealthResponse {
  status: string
  environment: string
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_URL}/health`)
  if (!response.ok) {
    throw new Error(`La API respondió con estado ${response.status}`)
  }
  return (await response.json()) as HealthResponse
}

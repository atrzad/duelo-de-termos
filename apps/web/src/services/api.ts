export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export interface HealthResponse {
  status: 'ok'
}

function isHealthResponse(value: unknown): value is HealthResponse {
  return typeof value === 'object' && value !== null && 'status' in value && value.status === 'ok'
}

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${API_URL}/health`, signal ? { signal } : {})
  if (!response.ok) {
    throw new Error(`Falha ao consultar /health (HTTP ${String(response.status)})`)
  }
  const data: unknown = await response.json()
  if (!isHealthResponse(data)) {
    throw new Error('Resposta inesperada de /health')
  }
  return data
}

import { afterEach, describe, expect, it, vi } from 'vitest'

import { getHealth } from './api'

function mockFetch(body: unknown, status = 200) {
  const fetchMock = vi.fn(() => Promise.resolve(Response.json(body, { status })))
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('getHealth', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('retorna o status quando a API responde ok', async () => {
    const fetchMock = mockFetch({ status: 'ok' })

    await expect(getHealth()).resolves.toEqual({ status: 'ok' })
    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/health', {})
  })

  it('falha com erro HTTP', async () => {
    mockFetch({ detail: 'erro' }, 503)

    await expect(getHealth()).rejects.toThrow('HTTP 503')
  })

  it('rejeita resposta com formato inesperado', async () => {
    mockFetch({ status: 'talvez' })

    await expect(getHealth()).rejects.toThrow('Resposta inesperada')
  })
})

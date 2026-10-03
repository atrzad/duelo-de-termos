import { describe, expect, it } from 'vitest'

import { mesclarEstadosDoTeclado } from './keyStates'

describe('mesclarEstadosDoTeclado', () => {
  it('não erra com lista vazia', () => {
    expect(mesclarEstadosDoTeclado([])).toEqual({})
  })

  it('agrega o estado de cada letra pela tentativa mais recente', () => {
    const resultado = mesclarEstadosDoTeclado([
      { letters: ['A', 'B'], states: ['absent', 'present'] },
    ])

    expect(resultado.A).toBe('absent')
    expect(resultado.B).toBe('present')
  })

  it('prioriza correct sobre present e absent entre tentativas diferentes', () => {
    const resultado = mesclarEstadosDoTeclado([
      { letters: ['A'], states: ['absent'] },
      { letters: ['A'], states: ['present'] },
      { letters: ['A'], states: ['correct'] },
    ])

    expect(resultado.A).toBe('correct')
  })

  it('nunca rebaixa uma letra que já foi correct', () => {
    const resultado = mesclarEstadosDoTeclado([
      { letters: ['A'], states: ['correct'] },
      { letters: ['A'], states: ['absent'] },
    ])

    expect(resultado.A).toBe('correct')
  })
})

import { describe, expect, it } from 'vitest'

import { PALAVRAS, palavraAleatoria } from './words'

describe('PALAVRAS', () => {
  it('só contém palavras de exatamente 5 letras, maiúsculas, sem acento', () => {
    for (const palavra of PALAVRAS) {
      expect(palavra).toHaveLength(5)
      expect(palavra).toMatch(/^[A-Z]{5}$/)
    }
  })

  it('não tem palavras repetidas', () => {
    expect(new Set(PALAVRAS).size).toBe(PALAVRAS.length)
  })
})

describe('palavraAleatoria', () => {
  it('sempre retorna uma palavra do pool', () => {
    for (let i = 0; i < 20; i++) {
      expect(PALAVRAS).toContain(palavraAleatoria())
    }
  })

  it('evita repetir a palavra excluída quando há outras opções', () => {
    for (let i = 0; i < 20; i++) {
      expect(palavraAleatoria('TERMO')).not.toBe('TERMO')
    }
  })
})

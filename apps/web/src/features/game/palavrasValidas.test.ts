import { describe, expect, it } from 'vitest'

import { palavraEValida } from './palavrasValidas'
import { PALAVRAS } from './words'

describe('palavraEValida', () => {
  it('aceita todas as respostas possíveis', () => {
    for (const palavra of PALAVRAS) {
      expect(palavraEValida(palavra)).toBe(true)
    }
  })

  it('aceita uma palavra real que não é uma das respostas', () => {
    expect(palavraEValida('CASAS')).toBe(true)
  })

  it('rejeita uma sequência de letras sem sentido', () => {
    expect(palavraEValida('ZZZZZ')).toBe(false)
    expect(palavraEValida('QWXYZ')).toBe(false)
  })

  it('não depende da caixa', () => {
    expect(palavraEValida('termo')).toBe(true)
  })
})

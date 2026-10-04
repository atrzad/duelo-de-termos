import { describe, expect, it } from 'vitest'

import {
  apagarNoCursor,
  escreverNoCursor,
  fixarCursor,
  guessEstaCompleto,
  palpiteVazio,
} from './guessCursor'

describe('palpiteVazio', () => {
  it('cria um array do tamanho certo, todo vazio', () => {
    expect(palpiteVazio(5)).toEqual(['', '', '', '', ''])
  })
})

describe('fixarCursor', () => {
  it('não deixa passar do último índice', () => {
    expect(fixarCursor(10, 5)).toBe(4)
  })

  it('não deixa ficar negativo', () => {
    expect(fixarCursor(-3, 5)).toBe(0)
  })
})

describe('escreverNoCursor', () => {
  it('digitar sequencialmente do início reproduz o comportamento de só acrescentar', () => {
    let guess = palpiteVazio(5)
    let cursor = 0

    for (const letra of ['T', 'E', 'R', 'M', 'O']) {
      ;({ guess, cursor } = escreverNoCursor(guess, cursor, letra))
    }

    expect(guess).toEqual(['T', 'E', 'R', 'M', 'O'])
    expect(cursor).toBe(4) // não passa do último quadrado
  })

  it('clicar numa posição no meio sobrescreve só aquela letra', () => {
    const guess = ['T', 'E', 'R', 'M', 'O']

    const resultado = escreverNoCursor(guess, 2, 'X')

    expect(resultado.guess).toEqual(['T', 'E', 'X', 'M', 'O'])
    expect(resultado.cursor).toBe(3) // avança uma posição
  })
})

describe('apagarNoCursor', () => {
  it('backspace sem mover o cursor manualmente remove a última letra digitada', () => {
    let guess = ['T', 'E', 'R', 'M', 'O']
    let cursor = 4 // estado natural depois de digitar as 5 letras

    ;({ guess, cursor } = apagarNoCursor(guess, cursor))
    expect(guess).toEqual(['T', 'E', 'R', 'M', ''])
    expect(cursor).toBe(3)

    ;({ guess, cursor } = apagarNoCursor(guess, cursor))
    expect(guess).toEqual(['T', 'E', 'R', '', ''])
    expect(cursor).toBe(2)
  })

  it('apagar numa posição já vazia não quebra nada, só move o cursor', () => {
    const guess = ['T', 'E', '', '', '']

    const resultado = apagarNoCursor(guess, 3)

    expect(resultado.guess).toEqual(['T', 'E', '', '', ''])
    expect(resultado.cursor).toBe(2)
  })
})

describe('guessEstaCompleto', () => {
  it('falso se tiver qualquer buraco, mesmo no meio', () => {
    expect(guessEstaCompleto(['T', 'E', '', 'M', 'O'])).toBe(false)
  })

  it('verdadeiro só quando todas as posições têm letra', () => {
    expect(guessEstaCompleto(['T', 'E', 'R', 'M', 'O'])).toBe(true)
  })
})

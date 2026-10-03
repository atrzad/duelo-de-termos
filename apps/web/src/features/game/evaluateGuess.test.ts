import { describe, expect, it } from 'vitest'

import { evaluateGuess } from './evaluateGuess'

describe('evaluateGuess', () => {
  it('marca tudo como correto quando o palpite é igual ao segredo', () => {
    expect(evaluateGuess('TERMO', 'TERMO')).toEqual([
      'correct',
      'correct',
      'correct',
      'correct',
      'correct',
    ])
  })

  it('marca tudo como ausente quando não há letras em comum', () => {
    expect(evaluateGuess('ABCDF', 'TERMO')).toEqual([
      'absent',
      'absent',
      'absent',
      'absent',
      'absent',
    ])
  })

  it('é insensível a maiúsculas e minúsculas', () => {
    expect(evaluateGuess('termo', 'TERMO')).toEqual([
      'correct',
      'correct',
      'correct',
      'correct',
      'correct',
    ])
  })

  it('marca presente quando a letra existe em outra posição', () => {
    // segredo TERMO, palpite ROTEM: mesmas 5 letras, todas fora da posição original.
    expect(evaluateGuess('ROTEM', 'TERMO')).toEqual([
      'present',
      'present',
      'present',
      'present',
      'present',
    ])
  })

  it('não repete "present" além da quantidade real da letra no segredo', () => {
    // TERMO só tem um R (posição 2). Palpite com dois R: só o primeiro pode
    // virar 'present' (consome o único R que resta); o segundo fica 'absent'.
    const resultado = evaluateGuess('RRABC', 'TERMO')
    expect(resultado[0]).toBe('present')
    expect(resultado[1]).toBe('absent')
  })

  it('trata corretamente letras repetidas no segredo', () => {
    // segredo ARARA (A nas posições 0,2,4), palpite AAAAA: só existem 3 A's
    // no segredo, e todos já caem em posição exata -> 3 correct, resto absent.
    expect(evaluateGuess('AAAAA', 'ARARA')).toEqual([
      'correct',
      'absent',
      'correct',
      'absent',
      'correct',
    ])
  })
})

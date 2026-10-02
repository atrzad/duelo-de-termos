import { describe, expect, it } from 'vitest'

import { buildBoard } from './board'

describe('buildBoard', () => {
  it('cria uma grade vazia 6x5 por padrão', () => {
    const board = buildBoard([])

    expect(board).toHaveLength(6)
    for (const row of board) {
      expect(row).toHaveLength(5)
      expect(row.every((tile) => tile.state === 'empty' && tile.letter === '')).toBe(true)
    }
  })

  it('preserva as linhas informadas e completa o restante', () => {
    const board = buildBoard([[{ letter: 'T', state: 'filled' }]])

    expect(board[0]?.[0]).toEqual({ letter: 'T', state: 'filled' })
    expect(board[0]?.[1]).toEqual({ letter: '', state: 'empty' })
    expect(board[1]?.[0]).toEqual({ letter: '', state: 'empty' })
  })

  it('não descarta linhas além das seis regulares (prorrogação)', () => {
    const extraRows = Array.from({ length: 8 }, () => [])

    expect(buildBoard(extraRows)).toHaveLength(8)
  })
})

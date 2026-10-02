import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { buildBoard } from '../features/game/board'
import { GameBoard } from './GameBoard'

describe('GameBoard', () => {
  it('renderiza 6 linhas com 5 células cada', () => {
    render(<GameBoard rows={buildBoard([])} />)

    const board = screen.getByRole('grid', { name: 'Seu tabuleiro' })
    const rows = within(board).getAllByRole('row')

    expect(rows).toHaveLength(6)
    for (const row of rows) {
      expect(within(row).getAllByRole('gridcell')).toHaveLength(5)
    }
  })

  it('descreve o estado das letras sem depender só da cor', () => {
    render(
      <GameBoard
        rows={buildBoard([
          [
            { letter: 'R', state: 'present' },
            { letter: 'A', state: 'correct' },
            { letter: 'S', state: 'absent' },
          ],
        ])}
      />,
    )

    expect(
      screen.getByRole('gridcell', { name: 'R, presente em outra posição' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('gridcell', { name: 'A, na posição correta' })).toBeInTheDocument()
    expect(screen.getByRole('gridcell', { name: 'S, ausente na palavra' })).toBeInTheDocument()
  })
})

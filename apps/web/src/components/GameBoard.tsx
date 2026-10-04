import type { BoardRow } from '../types/game'
import { GuessRow } from './GuessRow'

interface GameBoardProps {
  rows: readonly BoardRow[]
  label?: string
  /** Índice da linha em digitação (a única clicável), ou null se nenhuma
   * (jogo parado/sem rodada ativa). */
  activeRowIndex?: number | null
  selectedColumn?: number | null
  onSelectTile?: ((indice: number) => void) | undefined
}

export function GameBoard({
  rows,
  label = 'Seu tabuleiro',
  activeRowIndex = null,
  selectedColumn = null,
  onSelectTile,
}: GameBoardProps) {
  return (
    <div role="grid" aria-label={label} className="mx-auto grid w-full max-w-[20rem] gap-1.5">
      {rows.map((row, index) => {
        const ehLinhaAtiva = onSelectTile !== undefined && index === activeRowIndex
        return (
          <GuessRow
            key={index}
            row={row}
            rowNumber={index + 1}
            onSelectColumn={ehLinhaAtiva ? onSelectTile : undefined}
            selectedColumn={ehLinhaAtiva ? selectedColumn : null}
          />
        )
      })}
    </div>
  )
}

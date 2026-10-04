import type { BoardRow } from '../types/game'
import { LetterTile } from './LetterTile'

interface GuessRowProps {
  row: BoardRow
  rowNumber: number
  /** Só a linha em digitação recebe isso -- as demais nunca são clicáveis. */
  onSelectColumn?: ((indice: number) => void) | undefined
  selectedColumn?: number | null
}

export function GuessRow({ row, rowNumber, onSelectColumn, selectedColumn }: GuessRowProps) {
  return (
    <div
      role="row"
      aria-label={`Tentativa ${String(rowNumber)}`}
      className="grid grid-cols-5 gap-1.5"
    >
      {row.map((tile, index) => (
        <LetterTile
          key={index}
          tile={tile}
          onSelect={
            onSelectColumn
              ? () => {
                  onSelectColumn(index)
                }
              : undefined
          }
          selected={selectedColumn === index}
        />
      ))}
    </div>
  )
}

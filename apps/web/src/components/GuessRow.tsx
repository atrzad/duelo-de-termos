import type { BoardRow } from '../types/game'
import { LetterTile } from './LetterTile'

interface GuessRowProps {
  row: BoardRow
  rowNumber: number
}

export function GuessRow({ row, rowNumber }: GuessRowProps) {
  return (
    <div
      role="row"
      aria-label={`Tentativa ${String(rowNumber)}`}
      className="grid grid-cols-5 gap-1.5"
    >
      {row.map((tile, index) => (
        <LetterTile key={index} tile={tile} />
      ))}
    </div>
  )
}

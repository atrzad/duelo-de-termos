import type { BoardRow } from '../types/game'
import { GuessRow } from './GuessRow'

interface GameBoardProps {
  rows: readonly BoardRow[]
  label?: string
}

export function GameBoard({ rows, label = 'Seu tabuleiro' }: GameBoardProps) {
  return (
    <div role="grid" aria-label={label} className="mx-auto grid w-full max-w-[20rem] gap-1.5">
      {rows.map((row, index) => (
        <GuessRow key={index} row={row} rowNumber={index + 1} />
      ))}
    </div>
  )
}

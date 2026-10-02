import type { Tile, TileState } from '../types/game'

const stateClasses: Record<TileState, string> = {
  empty: 'border-2 border-tile-border bg-transparent',
  filled: 'border-2 border-tile-border-filled bg-transparent text-fg',
  correct: 'border-2 border-tile-correct bg-tile-correct text-tile-fg',
  // Borda tracejada interna: o estado não depende só da cor.
  present:
    'border-2 border-tile-present bg-tile-present text-tile-fg outline-2 outline-dashed outline-tile-fg/70',
  absent: 'border-2 border-tile-absent bg-tile-absent text-tile-fg',
}

const stateDescriptions: Record<TileState, string> = {
  empty: 'vazia',
  filled: 'digitada',
  correct: 'na posição correta',
  present: 'presente em outra posição',
  absent: 'ausente na palavra',
}

function describeTile({ letter, state }: Tile): string {
  return state === 'empty' ? 'Vazia' : `${letter}, ${stateDescriptions[state]}`
}

const sizeClasses = {
  md: 'rounded-md text-[clamp(1.25rem,7vw,2rem)] -outline-offset-[6px]',
  sm: 'rounded text-base -outline-offset-[4px]',
} as const

interface LetterTileProps {
  tile: Tile
  size?: keyof typeof sizeClasses
}

export function LetterTile({ tile, size = 'md' }: LetterTileProps) {
  return (
    <div
      role="gridcell"
      aria-label={describeTile(tile)}
      data-state={tile.state}
      className={`flex aspect-square w-full items-center justify-center font-bold uppercase select-none ${sizeClasses[size]} ${stateClasses[tile.state]}`}
    >
      {tile.letter}
    </div>
  )
}

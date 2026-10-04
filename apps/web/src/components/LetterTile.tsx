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
  /** Só a linha em digitação pode ser clicada, pra escolher onde a próxima
   * letra digitada vai entrar. Tentativas já enviadas nunca são clicáveis. */
  onSelect?: (() => void) | undefined
  selected?: boolean
}

export function LetterTile({ tile, size = 'md', onSelect, selected = false }: LetterTileProps) {
  const clicavel = onSelect !== undefined

  return (
    <div
      role="gridcell"
      aria-label={describeTile(tile)}
      aria-selected={clicavel ? selected : undefined}
      data-state={tile.state}
      tabIndex={clicavel ? 0 : undefined}
      onClick={onSelect}
      onKeyDown={
        clicavel
          ? (evento) => {
              if (evento.key === 'Enter' || evento.key === ' ') {
                evento.preventDefault()
                onSelect()
              }
            }
          : undefined
      }
      className={`flex aspect-square w-full items-center justify-center font-bold uppercase select-none ${sizeClasses[size]} ${stateClasses[tile.state]} ${clicavel ? 'cursor-pointer' : ''} ${selected ? 'outline-2 outline-offset-2 outline-tile-border-filled' : ''}`}
    >
      {tile.letter}
    </div>
  )
}

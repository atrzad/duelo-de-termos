import { Link } from 'react-router'

import { GameBoard } from '../components/GameBoard'
import { TileLegend } from '../components/TileLegend'
import { buildBoard } from '../features/game/board'
import type { BoardRow } from '../types/game'

// Linhas de demonstração apenas visuais. Nas próximas fases o tabuleiro
// será montado com os resultados oficiais recebidos do backend.
const demoRows: BoardRow[] = [
  [
    { letter: 'R', state: 'present' },
    { letter: 'A', state: 'present' },
    { letter: 'R', state: 'correct' },
    { letter: 'A', state: 'absent' },
    { letter: 'S', state: 'absent' },
  ],
  [
    { letter: 'T', state: 'filled' },
    { letter: 'E', state: 'filled' },
  ],
]

const board = buildBoard(demoRows)

export function GamePage() {
  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-md flex-col gap-8 px-4 py-6">
      <header className="flex items-center justify-between gap-4">
        <Link to="/" className="text-sm font-semibold underline underline-offset-4">
          ← Início
        </Link>
        <h1 className="text-lg font-bold">Duelo de Termos</h1>
        <span className="w-12" aria-hidden="true" />
      </header>

      <GameBoard rows={board} />

      <section aria-labelledby="legend-title" className="grid gap-3">
        <h2
          id="legend-title"
          className="text-sm font-semibold uppercase tracking-wide text-fg-muted"
        >
          Legenda
        </h2>
        <TileLegend />
      </section>
    </main>
  )
}

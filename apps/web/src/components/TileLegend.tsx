import type { LetterState } from '../types/game'
import { LetterTile } from './LetterTile'

const legend: { state: LetterState; letter: string; text: string }[] = [
  { state: 'correct', letter: 'R', text: 'Letra na posição certa' },
  { state: 'present', letter: 'A', text: 'Letra existe, em outra posição' },
  { state: 'absent', letter: 'S', text: 'Letra não está na palavra' },
]

export function TileLegend() {
  return (
    <ul className="grid gap-2 text-sm text-fg-muted">
      {legend.map(({ state, letter, text }) => (
        <li key={state} className="flex items-center gap-3">
          <span className="w-8" role="grid" aria-hidden="true">
            <LetterTile tile={{ letter, state }} size="sm" />
          </span>
          {text}
        </li>
      ))}
    </ul>
  )
}

import type { LetterState } from '../types/game'

const ROWS = [
  ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
  ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
  ['ENTER', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', '⌫'],
]

const keyStateClasses: Record<LetterState | 'default', string> = {
  default: 'bg-tile-border-filled text-fg hover:opacity-80',
  correct: 'bg-tile-correct text-tile-fg',
  present: 'bg-tile-present text-tile-fg',
  absent: 'bg-tile-absent text-tile-fg',
}

const keyLabel: Record<string, string> = {
  ENTER: 'Enviar palpite',
  '⌫': 'Apagar letra',
}

interface KeyboardProps {
  keyStates: Record<string, LetterState | undefined>
  onLetter: (letter: string) => void
  onEnter: () => void
  onBackspace: () => void
}

export function Keyboard({ keyStates, onLetter, onEnter, onBackspace }: KeyboardProps) {
  function handleKeyClick(key: string) {
    if (key === 'ENTER') {
      onEnter()
    } else if (key === '⌫') {
      onBackspace()
    } else {
      onLetter(key)
    }
  }

  return (
    <div className="mx-auto grid w-full max-w-md gap-1.5" role="group" aria-label="Teclado virtual">
      {ROWS.map((row, rowIndex) => (
        <div key={rowIndex} className="flex justify-center gap-1.5">
          {row.map((key) => {
            const isSpecial = key === 'ENTER' || key === '⌫'
            const state = keyStates[key]

            return (
              <button
                key={key}
                type="button"
                onClick={() => {
                  handleKeyClick(key)
                }}
                aria-label={keyLabel[key] ?? key}
                className={`flex h-12 items-center justify-center rounded-md text-sm font-bold uppercase transition-colors ${
                  isSpecial ? 'flex-[1.6] text-xs' : 'flex-1'
                } ${keyStateClasses[state ?? 'default']}`}
              >
                {key}
              </button>
            )
          })}
        </div>
      ))}
    </div>
  )
}

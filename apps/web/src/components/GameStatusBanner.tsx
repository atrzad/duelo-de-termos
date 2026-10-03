interface GameStatusBannerProps {
  status: 'won' | 'lost'
  secretWord: string
  streak: number
  onRestart: () => void
}

export function GameStatusBanner({ status, secretWord, streak, onRestart }: GameStatusBannerProps) {
  const venceu = status === 'won'

  return (
    <div
      role="status"
      aria-live="polite"
      className="grid gap-3 rounded-lg border-2 border-tile-border-filled bg-surface p-4 text-center"
    >
      <p className="text-lg font-bold">{venceu ? 'Você venceu!' : 'Você perdeu.'}</p>
      <p className="text-sm text-fg-muted">
        A palavra era <strong className="uppercase">{secretWord}</strong>.
      </p>
      <p className="text-sm text-fg-muted">
        Sequência atual: <strong>{streak}</strong>
      </p>
      <button type="button" onClick={onRestart} className="btn-primary mx-auto">
        Próxima palavra
      </button>
    </div>
  )
}

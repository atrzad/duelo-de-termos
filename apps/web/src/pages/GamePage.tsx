import { useEffect } from 'react'
import { Link } from 'react-router'

import { GameBoard } from '../components/GameBoard'
import { GameStatusBanner } from '../components/GameStatusBanner'
import { Keyboard } from '../components/Keyboard'
import { TileLegend } from '../components/TileLegend'
import { buildBoard, toBoardRows } from '../features/game/board'
import { useGameState } from '../features/game/useGameState'

export function GamePage() {
  const {
    currentGuess,
    submittedGuesses,
    status,
    message,
    secretWord,
    keyStates,
    streak,
    addLetter,
    removeLetter,
    submitGuess,
    resetGame,
  } = useGameState()

  // Teclado físico: só liga quando a rodada está em andamento (os handlers do
  // hook já se protegem sozinhos, mas nem registrar o listener é mais simples).
  useEffect(() => {
    if (status !== 'playing') return

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Enter') {
        submitGuess()
      } else if (event.key === 'Backspace') {
        removeLetter()
      } else if (/^[a-zA-Z]$/.test(event.key)) {
        addLetter(event.key)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [status, addLetter, removeLetter, submitGuess])

  const board = buildBoard(toBoardRows(submittedGuesses, currentGuess))

  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-md flex-col gap-6 px-4 py-6">
      <header className="flex items-center justify-between gap-4">
        <Link to="/" className="text-sm font-semibold underline underline-offset-4">
          ← Início
        </Link>
        <h1 className="text-lg font-bold">Modo infinito</h1>
        <span
          className="w-12 text-right text-sm text-fg-muted"
          aria-label={`Sequência: ${String(streak)}`}
        >
          🔥{streak}
        </span>
      </header>

      <GameBoard rows={board} />

      <p role="status" aria-live="polite" className="h-5 text-center text-sm text-danger">
        {message}
      </p>

      {status === 'playing' ? (
        <Keyboard
          keyStates={keyStates}
          onLetter={addLetter}
          onEnter={submitGuess}
          onBackspace={removeLetter}
        />
      ) : (
        <GameStatusBanner
          status={status}
          secretWord={secretWord}
          streak={streak}
          onRestart={resetGame}
        />
      )}

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

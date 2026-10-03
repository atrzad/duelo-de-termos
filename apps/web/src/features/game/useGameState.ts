import { useCallback, useMemo, useState } from 'react'

import type { LetterState, SubmittedGuess } from '../../types/game'
import { evaluateGuess } from './evaluateGuess'
import { mesclarEstadosDoTeclado } from './keyStates'
import { palavraAleatoria } from './words'

export const WORD_LENGTH = 5
export const MAX_ATTEMPTS = 6

export type GameStatus = 'playing' | 'won' | 'lost'

export interface GameState {
  currentGuess: string
  submittedGuesses: SubmittedGuess[]
  status: GameStatus
  message: string | null
  secretWord: string
  keyStates: Record<string, LetterState | undefined>
  /** Sequência de palavras acertadas seguidas, no modo infinito. */
  streak: number
}

export interface GameActions {
  addLetter: (letter: string) => void
  removeLetter: () => void
  submitGuess: () => void
  resetGame: () => void
}

export function useGameState(): GameState & GameActions {
  // Modo infinito: cada rodada sorteia uma palavra nova (ver features/game/words.ts).
  const [secretWord, setSecretWord] = useState(() => palavraAleatoria())
  const [currentGuess, setCurrentGuess] = useState('')
  const [submittedGuesses, setSubmittedGuesses] = useState<SubmittedGuess[]>([])
  const [status, setStatus] = useState<GameStatus>('playing')
  const [message, setMessage] = useState<string | null>(null)
  const [streak, setStreak] = useState(0)

  const addLetter = useCallback((letter: string) => {
    if (!/^[a-zA-Z]$/.test(letter)) return
    setMessage(null)
    setCurrentGuess((atual) => (atual.length < WORD_LENGTH ? atual + letter.toUpperCase() : atual))
  }, [])

  const removeLetter = useCallback(() => {
    setMessage(null)
    setCurrentGuess((atual) => atual.slice(0, -1))
  }, [])

  const submitGuess = useCallback(() => {
    setCurrentGuess((atual) => {
      if (atual.length < WORD_LENGTH) {
        setMessage('Palavra incompleta.')
        return atual
      }

      const states = evaluateGuess(atual, secretWord)
      const guess: SubmittedGuess = { letters: atual.split(''), states }
      const acertou = atual === secretWord

      setSubmittedGuesses((tentativasAnteriores) => {
        const proximasTentativas = [...tentativasAnteriores, guess]

        if (acertou) {
          setStatus('won')
          setStreak((valor) => valor + 1)
        } else if (proximasTentativas.length >= MAX_ATTEMPTS) {
          setStatus('lost')
          setStreak(0)
        }

        return proximasTentativas
      })

      setMessage(null)
      return ''
    })
  }, [secretWord])

  const resetGame = useCallback(() => {
    setSecretWord((anterior) => palavraAleatoria(anterior))
    setCurrentGuess('')
    setSubmittedGuesses([])
    setStatus('playing')
    setMessage(null)
  }, [])

  const guardedAddLetter = useCallback(
    (letter: string) => {
      if (status !== 'playing') return
      addLetter(letter)
    },
    [status, addLetter],
  )

  const guardedRemoveLetter = useCallback(() => {
    if (status !== 'playing') return
    removeLetter()
  }, [status, removeLetter])

  const guardedSubmitGuess = useCallback(() => {
    if (status !== 'playing') return
    submitGuess()
  }, [status, submitGuess])

  const keyStates = useMemo(() => mesclarEstadosDoTeclado(submittedGuesses), [submittedGuesses])

  return {
    currentGuess,
    submittedGuesses,
    status,
    message,
    secretWord,
    keyStates,
    streak,
    addLetter: guardedAddLetter,
    removeLetter: guardedRemoveLetter,
    submitGuess: guardedSubmitGuess,
    resetGame,
  }
}

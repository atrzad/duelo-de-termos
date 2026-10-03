import { useCallback, useMemo, useState } from 'react'

import type { LetterState, SubmittedGuess } from '../../types/game'
import { evaluateGuess } from './evaluateGuess'

export const WORD_LENGTH = 5
export const MAX_ATTEMPTS = 6

/**
 * Fase 1: palavra secreta fixa e temporária, só pra validar a mecânica no
 * navegador sem rede. A partir da Fase 2 (motor de regras no backend) o
 * servidor decide a palavra e nunca entrega isso ao cliente durante a rodada.
 */
const SECRET_WORD = 'TERMO'

export type GameStatus = 'playing' | 'won' | 'lost'

export interface GameState {
  currentGuess: string
  submittedGuesses: SubmittedGuess[]
  status: GameStatus
  message: string | null
  secretWord: string
  keyStates: Record<string, LetterState | undefined>
}

export interface GameActions {
  addLetter: (letter: string) => void
  removeLetter: () => void
  submitGuess: () => void
  resetGame: () => void
}

const PRIORIDADE_ESTADO: Record<LetterState, number> = { absent: 0, present: 1, correct: 2 }

function mesclarEstadosDoTeclado(
  guesses: readonly SubmittedGuess[],
): Record<string, LetterState | undefined> {
  const estados: Record<string, LetterState | undefined> = {}

  for (const { letters, states } of guesses) {
    for (let i = 0; i < letters.length; i++) {
      const letra = letters[i]
      const estado = states[i]
      if (letra === undefined || estado === undefined) continue

      const atual = estados[letra]
      if (atual === undefined || PRIORIDADE_ESTADO[estado] > PRIORIDADE_ESTADO[atual]) {
        estados[letra] = estado
      }
    }
  }

  return estados
}

export function useGameState(): GameState & GameActions {
  const [currentGuess, setCurrentGuess] = useState('')
  const [submittedGuesses, setSubmittedGuesses] = useState<SubmittedGuess[]>([])
  const [status, setStatus] = useState<GameStatus>('playing')
  const [message, setMessage] = useState<string | null>(null)

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

      const states = evaluateGuess(atual, SECRET_WORD)
      const guess: SubmittedGuess = { letters: atual.split(''), states }

      setSubmittedGuesses((tentativasAnteriores) => {
        const proximasTentativas = [...tentativasAnteriores, guess]

        if (atual === SECRET_WORD) {
          setStatus('won')
        } else if (proximasTentativas.length >= MAX_ATTEMPTS) {
          setStatus('lost')
        }

        return proximasTentativas
      })

      setMessage(null)
      return ''
    })
  }, [])

  const resetGame = useCallback(() => {
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
    secretWord: SECRET_WORD,
    keyStates,
    addLetter: guardedAddLetter,
    removeLetter: guardedRemoveLetter,
    submitGuess: guardedSubmitGuess,
    resetGame,
  }
}

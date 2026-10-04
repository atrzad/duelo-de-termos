import { useCallback, useMemo, useState } from 'react'

import type { LetterState, SubmittedGuess } from '../../types/game'
import { evaluateGuess } from './evaluateGuess'
import {
  apagarNoCursor,
  escreverNoCursor,
  fixarCursor,
  guessEstaCompleto,
  palpiteVazio,
} from './guessCursor'
import { mesclarEstadosDoTeclado } from './keyStates'
import { palavraEValida } from './palavrasValidas'
import { palavraAleatoria } from './words'

export const WORD_LENGTH = 5
export const MAX_ATTEMPTS = 6

export type GameStatus = 'playing' | 'won' | 'lost'

export interface GameState {
  /** Array de WORD_LENGTH posições ('' = ainda vazia) -- não uma string,
   * porque o cursor pode ser movido pra qualquer quadrado (ver cursor). */
  currentGuess: string[]
  /** Posição do quadrado selecionado na linha em digitação. */
  cursor: number
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
  selectPosition: (indice: number) => void
  submitGuess: () => void
  resetGame: () => void
}

export function useGameState(): GameState & GameActions {
  // Modo infinito: cada rodada sorteia uma palavra nova (ver features/game/words.ts).
  const [secretWord, setSecretWord] = useState(() => palavraAleatoria())
  const [currentGuess, setCurrentGuess] = useState<string[]>(() => palpiteVazio(WORD_LENGTH))
  const [cursor, setCursor] = useState(0)
  const [submittedGuesses, setSubmittedGuesses] = useState<SubmittedGuess[]>([])
  const [status, setStatus] = useState<GameStatus>('playing')
  const [message, setMessage] = useState<string | null>(null)
  const [streak, setStreak] = useState(0)

  const addLetter = useCallback(
    (letter: string) => {
      if (!/^[a-zA-Z]$/.test(letter)) return
      setMessage(null)
      const resultado = escreverNoCursor(currentGuess, cursor, letter.toUpperCase())
      setCurrentGuess(resultado.guess)
      setCursor(resultado.cursor)
    },
    [currentGuess, cursor],
  )

  const removeLetter = useCallback(() => {
    setMessage(null)
    const resultado = apagarNoCursor(currentGuess, cursor)
    setCurrentGuess(resultado.guess)
    setCursor(resultado.cursor)
  }, [currentGuess, cursor])

  const selectPosition = useCallback((indice: number) => {
    setCursor(fixarCursor(indice, WORD_LENGTH))
  }, [])

  const submitGuess = useCallback(() => {
    setCurrentGuess((atual) => {
      if (!guessEstaCompleto(atual)) {
        setMessage('Palavra incompleta.')
        return atual
      }

      const palavra = atual.join('')
      if (!palavraEValida(palavra)) {
        setMessage('Essa palavra não existe.')
        return atual
      }

      const states = evaluateGuess(palavra, secretWord)
      const guess: SubmittedGuess = { letters: atual, states }
      const acertou = palavra === secretWord

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
      setCursor(0)
      return palpiteVazio(WORD_LENGTH)
    })
  }, [secretWord])

  const resetGame = useCallback(() => {
    setSecretWord((anterior) => palavraAleatoria(anterior))
    setCurrentGuess(palpiteVazio(WORD_LENGTH))
    setCursor(0)
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

  const guardedSelectPosition = useCallback(
    (indice: number) => {
      if (status !== 'playing') return
      selectPosition(indice)
    },
    [status, selectPosition],
  )

  const guardedSubmitGuess = useCallback(() => {
    if (status !== 'playing') return
    submitGuess()
  }, [status, submitGuess])

  const keyStates = useMemo(() => mesclarEstadosDoTeclado(submittedGuesses), [submittedGuesses])

  return {
    currentGuess,
    cursor,
    submittedGuesses,
    status,
    message,
    secretWord,
    keyStates,
    streak,
    addLetter: guardedAddLetter,
    removeLetter: guardedRemoveLetter,
    selectPosition: guardedSelectPosition,
    submitGuess: guardedSubmitGuess,
    resetGame,
  }
}

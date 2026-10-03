import type { LetterState } from '../../types/game'

/**
 * Avalia um palpite contra a palavra secreta, posição a posição.
 * Função pura — sem estado, sem efeitos colaterais.
 *
 * Trata letras repetidas em duas passadas (como o Wordle/Termo original):
 * 1ª passada marca os acertos exatos e sobra quantas vezes cada letra não-acertada
 * ainda existe no segredo; 2ª passada consome essa sobra pra decidir 'present'/'absent'.
 * Isso evita marcar uma letra repetida como presente mais vezes do que ela realmente
 * aparece no segredo.
 */
export function evaluateGuess(guess: string, secret: string): LetterState[] {
  const guessLetters = guess.toUpperCase().split('')
  const secretLetters = secret.toUpperCase().split('')
  const length = secretLetters.length

  const states: LetterState[] = new Array<LetterState>(length).fill('absent')
  const sobraNoSegredo: Record<string, number> = {}

  for (let i = 0; i < length; i++) {
    if (guessLetters[i] === secretLetters[i]) {
      states[i] = 'correct'
    } else {
      const letra = secretLetters[i] ?? ''
      sobraNoSegredo[letra] = (sobraNoSegredo[letra] ?? 0) + 1
    }
  }

  for (let i = 0; i < length; i++) {
    if (states[i] === 'correct') continue

    const letra = guessLetters[i] ?? ''
    const restante = sobraNoSegredo[letra] ?? 0
    if (restante > 0) {
      states[i] = 'present'
      sobraNoSegredo[letra] = restante - 1
    }
  }

  return states
}

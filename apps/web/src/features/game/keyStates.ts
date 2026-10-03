import type { LetterState, SubmittedGuess } from '../../types/game'

const PRIORIDADE_ESTADO: Record<LetterState, number> = { absent: 0, present: 1, correct: 2 }

/** Agrega, por letra, o melhor estado já visto nas tentativas — pra colorir o teclado. */
export function mesclarEstadosDoTeclado(
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

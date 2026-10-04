/**
 * Lógica pura de edição do palpite em digitação com cursor móvel: em vez de
 * só acrescentar/apagar no final (string), o palpite é um array de tamanho
 * fixo (uma posição por quadrado do tabuleiro, '' = vazia) e o cursor pode
 * ser movido pra qualquer posição clicando num quadrado. Compartilhado entre
 * o modo solo (useGameState) e o 1v1 (useDuel) pra não duplicar a regra.
 */

export function palpiteVazio(wordLength: number): string[] {
  return Array.from({ length: wordLength }, () => '')
}

export function fixarCursor(cursor: number, wordLength: number): number {
  return Math.min(Math.max(cursor, 0), wordLength - 1)
}

/** Digitar sempre sobrescreve a posição do cursor e avança pra direita. */
export function escreverNoCursor(
  guess: readonly string[],
  cursor: number,
  letra: string,
): { guess: string[]; cursor: number } {
  const novoGuess = [...guess]
  novoGuess[cursor] = letra
  return { guess: novoGuess, cursor: fixarCursor(cursor + 1, guess.length) }
}

/** Backspace sempre apaga a posição do cursor (não-op se já vazia) e volta
 * o cursor uma posição pra esquerda -- reproduz "remover a última letra"
 * quando o cursor nunca foi movido manualmente. */
export function apagarNoCursor(
  guess: readonly string[],
  cursor: number,
): { guess: string[]; cursor: number } {
  const novoGuess = [...guess]
  novoGuess[cursor] = ''
  return { guess: novoGuess, cursor: fixarCursor(cursor - 1, guess.length) }
}

export function guessEstaCompleto(guess: readonly string[]): boolean {
  return guess.every((letra) => letra !== '')
}

import type { BoardRow, SubmittedGuess, Tile } from '../../types/game'

export const WORD_LENGTH = 5
export const REGULAR_ATTEMPTS = 6

const EMPTY_TILE: Tile = { letter: '', state: 'empty' }

/**
 * Completa as linhas recebidas até formar a grade visual (6×5 por padrão).
 * Função pura de apresentação: não avalia palpites.
 */
export function buildBoard(
  rows: readonly BoardRow[],
  rowCount: number = REGULAR_ATTEMPTS,
  wordLength: number = WORD_LENGTH,
): BoardRow[] {
  return Array.from({ length: Math.max(rowCount, rows.length) }, (_, rowIndex) => {
    const row = rows[rowIndex] ?? []
    return Array.from({ length: wordLength }, (_, colIndex) => row[colIndex] ?? EMPTY_TILE)
  })
}

/**
 * Converte as tentativas já enviadas + o palpite em digitação numa lista de
 * linhas visuais (BoardRow[]). Função pura de apresentação: não avalia nada,
 * só traduz o estado do jogo pro formato que o tabuleiro sabe desenhar.
 *
 * `currentGuess` é um array de tamanho fixo (WORD_LENGTH posições, '' onde
 * ainda não foi digitada nenhuma letra) — não uma string — porque o cursor
 * pode ser movido pra qualquer posição (clique num quadrado), deixando
 * buracos no meio da palavra em digitação.
 */
export function toBoardRows(
  submittedGuesses: readonly SubmittedGuess[],
  currentGuess: readonly string[],
): BoardRow[] {
  const linhasEnviadas: BoardRow[] = submittedGuesses.map(({ letters, states }) =>
    letters.map((letter, index) => ({ letter, state: states[index] ?? 'absent' })),
  )

  if (currentGuess.every((letra) => letra === '')) {
    return linhasEnviadas
  }

  const linhaAtual: BoardRow = currentGuess.map((letra) => ({
    letter: letra,
    state: letra === '' ? 'empty' : 'filled',
  }))

  return [...linhasEnviadas, linhaAtual]
}

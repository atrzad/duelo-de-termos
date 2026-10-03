/**
 * Estados oficiais de uma letra avaliada. A partir da Fase 2 (motor de regras
 * no backend) quem calcula isso é sempre o servidor; na Fase 1 (jogo local,
 * sem rede) o cálculo roda no frontend via evaluateGuess().
 */
export type LetterState = 'correct' | 'present' | 'absent'

/** Estados visuais de uma célula: avaliada, digitada (ainda não enviada) ou vazia. */
export type TileState = LetterState | 'filled' | 'empty'

export interface Tile {
  letter: string
  state: TileState
}

export type BoardRow = readonly Tile[]

/** Uma tentativa já enviada: as letras digitadas e o resultado de evaluateGuess(). */
export interface SubmittedGuess {
  letters: readonly string[]
  states: readonly LetterState[]
}

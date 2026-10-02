/** Estados oficiais de uma letra avaliada. Quem calcula é sempre o backend. */
export type LetterState = 'correct' | 'present' | 'absent'

/** Estados visuais de uma célula: avaliada, digitada (ainda não enviada) ou vazia. */
export type TileState = LetterState | 'filled' | 'empty'

export interface Tile {
  letter: string
  state: TileState
}

export type BoardRow = readonly Tile[]

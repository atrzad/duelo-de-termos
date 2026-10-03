import type { LetterState } from '../../types/game'

export interface SalaCriadaPayload {
  codigo: string
}

export interface PartidaIniciadaPayload {
  oponente: string
}

export interface ResultadoPalpitePayload {
  letras: string[]
  estados: LetterState[]
  tentativasRestantes: number
}

export interface OponenteJogouPayload {
  tentativasUsadas: number
}

export type ResultadoFinal = 'venceu' | 'perdeu' | 'empate'

export interface FimDeJogoPayload {
  resultado: ResultadoFinal
  palavraSecreta: string
}

export interface ErroPayload {
  mensagem: string
}

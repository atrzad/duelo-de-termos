import type { LetterState } from '../../types/game'

export type GameMode = 'normal' | 'competitivo' | 'hardcore'

export const MODOS: { valor: GameMode; rotulo: string; descricao: string }[] = [
  {
    valor: 'competitivo',
    rotulo: 'Competitivo',
    descricao: '6 tentativas cada, sem timer. Quem usa menos tentativas pontua mais.',
  },
  {
    valor: 'hardcore',
    rotulo: 'Hardcore',
    descricao: '90s no relógio. O primeiro a acertar vence a partida na hora.',
  },
  {
    valor: 'normal',
    rotulo: 'Normal',
    descricao:
      '90s + prorrogação enquanto o tempo não acaba, e 1 tentativa final pra quem não acertou.',
  },
]

export interface SalaCriadaPayload {
  codigo: string
  modo: GameMode
}

export interface PartidaIniciadaPayload {
  oponente: string
  modo: GameMode
  duracaoSegundos: number | null
}

export interface ResultadoPalpitePayload {
  letras: string[]
  estados: LetterState[]
  numeroTentativa: number
}

export interface OponenteJogouPayload {
  tentativasUsadas: number
}

export type ResultadoFinal = 'venceu' | 'perdeu' | 'empate'

export interface FimDeJogoPayload {
  resultado: ResultadoFinal
  palavraSecreta: string
  meusPontos: number
  pontosOponente: number
}

export interface ErroPayload {
  mensagem: string
}

import type { LetterState } from '../../types/game'

export type GameMode = 'normal' | 'competitivo' | 'hardcore' | 'infinito'

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
  {
    valor: 'infinito',
    rotulo: 'Infinito',
    descricao: 'Rodada atrás de rodada contra o mesmo oponente. O placar acumula até alguém sair.',
  },
]

export interface SalaCriadaPayload {
  codigo: string
  modo: GameMode
  meuToken: string
}

export interface PartidaIniciadaPayload {
  codigo: string
  oponente: string
  modo: GameMode
  duracaoSegundos: number | null
  // Só relevantes no modo Infinito: número da rodada atual e placar
  // acumulado entre rodadas. Nos outros 3 modos ficam em 1 / 0 / 0.
  rodada: number
  meuTotal: number
  totalOponente: number
  meuToken: string
}

export interface ReconectadoPayload {
  oponente: string
  modo: GameMode
  duracaoSegundos: number | null
  rodada: number
  meuTotal: number
  totalOponente: number
  meuToken: string
  minhasTentativas: { letras: string[]; estados: LetterState[] }[]
  tentativasOponente: number
  tempoEsgotado: boolean
  euConclui: boolean
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

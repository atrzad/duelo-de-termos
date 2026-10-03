import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { mesclarEstadosDoTeclado } from '../game/keyStates'
import type { LetterState, SubmittedGuess } from '../../types/game'
import { getSocket } from './socket'
import { carregarSessao, limparSessao, salvarSessao } from './sessao'
import type {
  ErroPayload,
  FimDeJogoPayload,
  GameMode,
  OponenteJogouPayload,
  PartidaIniciadaPayload,
  ReconectadoPayload,
  ResultadoFinal,
  ResultadoPalpitePayload,
  SalaCriadaPayload,
} from './types'

export const WORD_LENGTH = 5
export const MAX_ATTEMPTS = 6

export type FaseDuelo = 'lobby' | 'aguardando' | 'reconectando' | 'jogando' | 'fim'

export interface DuelState {
  fase: FaseDuelo
  codigo: string | null
  modo: GameMode | null
  duracaoSegundos: number | null
  nomeOponente: string | null
  currentGuess: string
  submittedGuesses: SubmittedGuess[]
  tentativasOponente: number
  tempoEsgotado: boolean
  resultadoFinal: ResultadoFinal | null
  palavraSecreta: string | null
  meusPontos: number | null
  pontosOponente: number | null
  mensagemErro: string | null
  oponenteSaiu: boolean
  /** Oponente caiu, mas ainda está dentro da janela de 30s pra reconectar
   * (seção 14 do PROJECT_SCOPE.md) -- a partida continua, só avisa. */
  oponenteDesconectadoTemporariamente: boolean
  // Revanche direta (fora da seção 9, pedido à parte): só faz sentido na
  // tela de fim de jogo (fase 'fim', sem o oponente ter saído).
  euPediRevanche: boolean
  oponentePediuRevanche: boolean
  // Só usados no modo Infinito (ver types.ts).
  rodada: number
  meuTotal: number
  totalOponente: number
}

export interface DuelActions {
  criarSala: (nome: string, modo: GameMode) => void
  entrarSala: (nome: string, codigo: string) => void
  addLetter: (letter: string) => void
  removeLetter: () => void
  enviarPalpite: () => void
  pedirRevanche: () => void
  reiniciar: () => void
}

const ESTADO_INICIAL: DuelState = {
  fase: 'lobby',
  codigo: null,
  modo: null,
  duracaoSegundos: null,
  nomeOponente: null,
  currentGuess: '',
  submittedGuesses: [],
  tentativasOponente: 0,
  tempoEsgotado: false,
  resultadoFinal: null,
  palavraSecreta: null,
  meusPontos: null,
  pontosOponente: null,
  mensagemErro: null,
  oponenteSaiu: false,
  oponenteDesconectadoTemporariamente: false,
  euPediRevanche: false,
  oponentePediuRevanche: false,
  rodada: 1,
  meuTotal: 0,
  totalOponente: 0,
}

interface DuelDerived {
  keyStates: Record<string, LetterState | undefined>
  /** Já não pode mais jogar nesta partida (acertou, esgotou tentativas
   * regulares no Competitivo, ou já usou a tentativa final no Normal) mas a
   * partida pode continuar rolando pro lado do oponente. */
  euConclui: boolean
}

function calcularEuConclui(
  submittedGuesses: readonly SubmittedGuess[],
  modo: GameMode | null,
  tempoEsgotado: boolean,
): boolean {
  if (submittedGuesses.length === 0) return false

  const ultima = submittedGuesses[submittedGuesses.length - 1]
  if (ultima?.states.every((estado) => estado === 'correct')) return true

  if (modo === 'competitivo' || modo === 'infinito') return submittedGuesses.length >= MAX_ATTEMPTS
  if (modo === 'normal') return tempoEsgotado
  return false
}

function estadoInicialComSessao(): DuelState {
  // Lazy initializer (roda só na 1ª renderização, nunca num efeito) -- é
  // aqui, não num setState dentro de effect, que a fase vira 'reconectando'
  // quando já existe uma sessão salva (react-hooks/set-state-in-effect não
  // deixa um effect fazer isso sozinho).
  return carregarSessao() ? { ...ESTADO_INICIAL, fase: 'reconectando' } : ESTADO_INICIAL
}

export function useDuel(): DuelState & DuelActions & DuelDerived {
  const [estado, setEstado] = useState<DuelState>(estadoInicialComSessao)

  // Pra ler o palpite atual / a fase dentro de callbacks estáveis (useCallback
  // com deps vazias), sem recriar a função a cada letra digitada. Atualizados
  // depois da renderização (nunca durante) — regra do react-hooks/refs.
  const currentGuessRef = useRef('')
  const faseRef = useRef<FaseDuelo>('lobby')
  const euConcluiRef = useRef(false)
  useEffect(() => {
    currentGuessRef.current = estado.currentGuess
    faseRef.current = estado.fase
    euConcluiRef.current = calcularEuConclui(
      estado.submittedGuesses,
      estado.modo,
      estado.tempoEsgotado,
    )
  })

  useEffect(() => {
    const socket = getSocket()
    socket.connect()

    const aoSalaCriada = (dados: SalaCriadaPayload) => {
      salvarSessao({ token: dados.meuToken, codigo: dados.codigo })
      setEstado((anterior) => ({
        ...anterior,
        fase: 'aguardando',
        codigo: dados.codigo,
        modo: dados.modo,
      }))
    }

    const aoAguardandoOponente = () => {
      setEstado((anterior) => ({ ...anterior, fase: 'aguardando' }))
    }

    const aoPartidaIniciada = (dados: PartidaIniciadaPayload) => {
      salvarSessao({ token: dados.meuToken, codigo: dados.codigo })
      setEstado((anterior) => ({
        ...anterior,
        fase: 'jogando',
        codigo: dados.codigo,
        modo: dados.modo,
        duracaoSegundos: dados.duracaoSegundos,
        nomeOponente: dados.oponente,
        currentGuess: '',
        submittedGuesses: [],
        tentativasOponente: 0,
        tempoEsgotado: false,
        resultadoFinal: null,
        palavraSecreta: null,
        meusPontos: null,
        pontosOponente: null,
        oponenteSaiu: false,
        oponenteDesconectadoTemporariamente: false,
        euPediRevanche: false,
        oponentePediuRevanche: false,
        mensagemErro: null,
        rodada: dados.rodada,
        meuTotal: dados.meuTotal,
        totalOponente: dados.totalOponente,
      }))
    }

    const aoRevanchePedida = () => {
      setEstado((anterior) => ({ ...anterior, oponentePediuRevanche: true }))
    }

    const aoReconectado = (dados: ReconectadoPayload) => {
      setEstado((anterior) => ({
        ...anterior,
        fase: 'jogando',
        modo: dados.modo,
        duracaoSegundos: dados.duracaoSegundos,
        nomeOponente: dados.oponente,
        currentGuess: '',
        submittedGuesses: dados.minhasTentativas.map((t) => ({
          letters: t.letras,
          states: t.estados,
        })),
        tentativasOponente: dados.tentativasOponente,
        tempoEsgotado: dados.tempoEsgotado,
        resultadoFinal: null,
        palavraSecreta: null,
        meusPontos: null,
        pontosOponente: null,
        oponenteSaiu: false,
        oponenteDesconectadoTemporariamente: false,
        euPediRevanche: false,
        oponentePediuRevanche: false,
        mensagemErro: null,
        rodada: dados.rodada,
        meuTotal: dados.meuTotal,
        totalOponente: dados.totalOponente,
      }))
    }

    const aoOponenteDesconectadoTemporariamente = () => {
      setEstado((anterior) => ({ ...anterior, oponenteDesconectadoTemporariamente: true }))
    }

    const aoOponenteReconectou = () => {
      setEstado((anterior) => ({ ...anterior, oponenteDesconectadoTemporariamente: false }))
    }

    const aoResultadoPalpite = (dados: ResultadoPalpitePayload) => {
      setEstado((anterior) => ({
        ...anterior,
        currentGuess: '',
        mensagemErro: null,
        submittedGuesses: [
          ...anterior.submittedGuesses,
          { letters: dados.letras, states: dados.estados },
        ],
      }))
    }

    const aoOponenteJogou = (dados: OponenteJogouPayload) => {
      setEstado((anterior) => ({ ...anterior, tentativasOponente: dados.tentativasUsadas }))
    }

    const aoTempoEsgotado = () => {
      setEstado((anterior) => ({ ...anterior, tempoEsgotado: true, currentGuess: '' }))
    }

    const aoFimDeJogo = (dados: FimDeJogoPayload) => {
      limparSessao()
      setEstado((anterior) => ({
        ...anterior,
        fase: 'fim',
        resultadoFinal: dados.resultado,
        palavraSecreta: dados.palavraSecreta,
        meusPontos: dados.meusPontos,
        pontosOponente: dados.pontosOponente,
      }))
    }

    const aoOponenteSaiu = () => {
      limparSessao()
      setEstado((anterior) => ({ ...anterior, fase: 'fim', oponenteSaiu: true }))
    }

    const aoErro = (dados: ErroPayload) => {
      setEstado((anterior) => {
        // Se o erro chegou durante uma tentativa de reconexão automática
        // (token expirado, sala não existe mais etc.), não trava no limbo:
        // limpa a sessão e volta pro lobby.
        if (anterior.fase === 'reconectando') {
          limparSessao()
          return { ...ESTADO_INICIAL, mensagemErro: dados.mensagem }
        }
        return { ...anterior, mensagemErro: dados.mensagem }
      })
    }

    socket.on('sala_criada', aoSalaCriada)
    socket.on('aguardando_oponente', aoAguardandoOponente)
    socket.on('partida_iniciada', aoPartidaIniciada)
    socket.on('reconectado', aoReconectado)
    socket.on('oponente_desconectado_temporariamente', aoOponenteDesconectadoTemporariamente)
    socket.on('oponente_reconectou', aoOponenteReconectou)
    socket.on('revanche_pedida', aoRevanchePedida)
    socket.on('resultado_palpite', aoResultadoPalpite)
    socket.on('oponente_jogou', aoOponenteJogou)
    socket.on('tempo_esgotado', aoTempoEsgotado)
    socket.on('fim_de_jogo', aoFimDeJogo)
    socket.on('oponente_saiu', aoOponenteSaiu)
    socket.on('erro', aoErro)

    const sessaoSalva = carregarSessao()
    if (sessaoSalva) {
      socket.emit('reconectar', { token: sessaoSalva.token })
    }

    return () => {
      socket.off('sala_criada', aoSalaCriada)
      socket.off('aguardando_oponente', aoAguardandoOponente)
      socket.off('partida_iniciada', aoPartidaIniciada)
      socket.off('reconectado', aoReconectado)
      socket.off('oponente_desconectado_temporariamente', aoOponenteDesconectadoTemporariamente)
      socket.off('oponente_reconectou', aoOponenteReconectou)
      socket.off('revanche_pedida', aoRevanchePedida)
      socket.off('resultado_palpite', aoResultadoPalpite)
      socket.off('oponente_jogou', aoOponenteJogou)
      socket.off('tempo_esgotado', aoTempoEsgotado)
      socket.off('fim_de_jogo', aoFimDeJogo)
      socket.off('oponente_saiu', aoOponenteSaiu)
      socket.off('erro', aoErro)
      socket.disconnect()
    }
  }, [])

  const criarSala = useCallback((nome: string, modo: GameMode) => {
    setEstado((anterior) => ({ ...anterior, mensagemErro: null }))
    getSocket().emit('criar_sala', { nome, modo })
  }, [])

  const entrarSala = useCallback((nome: string, codigo: string) => {
    setEstado((anterior) => ({ ...anterior, mensagemErro: null }))
    getSocket().emit('entrar_sala', { nome, codigo: codigo.toUpperCase() })
  }, [])

  const addLetter = useCallback((letter: string) => {
    if (faseRef.current !== 'jogando' || euConcluiRef.current) return
    if (!/^[a-zA-Z]$/.test(letter)) return
    setEstado((anterior) => {
      if (anterior.currentGuess.length >= WORD_LENGTH) return anterior
      return { ...anterior, currentGuess: anterior.currentGuess + letter.toUpperCase() }
    })
  }, [])

  const removeLetter = useCallback(() => {
    if (faseRef.current !== 'jogando' || euConcluiRef.current) return
    setEstado((anterior) => ({ ...anterior, currentGuess: anterior.currentGuess.slice(0, -1) }))
  }, [])

  const enviarPalpite = useCallback(() => {
    if (faseRef.current !== 'jogando' || euConcluiRef.current) return
    const palavra = currentGuessRef.current
    if (palavra.length < WORD_LENGTH) {
      setEstado((anterior) => ({ ...anterior, mensagemErro: 'Palavra incompleta.' }))
      return
    }
    getSocket().emit('enviar_palpite', { palavra })
  }, [])

  const pedirRevanche = useCallback(() => {
    if (faseRef.current !== 'fim') return
    setEstado((anterior) => ({ ...anterior, euPediRevanche: true }))
    getSocket().emit('pedir_revanche', {})
  }, [])

  const reiniciar = useCallback(() => {
    limparSessao()
    setEstado(ESTADO_INICIAL)
  }, [])

  const keyStates = useMemo(
    () => mesclarEstadosDoTeclado(estado.submittedGuesses),
    [estado.submittedGuesses],
  )

  const euConclui = calcularEuConclui(estado.submittedGuesses, estado.modo, estado.tempoEsgotado)

  return {
    ...estado,
    keyStates,
    euConclui,
    criarSala,
    entrarSala,
    addLetter,
    removeLetter,
    enviarPalpite,
    pedirRevanche,
    reiniciar,
  }
}

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { mesclarEstadosDoTeclado } from '../game/keyStates'
import type { LetterState, SubmittedGuess } from '../../types/game'
import { getSocket } from './socket'
import type {
  ErroPayload,
  FimDeJogoPayload,
  GameMode,
  OponenteJogouPayload,
  PartidaIniciadaPayload,
  ResultadoFinal,
  ResultadoPalpitePayload,
  SalaCriadaPayload,
} from './types'

export const WORD_LENGTH = 5
export const MAX_ATTEMPTS = 6

export type FaseDuelo = 'lobby' | 'aguardando' | 'jogando' | 'fim'

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
}

export interface DuelActions {
  criarSala: (nome: string, modo: GameMode) => void
  entrarSala: (nome: string, codigo: string) => void
  addLetter: (letter: string) => void
  removeLetter: () => void
  enviarPalpite: () => void
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

  if (modo === 'competitivo') return submittedGuesses.length >= MAX_ATTEMPTS
  if (modo === 'normal') return tempoEsgotado
  return false
}

export function useDuel(): DuelState & DuelActions & DuelDerived {
  const [estado, setEstado] = useState<DuelState>(ESTADO_INICIAL)

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
      setEstado((anterior) => ({
        ...anterior,
        fase: 'jogando',
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
        mensagemErro: null,
      }))
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
      setEstado((anterior) => ({ ...anterior, fase: 'fim', oponenteSaiu: true }))
    }

    const aoErro = (dados: ErroPayload) => {
      setEstado((anterior) => ({ ...anterior, mensagemErro: dados.mensagem }))
    }

    socket.on('sala_criada', aoSalaCriada)
    socket.on('aguardando_oponente', aoAguardandoOponente)
    socket.on('partida_iniciada', aoPartidaIniciada)
    socket.on('resultado_palpite', aoResultadoPalpite)
    socket.on('oponente_jogou', aoOponenteJogou)
    socket.on('tempo_esgotado', aoTempoEsgotado)
    socket.on('fim_de_jogo', aoFimDeJogo)
    socket.on('oponente_saiu', aoOponenteSaiu)
    socket.on('erro', aoErro)

    return () => {
      socket.off('sala_criada', aoSalaCriada)
      socket.off('aguardando_oponente', aoAguardandoOponente)
      socket.off('partida_iniciada', aoPartidaIniciada)
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

  const reiniciar = useCallback(() => {
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
    reiniciar,
  }
}

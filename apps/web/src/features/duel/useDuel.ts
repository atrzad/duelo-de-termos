import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { mesclarEstadosDoTeclado } from '../game/keyStates'
import type { LetterState, SubmittedGuess } from '../../types/game'
import { getSocket } from './socket'
import type {
  ErroPayload,
  FimDeJogoPayload,
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
  nomeOponente: string | null
  currentGuess: string
  submittedGuesses: SubmittedGuess[]
  tentativasOponente: number
  resultadoFinal: ResultadoFinal | null
  palavraSecreta: string | null
  mensagemErro: string | null
  oponenteSaiu: boolean
}

export interface DuelActions {
  criarSala: (nome: string) => void
  entrarSala: (nome: string, codigo: string) => void
  addLetter: (letter: string) => void
  removeLetter: () => void
  enviarPalpite: () => void
  reiniciar: () => void
}

const ESTADO_INICIAL: DuelState = {
  fase: 'lobby',
  codigo: null,
  nomeOponente: null,
  currentGuess: '',
  submittedGuesses: [],
  tentativasOponente: 0,
  resultadoFinal: null,
  palavraSecreta: null,
  mensagemErro: null,
  oponenteSaiu: false,
}

interface DuelDerived {
  keyStates: Record<string, LetterState | undefined>
}

export function useDuel(): DuelState & DuelActions & DuelDerived {
  const [estado, setEstado] = useState<DuelState>(ESTADO_INICIAL)

  // Pra ler o palpite atual dentro de um callback estável (useCallback com
  // deps vazias), sem recriar a função a cada letra digitada. Atualizados
  // depois da renderização (nunca durante) — regra do react-hooks/refs.
  const currentGuessRef = useRef('')
  const faseRef = useRef<FaseDuelo>('lobby')
  useEffect(() => {
    currentGuessRef.current = estado.currentGuess
    faseRef.current = estado.fase
  })

  useEffect(() => {
    const socket = getSocket()
    socket.connect()

    const aoSalaCriada = (dados: SalaCriadaPayload) => {
      setEstado((anterior) => ({ ...anterior, fase: 'aguardando', codigo: dados.codigo }))
    }

    const aoAguardandoOponente = () => {
      setEstado((anterior) => ({ ...anterior, fase: 'aguardando' }))
    }

    const aoPartidaIniciada = (dados: PartidaIniciadaPayload) => {
      setEstado((anterior) => ({
        ...anterior,
        fase: 'jogando',
        nomeOponente: dados.oponente,
        currentGuess: '',
        submittedGuesses: [],
        tentativasOponente: 0,
        resultadoFinal: null,
        palavraSecreta: null,
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

    const aoFimDeJogo = (dados: FimDeJogoPayload) => {
      setEstado((anterior) => ({
        ...anterior,
        fase: 'fim',
        resultadoFinal: dados.resultado,
        palavraSecreta: dados.palavraSecreta,
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
    socket.on('fim_de_jogo', aoFimDeJogo)
    socket.on('oponente_saiu', aoOponenteSaiu)
    socket.on('erro', aoErro)

    return () => {
      socket.off('sala_criada', aoSalaCriada)
      socket.off('aguardando_oponente', aoAguardandoOponente)
      socket.off('partida_iniciada', aoPartidaIniciada)
      socket.off('resultado_palpite', aoResultadoPalpite)
      socket.off('oponente_jogou', aoOponenteJogou)
      socket.off('fim_de_jogo', aoFimDeJogo)
      socket.off('oponente_saiu', aoOponenteSaiu)
      socket.off('erro', aoErro)
      socket.disconnect()
    }
  }, [])

  const criarSala = useCallback((nome: string) => {
    setEstado((anterior) => ({ ...anterior, mensagemErro: null }))
    getSocket().emit('criar_sala', { nome })
  }, [])

  const entrarSala = useCallback((nome: string, codigo: string) => {
    setEstado((anterior) => ({ ...anterior, mensagemErro: null }))
    getSocket().emit('entrar_sala', { nome, codigo: codigo.toUpperCase() })
  }, [])

  const addLetter = useCallback((letter: string) => {
    if (faseRef.current !== 'jogando') return
    if (!/^[a-zA-Z]$/.test(letter)) return
    setEstado((anterior) => {
      if (anterior.currentGuess.length >= WORD_LENGTH) return anterior
      return { ...anterior, currentGuess: anterior.currentGuess + letter.toUpperCase() }
    })
  }, [])

  const removeLetter = useCallback(() => {
    if (faseRef.current !== 'jogando') return
    setEstado((anterior) => ({ ...anterior, currentGuess: anterior.currentGuess.slice(0, -1) }))
  }, [])

  const enviarPalpite = useCallback(() => {
    if (faseRef.current !== 'jogando') return
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

  return {
    ...estado,
    keyStates,
    criarSala,
    entrarSala,
    addLetter,
    removeLetter,
    enviarPalpite,
    reiniciar,
  }
}

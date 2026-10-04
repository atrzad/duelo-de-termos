import { useEffect, useState } from 'react'
import type { SubmitEvent } from 'react'
import { Link } from 'react-router'

import { GameBoard } from '../components/GameBoard'
import { Keyboard } from '../components/Keyboard'
import { OpponentProgress } from '../components/OpponentProgress'
import { buildBoard, toBoardRows } from '../features/game/board'
import { MAX_ATTEMPTS, useDuel } from '../features/duel/useDuel'
import { useCountdown } from '../features/duel/useCountdown'
import { MODOS } from '../features/duel/types'
import type { GameMode } from '../features/duel/types'

const RESULTADO_TEXTO: Record<string, string> = {
  venceu: 'Você venceu!',
  perdeu: 'Você perdeu.',
  empate: 'Empate.',
}

function formatarTempo(segundos: number): string {
  const minutos = Math.floor(segundos / 60)
  const resto = segundos % 60
  return `${String(minutos)}:${String(resto).padStart(2, '0')}`
}

export function DuelPage() {
  const {
    fase,
    codigo,
    modo,
    duracaoSegundos,
    nomeOponente,
    currentGuess,
    cursor,
    submittedGuesses,
    keyStates,
    euConclui,
    tentativasOponente,
    tempoEsgotado,
    resultadoFinal,
    palavraSecreta,
    meusPontos,
    pontosOponente,
    mensagemErro,
    oponenteSaiu,
    oponenteDesconectadoTemporariamente,
    euPediRevanche,
    oponentePediuRevanche,
    rodada,
    meuTotal,
    totalOponente,
    criarSala,
    entrarSala,
    addLetter,
    removeLetter,
    selectPosition,
    enviarPalpite,
    pedirRevanche,
    reiniciar,
  } = useDuel()

  const [nome, setNome] = useState('')
  const [codigoDigitado, setCodigoDigitado] = useState('')
  const [modoEscolhido, setModoEscolhido] = useState<GameMode>('competitivo')

  const tempoRestante = useCountdown(duracaoSegundos, fase === 'jogando' && !tempoEsgotado)

  useEffect(() => {
    if (fase !== 'jogando' || euConclui) return

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Enter') {
        enviarPalpite()
      } else if (event.key === 'Backspace') {
        removeLetter()
      } else if (/^[a-zA-Z]$/.test(event.key)) {
        addLetter(event.key)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [fase, euConclui, addLetter, removeLetter, enviarPalpite])

  function handleCriar(event: SubmitEvent) {
    event.preventDefault()
    if (nome.trim().length === 0) return
    criarSala(nome.trim(), modoEscolhido)
  }

  function handleEntrar(event: SubmitEvent) {
    event.preventDefault()
    if (nome.trim().length === 0 || codigoDigitado.trim().length !== 4) return
    entrarSala(nome.trim(), codigoDigitado.trim())
  }

  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-md flex-col gap-6 px-4 py-6">
      <header className="flex items-center justify-between gap-4">
        <Link to="/" className="text-sm font-semibold underline underline-offset-4">
          ← Início
        </Link>
        <h1 className="text-lg font-bold">Duelo 1v1</h1>
        <span className="w-12 text-right text-xs font-bold text-fg-muted">
          {fase === 'jogando' && tempoRestante !== null ? formatarTempo(tempoRestante) : ''}
        </span>
      </header>

      {mensagemErro && (
        <p role="alert" className="text-center text-sm text-danger">
          {mensagemErro}
        </p>
      )}

      {fase === 'lobby' && (
        <div className="grid gap-6">
          <form onSubmit={handleCriar} className="grid gap-3">
            <label className="grid gap-1 text-sm">
              Seu nome
              <input
                value={nome}
                onChange={(evento) => {
                  setNome(evento.target.value)
                }}
                maxLength={24}
                className="rounded-md border-2 border-border bg-surface px-3 py-2"
                placeholder="Como quer ser chamado"
              />
            </label>

            <fieldset className="grid gap-2">
              <legend className="text-sm font-semibold">Modo</legend>
              {MODOS.map((opcao) => (
                <label
                  key={opcao.valor}
                  className="flex cursor-pointer items-start gap-2 rounded-md border-2 border-border bg-surface p-2 text-sm has-[:checked]:border-tile-border-filled"
                >
                  <input
                    type="radio"
                    name="modo"
                    value={opcao.valor}
                    checked={modoEscolhido === opcao.valor}
                    onChange={() => {
                      setModoEscolhido(opcao.valor)
                    }}
                    className="mt-1"
                  />
                  <span>
                    <strong>{opcao.rotulo}</strong>
                    <br />
                    <span className="text-fg-muted">{opcao.descricao}</span>
                  </span>
                </label>
              ))}
            </fieldset>

            <button type="submit" className="btn-primary">
              Criar sala
            </button>
          </form>

          <form onSubmit={handleEntrar} className="grid gap-3 border-t-2 border-border pt-6">
            <label className="grid gap-1 text-sm">
              Código da sala
              <input
                value={codigoDigitado}
                onChange={(evento) => {
                  setCodigoDigitado(evento.target.value.toUpperCase())
                }}
                maxLength={4}
                className="rounded-md border-2 border-border bg-surface px-3 py-2 uppercase"
                placeholder="Ex: ABCD"
              />
            </label>
            <button type="submit" className="btn-secondary">
              Entrar em sala
            </button>
          </form>
        </div>
      )}

      {fase === 'reconectando' && (
        <div className="grid gap-3 rounded-lg border-2 border-tile-border-filled bg-surface p-6 text-center">
          <p className="text-sm text-fg-muted">Reconectando à sua partida…</p>
        </div>
      )}

      {fase === 'aguardando' && codigo && (
        <div className="grid gap-3 rounded-lg border-2 border-tile-border-filled bg-surface p-6 text-center">
          <p className="text-sm text-fg-muted">Código da sala</p>
          <p className="text-4xl font-bold tracking-[0.3em]">{codigo}</p>
          <p className="text-sm text-fg-muted">
            Modo: <strong>{MODOS.find((m) => m.valor === modo)?.rotulo}</strong>
          </p>
          <p className="text-sm text-fg-muted">
            Passe esse código pra outra pessoa jogar. Aguardando oponente…
          </p>
        </div>
      )}

      {fase === 'jogando' && (
        <>
          {oponenteDesconectadoTemporariamente && (
            <p
              role="status"
              className="rounded-md bg-tile-present p-2 text-center text-sm font-bold text-tile-fg"
            >
              {nomeOponente ?? 'Oponente'} desconectou. Esperando reconectar…
            </p>
          )}
          {modo === 'infinito' && (
            <p className="text-center text-sm font-semibold text-fg-muted">
              Rodada {rodada} · Você <strong>{meuTotal}</strong> x <strong>{totalOponente}</strong>{' '}
              {nomeOponente ?? 'Oponente'}
            </p>
          )}
          {tempoEsgotado && modo === 'normal' && !euConclui && (
            <p
              role="status"
              className="rounded-md bg-tile-present p-2 text-center text-sm font-bold text-tile-fg"
            >
              Tempo esgotado! Última tentativa.
            </p>
          )}
          {!tempoEsgotado &&
            modo === 'normal' &&
            submittedGuesses.length >= MAX_ATTEMPTS &&
            !euConclui && (
              <p className="text-center text-sm font-semibold text-fg-muted">Prorrogação</p>
            )}

          <GameBoard
            rows={buildBoard(toBoardRows(submittedGuesses, currentGuess))}
            activeRowIndex={submittedGuesses.length}
            selectedColumn={cursor}
            onSelectTile={euConclui ? undefined : selectPosition}
          />
          <OpponentProgress
            nome={nomeOponente ?? 'Oponente'}
            tentativasUsadas={tentativasOponente}
          />

          {euConclui ? (
            <p className="text-center text-sm text-fg-muted">
              Você concluiu. Aguardando o oponente…
            </p>
          ) : (
            <Keyboard
              keyStates={keyStates}
              onLetter={addLetter}
              onEnter={enviarPalpite}
              onBackspace={removeLetter}
            />
          )}
        </>
      )}

      {fase === 'fim' && (
        <div className="grid gap-3 rounded-lg border-2 border-tile-border-filled bg-surface p-4 text-center">
          {oponenteSaiu ? (
            <>
              <p className="text-lg font-bold">O oponente saiu da partida.</p>
              {modo === 'infinito' && (
                <p className="text-sm text-fg-muted">
                  Placar final da sessão: <strong>{meuTotal}</strong> x{' '}
                  <strong>{totalOponente}</strong>, em {rodada} rodada
                  {rodada !== 1 ? 's' : ''}.
                </p>
              )}
            </>
          ) : (
            <>
              <p className="text-lg font-bold">
                {resultadoFinal ? RESULTADO_TEXTO[resultadoFinal] : ''}
              </p>
              <p className="text-sm text-fg-muted">
                Você: <strong>{meusPontos ?? 0} pts</strong> · {nomeOponente ?? 'Oponente'}:{' '}
                <strong>{pontosOponente ?? 0} pts</strong>
              </p>
              {palavraSecreta && (
                <p className="text-sm text-fg-muted">
                  A palavra era <strong className="uppercase">{palavraSecreta}</strong>.
                </p>
              )}
              {oponentePediuRevanche && !euPediRevanche && (
                <p className="text-sm font-semibold text-tile-border-filled">
                  {nomeOponente ?? 'Oponente'} quer jogar de novo!
                </p>
              )}
            </>
          )}
          <div className="flex flex-col items-center gap-2">
            {!oponenteSaiu && (
              <button
                type="button"
                onClick={pedirRevanche}
                disabled={euPediRevanche}
                className="btn-primary mx-auto disabled:opacity-60"
              >
                {euPediRevanche ? 'Aguardando o oponente…' : 'Jogar de novo'}
              </button>
            )}
            <button type="button" onClick={reiniciar} className="btn-secondary mx-auto">
              Voltar pro lobby
            </button>
          </div>
        </div>
      )}
    </main>
  )
}

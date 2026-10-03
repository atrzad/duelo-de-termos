import { useEffect, useState } from 'react'
import type { SubmitEvent } from 'react'
import { Link } from 'react-router'

import { GameBoard } from '../components/GameBoard'
import { Keyboard } from '../components/Keyboard'
import { OpponentProgress } from '../components/OpponentProgress'
import { buildBoard, toBoardRows } from '../features/game/board'
import { MAX_ATTEMPTS, useDuel } from '../features/duel/useDuel'

const RESULTADO_TEXTO: Record<string, string> = {
  venceu: 'Você venceu!',
  perdeu: 'Você perdeu.',
  empate: 'Empate — ninguém acertou a tempo.',
}

export function DuelPage() {
  const {
    fase,
    codigo,
    nomeOponente,
    currentGuess,
    submittedGuesses,
    keyStates,
    tentativasOponente,
    resultadoFinal,
    palavraSecreta,
    mensagemErro,
    oponenteSaiu,
    criarSala,
    entrarSala,
    addLetter,
    removeLetter,
    enviarPalpite,
    reiniciar,
  } = useDuel()

  const [nome, setNome] = useState('')
  const [codigoDigitado, setCodigoDigitado] = useState('')

  useEffect(() => {
    if (fase !== 'jogando') return

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
  }, [fase, addLetter, removeLetter, enviarPalpite])

  function handleCriar(event: SubmitEvent) {
    event.preventDefault()
    if (nome.trim().length === 0) return
    criarSala(nome.trim())
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
        <span className="w-12" aria-hidden="true" />
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

      {fase === 'aguardando' && codigo && (
        <div className="grid gap-3 rounded-lg border-2 border-tile-border-filled bg-surface p-6 text-center">
          <p className="text-sm text-fg-muted">Código da sala</p>
          <p className="text-4xl font-bold tracking-[0.3em]">{codigo}</p>
          <p className="text-sm text-fg-muted">
            Passe esse código pra outra pessoa jogar. Aguardando oponente…
          </p>
        </div>
      )}

      {fase === 'jogando' && (
        <>
          <GameBoard rows={buildBoard(toBoardRows(submittedGuesses, currentGuess))} />
          <OpponentProgress
            nome={nomeOponente ?? 'Oponente'}
            tentativasUsadas={tentativasOponente}
            maxTentativas={MAX_ATTEMPTS}
          />
          <Keyboard
            keyStates={keyStates}
            onLetter={addLetter}
            onEnter={enviarPalpite}
            onBackspace={removeLetter}
          />
        </>
      )}

      {fase === 'fim' && (
        <div className="grid gap-3 rounded-lg border-2 border-tile-border-filled bg-surface p-4 text-center">
          {oponenteSaiu ? (
            <p className="text-lg font-bold">O oponente saiu da partida.</p>
          ) : (
            <>
              <p className="text-lg font-bold">
                {resultadoFinal ? RESULTADO_TEXTO[resultadoFinal] : ''}
              </p>
              {palavraSecreta && (
                <p className="text-sm text-fg-muted">
                  A palavra era <strong className="uppercase">{palavraSecreta}</strong>.
                </p>
              )}
            </>
          )}
          <button type="button" onClick={reiniciar} className="btn-primary mx-auto">
            Voltar pro lobby
          </button>
        </div>
      )}
    </main>
  )
}

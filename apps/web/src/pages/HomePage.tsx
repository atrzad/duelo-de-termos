import { Link } from 'react-router'

import { ServerStatus } from '../components/ServerStatus'

export function HomePage() {
  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-md flex-col justify-center gap-10 px-4 py-10">
      <header className="grid gap-3 text-center">
        <h1 className="text-4xl font-extrabold tracking-tight">Duelo de Termos</h1>
        <p className="text-fg-muted">
          Duas pessoas, a mesma palavra de cinco letras. Quem descobre primeiro?
        </p>
      </header>

      <div className="grid gap-3">
        <Link to="/duelo" className="btn-primary">
          Jogar 1v1
        </Link>
        <Link to="/jogo" className="btn-secondary">
          Modo infinito (solo)
        </Link>
      </div>

      <footer className="grid justify-items-center gap-4">
        <ServerStatus />
      </footer>
    </main>
  )
}

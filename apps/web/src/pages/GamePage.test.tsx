import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { describe, expect, it, vi } from 'vitest'

import type * as WordsModule from '../features/game/words'
import { GamePage } from './GamePage'

// Fixa a palavra sorteada pra cada teste ficar determinístico (sem isso o
// modo infinito sorteia uma palavra nova a cada montagem do componente).
// importOriginal preserva PALAVRAS -- palavrasValidas.ts depende dela pra
// garantir que toda resposta possível também é um palpite válido.
vi.mock('../features/game/words', async (importOriginal) => {
  const original = await importOriginal<typeof WordsModule>()
  return {
    ...original,
    palavraAleatoria: () => 'TERMO',
  }
})

async function digitarPalpite(usuario: ReturnType<typeof userEvent.setup>, palavra: string) {
  await usuario.keyboard(`${palavra}{Enter}`)
}

function renderizarPagina() {
  return render(
    <MemoryRouter>
      <GamePage />
    </MemoryRouter>,
  )
}

describe('GamePage', () => {
  it('avalia um palpite errado e mostra o estado de cada letra no tabuleiro', async () => {
    const usuario = userEvent.setup()
    renderizarPagina()

    // TERMO é a palavra secreta mockada; CULPA não tem nenhuma letra em comum.
    await digitarPalpite(usuario, 'CULPA')

    expect(screen.getByRole('gridcell', { name: 'C, ausente na palavra' })).toBeInTheDocument()
    expect(screen.getByRole('gridcell', { name: 'U, ausente na palavra' })).toBeInTheDocument()
  })

  it('declara vitória ao acertar a palavra, soma a sequência e permite jogar a próxima', async () => {
    const usuario = userEvent.setup()
    renderizarPagina()

    await digitarPalpite(usuario, 'TERMO')

    expect(await screen.findByText('Você venceu!')).toBeInTheDocument()
    expect(screen.getByText('TERMO')).toBeInTheDocument()
    expect(screen.getByLabelText('Sequência: 1')).toBeInTheDocument()

    await usuario.click(screen.getByRole('button', { name: 'Próxima palavra' }))

    expect(screen.queryByText('Você venceu!')).not.toBeInTheDocument()
    expect(screen.getByRole('group', { name: 'Teclado virtual' })).toBeInTheDocument()
  })

  it('mostra mensagem amigável ao tentar enviar palpite incompleto', async () => {
    const usuario = userEvent.setup()
    renderizarPagina()

    await usuario.keyboard('AB{Enter}')

    expect(await screen.findByText('Palavra incompleta.')).toBeInTheDocument()
  })

  it('mostra mensagem amigável ao tentar enviar uma palavra que não existe', async () => {
    const usuario = userEvent.setup()
    renderizarPagina()

    await digitarPalpite(usuario, 'ZZZZZ')

    expect(await screen.findByText('Essa palavra não existe.')).toBeInTheDocument()
    // Não consumiu a tentativa -- o tabuleiro continua vazio.
    expect(screen.queryByRole('gridcell', { name: /ausente|presente|correta/ })).toBeNull()
  })

  it('declara derrota depois de seis tentativas erradas, revela a palavra e zera a sequência', async () => {
    const usuario = userEvent.setup()
    renderizarPagina()

    for (let tentativa = 0; tentativa < 6; tentativa++) {
      await digitarPalpite(usuario, 'CULPA')
    }

    expect(await screen.findByText('Você perdeu.')).toBeInTheDocument()
    expect(screen.getByText('TERMO')).toBeInTheDocument()
    expect(screen.getByText('Sequência atual:')).toBeInTheDocument()
  })
})

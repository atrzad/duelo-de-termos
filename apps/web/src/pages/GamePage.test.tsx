import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'

import { GamePage } from './GamePage'

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

    // TERMO é a palavra secreta fixa da Fase 1; ABCDF não tem nenhuma letra em comum.
    await digitarPalpite(usuario, 'ABCDF')

    expect(screen.getByRole('gridcell', { name: 'A, ausente na palavra' })).toBeInTheDocument()
    expect(screen.getByRole('gridcell', { name: 'F, ausente na palavra' })).toBeInTheDocument()
  })

  it('declara vitória ao acertar a palavra e permite jogar de novo', async () => {
    const usuario = userEvent.setup()
    renderizarPagina()

    await digitarPalpite(usuario, 'TERMO')

    expect(await screen.findByText('Você venceu!')).toBeInTheDocument()
    expect(screen.getByText('TERMO')).toBeInTheDocument()

    await usuario.click(screen.getByRole('button', { name: 'Jogar de novo' }))

    expect(screen.queryByText('Você venceu!')).not.toBeInTheDocument()
    expect(screen.getByRole('group', { name: 'Teclado virtual' })).toBeInTheDocument()
  })

  it('mostra mensagem amigável ao tentar enviar palpite incompleto', async () => {
    const usuario = userEvent.setup()
    renderizarPagina()

    await usuario.keyboard('AB{Enter}')

    expect(await screen.findByText('Palavra incompleta.')).toBeInTheDocument()
  })

  it('declara derrota depois de seis tentativas erradas e revela a palavra', async () => {
    const usuario = userEvent.setup()
    renderizarPagina()

    for (let tentativa = 0; tentativa < 6; tentativa++) {
      await digitarPalpite(usuario, 'ABCDF')
    }

    expect(await screen.findByText('Você perdeu.')).toBeInTheDocument()
    expect(screen.getByText('TERMO')).toBeInTheDocument()
  })
})

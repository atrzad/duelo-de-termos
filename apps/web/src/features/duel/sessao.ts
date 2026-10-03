const CHAVE = 'duelo:sessao'

export interface SessaoSalva {
  token: string
  codigo: string
}

function ehSessaoValida(valor: unknown): valor is SessaoSalva {
  return (
    typeof valor === 'object' &&
    valor !== null &&
    typeof (valor as Record<string, unknown>).token === 'string' &&
    typeof (valor as Record<string, unknown>).codigo === 'string'
  )
}

export function salvarSessao(sessao: SessaoSalva): void {
  try {
    localStorage.setItem(CHAVE, JSON.stringify(sessao))
  } catch {
    // Storage bloqueado (modo privado, etc.) -- só perde a reconexão automática.
  }
}

export function carregarSessao(): SessaoSalva | null {
  try {
    const bruto = localStorage.getItem(CHAVE)
    if (!bruto) return null
    const dados: unknown = JSON.parse(bruto)
    return ehSessaoValida(dados) ? dados : null
  } catch {
    return null
  }
}

export function limparSessao(): void {
  try {
    localStorage.removeItem(CHAVE)
  } catch {
    // ignora
  }
}

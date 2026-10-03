import { useEffect, useState } from 'react'

/**
 * Contagem regressiva local (aproximada, só visual). Quem decide de verdade
 * quando o tempo acabou é sempre o servidor — ver o evento `tempo_esgotado`.
 *
 * `Date.now()` só é chamado dentro do callback do interval (nunca durante o
 * corpo do efeito nem durante a renderização) — regras react-hooks/purity e
 * react-hooks/set-state-in-effect. Isso significa que, ao trocar de partida,
 * o valor antigo pode ficar na tela por até 250ms até o primeiro tick
 * corrigir — defasagem pequena o suficiente pra não importar aqui.
 */
export function useCountdown(duracaoSegundos: number | null, ativo: boolean): number | null {
  const [restante, setRestante] = useState<number | null>(duracaoSegundos)

  useEffect(() => {
    if (!ativo || duracaoSegundos === null) return

    const inicio = Date.now()
    const intervalo = setInterval(() => {
      const passado = Math.floor((Date.now() - inicio) / 1000)
      setRestante(Math.max(0, duracaoSegundos - passado))
    }, 250)

    return () => {
      clearInterval(intervalo)
    }
  }, [ativo, duracaoSegundos])

  return restante
}

/**
 * Pool de palavras de 5 letras (sem acento) pro modo infinito, sorteada
 * localmente a cada rodada. Mesma lista existe em apps/api/app/game/words.py
 * pro 1v1 (lá o sorteio é no servidor, nunca revelado ao cliente); manter as
 * duas em sincronia é dívida técnica consciente — não há um ponto único de
 * verdade ainda porque o modo infinito continua 100% local (Fase 1).
 *
 * 2283 palavras (pedido à parte em 2026-10-04, "pelo menos 2000"): geradas a
 * partir dos lemas de 5 letras do dicionário hunspell pt_BR, ranqueados por
 * frequência real de uso (`wordfreq`, corpus "pt", corte em zipf >= 1.5) +
 * as 90 escolhidas à mão originalmente (sempre inclusas). Ver
 * apps/api/app/game/words.py pro histórico completo de como foi gerado.
 */
import textoBruto from './data/palavras_respostas.txt?raw'

export const PALAVRAS: readonly string[] = textoBruto
  .split('\n')
  .map((linha) => linha.trim())
  .filter(Boolean)

export function palavraAleatoria(excluir?: string): string {
  if (PALAVRAS.length <= 1) return PALAVRAS[0] ?? 'TERMO'

  let escolhida: string
  do {
    const indice = Math.floor(Math.random() * PALAVRAS.length)
    escolhida = PALAVRAS[indice] ?? 'TERMO'
  } while (escolhida === excluir)

  return escolhida
}

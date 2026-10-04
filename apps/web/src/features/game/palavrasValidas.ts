// Dicionário de ~18 mil palavras de 5 letras pra validar PALPITES no modo
// infinito (100% local, sem servidor pra validar) -- diferente de
// words.ts (PALAVRAS), que são só as ~90 possíveis RESPOSTAS secretas.
// Gerado a partir do hunspell pt_BR; mesmo arquivo duplicado em
// apps/api/app/game/data/ pro 1v1 (que valida no servidor). Ver words.py
// pro histórico completo de como foi gerado.
import textoBruto from './data/palavras_validas.txt?raw'
import { PALAVRAS } from './words'

const PALAVRAS_VALIDAS: ReadonlySet<string> = new Set([
  ...textoBruto
    .split('\n')
    .map((linha) => linha.trim())
    .filter(Boolean),
  ...PALAVRAS,
])

export function palavraEValida(palavra: string): boolean {
  return PALAVRAS_VALIDAS.has(palavra.toUpperCase())
}

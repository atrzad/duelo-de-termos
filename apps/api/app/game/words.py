"""Pool de palavras de 5 letras (sem acento) pro 1v1. O sorteio é sempre no
servidor — o cliente nunca recebe a palavra secreta durante a partida (regra 4
do PROJECT_SCOPE.md). Mesma lista existe em apps/web/src/features/game/words.ts
pro modo infinito (que roda 100% local); mantê-las em sincronia é dívida
técnica consciente, aceita pra entregar o 1v1 rápido.

PALAVRAS (2283 palavras, pedido à parte em 2026-10-04 -- "pelo menos 2000"):
gerada a partir das ~7300 palavras-base (lemas, sem flexão) de 5 letras do
dicionário hunspell pt_BR, ranqueadas por frequência de uso real (pacote
`wordfreq`, corpus "pt") e cortadas em zipf >= 1.5 -- filtra as mais raras
sem exigir frequência alta igual a PALAVRAS_VALIDAS (que aceita qualquer
palavra real como palpite). Um denylist manual pequeno remove termos
ofensivos/vulgares que apareceram na lista. As 90 palavras escolhidas à mão
originalmente sempre entram também (união), mesmo as que não bateram o corte
de frequência -- ver data/palavras_respostas.txt.

PALAVRAS_VALIDAS (pedido à parte, 2026-10-03): dicionário de ~18 mil palavras
de 5 letras pra validar PALPITES (diferente de PALAVRAS, que são as possíveis
RESPOSTAS secretas) -- gerado a partir do dicionário hunspell pt_BR (pacote
AUR hunspell-pt-br), expandindo todas as formas de cada palavra (unmunch),
removendo acento e filtrando pra exatamente 5 letras. Mesmo arquivo
(data/palavras_validas.txt) duplicado em apps/web/src/features/game/data/
pro modo infinito local.
"""

import random
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data"


def _carregar_palavras() -> tuple[str, ...]:
    linhas = (_DATA_DIR / "palavras_respostas.txt").read_text(encoding="utf-8").splitlines()
    return tuple(linhas)


PALAVRAS: tuple[str, ...] = _carregar_palavras()


def _carregar_palavras_validas() -> frozenset[str]:
    linhas = (_DATA_DIR / "palavras_validas.txt").read_text(encoding="utf-8").splitlines()
    # As respostas possíveis entram também, garantido: sempre dá pra acertar
    # a própria palavra secreta (união, não assume que o dicionário já
    # cobre todas -- é gerado por fora, não é pra travar nisso).
    return frozenset(linhas) | frozenset(PALAVRAS)


PALAVRAS_VALIDAS: frozenset[str] = _carregar_palavras_validas()


def palavra_aleatoria() -> str:
    return random.choice(PALAVRAS)


def palavra_e_valida(palavra: str) -> bool:
    return palavra.upper() in PALAVRAS_VALIDAS

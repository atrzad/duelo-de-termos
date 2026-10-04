"""Pool de palavras de 5 letras (sem acento) pro 1v1. O sorteio é sempre no
servidor — o cliente nunca recebe a palavra secreta durante a partida (regra 4
do PROJECT_SCOPE.md). Mesma lista existe em apps/web/src/features/game/words.ts
pro modo infinito (que roda 100% local); mantê-las em sincronia é dívida
técnica consciente, aceita pra entregar o 1v1 rápido.

PALAVRAS_VALIDAS (pedido à parte, 2026-10-03): dicionário de ~18 mil palavras
de 5 letras pra validar PALPITES (diferente de PALAVRAS, que são só as ~90
possíveis RESPOSTAS secretas) -- gerado a partir do dicionário hunspell
pt_BR (pacote AUR hunspell-pt-br), expandindo todas as formas de cada palavra
(unmunch), removendo acento e filtrando pra exatamente 5 letras. Mesmo
arquivo (data/palavras_validas.txt) duplicado em
apps/web/src/features/game/data/ pro modo infinito local.
"""

import random
from pathlib import Path

PALAVRAS: tuple[str, ...] = (
    "TERMO", "PRATO", "CARRO", "LIVRO", "BANCO", "CAMPO", "FESTA", "MUNDO",
    "PORTA", "VIDRO", "TEMPO", "GRUPO", "CARTA", "CORPO", "MORTE", "NOITE",
    "FONTE", "LENTE", "FRUTA", "PEIXE", "LEITE", "BARCO", "TIGRE", "GRAVE",
    "FRASE", "CLIMA", "TECLA", "VALOR", "HONRA", "CULPA", "SONHO", "TOQUE",
    "FOLHA", "CHUVA", "PEDRA", "AREIA", "VERME", "NAVIO", "BARRO", "FIBRA",
    "GESSO", "LINHA", "MANGA", "SALTO", "PONTE", "FORNO", "MOEDA", "PALCO",
    "TORRE", "FOLGA", "GRAMA", "CARGO", "SURTO", "MOLHO", "CESTO", "PONTO",
    "FORTE", "BRISA", "PRESA", "FELIZ", "VERDE", "PRETO", "SUAVE", "NOBRE",
    "LIVRE", "BREVE", "JOVEM", "MACIO", "RIGOR", "VAPOR", "MOTOR", "SETOR",
    "FATOR", "LITRO", "METRO", "VENTO", "PESCA", "TEXTO", "PACTO", "FATIA",
    "BOLHA", "GALHO", "OUTRO", "RURAL", "LOCAL", "FINAL", "IDEAL", "METAL",
    "SINAL", "CANAL",
)  # fmt: skip


def _carregar_palavras_validas() -> frozenset[str]:
    caminho = Path(__file__).resolve().parent / "data" / "palavras_validas.txt"
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    # As ~90 respostas possíveis entram também, garantido: sempre dá pra
    # acertar a própria palavra secreta (união, não assume que o dicionário
    # já cobre todas -- é gerado por fora, não é pra travar nisso).
    return frozenset(linhas) | frozenset(PALAVRAS)


PALAVRAS_VALIDAS: frozenset[str] = _carregar_palavras_validas()


def palavra_aleatoria() -> str:
    return random.choice(PALAVRAS)


def palavra_e_valida(palavra: str) -> bool:
    return palavra.upper() in PALAVRAS_VALIDAS

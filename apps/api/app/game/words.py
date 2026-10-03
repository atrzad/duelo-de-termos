"""Pool de palavras de 5 letras (sem acento) pro 1v1. O sorteio é sempre no
servidor — o cliente nunca recebe a palavra secreta durante a partida (regra 4
do PROJECT_SCOPE.md). Mesma lista existe em apps/web/src/features/game/words.ts
pro modo infinito (que roda 100% local); mantê-las em sincronia é dívida
técnica consciente, aceita pra entregar o 1v1 rápido.
"""

import random

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


def palavra_aleatoria() -> str:
    return random.choice(PALAVRAS)

"""Regras específicas de cada modo (seção 9 do PROJECT_SCOPE.md): só as
tabelas de pontuação, puras. As condições de quando o palpite é aceito e
quando a partida termina ficam em `rooms.py` (lá é onde mora o estado).
"""

import enum
from typing import Literal

CategoriaNormal = Literal["1-3", "4-6", "prorrogacao", "tentativa_final", "nao_acertou"]


class GameMode(enum.StrEnum):
    normal = "normal"
    competitivo = "competitivo"
    hardcore = "hardcore"
    # Não é um dos 3 modos da seção 9 do PROJECT_SCOPE.md — pedido à parte do
    # usuário. Reaproveita a pontuação por rodada do Competitivo (6
    # tentativas, pontos = 7-tentativas, sem timer), mas a sala nunca
    # "finaliza" sozinha: ao concluir uma rodada sorteia outra palavra e
    # acumula o placar, até alguém sair.
    infinito = "infinito"


TENTATIVAS_REGULARES = 6
TIMER_NORMAL_SEGUNDOS = 90
TIMER_HARDCORE_SEGUNDOS = 90

_TABELA_NORMAL: dict[CategoriaNormal, int] = {
    "1-3": 3,
    "4-6": 2,
    "prorrogacao": 1,
    "tentativa_final": 1,
    "nao_acertou": 0,
}


def categoria_normal(
    numero_tentativa: int, *, em_prorrogacao: bool, via_tentativa_final: bool
) -> CategoriaNormal:
    if via_tentativa_final:
        return "tentativa_final"
    if em_prorrogacao:
        return "prorrogacao"
    if 1 <= numero_tentativa <= 3:
        return "1-3"
    return "4-6"


def pontuacao_normal(categoria: CategoriaNormal, *, primeiro_a_acertar: bool) -> int:
    pontos = _TABELA_NORMAL[categoria]
    if pontos > 0 and primeiro_a_acertar:
        pontos += 1
    return pontos


def pontuacao_competitivo(tentativas_usadas: int | None) -> int:
    """pontos = 7 - tentativas_usadas (seção 9.2); 0 se não acertou."""
    if tentativas_usadas is None or not (1 <= tentativas_usadas <= TENTATIVAS_REGULARES):
        return 0
    return 7 - tentativas_usadas


def pontuacao_hardcore(*, foi_o_primeiro_a_acertar: bool) -> int:
    return 3 if foi_o_primeiro_a_acertar else 0

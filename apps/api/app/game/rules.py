"""Motor de regras do jogo (Fase 2): mesma lógica de
apps/web/src/features/game/evaluateGuess.ts, agora como autoridade — quem usa
isso pra decidir o resultado de uma partida é sempre o servidor.
"""

from typing import Literal

LetterState = Literal["correct", "present", "absent"]


def evaluate_guess(palpite: str, segredo: str) -> list[LetterState]:
    """Avalia um palpite contra a palavra secreta, posição a posição.

    Função pura. Trata letras repetidas em duas passadas: a primeira marca os
    acertos exatos e conta quantas vezes cada letra não-acertada ainda sobra
    no segredo; a segunda consome essa sobra pra decidir 'present'/'absent'.
    """
    palpite_letras = list(palpite.upper())
    segredo_letras = list(segredo.upper())
    tamanho = len(segredo_letras)

    estados: list[LetterState] = ["absent"] * tamanho
    sobra_no_segredo: dict[str, int] = {}

    for i in range(tamanho):
        if palpite_letras[i] == segredo_letras[i]:
            estados[i] = "correct"
        else:
            letra = segredo_letras[i]
            sobra_no_segredo[letra] = sobra_no_segredo.get(letra, 0) + 1

    for i in range(tamanho):
        if estados[i] == "correct":
            continue

        letra = palpite_letras[i]
        restante = sobra_no_segredo.get(letra, 0)
        if restante > 0:
            estados[i] = "present"
            sobra_no_segredo[letra] = restante - 1

    return estados

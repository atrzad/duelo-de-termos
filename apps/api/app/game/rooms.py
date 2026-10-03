"""Estado das salas do 1v1, em memória (um processo só, sem persistência —
decisão consciente pra entregar rápido; regra 2 do PROJECT_SCOPE.md também
pede pra não antecipar Redis/filas sem necessidade real).
"""

import secrets
import string
from dataclasses import dataclass, field
from typing import Literal

from app.game.rules import LetterState, evaluate_guess
from app.game.words import palavra_aleatoria

MAX_TENTATIVAS = 6
TAMANHO_PALAVRA = 5

RoomStatus = Literal["aguardando", "jogando", "finalizada"]
Resultado = Literal["venceu", "perdeu", "empate"]


@dataclass
class Tentativa:
    letras: list[str]
    estados: list[LetterState]


@dataclass
class Jogador:
    sid: str
    nome: str
    tentativas: list[Tentativa] = field(default_factory=list)
    venceu: bool = False
    esgotou_tentativas: bool = False


@dataclass
class Sala:
    codigo: str
    jogadores: dict[str, Jogador] = field(default_factory=dict)
    status: RoomStatus = "aguardando"
    palavra_secreta: str | None = None

    def outro_jogador(self, sid: str) -> Jogador | None:
        for outro_sid, jogador in self.jogadores.items():
            if outro_sid != sid:
                return jogador
        return None

    def resultado_para(self, sid: str) -> Resultado | None:
        """Só faz sentido depois que a sala terminou (status == 'finalizada')."""
        if self.status != "finalizada":
            return None

        jogador = self.jogadores.get(sid)
        if jogador is None:
            return None
        if jogador.venceu:
            return "venceu"

        oponente = self.outro_jogador(sid)
        if oponente is not None and oponente.venceu:
            return "perdeu"
        return "empate"


class SalaNaoEncontradaError(Exception):
    pass


class SalaEmAndamentoError(Exception):
    pass


class GerenciadorDeSalas:
    def __init__(self) -> None:
        self._salas: dict[str, Sala] = {}
        self._sala_do_jogador: dict[str, str] = {}

    def _gerar_codigo(self) -> str:
        # secrets, não random: o código é o único controle de acesso à sala.
        alfabeto = string.ascii_uppercase
        while True:
            codigo = "".join(secrets.choice(alfabeto) for _ in range(4))
            if codigo not in self._salas:
                return codigo

    def criar_sala(self, sid: str, nome: str) -> Sala:
        codigo = self._gerar_codigo()
        sala = Sala(codigo=codigo)
        sala.jogadores[sid] = Jogador(sid=sid, nome=nome)
        self._salas[codigo] = sala
        self._sala_do_jogador[sid] = codigo
        return sala

    def entrar_sala(self, sid: str, nome: str, codigo: str) -> Sala:
        sala = self._salas.get(codigo.upper())
        if sala is None:
            raise SalaNaoEncontradaError(codigo)
        if sala.status != "aguardando":
            # Única forma de a sala sair de "aguardando" é o 2º jogador entrar
            # (o que já a deixa "jogando" na hora) — ou seja, isso cobre tanto
            # "sala cheia" quanto "partida em andamento/terminada" com o mesmo erro.
            raise SalaEmAndamentoError(codigo)

        sala.jogadores[sid] = Jogador(sid=sid, nome=nome)
        self._sala_do_jogador[sid] = sala.codigo

        if len(sala.jogadores) == 2:
            sala.status = "jogando"
            sala.palavra_secreta = palavra_aleatoria()

        return sala

    def sala_do_jogador(self, sid: str) -> Sala | None:
        codigo = self._sala_do_jogador.get(sid)
        return self._salas.get(codigo) if codigo else None

    def registrar_palpite(self, sid: str, palavra: str) -> tuple[Sala, Tentativa]:
        """Avalia o palpite e atualiza o estado da sala. Depois de chamar isso,
        confira `sala.status` — se virou 'finalizada', use `sala.resultado_para(sid)`
        pra CADA jogador da sala (os dois, não só quem acabou de jogar: quem já
        tinha esgotado as tentativas antes só descobre o resultado agora)."""
        sala = self.sala_do_jogador(sid)
        if sala is None:
            raise SalaNaoEncontradaError(sid)
        if sala.status != "jogando" or sala.palavra_secreta is None:
            raise SalaEmAndamentoError(sid)

        jogador = sala.jogadores[sid]
        if jogador.venceu or jogador.esgotou_tentativas:
            raise SalaEmAndamentoError(sid)

        estados = evaluate_guess(palavra, sala.palavra_secreta)
        tentativa = Tentativa(letras=list(palavra.upper()), estados=estados)
        jogador.tentativas.append(tentativa)

        acertou = palavra.upper() == sala.palavra_secreta
        if acertou:
            jogador.venceu = True
            sala.status = "finalizada"
        else:
            if len(jogador.tentativas) >= MAX_TENTATIVAS:
                jogador.esgotou_tentativas = True

            oponente = sala.outro_jogador(sid)
            jogador_parado = jogador.venceu or jogador.esgotou_tentativas
            oponente_parado = oponente is None or oponente.venceu or oponente.esgotou_tentativas
            if jogador_parado and oponente_parado:
                sala.status = "finalizada"

        return sala, tentativa

    def remover_jogador(self, sid: str) -> Sala | None:
        codigo = self._sala_do_jogador.pop(sid, None)
        if codigo is None:
            return None

        sala = self._salas.get(codigo)
        if sala is None:
            return None

        sala.jogadores.pop(sid, None)
        if not sala.jogadores:
            self._salas.pop(codigo, None)
            return None

        sala.status = "finalizada"
        return sala


gerenciador = GerenciadorDeSalas()

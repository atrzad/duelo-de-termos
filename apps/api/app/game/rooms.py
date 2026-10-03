"""Estado das salas do 1v1, em memória (um processo só, sem persistência de
estado AO VIVO — decisão consciente; ver app/game/persistence.py pro que É
persistido: o resultado de partidas já terminadas). Regras de cada modo:
seção 9 do PROJECT_SCOPE.md; implementação da pontuação em app/game/modes.py.
"""

import secrets
import string
import time
from dataclasses import dataclass, field
from typing import Literal

from app.game.modes import (
    TENTATIVAS_REGULARES,
    GameMode,
    categoria_normal,
    pontuacao_competitivo,
    pontuacao_hardcore,
    pontuacao_normal,
)
from app.game.rules import LetterState, evaluate_guess
from app.game.words import palavra_aleatoria

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
    pontos: int = 0
    resolvido_em: float | None = None
    tentativa_final_usada: bool = False

    @property
    def concluido(self) -> bool:
        """Não pode mais enviar palpite nesta partida: já venceu, esgotou as
        tentativas regulares (Competitivo) ou já usou a tentativa final
        pós-tempo (Normal)."""
        return self.venceu or self.esgotou_tentativas or self.tentativa_final_usada


@dataclass
class Sala:
    codigo: str
    modo: GameMode = GameMode.competitivo
    jogadores: dict[str, Jogador] = field(default_factory=dict)
    status: RoomStatus = "aguardando"
    palavra_secreta: str | None = None
    tempo_expirado: bool = False
    iniciada_em: float | None = None

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
        oponente = self.outro_jogador(sid)
        if jogador is None or oponente is None:
            return None

        if jogador.pontos > oponente.pontos:
            return "venceu"
        if jogador.pontos < oponente.pontos:
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

    def criar_sala(self, sid: str, nome: str, modo: GameMode) -> Sala:
        codigo = self._gerar_codigo()
        sala = Sala(codigo=codigo, modo=modo)
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
            sala.iniciada_em = time.time()

        return sala

    def sala_do_jogador(self, sid: str) -> Sala | None:
        codigo = self._sala_do_jogador.get(sid)
        return self._salas.get(codigo) if codigo else None

    def _checar_fim_de_partida(self, sala: Sala) -> None:
        if len(sala.jogadores) == 2 and all(j.concluido for j in sala.jogadores.values()):
            sala.status = "finalizada"

    def _aplicar_competitivo(self, sala: Sala, jogador: Jogador, acertou: bool) -> None:
        if acertou:
            jogador.venceu = True
            jogador.resolvido_em = time.time()
            jogador.pontos = pontuacao_competitivo(len(jogador.tentativas))
        elif len(jogador.tentativas) >= TENTATIVAS_REGULARES:
            jogador.esgotou_tentativas = True
            jogador.pontos = 0
        self._checar_fim_de_partida(sala)

    def _aplicar_hardcore(self, sala: Sala, jogador: Jogador, acertou: bool) -> None:
        if not acertou:
            return
        jogador.venceu = True
        jogador.resolvido_em = time.time()
        jogador.pontos = pontuacao_hardcore(foi_o_primeiro_a_acertar=True)
        # Hardcore: primeiro acerto válido encerra a partida pra todo mundo
        # na hora (seção 9.3) — diferente dos outros modos, o oponente NÃO
        # continua jogando depois disso.
        sala.status = "finalizada"
        oponente = sala.outro_jogador(jogador.sid)
        if oponente is not None and not oponente.venceu:
            oponente.pontos = 0

    def _aplicar_normal(self, sala: Sala, jogador: Jogador, acertou: bool) -> None:
        numero_tentativa = len(jogador.tentativas)
        via_tentativa_final = sala.tempo_expirado
        em_prorrogacao = numero_tentativa > TENTATIVAS_REGULARES and not via_tentativa_final

        if via_tentativa_final:
            jogador.tentativa_final_usada = True

        if acertou:
            jogador.venceu = True
            jogador.resolvido_em = time.time()
            categoria = categoria_normal(
                numero_tentativa,
                em_prorrogacao=em_prorrogacao,
                via_tentativa_final=via_tentativa_final,
            )
            oponente = sala.outro_jogador(jogador.sid)
            primeiro = (
                oponente is None
                or oponente.resolvido_em is None
                or jogador.resolvido_em < oponente.resolvido_em
            )
            jogador.pontos = pontuacao_normal(categoria, primeiro_a_acertar=primeiro)
        elif via_tentativa_final:
            jogador.pontos = 0

        self._checar_fim_de_partida(sala)

    def registrar_palpite(self, sid: str, palavra: str) -> tuple[Sala, Tentativa]:
        """Avalia o palpite e atualiza o estado da sala. Depois de chamar isso,
        confira `sala.status` — se virou 'finalizada', use `sala.resultado_para(sid)`
        pra CADA jogador da sala (os dois, não só quem acabou de jogar)."""
        sala = self.sala_do_jogador(sid)
        if sala is None:
            raise SalaNaoEncontradaError(sid)
        if sala.status != "jogando" or sala.palavra_secreta is None:
            raise SalaEmAndamentoError(sid)

        jogador = sala.jogadores[sid]
        if jogador.concluido:
            raise SalaEmAndamentoError(sid)
        if sala.modo != GameMode.normal and sala.tempo_expirado:
            # Só o modo Normal tem tentativa pós-tempo; os outros dois não.
            raise SalaEmAndamentoError(sid)

        estados = evaluate_guess(palavra, sala.palavra_secreta)
        tentativa = Tentativa(letras=list(palavra.upper()), estados=estados)
        jogador.tentativas.append(tentativa)
        acertou = palavra.upper() == sala.palavra_secreta

        if sala.modo == GameMode.competitivo:
            self._aplicar_competitivo(sala, jogador, acertou)
        elif sala.modo == GameMode.hardcore:
            self._aplicar_hardcore(sala, jogador, acertou)
        else:
            self._aplicar_normal(sala, jogador, acertou)

        return sala, tentativa

    def expirar_tempo(self, codigo: str) -> Sala | None:
        """Chamado pela task de timer (sockets.py) quando os 90s acabam.
        Hardcore: ninguém acertou -> partida termina sem vencedor. Normal:
        só libera a janela de tentativa final (a partida só termina quando
        todo mundo concluir — ver forcar_fim_tentativa_final pro timeout
        de segurança caso alguém nunca envie essa tentativa final)."""
        sala = self._salas.get(codigo)
        if sala is None or sala.status != "jogando" or sala.tempo_expirado:
            return None

        sala.tempo_expirado = True

        if sala.modo == GameMode.hardcore:
            sala.status = "finalizada"
            for jogador in sala.jogadores.values():
                jogador.pontos = 0

        return sala

    def forcar_fim_tentativa_final(self, codigo: str) -> Sala | None:
        """Timeout de segurança do modo Normal: se alguém não usar a
        tentativa final a tempo, força a conclusão (evita a sala travada pra
        sempre esperando um palpite que nunca chega)."""
        sala = self._salas.get(codigo)
        if sala is None or sala.status != "jogando":
            return None

        for jogador in sala.jogadores.values():
            if not jogador.concluido:
                jogador.tentativa_final_usada = True
                jogador.pontos = 0

        sala.status = "finalizada"
        return sala

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

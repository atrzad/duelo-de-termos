"""Rate limit simples (regra 9.1 do PROJECT_SCOPE.md: "O servidor deve
aplicar rate limit para evitar spam de palpites"). Cooldown mínimo entre
ações da mesma chave (sid) — não é janela deslizante nem burst, só o
suficiente pra impedir flood de eventos.
"""

import time


class LimitadorDeTaxa:
    def __init__(self, intervalo_minimo_segundos: float) -> None:
        self._intervalo = intervalo_minimo_segundos
        self._ultima_acao: dict[str, float] = {}

    def permitido(self, chave: str) -> bool:
        agora = time.monotonic()
        ultima = self._ultima_acao.get(chave)
        if ultima is not None and (agora - ultima) < self._intervalo:
            return False
        self._ultima_acao[chave] = agora
        return True

    def esquecer(self, chave: str) -> None:
        self._ultima_acao.pop(chave, None)

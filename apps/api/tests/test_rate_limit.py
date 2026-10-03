import time

from app.game.rate_limit import LimitadorDeTaxa


def test_primeira_acao_sempre_e_permitida() -> None:
    limitador = LimitadorDeTaxa(intervalo_minimo_segundos=10)
    assert limitador.permitido("sid-1") is True


def test_segunda_acao_dentro_do_intervalo_e_bloqueada() -> None:
    limitador = LimitadorDeTaxa(intervalo_minimo_segundos=10)
    limitador.permitido("sid-1")

    assert limitador.permitido("sid-1") is False


def test_acao_e_permitida_de_novo_depois_do_intervalo_passar() -> None:
    limitador = LimitadorDeTaxa(intervalo_minimo_segundos=0.05)
    limitador.permitido("sid-1")

    time.sleep(0.07)

    assert limitador.permitido("sid-1") is True


def test_chaves_diferentes_nao_se_afetam() -> None:
    limitador = LimitadorDeTaxa(intervalo_minimo_segundos=10)
    limitador.permitido("sid-1")

    assert limitador.permitido("sid-2") is True


def test_esquecer_libera_a_chave_imediatamente() -> None:
    limitador = LimitadorDeTaxa(intervalo_minimo_segundos=10)
    limitador.permitido("sid-1")
    limitador.esquecer("sid-1")

    assert limitador.permitido("sid-1") is True

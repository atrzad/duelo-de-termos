import pytest

from app.game.rooms import GerenciadorDeSalas, SalaEmAndamentoError, SalaNaoEncontradaError


@pytest.fixture
def gerenciador() -> GerenciadorDeSalas:
    return GerenciadorDeSalas()


def test_criar_sala_comeca_aguardando_com_um_jogador(gerenciador: GerenciadorDeSalas) -> None:
    sala = gerenciador.criar_sala("sid-1", "Ana")

    assert sala.status == "aguardando"
    assert len(sala.jogadores) == 1
    assert sala.palavra_secreta is None
    assert len(sala.codigo) == 4


def test_segundo_jogador_inicia_a_partida(gerenciador: GerenciadorDeSalas) -> None:
    sala = gerenciador.criar_sala("sid-1", "Ana")
    sala2 = gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)

    assert sala2 is sala
    assert sala.status == "jogando"
    assert len(sala.jogadores) == 2
    assert sala.palavra_secreta is not None
    assert len(sala.palavra_secreta) == 5


def test_entrar_em_sala_inexistente_da_erro(gerenciador: GerenciadorDeSalas) -> None:
    with pytest.raises(SalaNaoEncontradaError):
        gerenciador.entrar_sala("sid-1", "Ana", "ZZZZ")


def test_entrar_em_sala_ja_cheia_e_em_andamento_da_erro(gerenciador: GerenciadorDeSalas) -> None:
    sala = gerenciador.criar_sala("sid-1", "Ana")
    gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)

    with pytest.raises(SalaEmAndamentoError):
        gerenciador.entrar_sala("sid-3", "Caio", sala.codigo)


def test_codigo_da_sala_e_case_insensitive(gerenciador: GerenciadorDeSalas) -> None:
    sala = gerenciador.criar_sala("sid-1", "Ana")
    sala2 = gerenciador.entrar_sala("sid-2", "Beto", sala.codigo.lower())

    assert sala2 is sala


def test_palpite_correto_declara_vitoria_imediata(gerenciador: GerenciadorDeSalas) -> None:
    sala = gerenciador.criar_sala("sid-1", "Ana")
    gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
    assert sala.palavra_secreta is not None
    segredo = sala.palavra_secreta

    sala_atualizada, tentativa = gerenciador.registrar_palpite("sid-1", segredo)

    assert sala_atualizada.status == "finalizada"
    assert tentativa.estados == ["correct"] * 5
    assert sala_atualizada.resultado_para("sid-1") == "venceu"
    assert sala_atualizada.resultado_para("sid-2") == "perdeu"


def test_palpite_errado_nao_termina_a_partida(gerenciador: GerenciadorDeSalas) -> None:
    sala = gerenciador.criar_sala("sid-1", "Ana")
    gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
    assert sala.palavra_secreta is not None

    palpite_errado = "ZZZZZ" if sala.palavra_secreta != "ZZZZZ" else "XXXXX"
    sala_atualizada, _ = gerenciador.registrar_palpite("sid-1", palpite_errado)

    assert sala_atualizada.status == "jogando"
    assert sala_atualizada.resultado_para("sid-1") is None


def test_quem_esgota_tentativas_so_sabe_o_resultado_quando_o_outro_tambem_termina(
    gerenciador: GerenciadorDeSalas,
) -> None:
    sala = gerenciador.criar_sala("sid-1", "Ana")
    gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
    assert sala.palavra_secreta is not None
    segredo = sala.palavra_secreta
    errado = "ZZZZZ" if segredo != "ZZZZZ" else "XXXXX"

    for _ in range(6):
        sala_atualizada, _ = gerenciador.registrar_palpite("sid-1", errado)

    # sid-1 esgotou as 6 tentativas, mas sid-2 ainda não jogou nenhuma vez:
    # a sala continua em andamento até sid-2 também terminar.
    assert sala_atualizada.status == "jogando"
    assert sala_atualizada.resultado_para("sid-1") is None

    for _ in range(5):
        sala_atualizada, _ = gerenciador.registrar_palpite("sid-2", errado)
    assert sala_atualizada.status == "jogando"

    sala_atualizada, _ = gerenciador.registrar_palpite("sid-2", errado)

    assert sala_atualizada.status == "finalizada"
    assert sala_atualizada.resultado_para("sid-1") == "empate"
    assert sala_atualizada.resultado_para("sid-2") == "empate"


def test_nao_deixa_jogar_depois_que_a_partida_terminou(
    gerenciador: GerenciadorDeSalas,
) -> None:
    sala = gerenciador.criar_sala("sid-1", "Ana")
    gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
    assert sala.palavra_secreta is not None
    segredo = sala.palavra_secreta

    gerenciador.registrar_palpite("sid-1", segredo)

    with pytest.raises(SalaEmAndamentoError):
        gerenciador.registrar_palpite("sid-2", segredo)


def test_remover_jogador_mantem_sala_pro_oponente_restante(
    gerenciador: GerenciadorDeSalas,
) -> None:
    sala = gerenciador.criar_sala("sid-1", "Ana")
    gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)

    sala_restante = gerenciador.remover_jogador("sid-1")

    assert sala_restante is not None
    assert "sid-1" not in sala_restante.jogadores
    assert "sid-2" in sala_restante.jogadores
    assert sala_restante.status == "finalizada"


def test_remover_ultimo_jogador_apaga_a_sala(gerenciador: GerenciadorDeSalas) -> None:
    sala = gerenciador.criar_sala("sid-1", "Ana")

    resultado = gerenciador.remover_jogador("sid-1")

    assert resultado is None
    with pytest.raises(SalaNaoEncontradaError):
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)

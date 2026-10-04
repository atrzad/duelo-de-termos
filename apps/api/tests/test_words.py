from app.game.words import PALAVRAS, palavra_aleatoria, palavra_e_valida


def test_todas_as_respostas_possiveis_sao_palavras_validas() -> None:
    # Garantido por união em words.py: sempre dá pra acertar a própria
    # palavra secreta, mesmo que o dicionário gerado por fora não a cubra.
    for palavra in PALAVRAS:
        assert palavra_e_valida(palavra)


def test_palavra_real_fora_da_lista_de_respostas_e_aceita() -> None:
    assert palavra_e_valida("CASAS")


def test_palavra_sem_sentido_e_rejeitada() -> None:
    assert not palavra_e_valida("ZZZZZ")
    assert not palavra_e_valida("QWXYZ")


def test_validacao_e_insensivel_a_caixa() -> None:
    assert palavra_e_valida("termo")
    assert palavra_e_valida("Termo")


def test_palavra_aleatoria_sempre_vem_da_lista_de_respostas() -> None:
    for _ in range(20):
        assert palavra_aleatoria() in PALAVRAS

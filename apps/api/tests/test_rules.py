from app.game.rules import evaluate_guess


def test_marca_tudo_correto_quando_palpite_igual_ao_segredo() -> None:
    assert evaluate_guess("TERMO", "TERMO") == [
        "correct", "correct", "correct", "correct", "correct",
    ]  # fmt: skip


def test_marca_tudo_ausente_quando_nao_ha_letras_em_comum() -> None:
    assert evaluate_guess("ABCDF", "TERMO") == [
        "absent", "absent", "absent", "absent", "absent",
    ]  # fmt: skip


def test_e_insensivel_a_maiusculas_e_minusculas() -> None:
    assert evaluate_guess("termo", "TERMO") == [
        "correct", "correct", "correct", "correct", "correct",
    ]  # fmt: skip


def test_marca_presente_quando_letra_existe_em_outra_posicao() -> None:
    assert evaluate_guess("ROTEM", "TERMO") == [
        "present", "present", "present", "present", "present",
    ]  # fmt: skip


def test_nao_repete_present_alem_da_quantidade_real_da_letra_no_segredo() -> None:
    resultado = evaluate_guess("RRABC", "TERMO")
    assert resultado[0] == "present"
    assert resultado[1] == "absent"


def test_trata_corretamente_letras_repetidas_no_segredo() -> None:
    assert evaluate_guess("AAAAA", "ARARA") == [
        "correct", "absent", "correct", "absent", "correct",
    ]  # fmt: skip

from app.game.modes import (
    categoria_normal,
    pontuacao_competitivo,
    pontuacao_hardcore,
    pontuacao_normal,
)


class TestPontuacaoCompetitivo:
    def test_pontos_igual_a_sete_menos_tentativas(self) -> None:
        assert pontuacao_competitivo(1) == 6
        assert pontuacao_competitivo(2) == 5
        assert pontuacao_competitivo(3) == 4
        assert pontuacao_competitivo(4) == 3
        assert pontuacao_competitivo(5) == 2
        assert pontuacao_competitivo(6) == 1

    def test_zero_pontos_quando_nao_acertou(self) -> None:
        assert pontuacao_competitivo(None) == 0

    def test_zero_pontos_fora_do_intervalo_valido(self) -> None:
        assert pontuacao_competitivo(0) == 0
        assert pontuacao_competitivo(7) == 0


class TestPontuacaoHardcore:
    def test_primeiro_a_acertar_ganha_tres(self) -> None:
        assert pontuacao_hardcore(foi_o_primeiro_a_acertar=True) == 3

    def test_quem_nao_foi_o_primeiro_ganha_zero(self) -> None:
        assert pontuacao_hardcore(foi_o_primeiro_a_acertar=False) == 0


class TestCategoriaNormal:
    def test_tentativas_1_a_3(self) -> None:
        assert categoria_normal(1, em_prorrogacao=False, via_tentativa_final=False) == "1-3"
        assert categoria_normal(3, em_prorrogacao=False, via_tentativa_final=False) == "1-3"

    def test_tentativas_4_a_6(self) -> None:
        assert categoria_normal(4, em_prorrogacao=False, via_tentativa_final=False) == "4-6"
        assert categoria_normal(6, em_prorrogacao=False, via_tentativa_final=False) == "4-6"

    def test_prorrogacao_tem_prioridade_sobre_o_numero_da_tentativa(self) -> None:
        assert categoria_normal(9, em_prorrogacao=True, via_tentativa_final=False) == "prorrogacao"

    def test_tentativa_final_tem_prioridade_sobre_tudo(self) -> None:
        resultado = categoria_normal(2, em_prorrogacao=True, via_tentativa_final=True)
        assert resultado == "tentativa_final"


class TestPontuacaoNormal:
    def test_tabela_basica(self) -> None:
        assert pontuacao_normal("1-3", primeiro_a_acertar=False) == 3
        assert pontuacao_normal("4-6", primeiro_a_acertar=False) == 2
        assert pontuacao_normal("prorrogacao", primeiro_a_acertar=False) == 1
        assert pontuacao_normal("tentativa_final", primeiro_a_acertar=False) == 1
        assert pontuacao_normal("nao_acertou", primeiro_a_acertar=False) == 0

    def test_bonus_de_um_ponto_pro_primeiro_a_acertar(self) -> None:
        assert pontuacao_normal("1-3", primeiro_a_acertar=True) == 4
        assert pontuacao_normal("prorrogacao", primeiro_a_acertar=True) == 2

    def test_sem_bonus_quando_nao_acertou(self) -> None:
        # "primeiro a acertar" não faz sentido pra quem não acertou.
        assert pontuacao_normal("nao_acertou", primeiro_a_acertar=True) == 0

import pytest

from app.game.modes import GameMode
from app.game.rooms import GerenciadorDeSalas, Sala, SalaEmAndamentoError, SalaNaoEncontradaError


@pytest.fixture
def gerenciador() -> GerenciadorDeSalas:
    return GerenciadorDeSalas()


def _palpite_errado(segredo: str) -> str:
    return "ZZZZZ" if segredo != "ZZZZZ" else "XXXXX"


class TestCriarEEntrar:
    def test_criar_sala_comeca_aguardando_com_um_jogador(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)

        assert sala.status == "aguardando"
        assert len(sala.jogadores) == 1
        assert sala.palavra_secreta is None
        assert len(sala.codigo) == 4

    def test_segundo_jogador_inicia_a_partida(self, gerenciador: GerenciadorDeSalas) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)
        sala2 = gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)

        assert sala2 is sala
        assert sala.status == "jogando"
        assert len(sala.jogadores) == 2
        assert sala.palavra_secreta is not None
        assert len(sala.palavra_secreta) == 5
        assert sala.iniciada_em is not None

    def test_entrar_em_sala_inexistente_da_erro(self, gerenciador: GerenciadorDeSalas) -> None:
        with pytest.raises(SalaNaoEncontradaError):
            gerenciador.entrar_sala("sid-1", "Ana", "ZZZZ")

    def test_entrar_em_sala_ja_cheia_e_em_andamento_da_erro(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)

        with pytest.raises(SalaEmAndamentoError):
            gerenciador.entrar_sala("sid-3", "Caio", sala.codigo)

    def test_codigo_da_sala_e_case_insensitive(self, gerenciador: GerenciadorDeSalas) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)
        sala2 = gerenciador.entrar_sala("sid-2", "Beto", sala.codigo.lower())

        assert sala2 is sala

    def test_nao_deixa_jogar_depois_que_a_partida_terminou(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
        assert sala.palavra_secreta is not None

        for _ in range(6):
            gerenciador.registrar_palpite("sid-1", _palpite_errado(sala.palavra_secreta))
        for _ in range(6):
            gerenciador.registrar_palpite("sid-2", _palpite_errado(sala.palavra_secreta))

        with pytest.raises(SalaEmAndamentoError):
            gerenciador.registrar_palpite("sid-1", sala.palavra_secreta)

    def test_remover_jogador_mantem_sala_pro_oponente_restante(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)

        sala_restante = gerenciador.remover_jogador("sid-1")

        assert sala_restante is not None
        assert "sid-1" not in sala_restante.jogadores
        assert "sid-2" in sala_restante.jogadores
        assert sala_restante.status == "finalizada"

    def test_remover_ultimo_jogador_apaga_a_sala(self, gerenciador: GerenciadorDeSalas) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)

        resultado = gerenciador.remover_jogador("sid-1")

        assert resultado is None
        with pytest.raises(SalaNaoEncontradaError):
            gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)


class TestModoCompetitivo:
    def test_quem_acerta_primeiro_nao_bloqueia_o_outro(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
        assert sala.palavra_secreta is not None
        segredo = sala.palavra_secreta

        sala_atualizada, _, _, _ = gerenciador.registrar_palpite("sid-1", segredo)

        # Ana acertou de primeira, mas a sala continua em andamento: Beto
        # ainda pode jogar (diferente do Hardcore).
        assert sala_atualizada.status == "jogando"
        assert sala_atualizada.jogadores["sid-1"].pontos == 6

    def test_pontuacao_sete_menos_tentativas_decide_o_resultado(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
        assert sala.palavra_secreta is not None
        segredo = sala.palavra_secreta
        errado = _palpite_errado(segredo)

        # Ana acerta de primeira (6 pontos).
        gerenciador.registrar_palpite("sid-1", segredo)
        # Beto erra duas vezes e acerta na 3ª (4 pontos).
        gerenciador.registrar_palpite("sid-2", errado)
        gerenciador.registrar_palpite("sid-2", errado)
        sala_final, _, _, _ = gerenciador.registrar_palpite("sid-2", segredo)

        assert sala_final.status == "finalizada"
        assert sala_final.resultado_para("sid-1") == "venceu"
        assert sala_final.resultado_para("sid-2") == "perdeu"

    def test_quem_esgota_tentativas_sem_acertar_fica_com_zero(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
        assert sala.palavra_secreta is not None
        segredo = sala.palavra_secreta
        errado = _palpite_errado(segredo)

        for _ in range(6):
            sala_atualizada, _, _, _ = gerenciador.registrar_palpite("sid-1", errado)
        assert sala_atualizada.status == "jogando"  # Beto ainda não jogou

        sala_final, _, _, _ = gerenciador.registrar_palpite("sid-2", segredo)

        assert sala_final.status == "finalizada"
        assert sala_final.jogadores["sid-1"].pontos == 0
        assert sala_final.resultado_para("sid-2") == "venceu"

    def test_empate_quando_ambos_tem_a_mesma_pontuacao(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
        assert sala.palavra_secreta is not None
        segredo = sala.palavra_secreta
        errado = _palpite_errado(segredo)

        gerenciador.registrar_palpite("sid-1", errado)
        gerenciador.registrar_palpite("sid-1", segredo)
        gerenciador.registrar_palpite("sid-2", errado)
        sala_final, _, _, _ = gerenciador.registrar_palpite("sid-2", segredo)

        assert sala_final.jogadores["sid-1"].pontos == sala_final.jogadores["sid-2"].pontos
        assert sala_final.resultado_para("sid-1") == "empate"
        assert sala_final.resultado_para("sid-2") == "empate"


class TestModoHardcore:
    def test_primeiro_acerto_encerra_a_partida_na_hora(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.hardcore)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
        assert sala.palavra_secreta is not None

        sala_final, _, _, _ = gerenciador.registrar_palpite("sid-1", sala.palavra_secreta)

        assert sala_final.status == "finalizada"
        assert sala_final.jogadores["sid-1"].pontos == 3
        assert sala_final.jogadores["sid-2"].pontos == 0
        assert sala_final.resultado_para("sid-1") == "venceu"
        assert sala_final.resultado_para("sid-2") == "perdeu"

    def test_oponente_nao_pode_mais_jogar_depois_do_encerramento(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.hardcore)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
        assert sala.palavra_secreta is not None

        gerenciador.registrar_palpite("sid-1", sala.palavra_secreta)

        with pytest.raises(SalaEmAndamentoError):
            gerenciador.registrar_palpite("sid-2", sala.palavra_secreta)

    def test_tempo_esgotado_sem_ninguem_acertar_nao_da_ponto_a_ninguem(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.hardcore)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)

        sala_final = gerenciador.expirar_tempo(sala.codigo)

        assert sala_final is not None
        assert sala_final.status == "finalizada"
        assert sala_final.jogadores["sid-1"].pontos == 0
        assert sala_final.jogadores["sid-2"].pontos == 0
        assert sala_final.resultado_para("sid-1") == "empate"

    def test_expirar_tempo_e_idempotente(self, gerenciador: GerenciadorDeSalas) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.hardcore)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)

        gerenciador.expirar_tempo(sala.codigo)
        resultado_repetido = gerenciador.expirar_tempo(sala.codigo)

        assert resultado_repetido is None


class TestModoNormal:
    def test_acerto_na_tentativa_1_a_3_vale_tres_pontos(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.normal)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
        assert sala.palavra_secreta is not None

        sala_atualizada, _, _, _ = gerenciador.registrar_palpite("sid-1", sala.palavra_secreta)

        # Ana concluiu, mas a sala continua: Beto ainda não jogou.
        assert sala_atualizada.status == "jogando"
        assert sala_atualizada.jogadores["sid-1"].pontos == 4  # 3 + bônus de primeiro

    def test_oponente_continua_jogando_depois_que_o_outro_acerta(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.normal)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
        assert sala.palavra_secreta is not None
        segredo = sala.palavra_secreta
        errado = _palpite_errado(segredo)

        gerenciador.registrar_palpite("sid-1", segredo)  # Ana resolve
        sala_atualizada, _, _, _ = gerenciador.registrar_palpite("sid-2", errado)  # Beto ainda joga

        assert sala_atualizada.status == "jogando"

    def test_prorrogacao_depois_da_sexta_tentativa_vale_um_ponto(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.normal)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
        assert sala.palavra_secreta is not None
        segredo = sala.palavra_secreta
        errado = _palpite_errado(segredo)

        for _ in range(6):
            gerenciador.registrar_palpite("sid-1", errado)
        sala_atualizada, _, _, _ = gerenciador.registrar_palpite("sid-1", segredo)  # 7ª tentativa

        assert sala_atualizada.jogadores["sid-1"].pontos == 2  # 1 + bônus de primeiro

    def test_tempo_esgotado_libera_exatamente_uma_tentativa_final(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.normal)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
        assert sala.palavra_secreta is not None
        segredo = sala.palavra_secreta
        errado = _palpite_errado(segredo)

        gerenciador.expirar_tempo(sala.codigo)

        # Tentativa final: acerta -> 1 ponto (+ bônus de primeiro, já que
        # ninguém mais tinha acertado ainda).
        sala_atualizada, _, _, _ = gerenciador.registrar_palpite("sid-1", segredo)
        assert sala_atualizada.jogadores["sid-1"].pontos == 2

        # Segunda tentativa depois do tempo: não é mais permitida.
        with pytest.raises(SalaEmAndamentoError):
            gerenciador.registrar_palpite("sid-1", errado)

        # Beto ainda não usou a tentativa final dele -> sala segue aberta.
        assert sala_atualizada.status == "jogando"
        sala_final, _, _, _ = gerenciador.registrar_palpite("sid-2", errado)
        assert sala_final.status == "finalizada"
        assert sala_final.jogadores["sid-2"].pontos == 0

    def test_forcar_fim_conclui_quem_nao_usou_a_tentativa_final(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.normal)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)

        gerenciador.expirar_tempo(sala.codigo)
        sala_final = gerenciador.forcar_fim_tentativa_final(sala.codigo)

        assert sala_final is not None
        assert sala_final.status == "finalizada"
        assert sala_final.jogadores["sid-1"].pontos == 0
        assert sala_final.jogadores["sid-2"].pontos == 0


class TestModoInfinito:
    def test_rodada_avanca_sem_finalizar_a_sala(self, gerenciador: GerenciadorDeSalas) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.infinito)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
        assert sala.palavra_secreta is not None
        segredo = sala.palavra_secreta
        errado = _palpite_errado(segredo)

        gerenciador.registrar_palpite("sid-1", segredo)  # Ana acerta de primeira: 6 pontos
        for _ in range(6):
            sala_atualizada, _, _, rodada_avancou = gerenciador.registrar_palpite("sid-2", errado)

        # A última tentativa de Beto (6ª, esgotando as tentativas) é o que
        # fecha a rodada -- os dois já tinham concluído.
        assert rodada_avancou is True
        assert sala_atualizada.status == "jogando"  # nunca finaliza sozinha
        assert sala_atualizada.rodada_atual == 2
        assert sala_atualizada.palavra_secreta is not None

        # Placar da rodada 1 foi pro total; placar da rodada (novo) zerado.
        ana = sala_atualizada.jogadores["sid-1"]
        beto = sala_atualizada.jogadores["sid-2"]
        assert ana.pontos_totais == 6  # 7 - 1 tentativa
        assert ana.pontos == 0
        assert beto.pontos_totais == 0
        assert beto.pontos == 0

        # Estado da rodada anterior não sobrevive.
        assert ana.tentativas == []
        assert beto.tentativas == []
        assert ana.venceu is False
        assert beto.esgotou_tentativas is False

    def test_numero_da_tentativa_retornado_nao_e_afetado_pelo_reset_da_rodada(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.infinito)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
        assert sala.palavra_secreta is not None
        segredo = sala.palavra_secreta
        errado = _palpite_errado(segredo)

        gerenciador.registrar_palpite("sid-1", segredo)
        for _ in range(5):
            gerenciador.registrar_palpite("sid-2", errado)

        # 6ª tentativa de Beto: fecha a rodada (reseta jogador.tentativas),
        # mas o número retornado tem que refletir que foi a 6ª mesmo assim.
        _, _, numero_tentativa, rodada_avancou = gerenciador.registrar_palpite("sid-2", errado)

        assert rodada_avancou is True
        assert numero_tentativa == 6

    def test_pontuacao_acumula_entre_rodadas(self, gerenciador: GerenciadorDeSalas) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.infinito)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)

        for _ in range(2):  # joga 2 rodadas completas
            assert sala.palavra_secreta is not None
            segredo = sala.palavra_secreta
            errado = _palpite_errado(segredo)
            gerenciador.registrar_palpite("sid-1", segredo)  # Ana: 6 pontos
            for _ in range(6):
                sala, *_ = gerenciador.registrar_palpite("sid-2", errado)  # Beto: 0 pontos

        assert sala.jogadores["sid-1"].pontos_totais == 12  # 6 + 6
        assert sala.jogadores["sid-2"].pontos_totais == 0
        assert sala.rodada_atual == 3

    def test_sair_no_meio_de_uma_sessao_infinita_finaliza_a_sala(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.infinito)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)

        sala_restante = gerenciador.remover_jogador("sid-2")

        assert sala_restante is not None
        assert sala_restante.status == "finalizada"


class TestReconexao:
    def test_marcar_desconectado_nao_remove_o_jogador(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)

        sala_atualizada = gerenciador.marcar_desconectado("sid-1")

        assert sala_atualizada is not None
        assert "sid-1" in sala_atualizada.jogadores
        assert sala_atualizada.jogadores["sid-1"].desconectado_em is not None
        assert sala_atualizada.status == "jogando"  # não finaliza na hora

    def test_reconectar_com_token_valido_troca_o_sid(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
        token_ana = sala.jogadores["sid-1"].token

        gerenciador.marcar_desconectado("sid-1")
        resultado = gerenciador.reconectar(token_ana, "sid-1-novo")

        assert resultado is not None
        sala_atualizada, jogador, sid_antigo = resultado
        assert sid_antigo == "sid-1"
        assert jogador.nome == "Ana"
        assert jogador.sid == "sid-1-novo"
        assert jogador.desconectado_em is None
        assert "sid-1" not in sala_atualizada.jogadores
        assert "sid-1-novo" in sala_atualizada.jogadores
        assert gerenciador.sala_do_jogador("sid-1-novo") is sala_atualizada
        assert gerenciador.sala_do_jogador("sid-1") is None

    def test_reconectar_preserva_tentativas_e_pontos(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
        assert sala.palavra_secreta is not None
        token_ana = sala.jogadores["sid-1"].token
        errado = _palpite_errado(sala.palavra_secreta)

        gerenciador.registrar_palpite("sid-1", errado)
        gerenciador.marcar_desconectado("sid-1")
        _, jogador, _ = gerenciador.reconectar(token_ana, "sid-1-novo")  # type: ignore[misc]

        assert len(jogador.tentativas) == 1
        assert jogador.tentativas[0].letras == list(errado)

    def test_reconectar_com_token_invalido_retorna_none(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)

        assert gerenciador.reconectar("token-que-nao-existe", "sid-novo") is None

    def test_remover_se_ainda_desconectado_remove_depois_do_timeout(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
        gerenciador.marcar_desconectado("sid-1")

        sala_restante = gerenciador.remover_se_ainda_desconectado("sid-1")

        assert sala_restante is not None
        assert "sid-1" not in sala_restante.jogadores
        assert sala_restante.status == "finalizada"

    def test_remover_se_ainda_desconectado_e_noop_se_ja_reconectou(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
        token_ana = sala.jogadores["sid-1"].token

        gerenciador.marcar_desconectado("sid-1")
        gerenciador.reconectar(token_ana, "sid-1-novo")

        # Timeout chega depois, mas pelo sid ANTIGO -- já não existe mais.
        resultado = gerenciador.remover_se_ainda_desconectado("sid-1")

        assert resultado is None
        sala_ainda_ativa = gerenciador.sala_do_jogador("sid-1-novo")
        assert sala_ainda_ativa is not None
        assert "sid-1-novo" in sala_ainda_ativa.jogadores


class TestRevanche:
    def _jogar_ate_terminar(self, gerenciador: GerenciadorDeSalas, sala: Sala) -> None:
        assert sala.palavra_secreta is not None
        errado = _palpite_errado(sala.palavra_secreta)
        gerenciador.registrar_palpite("sid-1", sala.palavra_secreta)
        for _ in range(6):
            gerenciador.registrar_palpite("sid-2", errado)

    def test_um_pedido_so_nao_reinicia_a_partida(self, gerenciador: GerenciadorDeSalas) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
        self._jogar_ate_terminar(gerenciador, sala)
        assert sala.status == "finalizada"

        sala_atualizada, os_dois_pediram = gerenciador.pedir_revanche("sid-1")

        assert os_dois_pediram is False
        assert sala_atualizada.status == "finalizada"

    def test_os_dois_pedindo_reinicia_a_mesma_sala(self, gerenciador: GerenciadorDeSalas) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
        self._jogar_ate_terminar(gerenciador, sala)
        palavra_antiga = sala.palavra_secreta

        gerenciador.pedir_revanche("sid-1")
        sala_atualizada, os_dois_pediram = gerenciador.pedir_revanche("sid-2")

        assert os_dois_pediram is True
        assert sala_atualizada.codigo == sala.codigo
        assert sala_atualizada.status == "jogando"
        assert sala_atualizada.jogadores["sid-1"].nome == "Ana"
        assert sala_atualizada.jogadores["sid-2"].nome == "Beto"
        assert sala_atualizada.jogadores["sid-1"].pontos == 0
        assert sala_atualizada.jogadores["sid-1"].tentativas == []
        assert sala_atualizada.jogadores["sid-1"].venceu is False
        assert sala_atualizada.palavra_secreta is not None
        del palavra_antiga  # só documentando que a palavra pode (ou não) mudar

    def test_pedir_revanche_antes_da_partida_terminar_da_erro(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)

        with pytest.raises(SalaEmAndamentoError):
            gerenciador.pedir_revanche("sid-1")

    def test_revanche_zera_o_placar_acumulado_do_infinito(
        self, gerenciador: GerenciadorDeSalas
    ) -> None:
        sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.infinito)
        gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
        sala.jogadores["sid-1"].pontos_totais = 42  # simula sessão já jogada
        sala.status = "finalizada"  # só termina por desconexão, forçado aqui pro teste

        gerenciador.pedir_revanche("sid-1")
        sala_atualizada, os_dois_pediram = gerenciador.pedir_revanche("sid-2")

        assert os_dois_pediram is True
        assert sala_atualizada.jogadores["sid-1"].pontos_totais == 0
        assert sala_atualizada.rodada_atual == 1

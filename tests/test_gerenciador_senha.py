from security.gerenciador_senha import GerenciadorSenha


def test_hash_diferente_da_senha():
    hashe = GerenciadorSenha.gerar_hash("minha_senha")
    assert hashe != "minha_senha"


def test_senha_correta_valida():
    hashe = GerenciadorSenha.gerar_hash("minha_senha")
    assert GerenciadorSenha.verificar_hash("minha_senha", hashe) is True


def test_senha_errada_nao_valida():
    hashe = GerenciadorSenha.gerar_hash("minha_senha")
    assert GerenciadorSenha.verificar_hash("senha_errada", hashe) is False


def test_hashes_sao_unicos_por_salt():
    assert GerenciadorSenha.gerar_hash("igual") != GerenciadorSenha.gerar_hash("igual")


def test_senha_gigante_nao_estoura():
    """Regressao: bcrypt 5.x levanta ValueError acima de 72 bytes; a
    verificacao deve responder False, nunca propagar excecao (virava 500)."""
    hashe = GerenciadorSenha.gerar_hash("minha_senha")
    assert GerenciadorSenha.verificar_hash("x" * 10_000, hashe) is False

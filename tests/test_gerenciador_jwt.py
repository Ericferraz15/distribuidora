from security.gerenciador_jwt import GerenciadorJwt


def test_access_token_valido():
    g = GerenciadorJwt()
    token = g.gerar_token(1, "admin", "access")
    dados = g.verificar_token(token)
    assert dados is not None
    assert dados["sub"] == "1"
    assert dados["permissao"] == "admin"
    assert dados["tipo"] == "access"


def test_refresh_dura_mais_que_access():
    g = GerenciadorJwt()
    acc = g.verificar_token(g.gerar_token(1, "admin", "access"))
    ref = g.verificar_token(g.gerar_token(1, "admin", "refresh"))
    assert ref["exp"] > acc["exp"]


def test_token_invalido_retorna_none():
    g = GerenciadorJwt()
    assert g.verificar_token("xxx.yyy.zzz") is None


def test_renovar_com_refresh_gera_access():
    g = GerenciadorJwt()
    refresh = g.gerar_token(1, "admin", "refresh")
    novo = g.renovar_token(refresh)
    dados = g.verificar_token(novo)
    assert dados is not None
    assert dados["tipo"] == "access"


def test_renovar_com_access_retorna_none():
    g = GerenciadorJwt()
    access = g.gerar_token(1, "admin", "access")
    assert g.renovar_token(access) is None

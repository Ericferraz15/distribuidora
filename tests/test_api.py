"""Testes de integracao dos fluxos de negocio (RF/RNF/RN)."""


def _criar_produto(client, admin_headers, nome="Cerveja", valor=5.0, quantidade=10):
    resp = client.post(
        "/produtos",
        headers=admin_headers,
        json={"nome": nome, "valor": valor, "quantidade": quantidade, "fornecedor": "Ambev"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# --- RF01 / autenticacao -----------------------------------------------------
def test_login_sucesso_e_falha(client, admin):
    ok = client.post("/auth/login", data={"username": "admin", "password": "admin123"})
    assert ok.status_code == 200
    assert "access_token" in ok.json()

    ruim = client.post("/auth/login", data={"username": "admin", "password": "errada"})
    assert ruim.status_code == 401


def test_rota_protegida_sem_token(client):
    assert client.get("/produtos").status_code == 401


# --- RNF03 / RBAC ------------------------------------------------------------
def test_dashboard_exige_admin(client, func_headers):
    assert client.get("/dashboard/resumo", headers=func_headers).status_code == 403


def test_dashboard_admin_ok(client, admin_headers):
    resp = client.get("/dashboard/resumo", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["num_transacoes"] == 0


def test_funcionario_nao_cria_produto(client, func_headers):
    resp = client.post(
        "/produtos",
        headers=func_headers,
        json={"nome": "X", "valor": 1, "quantidade": 1, "fornecedor": "Y"},
    )
    assert resp.status_code == 403


# --- RF05 / estoque ----------------------------------------------------------
def test_funcionario_ve_estoque(client, admin_headers, func_headers):
    _criar_produto(client, admin_headers)
    resp = client.get("/produtos", headers=func_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# --- RF02 / RN02 -------------------------------------------------------------
def test_abrir_turno_e_bloqueio_rn02(client, func_headers, admin_headers):
    r1 = client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 100})
    assert r1.status_code == 201
    assert r1.json()["status"] == "aberto"

    # RN02: com um turno aberto, ninguem pode abrir outro.
    r2 = client.post("/turnos/abrir", headers=admin_headers, json={"saldo_inicial": 50})
    assert r2.status_code == 409


def test_encerrar_e_reabrir(client, func_headers):
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 100})
    fechar = client.post(
        "/turnos/encerrar", headers=func_headers, json={"saldo_final_informado": 100}
    )
    assert fechar.status_code == 200
    assert fechar.json()["status"] == "encerrado"

    reabrir = client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 0})
    assert reabrir.status_code == 201


# --- RF04 / RF06 / RNF02 -----------------------------------------------------
def test_venda_baixa_estoque_e_audita(client, admin_headers, func_headers, funcionario):
    produto = _criar_produto(client, admin_headers, valor=5.0, quantidade=10)
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 0})

    venda = client.post(
        "/transacoes/venda",
        headers=func_headers,
        json={
            "itens": [{"produto_id": produto["id"], "quantidade": 3}],
            "metodo_pagamento": "dinheiro",
        },
    )
    assert venda.status_code == 201, venda.text
    corpo = venda.json()
    assert float(corpo["valor"]) == 15.0  # 3 * 5.00
    assert corpo["funcionario_id"] == funcionario.id  # RNF02: auditoria

    # RF06: estoque baixado de 10 -> 7.
    lista = client.get("/produtos", headers=func_headers).json()
    assert lista[0]["quantidade"] == 7

    # RF03: saldo do caixa reflete a venda.
    caixa = client.get("/caixa/atual", headers=func_headers).json()
    assert caixa["aberto"] is True
    assert float(caixa["saldo_atual"]) == 15.0


def test_venda_estoque_insuficiente(client, admin_headers, func_headers):
    produto = _criar_produto(client, admin_headers, quantidade=2)
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 0})
    resp = client.post(
        "/transacoes/venda",
        headers=func_headers,
        json={
            "itens": [{"produto_id": produto["id"], "quantidade": 5}],
            "metodo_pagamento": "dinheiro",
        },
    )
    assert resp.status_code == 409


# --- RN01 --------------------------------------------------------------------
def test_rn01_apenas_dono_movimenta(client, admin_headers, func_headers, db_session):
    from models.usuario_model import Usuario
    from security.gerenciador_senha import GerenciadorSenha

    # func abre o turno; outro funcionario tenta vender.
    produto = _criar_produto(client, admin_headers)
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 0})

    outro = Usuario(
        nome="func2",
        senha_hash=GerenciadorSenha.gerar_hash("x"),
        permissao="funcionario",
    )
    db_session.add(outro)
    db_session.commit()
    login = client.post("/auth/login", data={"username": "func2", "password": "x"})
    outro_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = client.post(
        "/transacoes/venda",
        headers=outro_headers,
        json={
            "itens": [{"produto_id": produto["id"], "quantidade": 1}],
            "metodo_pagamento": "dinheiro",
        },
    )
    assert resp.status_code == 403  # RN01


def test_venda_sem_turno(client, admin_headers, func_headers):
    produto = _criar_produto(client, admin_headers)
    resp = client.post(
        "/transacoes/venda",
        headers=func_headers,
        json={
            "itens": [{"produto_id": produto["id"], "quantidade": 1}],
            "metodo_pagamento": "dinheiro",
        },
    )
    assert resp.status_code == 409


# --- RF07 / dashboard --------------------------------------------------------
def test_dashboard_mais_vendidos(client, admin_headers, func_headers):
    produto = _criar_produto(client, admin_headers, valor=5.0, quantidade=10)
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 0})
    client.post(
        "/transacoes/venda",
        headers=func_headers,
        json={
            "itens": [{"produto_id": produto["id"], "quantidade": 4}],
            "metodo_pagamento": "dinheiro",
        },
    )
    resp = client.get("/dashboard/mais-vendidos", headers=admin_headers)
    assert resp.status_code == 200
    dados = resp.json()
    assert dados[0]["produto_id"] == produto["id"]
    assert dados[0]["quantidade_total"] == 4

    resumo = client.get("/dashboard/resumo", headers=admin_headers).json()
    assert float(resumo["faturamento"]) == 20.0
    assert resumo["num_vendas"] == 1


# --- Seguranca -----------------------------------------------------------------
def test_cadastro_rejeita_senha_fraca_ou_gigante(client, admin_headers):
    # < 6 chars: fraca demais; > 72 bytes: estoura o limite do bcrypt (viraria 500).
    for senha in ("123", "x" * 73):
        resp = client.post(
            "/usuarios",
            headers=admin_headers,
            json={"nome": "novo_func", "senha": senha},
        )
        assert resp.status_code == 422, resp.text


def test_usuario_desativado_nao_loga(client, admin_headers, funcionario):
    resp = client.patch(
        f"/usuarios/{funcionario.id}", headers=admin_headers, json={"ativo": False}
    )
    assert resp.status_code == 200

    login = client.post("/auth/login", data={"username": "func", "password": "func123"})
    assert login.status_code == 401


def test_admin_nao_se_rebaixa_nem_se_desativa(client, admin, admin_headers):
    # Anti-lockout: evita que o unico admin se tranque para fora do sistema.
    rebaixar = client.patch(
        f"/usuarios/{admin.id}", headers=admin_headers, json={"permissao": "funcionario"}
    )
    assert rebaixar.status_code == 400

    desativar = client.patch(
        f"/usuarios/{admin.id}", headers=admin_headers, json={"ativo": False}
    )
    assert desativar.status_code == 400

    # Editar o proprio telefone continua permitido.
    telefone = client.patch(
        f"/usuarios/{admin.id}",
        headers=admin_headers,
        json={"numero_telefone": "11988887777"},
    )
    assert telefone.status_code == 200


def test_auth_me(client, admin, admin_headers):
    resp = client.get("/auth/me", headers=admin_headers)
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["nome"] == "admin"
    assert corpo["permissao"] == "admin"
    assert "senha_hash" not in corpo  # nunca vaza o hash


def test_caixa_informa_nome_do_funcionario(client, func_headers):
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 10})
    caixa = client.get("/caixa/atual", headers=func_headers).json()
    assert caixa["funcionario_nome"] == "func"


def test_patch_usuario_para_nome_ja_usado_da_409(client, admin_headers, funcionario):
    """Regressao: renomear para nome existente dava 500 (IntegrityError cru)."""
    r = client.post(
        "/usuarios", headers=admin_headers, json={"nome": "outro", "senha": "123456"}
    )
    uid = r.json()["id"]
    resp = client.patch(f"/usuarios/{uid}", headers=admin_headers, json={"nome": "func"})
    assert resp.status_code == 409, resp.text


# --- Caixa nunca fica negativo (regressao: sangria > saldo era aceita) --------
def test_sangria_nao_excede_o_dinheiro_da_gaveta(client, func_headers):
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 100})

    gigante = client.post(
        "/transacoes/saida", headers=func_headers, json={"valor": 150, "categoria": "sangria"}
    )
    assert gigante.status_code == 409, gigante.text

    exata = client.post(
        "/transacoes/saida", headers=func_headers, json={"valor": 100, "categoria": "sangria"}
    )
    assert exata.status_code == 201, exata.text

    # Caixa zerado: qualquer nova saida e negada.
    a_mais = client.post(
        "/transacoes/saida", headers=func_headers, json={"valor": 0.01, "categoria": "sangria"}
    )
    assert a_mais.status_code == 409
    saldo = client.get("/caixa/atual", headers=func_headers).json()["saldo_atual"]
    assert float(saldo) == 0.0


def test_venda_no_cartao_nao_vira_dinheiro_na_gaveta(client, admin_headers, func_headers):
    produto = _criar_produto(client, admin_headers, valor=50.0, quantidade=10)
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 0})
    client.post(
        "/transacoes/venda",
        headers=func_headers,
        json={"itens": [{"produto_id": produto["id"], "quantidade": 1}], "metodo_pagamento": "credito"},
    )

    # Ha 50 de saldo total, mas ZERO em notas: sangria em dinheiro e negada...
    sangria = client.post(
        "/transacoes/saida",
        headers=func_headers,
        json={"valor": 10, "categoria": "sangria", "metodo_pagamento": "dinheiro"},
    )
    assert sangria.status_code == 409, sangria.text

    # ...mas uma despesa paga no cartao (ate o saldo total) e valida.
    despesa = client.post(
        "/transacoes/saida",
        headers=func_headers,
        json={"valor": 50, "categoria": "despesa", "metodo_pagamento": "credito"},
    )
    assert despesa.status_code == 201, despesa.text


# --- Turno destravavel (regressao: deadlock RN01+RN02) -------------------------
def test_admin_pode_encerrar_turno_de_outro(client, admin_headers, func_headers):
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 10})
    resp = client.post(
        "/turnos/encerrar", headers=admin_headers, json={"saldo_final_informado": 10}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "encerrado"


def test_outro_funcionario_nao_encerra_turno(client, func_headers, db_session):
    from models.usuario_model import Usuario
    from security.gerenciador_senha import GerenciadorSenha

    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 10})
    db_session.add(
        Usuario(nome="func3", senha_hash=GerenciadorSenha.gerar_hash("x123456"), permissao="funcionario")
    )
    db_session.commit()
    login = client.post("/auth/login", data={"username": "func3", "password": "x123456"})
    outro = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = client.post("/turnos/encerrar", headers=outro, json={"saldo_final_informado": 10})
    assert resp.status_code == 403  # RN01 continua valendo entre funcionarios


# --- Limites de quantidade (regressao: int32 overflow virava 500) --------------
def test_quantidades_gigantes_dao_422(client, admin_headers, func_headers):
    tres_bi = 3_000_000_000
    criar = client.post(
        "/produtos",
        headers=admin_headers,
        json={"nome": "G", "valor": 1, "quantidade": tres_bi, "fornecedor": "x"},
    )
    assert criar.status_code == 422

    produto = _criar_produto(client, admin_headers)
    entrada = client.post(
        f"/produtos/{produto['id']}/entrada", headers=admin_headers, json={"quantidade": tres_bi}
    )
    assert entrada.status_code == 422

    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 0})
    venda = client.post(
        "/transacoes/venda",
        headers=func_headers,
        json={"itens": [{"produto_id": produto["id"], "quantidade": tres_bi}], "metodo_pagamento": "dinheiro"},
    )
    assert venda.status_code == 422


def test_entrada_estoque_respeita_teto_acumulado(client, admin_headers):
    produto = _criar_produto(client, admin_headers, quantidade=999_999)
    resp = client.post(
        f"/produtos/{produto['id']}/entrada", headers=admin_headers, json={"quantidade": 2}
    )
    assert resp.status_code == 409  # 999_999 + 2 estoura o teto de 1_000_000


def test_login_com_senha_gigante_da_401(client, admin):
    """Regressao: senha de 10KB estourava o bcrypt (ValueError -> 500)."""
    resp = client.post("/auth/login", data={"username": "admin", "password": "x" * 10_000})
    assert resp.status_code == 401


def test_venda_com_itens_demais_da_422(client, admin_headers, func_headers):
    produto = _criar_produto(client, admin_headers, quantidade=1000)
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 0})
    resp = client.post(
        "/transacoes/venda",
        headers=func_headers,
        json={
            "itens": [{"produto_id": produto["id"], "quantidade": 1}] * 101,
            "metodo_pagamento": "dinheiro",
        },
    )
    assert resp.status_code == 422


# --- Dashboard (regressao: LIMIT negativo derrubava a query no Postgres) -------
def test_mais_vendidos_limite_invalido_da_422(client, admin_headers):
    assert client.get("/dashboard/mais-vendidos?limite=-1", headers=admin_headers).status_code == 422
    assert client.get("/dashboard/mais-vendidos?limite=0", headers=admin_headers).status_code == 422
    assert client.get("/dashboard/mais-vendidos?limite=101", headers=admin_headers).status_code == 422


# --- Remocao da categoria "suprimento" (2026-07) -------------------------------
def test_suprimento_nao_e_mais_aceito(client, func_headers):
    """Escrita estrita: a categoria foi removida; criar uma agora e 422."""
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 100})
    resp = client.post(
        "/transacoes/saida",
        headers=func_headers,
        json={"valor": 10, "categoria": "suprimento"},
    )
    assert resp.status_code == 422, resp.text


def test_transacao_legada_suprimento_ainda_serializa(client, func_headers, db_session):
    """Leitura tolerante: linhas antigas com categoria legada nao quebram o GET."""
    from models.transacao_model import Transacao

    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 100})
    caixa = client.get("/caixa/atual", headers=func_headers).json()

    # Simula uma transacao historica gravada antes da remocao da categoria.
    db_session.add(
        Transacao(
            caixa_id=caixa["caixa_id"],
            funcionario_id=caixa["funcionario_id"],
            tipo="entrada",
            categoria="suprimento",
            valor=25,
            metodo_pagamento="dinheiro",
        )
    )
    db_session.commit()

    resp = client.get("/transacoes", headers=func_headers)
    assert resp.status_code == 200, resp.text
    assert any(t["categoria"] == "suprimento" for t in resp.json())

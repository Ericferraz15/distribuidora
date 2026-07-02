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

"""Bateria extra de testes de caca a bugs (integracao via TestClient).

Foco em casos de borda que a suite original nao cobre:
  - PATCH com campos null explicitos (robustez de API)
  - atomicidade da venda (rollback total em falha parcial)
  - RN01 para admins (movimentar caixa e exclusivo do dono)
  - produto inativo, /caixa/fechar, refresh token, fuso do dashboard
"""

from datetime import datetime, timezone
from decimal import Decimal


def _criar_produto(client, admin_headers, nome="Cerveja", valor=5.0, quantidade=10):
    resp = client.post(
        "/produtos",
        headers=admin_headers,
        json={"nome": nome, "valor": valor, "quantidade": quantidade, "fornecedor": "Ambev"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# --- Robustez: PATCH com null explicito ---------------------------------------
def test_patch_produto_com_nome_null_nao_da_500(client, admin_headers):
    """Regressao: campo NOT NULL com null explicito dava IntegrityError cru (500)."""
    produto = _criar_produto(client, admin_headers)
    resp = client.patch(
        f"/produtos/{produto['id']}", headers=admin_headers, json={"nome": None}
    )
    assert resp.status_code == 422, (
        f"esperava 422, veio {resp.status_code}: {resp.text}"
    )


def test_patch_produto_com_valor_null_nao_da_500(client, admin_headers):
    produto = _criar_produto(client, admin_headers)
    resp = client.patch(
        f"/produtos/{produto['id']}", headers=admin_headers, json={"valor": None}
    )
    assert resp.status_code == 422, (
        f"esperava 422, veio {resp.status_code}: {resp.text}"
    )


def test_patch_produto_com_ativo_null_nao_da_500(client, admin_headers):
    produto = _criar_produto(client, admin_headers)
    resp = client.patch(
        f"/produtos/{produto['id']}", headers=admin_headers, json={"ativo": None}
    )
    assert resp.status_code == 422, (
        f"esperava 422, veio {resp.status_code}: {resp.text}"
    )


def test_patch_usuario_com_nome_null_da_erro_claro(client, admin_headers, funcionario):
    """null em campo NOT NULL deve dar 422 (validacao), nao um 409 enganoso
    de 'nome ja existe' nem 500."""
    resp = client.patch(
        f"/usuarios/{funcionario.id}", headers=admin_headers, json={"nome": None}
    )
    assert resp.status_code == 422, (
        f"esperava 422, veio {resp.status_code}: {resp.text}"
    )


def test_patch_usuario_com_ativo_null_da_erro_claro(client, admin_headers, funcionario):
    resp = client.patch(
        f"/usuarios/{funcionario.id}", headers=admin_headers, json={"ativo": None}
    )
    assert resp.status_code == 422, (
        f"esperava 422, veio {resp.status_code}: {resp.text}"
    )


# --- Atomicidade da venda ------------------------------------------------------
def test_venda_multi_item_falha_no_meio_nao_baixa_nada(client, admin_headers, func_headers):
    """2o item sem estoque: a venda inteira deve ser desfeita (rollback),
    inclusive a baixa do 1o item."""
    p1 = _criar_produto(client, admin_headers, nome="Agua", quantidade=10)
    p2 = _criar_produto(client, admin_headers, nome="Vodka", quantidade=1)
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 0})

    resp = client.post(
        "/transacoes/venda",
        headers=func_headers,
        json={
            "itens": [
                {"produto_id": p1["id"], "quantidade": 5},
                {"produto_id": p2["id"], "quantidade": 3},  # so ha 1
            ],
            "metodo_pagamento": "dinheiro",
        },
    )
    assert resp.status_code == 409

    estoque = {p["nome"]: p["quantidade"] for p in client.get("/produtos", headers=func_headers).json()}
    assert estoque["Agua"] == 10, "estoque do 1o item nao foi restaurado no rollback"
    assert estoque["Vodka"] == 1

    # E o caixa nao pode ter registrado transacao nenhuma.
    transacoes = client.get("/transacoes", headers=func_headers).json()
    assert transacoes == [], "venda abortada deixou transacao orfa no caixa"


def test_venda_produto_duplicado_na_lista_soma_as_baixas(client, admin_headers, func_headers):
    """Mesmo produto 2x na lista: as quantidades devem se acumular."""
    produto = _criar_produto(client, admin_headers, valor=2.0, quantidade=10)
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 0})

    resp = client.post(
        "/transacoes/venda",
        headers=func_headers,
        json={
            "itens": [
                {"produto_id": produto["id"], "quantidade": 4},
                {"produto_id": produto["id"], "quantidade": 4},
            ],
            "metodo_pagamento": "dinheiro",
        },
    )
    assert resp.status_code == 201, resp.text
    assert float(resp.json()["valor"]) == 16.0

    lista = client.get("/produtos", headers=func_headers).json()
    assert lista[0]["quantidade"] == 2  # 10 - 8


def test_venda_produto_duplicado_excedendo_estoque_da_409_e_rollback(
    client, admin_headers, func_headers
):
    produto = _criar_produto(client, admin_headers, quantidade=5)
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 0})

    resp = client.post(
        "/transacoes/venda",
        headers=func_headers,
        json={
            "itens": [
                {"produto_id": produto["id"], "quantidade": 3},
                {"produto_id": produto["id"], "quantidade": 3},  # 3+3 > 5
            ],
            "metodo_pagamento": "dinheiro",
        },
    )
    assert resp.status_code == 409
    lista = client.get("/produtos", headers=func_headers).json()
    assert lista[0]["quantidade"] == 5, "rollback nao restaurou o estoque"


# --- Produto inativo -----------------------------------------------------------
def test_venda_de_produto_inativo_da_404(client, admin_headers, func_headers):
    produto = _criar_produto(client, admin_headers)
    client.patch(
        f"/produtos/{produto['id']}", headers=admin_headers, json={"ativo": False}
    )
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 0})
    resp = client.post(
        "/transacoes/venda",
        headers=func_headers,
        json={"itens": [{"produto_id": produto["id"], "quantidade": 1}], "metodo_pagamento": "dinheiro"},
    )
    assert resp.status_code == 404
    # E o produto inativo some da listagem (RF05 lista so ativos).
    assert client.get("/produtos", headers=func_headers).json() == []


# --- RN01: admin NAO movimenta caixa alheio (so encerra) ------------------------
def test_admin_nao_vende_no_turno_de_outro(client, admin_headers, func_headers, admin):
    produto = _criar_produto(client, admin_headers)
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 0})
    resp = client.post(
        "/transacoes/venda",
        headers=admin_headers,
        json={"itens": [{"produto_id": produto["id"], "quantidade": 1}], "metodo_pagamento": "dinheiro"},
    )
    assert resp.status_code == 403, (
        "RN01: movimentar o caixa e exclusivo do dono do turno, mesmo para admin"
    )


def test_admin_nao_faz_sangria_no_turno_de_outro(client, admin_headers, func_headers):
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 100})
    resp = client.post(
        "/transacoes/saida",
        headers=admin_headers,
        json={"valor": 10, "categoria": "sangria"},
    )
    assert resp.status_code == 403


# --- Saida com categoria errada --------------------------------------------------
def test_saida_com_categoria_venda_da_400(client, func_headers):
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 100})
    resp = client.post(
        "/transacoes/saida",
        headers=func_headers,
        json={"valor": 10, "categoria": "venda"},
    )
    assert resp.status_code == 400


# --- /caixa/fechar (rota irma de /turnos/encerrar) -------------------------------
def test_caixa_fechar_encerra_o_turno(client, func_headers):
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 50})
    resp = client.post(
        "/caixa/fechar", headers=func_headers, json={"saldo_final_informado": 50}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "encerrado"
    assert client.get("/caixa/atual", headers=func_headers).json()["aberto"] is False


def test_fechar_caixa_sem_turno_da_404(client, func_headers):
    resp = client.post(
        "/caixa/fechar", headers=func_headers, json={"saldo_final_informado": 0}
    )
    assert resp.status_code == 404


# --- Tokens ----------------------------------------------------------------------
def test_access_token_nao_serve_como_refresh(client, admin):
    login = client.post("/auth/login", data={"username": "admin", "password": "admin123"})
    access = login.json()["access_token"]
    resp = client.post("/auth/refresh", json={"refresh_token": access})
    assert resp.status_code == 401


def test_refresh_token_nao_acessa_rota_protegida(client, admin):
    login = client.post("/auth/login", data={"username": "admin", "password": "admin123"})
    refresh = login.json()["refresh_token"]
    resp = client.get("/produtos", headers={"Authorization": f"Bearer {refresh}"})
    assert resp.status_code == 401


def test_refresh_de_usuario_desativado_da_401(client, admin_headers, funcionario):
    login = client.post("/auth/login", data={"username": "func", "password": "func123"})
    refresh = login.json()["refresh_token"]
    client.patch(
        f"/usuarios/{funcionario.id}", headers=admin_headers, json={"ativo": False}
    )
    resp = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 401


def test_token_de_usuario_desativado_para_de_funcionar(client, admin_headers, funcionario):
    login = client.post("/auth/login", data={"username": "func", "password": "func123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/produtos", headers=headers).status_code == 200

    client.patch(
        f"/usuarios/{funcionario.id}", headers=admin_headers, json={"ativo": False}
    )
    assert client.get("/produtos", headers=headers).status_code == 401


# --- Fuso do dashboard (venda 22h em SP nao cai no dia seguinte) -----------------
def test_resumo_respeita_fuso_do_negocio(client, admin_headers, func_headers, db_session):
    from models.transacao_model import Transacao

    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 0})
    caixa = client.get("/caixa/atual", headers=func_headers).json()

    # 2026-07-12 01:00 UTC == 2026-07-11 22:00 em America/Sao_Paulo.
    db_session.add(
        Transacao(
            caixa_id=caixa["caixa_id"],
            funcionario_id=caixa["funcionario_id"],
            tipo="entrada",
            categoria="venda",
            valor=Decimal("40.00"),
            metodo_pagamento="dinheiro",
            data=datetime(2026, 7, 12, 1, 0, tzinfo=timezone.utc),
        )
    )
    db_session.commit()

    dia_11 = client.get("/dashboard/resumo?dia=2026-07-11", headers=admin_headers).json()
    dia_12 = client.get("/dashboard/resumo?dia=2026-07-12", headers=admin_headers).json()
    assert float(dia_11["faturamento"]) == 40.0, "venda das 22h (SP) sumiu do dia certo"
    assert float(dia_12["faturamento"]) == 0.0, "venda das 22h (SP) vazou para o dia seguinte"


# --- Miudezas de robustez ---------------------------------------------------------
def test_abrir_turno_com_saldo_negativo_da_422(client, func_headers):
    resp = client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": -1})
    assert resp.status_code == 422


def test_login_tolera_espacos_no_nome(client, admin):
    resp = client.post("/auth/login", data={"username": "  admin  ", "password": "admin123"})
    assert resp.status_code == 200


def test_trocar_senha_e_logar_com_a_nova(client, admin_headers, funcionario):
    r = client.patch(
        f"/usuarios/{funcionario.id}", headers=admin_headers, json={"senha": "novasenha1"}
    )
    assert r.status_code == 200
    assert client.post(
        "/auth/login", data={"username": "func", "password": "novasenha1"}
    ).status_code == 200
    assert client.post(
        "/auth/login", data={"username": "func", "password": "func123"}
    ).status_code == 401


def test_venda_zerando_o_estoque(client, admin_headers, func_headers):
    produto = _criar_produto(client, admin_headers, quantidade=4)
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 0})
    resp = client.post(
        "/transacoes/venda",
        headers=func_headers,
        json={"itens": [{"produto_id": produto["id"], "quantidade": 4}], "metodo_pagamento": "debito"},
    )
    assert resp.status_code == 201
    assert client.get("/produtos", headers=func_headers).json()[0]["quantidade"] == 0


# --- Cobertura: endpoints e caminhos sem nenhum teste ----------------------------
def test_turno_ativo_com_e_sem_turno(client, func_headers):
    assert client.get("/turnos/ativo", headers=func_headers).json() is None
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 5})
    corpo = client.get("/turnos/ativo", headers=func_headers).json()
    assert corpo["status"] == "aberto"


def test_listar_usuarios_admin_e_403_para_funcionario(client, admin_headers, func_headers):
    resp = client.get("/usuarios", headers=admin_headers)
    assert resp.status_code == 200
    nomes = [u["nome"] for u in resp.json()]
    assert "admin" in nomes and "func" in nomes
    assert client.get("/usuarios", headers=func_headers).status_code == 403


def test_dashboard_caixa_status(client, admin_headers, func_headers):
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 25})
    resp = client.get("/dashboard/caixa-status", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["aberto"] is True
    assert float(resp.json()["saldo_inicial"]) == 25.0


def test_logout(client, admin_headers):
    assert client.post("/auth/logout", headers=admin_headers).status_code == 200


def test_refresh_com_sucesso_emite_access_novo(client, admin):
    login = client.post(
        "/auth/login", data={"username": "admin", "password": "admin123"}
    ).json()
    resp = client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert resp.status_code == 200
    corpo = resp.json()
    headers = {"Authorization": f"Bearer {corpo['access_token']}"}
    assert client.get("/auth/me", headers=headers).status_code == 200
    # O refresh devolve o MESMO refresh token (nao ha rotacao).
    assert corpo["refresh_token"] == login["refresh_token"]


def test_promover_funcionario_a_admin(client, admin_headers, funcionario):
    r = client.patch(
        f"/usuarios/{funcionario.id}", headers=admin_headers, json={"permissao": "admin"}
    )
    assert r.status_code == 200 and r.json()["permissao"] == "admin"
    # A permissao nova vale no proximo login (o token carrega a permissao atual).
    login = client.post("/auth/login", data={"username": "func", "password": "func123"}).json()
    novo = {"Authorization": f"Bearer {login['access_token']}"}
    assert client.get("/dashboard/resumo", headers=novo).status_code == 200


def test_criar_usuario_nome_duplicado_da_409(client, admin_headers, funcionario):
    resp = client.post(
        "/usuarios", headers=admin_headers, json={"nome": "func", "senha": "abcdef"}
    )
    assert resp.status_code == 409


def test_patch_usuario_inexistente_da_404(client, admin_headers):
    resp = client.patch("/usuarios/9999", headers=admin_headers, json={"ativo": True})
    assert resp.status_code == 404


def test_reposicao_de_estoque_soma_e_audita(client, admin_headers, admin, db_session):
    from models.estoque_model import MovimentoEstoque

    produto = _criar_produto(client, admin_headers, quantidade=3)
    resp = client.post(
        f"/produtos/{produto['id']}/entrada",
        headers=admin_headers,
        json={"quantidade": 7, "motivo": "carga semanal"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["quantidade"] == 10

    mov = (
        db_session.query(MovimentoEstoque)
        .filter_by(produto_id=produto["id"], tipo="entrada")
        .one()
    )
    assert mov.funcionario_id == admin.id  # RNF02: quem repos fica registrado
    assert mov.motivo == "carga semanal"


def test_patch_produto_inexistente_da_404(client, admin_headers):
    resp = client.patch("/produtos/9999", headers=admin_headers, json={"nome": "X"})
    assert resp.status_code == 404


def test_venda_acima_do_teto_do_caixa_da_409(client, admin_headers, func_headers):
    caro = _criar_produto(
        client, admin_headers, nome="Diamante", valor=9_999_999_999.99, quantidade=10
    )
    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 0})
    resp = client.post(
        "/transacoes/venda",
        headers=func_headers,
        json={"itens": [{"produto_id": caro["id"], "quantidade": 2}], "metodo_pagamento": "credito"},
    )
    assert resp.status_code == 409


def test_listar_transacoes_sem_turno_devolve_vazio(client, func_headers):
    assert client.get("/transacoes", headers=func_headers).json() == []


def test_corrida_na_abertura_de_turno_da_409(client, func_headers, monkeypatch):
    """Simula a corrida de RN02: a checagem 'nao ha turno aberto' passa nas duas
    requests, mas o indice unico parcial barra o segundo INSERT."""
    from services import turno_service

    client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 0})
    monkeypatch.setattr(turno_service, "get_turno_aberto", lambda db: None)
    resp = client.post("/turnos/abrir", headers=func_headers, json={"saldo_inicial": 0})
    assert resp.status_code == 409


def test_corrida_na_criacao_de_usuario_da_409(client, admin_headers, funcionario, monkeypatch):
    """Simula a corrida do POST /usuarios: a checagem de nome passa nas duas
    requests e a segunda estoura o UNIQUE do banco."""
    from sqlalchemy import false
    from sqlalchemy import select as sa_select

    import routes.usuarios as modulo
    from models.usuario_model import Usuario

    monkeypatch.setattr(modulo, "select", lambda *a: sa_select(Usuario).where(false()))
    resp = client.post(
        "/usuarios", headers=admin_headers, json={"nome": "func", "senha": "abcdef"}
    )
    assert resp.status_code == 409


def test_corrida_no_rename_de_usuario_da_409(client, admin_headers, funcionario, monkeypatch):
    """Mesma corrida, via PATCH: renomear para um nome criado no meio do caminho."""
    from sqlalchemy import false
    from sqlalchemy import select as sa_select

    import routes.usuarios as modulo
    from models.usuario_model import Usuario

    monkeypatch.setattr(modulo, "select", lambda *a: sa_select(Usuario).where(false()))
    resp = client.patch(
        f"/usuarios/{funcionario.id}", headers=admin_headers, json={"nome": "admin"}
    )
    assert resp.status_code == 409


def test_get_db_fornece_e_fecha_sessao():
    """Cobre a dependencia real get_db (nos testes de rota ela e substituida)."""
    from sqlalchemy import text

    from database import get_db

    gen = get_db()
    db = next(gen)
    assert db.execute(text("SELECT 1")).scalar() == 1
    gen.close()


def test_lifespan_cria_tabelas_no_startup():
    """Sobe a app com lifespan (create_all roda no engine default, que nos
    testes aponta para SQLite em memoria — ver conftest)."""
    from fastapi.testclient import TestClient

    from main import app

    with TestClient(app):
        pass

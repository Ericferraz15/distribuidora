"""Testes de corrida (concorrencia real) — exigem Postgres.

SQLite em memoria nao reproduz corridas (uma conexao compartilhada), entao
estes testes so rodam quando TEST_PG_URL aponta para um banco DESCARTAVEL:

    docker exec distribuidora-db psql -U postgres -c "CREATE DATABASE distribuidora_corrida"
    TEST_PG_URL="postgresql+psycopg://postgres:postgres@localhost:5432/distribuidora_corrida" pytest tests/test_concorrencia.py

Sem a variavel, os testes sao pulados (skip) — a suite normal nao depende deles.
"""

import os
import threading
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PG_URL = os.getenv("TEST_PG_URL")
pytestmark = pytest.mark.skipif(
    not PG_URL, reason="corrida exige Postgres: defina TEST_PG_URL (banco descartavel)"
)


@pytest.fixture
def pg_sessions():
    import models  # noqa: F401  (registra tabelas)
    from database import Base

    engine = create_engine(PG_URL)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    Sess = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    yield Sess
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def _setup_turno_com_caixa(Sess, saldo_inicial):
    from models.caixa_model import Caixa
    from models.turno_model import Turno
    from models.usuario_model import Usuario

    db = Sess()
    u = Usuario(nome="corredora", senha_hash="x", permissao="funcionario")
    db.add(u)
    db.flush()
    t = Turno(funcionario_id=u.id, status="aberto")
    db.add(t)
    db.flush()
    db.add(Caixa(turno_id=t.id, saldo_inicial=saldo_inicial))
    db.commit()
    uid, tid = u.id, t.id
    db.close()
    return uid, tid


def test_sangrias_paralelas_nao_negativam_o_caixa(pg_sessions):
    """Regressao do bug #6: 10 sangrias de 30 num caixa de 100 -> no maximo 3
    passam; o caixa NUNCA fica negativo (linha do caixa e trancada, FOR UPDATE)."""
    from models.usuario_model import Usuario
    from schemas.transacao import SaidaRequest
    from services import transacao_service

    uid, _ = _setup_turno_com_caixa(pg_sessions, Decimal(100))
    resultados: list[int] = []
    trava = threading.Lock()

    def sangra():
        db = pg_sessions()
        try:
            usuario = db.get(Usuario, uid)
            transacao_service.registrar_saida(
                db, usuario, SaidaRequest(valor=Decimal(30), categoria="sangria")
            )
            codigo = 201
        except HTTPException as e:
            codigo = e.status_code
        finally:
            db.close()
        with trava:
            resultados.append(codigo)

    threads = [threading.Thread(target=sangra) for _ in range(10)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()

    aceitas = resultados.count(201)
    assert aceitas <= 3, f"{aceitas} sangrias de 30 aceitas com caixa de 100"

    db = pg_sessions()
    try:
        from services import caixa_service
        from services.turno_service import get_turno_aberto

        turno = get_turno_aberto(db)
        saldo = caixa_service.saldo_total(db, turno.caixa)
        assert saldo >= 0, f"caixa negativo: {saldo}"
    finally:
        db.close()


def test_vendas_paralelas_nao_negativam_o_estoque(pg_sessions):
    """20 vendas simultaneas de 3un com estoque 30: exatamente 10 passam."""
    from models.estoque_model import Produto
    from models.usuario_model import Usuario
    from schemas.transacao import ItemVendaInput, VendaRequest
    from services import transacao_service

    uid, _ = _setup_turno_com_caixa(pg_sessions, Decimal(0))
    db = pg_sessions()
    p = Produto(nome="ConcorridaLata", valor=Decimal(1), quantidade=30, fornecedor="x")
    db.add(p)
    db.commit()
    pid = p.id
    db.close()

    resultados: list[int] = []
    trava = threading.Lock()

    def vende():
        db = pg_sessions()
        try:
            usuario = db.get(Usuario, uid)
            transacao_service.registrar_venda(
                db,
                usuario,
                VendaRequest(
                    itens=[ItemVendaInput(produto_id=pid, quantidade=3)],
                    metodo_pagamento="dinheiro",
                ),
            )
            codigo = 201
        except HTTPException as e:
            codigo = e.status_code
        finally:
            db.close()
        with trava:
            resultados.append(codigo)

    threads = [threading.Thread(target=vende) for _ in range(20)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()

    assert resultados.count(201) == 10, resultados

    db = pg_sessions()
    try:
        from models.estoque_model import Produto as P

        assert db.get(P, pid).quantidade == 0
    finally:
        db.close()

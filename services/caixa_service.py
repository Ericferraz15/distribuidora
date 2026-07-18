from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.caixa_model import Caixa
from models.transacao_model import Transacao
from schemas.caixa import CaixaStatusOut
from services.turno_service import get_turno_aberto


def _soma(db: Session, caixa_id: int, tipo: str, metodo: str | None = None) -> Decimal:
    stmt = select(func.coalesce(func.sum(Transacao.valor), 0)).where(
        Transacao.caixa_id == caixa_id, Transacao.tipo == tipo
    )
    if metodo is not None:
        stmt = stmt.where(Transacao.metodo_pagamento == metodo)
    bruto = db.scalar(stmt)
    # func.sum pode voltar float (SQLite) ou Decimal (Postgres); normaliza.
    return Decimal(str(bruto))


def saldo_total(db: Session, caixa: Caixa) -> Decimal:
    """Saldo corrente do caixa: inicial + todas entradas - todas saidas."""
    return (
        caixa.saldo_inicial
        + _soma(db, caixa.id, "entrada")
        - _soma(db, caixa.id, "saida")
    )


def dinheiro_em_caixa(db: Session, caixa: Caixa) -> Decimal:
    """Dinheiro fisico na gaveta: troco inicial + entradas em dinheiro
    - saidas em dinheiro. Vendas no cartao nao colocam nota na gaveta."""
    return (
        caixa.saldo_inicial
        + _soma(db, caixa.id, "entrada", metodo="dinheiro")
        - _soma(db, caixa.id, "saida", metodo="dinheiro")
    )


def status_caixa_atual(db: Session) -> CaixaStatusOut:
    """RF03: status/saldo do caixa do turno ativo."""
    turno = get_turno_aberto(db)
    if turno is None:
        return CaixaStatusOut(aberto=False)

    caixa = turno.caixa
    entradas = _soma(db, caixa.id, "entrada")
    saidas = _soma(db, caixa.id, "saida")
    return CaixaStatusOut(
        aberto=True,
        turno_id=turno.id,
        caixa_id=caixa.id,
        funcionario_id=turno.funcionario_id,
        funcionario_nome=turno.funcionario.nome,
        saldo_inicial=caixa.saldo_inicial,
        total_entradas=entradas,
        total_saidas=saidas,
        saldo_atual=caixa.saldo_inicial + entradas - saidas,
        abertura=caixa.abertura,
    )

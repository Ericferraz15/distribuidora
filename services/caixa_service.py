from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.transacao_model import Transacao
from schemas.caixa import CaixaStatusOut
from services.turno_service import get_turno_aberto


def _soma(db: Session, caixa_id: int, tipo: str) -> Decimal:
    bruto = db.scalar(
        select(func.coalesce(func.sum(Transacao.valor), 0)).where(
            Transacao.caixa_id == caixa_id, Transacao.tipo == tipo
        )
    )
    # func.sum pode voltar float (SQLite) ou Decimal (Postgres); normaliza.
    return Decimal(str(bruto))


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
        saldo_inicial=caixa.saldo_inicial,
        total_entradas=entradas,
        total_saidas=saidas,
        saldo_atual=caixa.saldo_inicial + entradas - saidas,
        abertura=caixa.abertura,
    )

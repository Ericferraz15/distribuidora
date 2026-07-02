from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.estoque_model import Produto
from models.transacao_model import ItemVenda, Transacao
from schemas.caixa import CaixaStatusOut
from schemas.dashboard import ItemMaisVendido, ResumoDia
from services.caixa_service import status_caixa_atual


def _intervalo_dia(dia: date) -> tuple[datetime, datetime]:
    inicio = datetime.combine(dia, time.min, tzinfo=timezone.utc)
    return inicio, inicio + timedelta(days=1)


def resumo_dia(db: Session, dia: date) -> ResumoDia:
    """RF07: faturamento e volume do dia."""
    inicio, fim = _intervalo_dia(dia)
    no_dia = (Transacao.data >= inicio, Transacao.data < fim)

    faturamento = db.scalar(
        select(func.coalesce(func.sum(Transacao.valor), 0)).where(
            Transacao.tipo == "entrada", Transacao.categoria == "venda", *no_dia
        )
    )
    num_vendas = db.scalar(
        select(func.count()).select_from(Transacao).where(
            Transacao.categoria == "venda", *no_dia
        )
    )
    total_saidas = db.scalar(
        select(func.coalesce(func.sum(Transacao.valor), 0)).where(
            Transacao.tipo == "saida", *no_dia
        )
    )
    num_transacoes = db.scalar(
        select(func.count()).select_from(Transacao).where(*no_dia)
    )
    return ResumoDia(
        data=dia,
        faturamento=Decimal(str(faturamento)),
        num_vendas=int(num_vendas),
        total_saidas=Decimal(str(total_saidas)),
        num_transacoes=int(num_transacoes),
    )


def mais_vendidos(db: Session, limite: int = 10) -> list[ItemMaisVendido]:
    """RF07: itens mais vendidos por quantidade."""
    stmt = (
        select(
            Produto.id,
            Produto.nome,
            func.coalesce(func.sum(ItemVenda.quantidade), 0).label("qtd"),
            func.coalesce(
                func.sum(ItemVenda.quantidade * ItemVenda.valor_unitario), 0
            ).label("receita"),
        )
        .join(ItemVenda, ItemVenda.produto_id == Produto.id)
        .group_by(Produto.id, Produto.nome)
        .order_by(func.sum(ItemVenda.quantidade).desc())
        .limit(limite)
    )
    return [
        ItemMaisVendido(
            produto_id=pid,
            nome=nome,
            quantidade_total=int(qtd),
            receita_total=Decimal(str(receita)),
        )
        for pid, nome, qtd, receita in db.execute(stmt).all()
    ]


def caixa_status(db: Session) -> CaixaStatusOut:
    """RF07: status do caixa atual."""
    return status_caixa_atual(db)

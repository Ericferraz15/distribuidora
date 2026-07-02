from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from schemas.caixa import CaixaStatusOut


class ResumoDia(BaseModel):
    """Metricas globais do dia (RF07)."""

    data: date
    faturamento: Decimal
    num_vendas: int
    total_saidas: Decimal
    num_transacoes: int


class ItemMaisVendido(BaseModel):
    produto_id: int
    nome: str
    quantidade_total: int
    receita_total: Decimal


# Reaproveita o status do caixa ja definido em schemas.caixa.
__all__ = ["ResumoDia", "ItemMaisVendido", "CaixaStatusOut"]

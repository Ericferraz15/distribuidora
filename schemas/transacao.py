from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from schemas.caixa import MetodoPagamento


class TipoTransacao(str, Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"


class CategoriaTransacao(str, Enum):
    VENDA = "venda"
    SANGRIA = "sangria"
    DESPESA = "despesa"
    SUPRIMENTO = "suprimento"


class ItemVendaInput(BaseModel):
    produto_id: int
    quantidade: int = Field(gt=0)


class VendaRequest(BaseModel):
    itens: list[ItemVendaInput] = Field(min_length=1)
    metodo_pagamento: MetodoPagamento
    descricao: str | None = None


class SaidaRequest(BaseModel):
    valor: Decimal = Field(gt=0)
    categoria: CategoriaTransacao = CategoriaTransacao.SANGRIA
    metodo_pagamento: MetodoPagamento = MetodoPagamento.DINHEIRO
    descricao: str | None = None


class ItemVendaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    produto_id: int
    quantidade: int
    valor_unitario: Decimal


class TransacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    caixa_id: int
    funcionario_id: int
    tipo: TipoTransacao
    categoria: CategoriaTransacao
    valor: Decimal
    metodo_pagamento: MetodoPagamento
    data: datetime
    descricao: str | None = None
    itens: list[ItemVendaOut] = []

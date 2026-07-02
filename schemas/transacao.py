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
    descricao: str | None = Field(default=None, max_length=255)


class SaidaRequest(BaseModel):
    # max_digits=12 espelha a coluna Numeric(12, 2): valor absurdo vira 422
    # do Pydantic em vez de erro de banco (500).
    valor: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    categoria: CategoriaTransacao = CategoriaTransacao.SANGRIA
    metodo_pagamento: MetodoPagamento = MetodoPagamento.DINHEIRO
    descricao: str | None = Field(default=None, max_length=255)


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

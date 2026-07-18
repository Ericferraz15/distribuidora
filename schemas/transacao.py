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


class ItemVendaInput(BaseModel):
    produto_id: int
    # le espelha o teto de estoque por produto (schemas.estoque.LIMITE_ESTOQUE).
    quantidade: int = Field(gt=0, le=1_000_000)


class VendaRequest(BaseModel):
    # max_length: teto sano de linhas por venda; barra payloads gigantes que
    # fariam milhares de SELECTs/INSERTs numa unica requisicao.
    itens: list[ItemVendaInput] = Field(min_length=1, max_length=100)
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
    # str (nao enum): escrita e estrita, mas leitura tolera categorias legadas
    # ja gravadas no banco (ex.: "suprimento", removida em 2026-07) — apagar o
    # valor do enum aqui quebraria a serializacao do historico (RNF02).
    categoria: str
    valor: Decimal
    metodo_pagamento: MetodoPagamento
    data: datetime
    descricao: str | None = None
    itens: list[ItemVendaOut] = []

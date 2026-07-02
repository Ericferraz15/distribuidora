from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# --- Modelos de dominio (usados em testes unitarios) -------------------------
class Produto(BaseModel):
    id: int
    nome: str
    valor: Decimal
    quantidade: int = 0
    fornecedor: str
    descricao: str | None = None


class MovimentoEstoque(BaseModel):
    produto_id: int
    quantidade: int
    data: datetime = Field(default_factory=datetime.now)


class Estoque(BaseModel):
    id: int
    produtos: list[Produto] = []
    entradas: list[MovimentoEstoque] = []
    saidas: list[MovimentoEstoque] = []

    @property
    def saldo_estoque(self) -> Decimal:
        return sum(p.valor * p.quantidade for p in self.produtos)


# --- DTOs de API -------------------------------------------------------------
class ProdutoCreate(BaseModel):
    nome: str
    valor: Decimal = Field(ge=0)
    quantidade: int = Field(default=0, ge=0)
    fornecedor: str
    descricao: str | None = None


class ProdutoUpdate(BaseModel):
    nome: str | None = None
    valor: Decimal | None = Field(default=None, ge=0)
    fornecedor: str | None = None
    descricao: str | None = None
    ativo: bool | None = None


class ProdutoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    valor: Decimal
    quantidade: int
    fornecedor: str
    descricao: str | None = None
    ativo: bool = True


class EntradaEstoqueRequest(BaseModel):
    quantidade: int = Field(gt=0)
    motivo: str | None = None

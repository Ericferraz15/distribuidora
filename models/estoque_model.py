from datetime import datetime
from pydantic import BaseModel, Field
from decimal import Decimal


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

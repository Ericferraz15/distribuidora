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
        # start=Decimal: sum() de lista vazia devolveria int 0, nao Decimal.
        return sum(
            (produto.valor * produto.quantidade for produto in self.produtos),
            Decimal(0),
        )


# --- DTOs de API -------------------------------------------------------------
# max_length espelha as colunas (String(120)/String(255)) e max_digits=12 a
# Numeric(12, 2): melhor um 422 claro do Pydantic do que um erro de banco (500).

# Teto de unidades por produto: barra erro de digitacao e estouro do int32 do
# banco (que viraria 500). Compartilhado com services/estoque_service.py.
LIMITE_ESTOQUE = 1_000_000


class ProdutoCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    valor: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    quantidade: int = Field(default=0, ge=0, le=LIMITE_ESTOQUE)
    fornecedor: str = Field(min_length=1, max_length=120)
    descricao: str | None = Field(default=None, max_length=255)


class ProdutoUpdate(BaseModel):
    # Sem `quantidade` de proposito: estoque so muda por movimento auditado
    # (venda ou POST /produtos/{id}/entrada), nunca por edicao direta (RNF02).
    nome: str | None = Field(default=None, min_length=1, max_length=120)
    valor: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    fornecedor: str | None = Field(default=None, min_length=1, max_length=120)
    descricao: str | None = Field(default=None, max_length=255)
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
    quantidade: int = Field(gt=0, le=LIMITE_ESTOQUE)
    motivo: str | None = Field(default=None, max_length=255)

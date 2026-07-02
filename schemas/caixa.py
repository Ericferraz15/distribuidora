from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from schemas.usuario import Usuario


class MetodoPagamento(str, Enum):
    DINHEIRO = "dinheiro"
    DEBITO = "debito"
    CREDITO = "credito"


# --- Modelos de dominio (usados em testes unitarios) -------------------------
class Entrada(BaseModel):
    id: int
    valor: Decimal
    metodo: MetodoPagamento


class Saida(BaseModel):
    id: int
    valor: Decimal
    metodo: MetodoPagamento


class Caixa(BaseModel):
    id: int
    abertura: datetime = Field(default_factory=datetime.now)
    fechamento: datetime | None = None
    entradas: list[Entrada] = []
    saidas: list[Saida] = []
    responsavel: Usuario

    @property
    def saldo(self) -> Decimal:
        return sum(e.valor for e in self.entradas) - sum(s.valor for s in self.saidas)


class FechamentoMensal(BaseModel):
    id: int
    mes: int
    ano: int
    caixas: list[Caixa]

    @property
    def saldo_total(self) -> Decimal:
        return sum(c.saldo for c in self.caixas)


# --- DTOs de API -------------------------------------------------------------
class CaixaStatusOut(BaseModel):
    """Status do caixa do turno ativo (RF03)."""

    aberto: bool
    turno_id: int | None = None
    caixa_id: int | None = None
    funcionario_id: int | None = None
    # Nome junto do id para o front nao precisar de outra chamada.
    funcionario_nome: str | None = None
    saldo_inicial: Decimal | None = None
    total_entradas: Decimal | None = None
    total_saidas: Decimal | None = None
    saldo_atual: Decimal | None = None
    abertura: datetime | None = None

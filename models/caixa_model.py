from enum import Enum
from decimal import Decimal
from pydantic import BaseModel, Field
from models.usuario_model import Usuario
from datetime import datetime


class MetodoPagamento(str, Enum):
    DINHEIRO = "dinheiro"
    DEBITO = "debito"
    CREDITO = "credito"


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

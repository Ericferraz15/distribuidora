from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class StatusTurno(str, Enum):
    ABERTO = "aberto"
    ENCERRADO = "encerrado"


# max_digits=12 espelha a coluna Numeric(12, 2) do caixa.
class AbrirTurnoRequest(BaseModel):
    saldo_inicial: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class EncerrarTurnoRequest(BaseModel):
    saldo_final_informado: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class TurnoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    funcionario_id: int
    data_abertura: datetime
    data_fechamento: datetime | None = None
    status: StatusTurno

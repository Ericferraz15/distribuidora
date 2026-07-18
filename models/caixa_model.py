from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.transacao_model import Transacao
    from models.turno_model import Turno


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class Caixa(Base):
    __tablename__ = "caixas"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 1:1 com Turno (RF03): o caixa e o registro financeiro do turno.
    turno_id: Mapped[int] = mapped_column(ForeignKey("turnos.id"), unique=True, index=True)
    saldo_inicial: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    saldo_final_informado: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    abertura: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    fechamento: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    turno: Mapped["Turno"] = relationship(back_populates="caixa")
    transacoes: Mapped[list["Transacao"]] = relationship(back_populates="caixa")

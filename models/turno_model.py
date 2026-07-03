from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.caixa_model import Caixa
    from models.usuario_model import Usuario


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class Turno(Base):
    __tablename__ = "turnos"

    id: Mapped[int] = mapped_column(primary_key=True)
    funcionario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    data_abertura: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    data_fechamento: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # "aberto" | "encerrado" (ver schemas.turno.StatusTurno).
    status: Mapped[str] = mapped_column(String(20), default="aberto", index=True)

    funcionario: Mapped["Usuario"] = relationship(back_populates="turnos")
    caixa: Mapped["Caixa"] = relationship(back_populates="turno", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        # RN02: no maximo um turno "aberto" no sistema inteiro. Um indice unico
        # parcial sobre status garante isso no nivel do banco (Postgres e SQLite).
        Index(
            "uq_turno_unico_aberto",
            "status",
            unique=True,
            postgresql_where=text("status = 'aberto'"),
            sqlite_where=text("status = 'aberto'"),
        ),
    )

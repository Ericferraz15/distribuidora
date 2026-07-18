from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.turno_model import Turno


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    # Perfil: "admin" | "funcionario" (ver schemas.usuario.PermissaoUsuario).
    permissao: Mapped[str] = mapped_column(String(20), default="funcionario")
    numero_telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    turnos: Mapped[list["Turno"]] = relationship(back_populates="funcionario")

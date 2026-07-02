from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.usuario_model import Usuario


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), index=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    quantidade: Mapped[int] = mapped_column(default=0)
    fornecedor: Mapped[str] = mapped_column(String(120))
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class MovimentoEstoque(Base):
    __tablename__ = "movimentos_estoque"

    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), index=True)
    quantidade: Mapped[int] = mapped_column()  # sempre positivo; 'tipo' define o sentido
    tipo: Mapped[str] = mapped_column(String(10))  # "entrada" | "saida"
    data: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    # RNF02: quem causou o movimento (funcionario do turno / admin).
    funcionario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"), index=True
    )
    # Preenchido quando o movimento vem de uma venda.
    transacao_id: Mapped[int | None] = mapped_column(
        ForeignKey("transacoes.id"), nullable=True
    )
    motivo: Mapped[str | None] = mapped_column(String(255), nullable=True)

    produto: Mapped["Produto"] = relationship()
    funcionario: Mapped["Usuario"] = relationship()

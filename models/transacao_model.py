from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.caixa_model import Caixa
    from models.estoque_model import Produto
    from models.usuario_model import Usuario


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class Transacao(Base):
    __tablename__ = "transacoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    caixa_id: Mapped[int] = mapped_column(ForeignKey("caixas.id"), index=True)
    # RNF02: toda transacao grava o funcionario do turno ativo (auditoria).
    funcionario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"), index=True
    )
    tipo: Mapped[str] = mapped_column(String(10))  # "entrada" | "saida"
    # "venda" | "sangria" | "despesa" (linhas antigas podem ter "suprimento",
    # categoria removida em 2026-07; a leitura tolera — ver schemas.transacao)
    categoria: Mapped[str] = mapped_column(String(20))
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    metodo_pagamento: Mapped[str] = mapped_column(String(20))
    data: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_agora, index=True
    )
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)

    caixa: Mapped["Caixa"] = relationship(back_populates="transacoes")
    funcionario: Mapped["Usuario"] = relationship()
    itens: Mapped[list["ItemVenda"]] = relationship(
        back_populates="transacao", cascade="all, delete-orphan"
    )


class ItemVenda(Base):
    __tablename__ = "itens_venda"

    id: Mapped[int] = mapped_column(primary_key=True)
    transacao_id: Mapped[int] = mapped_column(
        ForeignKey("transacoes.id"), index=True
    )
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), index=True)
    quantidade: Mapped[int] = mapped_column()
    valor_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    transacao: Mapped["Transacao"] = relationship(back_populates="itens")
    produto: Mapped["Produto"] = relationship()

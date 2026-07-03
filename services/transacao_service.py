from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.caixa_model import Caixa
from models.estoque_model import MovimentoEstoque, Produto
from models.transacao_model import ItemVenda, Transacao
from models.usuario_model import Usuario
from schemas.transacao import CategoriaTransacao, SaidaRequest, VendaRequest
from services.turno_service import get_turno_aberto


def _turno_do_usuario(db: Session, current_user: Usuario):
    """Garante turno aberto E que o usuario atual e o dono (RN01)."""
    turno = get_turno_aberto(db)
    if turno is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nenhum turno aberto. Abra um turno antes de movimentar o caixa.",
        )
    if turno.funcionario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o dono do turno ativo pode movimentar o caixa (RN01).",
        )
    return turno


def registrar_venda(db: Session, current_user: Usuario, req: VendaRequest) -> Transacao:
    """RF04/RF06/RNF02: venda que baixa estoque e audita o funcionario.

    Tudo em uma unica transacao de banco (atomica).
    """
    turno = _turno_do_usuario(db, current_user)
    try:
        transacao = Transacao(
            caixa_id=turno.caixa.id,
            funcionario_id=turno.funcionario_id,  # RNF02
            tipo="entrada",
            categoria="venda",
            valor=Decimal(0),
            metodo_pagamento=req.metodo_pagamento.value,
            descricao=req.descricao,
        )
        db.add(transacao)
        db.flush()  # obtem transacao.id

        total = Decimal(0)
        for item in req.itens:
            # with_for_update = SELECT ... FOR UPDATE: tranca a linha do
            # produto ate o commit. Sem isso, duas vendas simultaneas leriam
            # o mesmo saldo e poderiam vender alem do estoque (race condition).
            # No SQLite dos testes e um no-op inofensivo.
            produto = db.get(Produto, item.produto_id, with_for_update=True)
            if produto is None or not produto.ativo:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Produto {item.produto_id} nao encontrado.",
                )
            if produto.quantidade < item.quantidade:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Estoque insuficiente para '{produto.nome}' "
                        f"(disponivel: {produto.quantidade})."
                    ),
                )

            produto.quantidade -= item.quantidade  # RF06: baixa de estoque
            db.add(
                ItemVenda(
                    transacao_id=transacao.id,
                    produto_id=produto.id,
                    quantidade=item.quantidade,
                    valor_unitario=produto.valor,
                )
            )
            db.add(
                MovimentoEstoque(
                    produto_id=produto.id,
                    quantidade=item.quantidade,
                    tipo="saida",
                    funcionario_id=turno.funcionario_id,  # RNF02
                    transacao_id=transacao.id,
                    motivo="venda",
                )
            )
            total += produto.valor * item.quantidade

        # Teto da coluna Numeric(12, 2): precos x quantidades extremos podem
        # passar de 10 bilhoes e derrubariam o INSERT no banco (500).
        if total > Decimal("9999999999.99"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Valor total da venda excede o limite suportado pelo caixa.",
            )

        transacao.valor = total
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(transacao)
    return transacao


def registrar_saida(
    db: Session, current_user: Usuario, req: SaidaRequest
) -> Transacao:
    """RF04: registra saida do caixa (sangria ou despesa).

    O caixa nunca fica negativo:
      - saida em dinheiro e limitada ao dinheiro fisico na gaveta;
      - saida em cartao e limitada ao saldo total do caixa.
    """
    from services import caixa_service  # import tardio: evita ciclo de modulo

    turno = _turno_do_usuario(db, current_user)
    if req.categoria == CategoriaTransacao.VENDA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use /transacoes/venda para registrar vendas.",
        )

    # Tranca a linha do caixa (SELECT ... FOR UPDATE): serializa saidas
    # concorrentes do mesmo caixa. Sem isso, duas sangrias simultaneas leem o
    # mesmo saldo, ambas passam na checagem e o caixa fica negativo (corrida
    # reproduzida em teste de carga; ver tests/test_concorrencia.py).
    caixa = db.get(Caixa, turno.caixa.id, with_for_update=True)

    total = caixa_service.saldo_total(db, caixa)
    if req.valor > total:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Saldo insuficiente no caixa (disponivel: {total:.2f}).",
        )
    if req.metodo_pagamento.value == "dinheiro":
        dinheiro = caixa_service.dinheiro_em_caixa(db, caixa)
        if req.valor > dinheiro:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Dinheiro insuficiente na gaveta (disponivel: {dinheiro:.2f}); "
                    "vendas no cartao nao viram dinheiro fisico."
                ),
            )

    transacao = Transacao(
        caixa_id=caixa.id,
        funcionario_id=turno.funcionario_id,  # RNF02
        tipo="saida",
        categoria=req.categoria.value,
        valor=req.valor,
        metodo_pagamento=req.metodo_pagamento.value,
        descricao=req.descricao,
    )
    db.add(transacao)
    db.commit()
    db.refresh(transacao)
    return transacao


def listar_transacoes_caixa_atual(db: Session, current_user: Usuario) -> list[Transacao]:
    turno = get_turno_aberto(db)
    if turno is None:
        return []
    return list(
        db.scalars(
            select(Transacao)
            .where(Transacao.caixa_id == turno.caixa.id)
            .order_by(Transacao.data.desc())
        )
    )

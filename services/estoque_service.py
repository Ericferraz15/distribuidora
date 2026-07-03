from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.estoque_model import MovimentoEstoque, Produto
from schemas.estoque import LIMITE_ESTOQUE, ProdutoCreate, ProdutoUpdate


def listar_produtos(db: Session) -> list[Produto]:
    """RF05: lista produtos ativos com quantidade em tempo real."""
    return list(
        db.scalars(select(Produto).where(Produto.ativo.is_(True)).order_by(Produto.nome))
    )


def obter_produto(
    db: Session, produto_id: int, para_atualizar_quantidade: bool = False
) -> Produto:
    # para_atualizar_quantidade=True tranca a linha (FOR UPDATE): quem mexe em
    # `quantidade` precisa serializar com as vendas, senao uma reposicao
    # simultanea a uma venda sobrescreve a baixa (lost update).
    produto = db.get(Produto, produto_id, with_for_update=para_atualizar_quantidade)
    if produto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Produto {produto_id} nao encontrado.",
        )
    return produto


def criar_produto(db: Session, req: ProdutoCreate) -> Produto:
    produto = Produto(
        nome=req.nome,
        valor=req.valor,
        quantidade=req.quantidade,
        fornecedor=req.fornecedor,
        descricao=req.descricao,
    )
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


def atualizar_produto(db: Session, produto_id: int, req: ProdutoUpdate) -> Produto:
    produto = obter_produto(db, produto_id)
    for campo, valor in req.model_dump(exclude_unset=True).items():
        setattr(produto, campo, valor)
    db.commit()
    db.refresh(produto)
    return produto


def registrar_entrada_estoque(
    db: Session, produto_id: int, quantidade: int, funcionario_id: int, motivo: str | None
) -> Produto:
    """RF06 (reposicao): soma ao estoque e audita quem fez (RNF02)."""
    produto = obter_produto(db, produto_id, para_atualizar_quantidade=True)
    if produto.quantidade + quantidade > LIMITE_ESTOQUE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Estoque maximo por produto e {LIMITE_ESTOQUE} unidades "
                f"(atual: {produto.quantidade})."
            ),
        )
    produto.quantidade += quantidade
    db.add(
        MovimentoEstoque(
            produto_id=produto.id,
            quantidade=quantidade,
            tipo="entrada",
            funcionario_id=funcionario_id,
            motivo=motivo or "reposicao",
        )
    )
    db.commit()
    db.refresh(produto)
    return produto

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from models.usuario_model import Usuario
from schemas.estoque import (
    EntradaEstoqueRequest,
    ProdutoCreate,
    ProdutoOut,
    ProdutoUpdate,
)
from security.dependencies import get_current_user, require_admin
from services import estoque_service

router = APIRouter(prefix="/produtos", tags=["estoque"])


@router.get("", response_model=list[ProdutoOut])
def listar_produtos(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """RF05: qualquer usuario autenticado consulta o estoque."""
    return estoque_service.listar_produtos(db)


@router.post("", response_model=ProdutoOut, status_code=status.HTTP_201_CREATED)
def criar_produto(
    body: ProdutoCreate,
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return estoque_service.criar_produto(db, body)


@router.patch("/{produto_id}", response_model=ProdutoOut)
def atualizar_produto(
    produto_id: int,
    body: ProdutoUpdate,
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return estoque_service.atualizar_produto(db, produto_id, body)


@router.post("/{produto_id}/entrada", response_model=ProdutoOut)
def entrada_estoque(
    produto_id: int,
    body: EntradaEstoqueRequest,
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Reposicao de estoque (admin); audita quem repos (RNF02)."""
    return estoque_service.registrar_entrada_estoque(
        db, produto_id, body.quantidade, admin.id, body.motivo
    )

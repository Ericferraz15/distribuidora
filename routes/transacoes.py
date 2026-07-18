from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from models.usuario_model import Usuario
from schemas.transacao import SaidaRequest, TransacaoOut, VendaRequest
from security.dependencies import get_current_user
from services import transacao_service

router = APIRouter(prefix="/transacoes", tags=["transacoes"])


@router.post("/venda", response_model=TransacaoOut, status_code=status.HTTP_201_CREATED)
def registrar_venda(
    body: VendaRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """RF04/RF06: registra venda (entrada) e baixa o estoque."""
    return transacao_service.registrar_venda(db, usuario, body)


@router.post("/saida", response_model=TransacaoOut, status_code=status.HTTP_201_CREATED)
def registrar_saida(
    body: SaidaRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """RF04: registra saida do caixa (sangria ou despesa)."""
    return transacao_service.registrar_saida(db, usuario, body)


@router.get("", response_model=list[TransacaoOut])
def listar_transacoes(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return transacao_service.listar_transacoes_caixa_atual(db, usuario)

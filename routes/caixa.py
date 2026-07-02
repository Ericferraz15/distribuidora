from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.usuario_model import Usuario
from schemas.caixa import CaixaStatusOut
from schemas.turno import EncerrarTurnoRequest, TurnoOut
from security.dependencies import get_current_user
from services import caixa_service, turno_service

router = APIRouter(prefix="/caixa", tags=["caixa"])


@router.get("/atual", response_model=CaixaStatusOut)
def caixa_atual(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """RF03: status e saldo do caixa do turno ativo."""
    return caixa_service.status_caixa_atual(db)


@router.post("/fechar", response_model=TurnoOut)
def fechar_caixa(
    body: EncerrarTurnoRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """RF03: conferencia/fechamento do caixa (encerra o turno ativo)."""
    return turno_service.encerrar_turno(db, usuario.id, body.saldo_final_informado)

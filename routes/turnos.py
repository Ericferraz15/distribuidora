from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from models.usuario_model import Usuario
from schemas.turno import AbrirTurnoRequest, EncerrarTurnoRequest, TurnoOut
from security.dependencies import get_current_user
from services import turno_service

router = APIRouter(prefix="/turnos", tags=["turnos"])


@router.post("/abrir", response_model=TurnoOut, status_code=status.HTTP_201_CREATED)
def abrir_turno(
    body: AbrirTurnoRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return turno_service.abrir_turno(db, usuario.id, body.saldo_inicial)


@router.post("/encerrar", response_model=TurnoOut)
def encerrar_turno(
    body: EncerrarTurnoRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return turno_service.encerrar_turno(db, usuario.id, body.saldo_final_informado)


@router.get("/ativo", response_model=TurnoOut | None)
def turno_ativo(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return turno_service.get_turno_aberto(db)

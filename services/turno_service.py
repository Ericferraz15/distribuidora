from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.caixa_model import Caixa
from models.turno_model import Turno


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def get_turno_aberto(db: Session) -> Turno | None:
    """Retorna o unico turno ABERTO do sistema, ou None."""
    return db.scalars(select(Turno).where(Turno.status == "aberto")).first()


def abrir_turno(db: Session, funcionario_id: int, saldo_inicial: Decimal) -> Turno:
    """RF02/RF03: abre turno + caixa com saldo inicial.

    RN02: bloqueia se ja houver turno aberto (checagem + indice unico parcial).
    """
    if get_turno_aberto(db) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ja existe um turno aberto no sistema. Encerre-o antes (RN02).",
        )

    turno = Turno(funcionario_id=funcionario_id, status="aberto")
    db.add(turno)
    try:
        db.flush()  # garante turno.id para o caixa
        db.add(Caixa(turno_id=turno.id, saldo_inicial=saldo_inicial))
        db.commit()
    except IntegrityError:
        # Corrida: o indice unico parcial barrou um segundo turno aberto.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ja existe um turno aberto no sistema (RN02).",
        )
    db.refresh(turno)
    return turno


def encerrar_turno(
    db: Session, funcionario_id: int, saldo_final_informado: Decimal
) -> Turno:
    """RF02/RF03: encerra o turno ativo e registra a conferencia do caixa.

    RN01: apenas o dono do turno pode encerra-lo.
    """
    turno = get_turno_aberto(db)
    if turno is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nao ha turno aberto para encerrar.",
        )
    if turno.funcionario_id != funcionario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o dono do turno pode encerra-lo (RN01).",
        )

    agora = _agora()
    turno.status = "encerrado"
    turno.data_fechamento = agora
    turno.caixa.saldo_final_informado = saldo_final_informado
    turno.caixa.fechamento = agora
    db.commit()
    db.refresh(turno)
    return turno

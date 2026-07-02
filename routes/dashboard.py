from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.caixa import CaixaStatusOut
from schemas.dashboard import ItemMaisVendido, ResumoDia
from security.dependencies import require_admin
from services import dashboard_service

# RNF03: metricas consolidadas sao exclusivas do administrador.
router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(require_admin)],
)


@router.get("/resumo", response_model=ResumoDia)
def resumo(dia: date | None = None, db: Session = Depends(get_db)):
    """RF07: faturamento e volume do dia (default: hoje em UTC).

    Timestamps sao gravados em UTC, entao o dia tambem e calculado em UTC
    para manter a consistencia da janela diaria.
    """
    return dashboard_service.resumo_dia(db, dia or datetime.now(timezone.utc).date())


@router.get("/mais-vendidos", response_model=list[ItemMaisVendido])
def mais_vendidos(limite: int = 10, db: Session = Depends(get_db)):
    return dashboard_service.mais_vendidos(db, limite)


@router.get("/caixa-status", response_model=CaixaStatusOut)
def caixa_status(db: Session = Depends(get_db)):
    return dashboard_service.caixa_status(db)

from datetime import date

from fastapi import APIRouter, Depends, Query
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
    """RF07: faturamento e volume do dia (default: hoje no fuso do negocio).

    A janela diaria e calculada em services/dashboard_service.py no fuso
    FUSO_NEGOCIO e convertida para UTC, que e como os timestamps sao gravados.
    """
    return dashboard_service.resumo_dia(db, dia or dashboard_service.hoje_negocio())


@router.get("/mais-vendidos", response_model=list[ItemMaisVendido])
def mais_vendidos(
    # ge/le: LIMIT negativo derruba a query no Postgres (500) e teto evita abuso.
    limite: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return dashboard_service.mais_vendidos(db, limite)


@router.get("/caixa-status", response_model=CaixaStatusOut)
def caixa_status(db: Session = Depends(get_db)):
    return dashboard_service.caixa_status(db)

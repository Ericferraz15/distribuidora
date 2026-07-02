from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models.usuario_model import Usuario
from schemas.auth import RefreshRequest, TokenResponse
from security.dependencies import gerenciador_jwt, get_current_user
from security.gerenciador_senha import GerenciadorSenha

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """RF01: valida credenciais e emite tokens access + refresh."""
    usuario = db.scalars(
        select(Usuario).where(Usuario.nome == form.username)
    ).first()
    if usuario is None or not GerenciadorSenha.verificar_hash(
        form.password, usuario.senha_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access = gerenciador_jwt.gerar_token(usuario.id, usuario.permissao, "access")
    refresh = gerenciador_jwt.gerar_token(usuario.id, usuario.permissao, "refresh")
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest):
    novo_access = gerenciador_jwt.renovar_token(body.refresh_token)
    if novo_access is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido ou expirado",
        )
    return TokenResponse(access_token=novo_access, refresh_token=body.refresh_token)


@router.post("/logout")
def logout(usuario: Usuario = Depends(get_current_user)):
    # JWT e stateless: o cliente deve descartar o token.
    return {"detail": "Logout efetuado. Descarte o token no cliente."}

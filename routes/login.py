from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models.usuario_model import Usuario
from schemas.auth import RefreshRequest, TokenResponse
from schemas.usuario import UsuarioOut
from security.dependencies import gerenciador_jwt, get_current_user
from security.gerenciador_senha import GerenciadorSenha

router = APIRouter(prefix="/auth", tags=["auth"])

# Hash "isca" para logins com usuario inexistente: sem ele, a resposta seria
# quase instantanea (pulou o bcrypt) e um atacante descobriria quais nomes de
# usuario existem cronometrando as respostas (user enumeration por timing).
_HASH_ISCA = GerenciadorSenha.gerar_hash("isca-anti-enumeracao")


@router.post("/login", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """RF01: valida credenciais e emite tokens access + refresh."""
    # strip: espaco acidental (autocomplete de celular adora) nao nega login.
    usuario = db.scalars(
        select(Usuario).where(Usuario.nome == form.username.strip())
    ).first()
    senha_ok = GerenciadorSenha.verificar_hash(
        form.password, usuario.senha_hash if usuario else _HASH_ISCA
    )
    # Mesma mensagem para "nao existe", "senha errada" e "desativado": nao dar
    # pista sobre quais contas existem. Usuario desativado nao ganha token.
    if usuario is None or not usuario.ativo or not senha_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access = gerenciador_jwt.gerar_token(usuario.id, usuario.permissao, "access")
    refresh = gerenciador_jwt.gerar_token(usuario.id, usuario.permissao, "refresh")
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.get("/me", response_model=UsuarioOut)
def me(usuario: Usuario = Depends(get_current_user)):
    """Perfil do usuario logado. O front usa para exibir nome e permissao
    sempre atualizados (o token so carrega o id e a permissao da epoca do login)."""
    return usuario


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    dados = gerenciador_jwt.verificar_token(body.refresh_token)
    if dados is None or dados.get("tipo") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido ou expirado",
        )
    # Rele o usuario do banco: desativado nao renova, e o novo access carrega a
    # permissao ATUAL (nao a da epoca do login — rebaixado nao continua admin).
    usuario = db.get(Usuario, int(dados["sub"]))
    if usuario is None or not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido ou expirado",
        )
    novo_access = gerenciador_jwt.gerar_token(usuario.id, usuario.permissao, "access")
    return TokenResponse(access_token=novo_access, refresh_token=body.refresh_token)


@router.post("/logout")
def logout(usuario: Usuario = Depends(get_current_user)):
    # JWT e stateless: o cliente deve descartar o token.
    return {"detail": "Logout efetuado. Descarte o token no cliente."}

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models.usuario_model import Usuario
from schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioUpdate
from security.dependencies import require_admin
from security.gerenciador_senha import GerenciadorSenha

# RNF03: todo o gerenciamento de usuarios exige perfil admin.
router = APIRouter(
    prefix="/usuarios",
    tags=["usuarios"],
    dependencies=[Depends(require_admin)],
)


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def criar_usuario(body: UsuarioCreate, db: Session = Depends(get_db)):
    if db.scalars(select(Usuario).where(Usuario.nome == body.nome)).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ja existe um usuario com esse nome.",
        )
    usuario = Usuario(
        nome=body.nome,
        senha_hash=GerenciadorSenha.gerar_hash(body.senha),
        permissao=body.permissao.value,
        numero_telefone=body.numero_telefone,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.get("", response_model=list[UsuarioOut])
def listar_usuarios(db: Session = Depends(get_db)):
    return list(db.scalars(select(Usuario).order_by(Usuario.nome)))


@router.patch("/{usuario_id}", response_model=UsuarioOut)
def atualizar_usuario(
    usuario_id: int, body: UsuarioUpdate, db: Session = Depends(get_db)
):
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario nao encontrado.",
        )

    dados = body.model_dump(exclude_unset=True)
    senha = dados.pop("senha", None)
    if senha is not None:
        usuario.senha_hash = GerenciadorSenha.gerar_hash(senha)
    permissao = dados.pop("permissao", None)
    if permissao is not None:
        usuario.permissao = getattr(permissao, "value", permissao)
    for campo, valor in dados.items():
        setattr(usuario, campo, valor)

    db.commit()
    db.refresh(usuario)
    return usuario

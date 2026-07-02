from enum import Enum

from pydantic import BaseModel, ConfigDict


class PermissaoUsuario(str, Enum):
    ADMIN = "admin"
    FUNCIONARIO = "funcionario"


class Usuario(BaseModel):
    """Modelo de dominio (usado em testes unitarios e como base de DTOs)."""

    id: int
    nome: str
    senha_hash: str
    permissao: PermissaoUsuario = PermissaoUsuario.FUNCIONARIO
    numero_telefone: str | None = None


class UsuarioCreate(BaseModel):
    nome: str
    senha: str
    permissao: PermissaoUsuario = PermissaoUsuario.FUNCIONARIO
    numero_telefone: str | None = None


class UsuarioUpdate(BaseModel):
    nome: str | None = None
    senha: str | None = None
    permissao: PermissaoUsuario | None = None
    numero_telefone: str | None = None
    ativo: bool | None = None


class UsuarioOut(BaseModel):
    """Resposta publica: nunca expoe senha_hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    permissao: PermissaoUsuario
    numero_telefone: str | None = None
    ativo: bool = True

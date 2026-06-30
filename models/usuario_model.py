from enum import Enum
from pydantic import BaseModel


class PermissaoUsuario(str, Enum):
    ADMIN = "admin"
    FUNCIONARIO = "funcionario"


class Usuario(BaseModel):
    id: int
    nome: str
    senha_hash: str
    permissao: PermissaoUsuario = PermissaoUsuario.FUNCIONARIO
    numero_telefone: str | None = None



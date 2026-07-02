from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

# Tipos reutilizados pelos DTOs de criacao e edicao:
#  - Senha: minimo 6 barra senha vazia/trivial; maximo 72 e o limite do bcrypt
#    (acima disso a lib levanta ValueError -> 500). Validar aqui devolve um
#    422 claro ao cliente em vez de derrubar a requisicao.
#  - Nome/Telefone: mesmos limites das colunas (String(120)/String(20)) para
#    o Postgres nunca rejeitar o INSERT com erro generico.
Senha = Annotated[str, Field(min_length=6, max_length=72)]
Nome = Annotated[str, Field(min_length=2, max_length=120)]
Telefone = Annotated[str, Field(max_length=20)]


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
    nome: Nome
    senha: Senha
    permissao: PermissaoUsuario = PermissaoUsuario.FUNCIONARIO
    numero_telefone: Telefone | None = None


class UsuarioUpdate(BaseModel):
    nome: Nome | None = None
    senha: Senha | None = None
    permissao: PermissaoUsuario | None = None
    numero_telefone: Telefone | None = None
    ativo: bool | None = None


class UsuarioOut(BaseModel):
    """Resposta publica: nunca expoe senha_hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    permissao: PermissaoUsuario
    numero_telefone: str | None = None
    ativo: bool = True

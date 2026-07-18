from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

# Tipos reutilizados pelos DTOs de criacao e edicao:
#  - Senha: minimo 6 barra senha vazia/trivial; maximo 72 e o limite do bcrypt
#    (acima disso a lib levanta ValueError -> 500). Validar aqui devolve um
#    422 claro ao cliente em vez de derrubar a requisicao.
#  - Nome/Telefone: mesmos limites das colunas (String(120)/String(20)) para
#    o Postgres nunca rejeitar o INSERT com erro generico.
#  - strip_whitespace no Nome: " maria " cadastrada com espaco nunca mais
#    conseguiria logar digitando "maria" (login compara nome exato).
Senha = Annotated[str, Field(min_length=6, max_length=72)]
Nome = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)
]
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

    # Num PATCH, "omitir o campo" significa "nao mexer"; null explicito em
    # campo obrigatorio viraria IntegrityError no banco (e um 409 enganoso de
    # "nome ja existe"). `numero_telefone` fica de fora: e anulavel.
    @field_validator("nome", "senha", "permissao", "ativo", mode="before")
    @classmethod
    def _rejeita_null_em_campo_obrigatorio(cls, v):
        if v is None:
            raise ValueError("campo obrigatorio nao aceita null; omita-o para nao altera-lo")
        return v


class UsuarioOut(BaseModel):
    """Resposta publica: nunca expoe senha_hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    permissao: PermissaoUsuario
    numero_telefone: str | None = None
    ativo: bool = True

"""Registra todos os modelos ORM no metadata do Base.

Importar `models` garante que todas as tabelas e relacionamentos estejam
disponiveis antes de `Base.metadata.create_all(...)` ou do Alembic.
"""

from models.caixa_model import Caixa
from models.estoque_model import MovimentoEstoque, Produto
from models.transacao_model import ItemVenda, Transacao
from models.turno_model import Turno
from models.usuario_model import Usuario

__all__ = [
    "Usuario",
    "Turno",
    "Caixa",
    "Transacao",
    "ItemVenda",
    "Produto",
    "MovimentoEstoque",
]

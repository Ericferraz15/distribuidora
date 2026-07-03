import os
from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt
from dotenv import load_dotenv

load_dotenv()

# Tempos de vida dos tokens (RF01):
#  - access:  curto, viaja em toda requisicao; se vazar, expira rapido.
#  - refresh: longo, usado apenas em /auth/refresh para emitir novos access.
ACCESS_TTL = timedelta(hours=1)
REFRESH_TTL = timedelta(days=7)

# HS256 assina com HMAC-SHA256; a RFC 7518 exige chave >= 32 bytes, senao
# fica viavel descobrir a chave por forca bruta e forjar tokens de admin.
TAMANHO_MINIMO_CHAVE = 32


class GerenciadorJwt:
    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY_JWT")
        # Falha na inicializacao ("fail fast"), nao no primeiro login: um
        # servidor que sobe sem chave assinaria tokens com segredo previsivel.
        if not self.secret_key or len(self.secret_key) < TAMANHO_MINIMO_CHAVE:
            raise RuntimeError(
                "SECRET_KEY_JWT ausente ou muito curta "
                f"(minimo {TAMANHO_MINIMO_CHAVE} caracteres). Gere uma com: "
                'python -c "import secrets; print(secrets.token_urlsafe(48))" '
                "e coloque no .env."
            )
        self.algoritmo = "HS256"

    def gerar_token(self, usuario_id: int, permissao: str, tipo: Literal["access", "refresh"]) -> str:
        validade = ACCESS_TTL if tipo == "access" else REFRESH_TTL
        payload = {
            # "sub" (subject) e string por convencao do JWT (RFC 7519).
            "sub": str(usuario_id),
            # A permissao no token e so informativa; a autorizacao real sempre
            # rele o usuario no banco (ver security/dependencies.py).
            "permissao": permissao,
            "tipo": tipo,
            "exp": datetime.now(timezone.utc) + validade,
        }
        return jwt.encode(payload, self.secret_key, self.algoritmo)

    def verificar_token(self, token: str) -> dict | None:
        """Retorna as claims se o token for valido; None caso contrario.

        jwt.decode ja confere assinatura E expiracao ("exp"). Fixar
        `algorithms` evita o ataque classico de trocar o algoritmo do header.
        """
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algoritmo])
        except jwt.InvalidTokenError:
            return None

    def renovar_token(self, refresh_token: str) -> str | None:
        """Emite um novo access token a partir de um refresh token valido."""
        dados = self.verificar_token(refresh_token)
        # Exigir tipo == "refresh" impede usar um access token (vida curta)
        # como se fosse refresh para se manter logado indefinidamente.
        if dados is not None and dados.get("tipo") == "refresh":
            return self.gerar_token(dados["sub"], dados["permissao"], "access")
        return None

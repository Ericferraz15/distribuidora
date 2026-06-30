import os
import jwt
from typing import Literal
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()


class GerenciadorJwt:
    def __init__(self):

        self.secret_key = os.getenv("SECRET_KEY_JWT")
        self.algoritmo = "HS256"
        self.expiracao = 3600

    def gerar_token(
        self, usuario_id: int, permissao: str, tipo: Literal["access", "refresh"]
    ):
        segundos = self.expiracao if tipo == "access" else 60 * 60 * 24 * 7
        payload = {
            "sub": str(usuario_id),
            "permissao": permissao,
            "tipo": tipo,
            "exp": datetime.now(timezone.utc) + timedelta(seconds=segundos),
        }
        token = jwt.encode(payload, self.secret_key, self.algoritmo)

        return token

    def verificar_token(self, token: str):

        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algoritmo])

        except jwt.InvalidTokenError:
            return None

    def renovar_token(self, refresh_token: str):
        dados = self.verificar_token(refresh_token)

        if dados is not None and dados.get("tipo") == "refresh":
            return self.gerar_token(dados["sub"], dados["permissao"], "access")

        return None

"""Cria o administrador inicial (bootstrap).

Como usuarios so podem ser criados por um admin (RNF03), este script gera o
primeiro admin caso o banco esteja vazio.

Uso:
    python scripts/seed.py

Variaveis de ambiente opcionais: ADMIN_NOME, ADMIN_SENHA.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models  # noqa: F401  (registra tabelas)
from database import Base, SessionLocal, engine
from models.usuario_model import Usuario
from security.gerenciador_senha import GerenciadorSenha


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Usuario).count() > 0:
            print("Ja existem usuarios; seed ignorado.")
            return
        nome = os.getenv("ADMIN_NOME", "admin")
        senha = os.getenv("ADMIN_SENHA", "admin123")
        admin = Usuario(
            nome=nome,
            senha_hash=GerenciadorSenha.gerar_hash(senha),
            permissao="admin",
        )
        db.add(admin)
        db.commit()
        print(f"Admin criado: nome='{nome}' (troque a senha em producao).")
    finally:
        db.close()


if __name__ == "__main__":
    main()

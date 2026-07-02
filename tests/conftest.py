import os

# Garante que a app nunca toque no Postgres real durante os testes.
os.environ.setdefault("DATABASE_URL", "sqlite://")
# 32+ chars: HS256 exige chave longa (ver security/gerenciador_jwt.py).
os.environ.setdefault("SECRET_KEY_JWT", "chave-de-teste-nao-usar-em-producao-0123456789")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401  (registra tabelas)
from database import Base, get_db
from main import app
from models.usuario_model import Usuario
from security.gerenciador_senha import GerenciadorSenha


@pytest.fixture
def db_session():
    # SQLite em memoria compartilhado (StaticPool) por teste.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    # TestClient sem context manager: nao dispara o lifespan (evita create_all
    # no engine real). As tabelas ja foram criadas na fixture db_session.
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _criar_usuario(db, nome, senha, permissao):
    usuario = Usuario(
        nome=nome,
        senha_hash=GerenciadorSenha.gerar_hash(senha),
        permissao=permissao,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@pytest.fixture
def admin(db_session):
    return _criar_usuario(db_session, "admin", "admin123", "admin")


@pytest.fixture
def funcionario(db_session):
    return _criar_usuario(db_session, "func", "func123", "funcionario")


def _headers(client, nome, senha):
    resp = client.post("/auth/login", data={"username": nome, "password": senha})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def admin_headers(client, admin):
    return _headers(client, "admin", "admin123")


@pytest.fixture
def func_headers(client, funcionario):
    return _headers(client, "func", "func123")

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

# Postgres em producao; ver .env / .env.example. O default facilita rodar local.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/distribuidora",
)

# SQLite (usado nos testes) precisa desse connect_arg para multiplas threads.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# pool_pre_ping evita conexoes mortas em operacao 24/7 (RNF01).
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependencia FastAPI: fornece uma sessao por request e sempre fecha."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

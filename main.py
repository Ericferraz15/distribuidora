import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models  # noqa: F401  (registra as tabelas no Base.metadata)
from database import Base, engine
from routes import (
    caixa,
    dashboard,
    estoque,
    login,
    transacoes,
    turnos,
    usuarios,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Conveniencia de dev: cria tabelas ausentes. Em producao use Alembic
    # (`alembic upgrade head`) para versionar o schema sem downtime (RNF01).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Distribuidora API",
    description="API de gestao de caixa, estoque e usuarios",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS: em dev o Vite faz proxy (mesma origem, dispensa CORS); em producao na
# rede local o front pode ser acessado por http://<ip-do-note>:3000, entao a
# lista de origens vem do .env. Nao usamos allow_credentials porque a auth
# viaja no header Authorization (Bearer), nao em cookies — e a combinacao
# credentials + origem "*" e invalida por especificacao (os navegadores bloqueiam).
origens = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origens,
    allow_methods=["*"],
    allow_headers=["*"],
)

for modulo in (login, usuarios, turnos, caixa, transacoes, estoque, dashboard):
    app.include_router(modulo.router)


if __name__ == "__main__":
    # host 0.0.0.0: expoe a API para todos os hosts da rede local (acesso via celular etc.)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

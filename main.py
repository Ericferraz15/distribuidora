import uvicorn
from routes import login
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Distribuidora API",
    description="API de gestao de caixa, estoque e usuarios",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(login.router)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)

from fastapi import APIRouter

router = APIRouter(prefix="/teste")


@router.post("/login")
def login(nome:str, senha:str):
    ...

@router.get("/logout")
def logout(nome: str):
    ...

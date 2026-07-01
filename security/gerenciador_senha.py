import bcrypt


class GerenciadorSenha:
    @staticmethod
    def gerar_hash(senha: str) -> str:
        hashe = bcrypt.hashpw(senha.encode(), bcrypt.gensalt())
        return hashe.decode()

    @staticmethod
    def verificar_hash(senha_request: str, senha_hash: str) -> bool:
        return bcrypt.checkpw(senha_request.encode(), senha_hash.encode())

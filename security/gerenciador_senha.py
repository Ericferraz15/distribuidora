import bcrypt


class GerenciadorSenha:
    @staticmethod
    def gerar_hash(senha: str) -> str:
        hashe = bcrypt.hashpw(senha.encode(), bcrypt.gensalt())
        return hashe.decode()

    @staticmethod
    def verificar_hash(senha_request: str, senha_hash: str) -> bool:
        try:
            return bcrypt.checkpw(senha_request.encode(), senha_hash.encode())
        except ValueError:
            # bcrypt 5.x recusa senha > 72 bytes com ValueError. Nenhuma senha
            # valida do sistema passa de 72 (schemas capam), entao a resposta
            # certa e "nao confere" — e nao um 500 na cara do usuario.
            return False

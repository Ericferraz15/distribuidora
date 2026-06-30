from models.usuario_model import Usuario, PermissaoUsuario


def test_permissao_padrao_funcionario():
    u = Usuario(id=1, nome="Eric", senha_hash="x")
    assert u.permissao == PermissaoUsuario.FUNCIONARIO


def test_telefone_opcional():
    u = Usuario(id=1, nome="Eric", senha_hash="x")
    assert u.numero_telefone is None


def test_admin_explicito():
    u = Usuario(
        id=2,
        nome="Chefe",
        senha_hash="x",
        permissao=PermissaoUsuario.ADMIN,
    )
    assert u.permissao == PermissaoUsuario.ADMIN

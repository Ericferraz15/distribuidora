from datetime import datetime

from schemas.estoque import Estoque, Produto, MovimentoEstoque


def test_saldo_estoque_considera_quantidade():
    p1 = Produto(id=1, nome="Cafe", valor=5.0, quantidade=10, fornecedor="X")
    p2 = Produto(id=2, nome="Acucar", valor=3.0, quantidade=2, fornecedor="Y")
    e = Estoque(id=1, produtos=[p1, p2])
    assert e.saldo_estoque == 56.0  # 5*10 + 3*2


def test_estoque_vazio():
    e = Estoque(id=1)
    assert e.saldo_estoque == 0
    assert e.produtos == []
    assert e.entradas == []
    assert e.saidas == []


def test_movimento_registra_data():
    m = MovimentoEstoque(produto_id=1, quantidade=10)
    assert isinstance(m.data, datetime)
    assert m.quantidade == 10


def test_quantidade_padrao_zero():
    p = Produto(id=1, nome="Cafe", valor=5.0, fornecedor="X")
    assert p.quantidade == 0

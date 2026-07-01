import time

from models.caixa_model import Caixa,Entrada,Saida,FechamentoMensal,MetodoPagamento
from models.usuario_model import Usuario


def novo_usuario():
    return Usuario(id=1, nome="Eric", senha_hash="x")


def test_saldo_caixa():
    c = Caixa(
        id=1,
        responsavel=novo_usuario(),
        entradas=[Entrada(id=1, valor=200, metodo=MetodoPagamento.DINHEIRO)],
        saidas=[Saida(id=1, valor=50, metodo=MetodoPagamento.DEBITO)],
    )
    assert c.saldo == 150.0


def test_caixa_vazio_tem_saldo_zero():
    c = Caixa(id=1, responsavel=novo_usuario())
    assert c.saldo == 0
    assert c.fechamento is None


def test_abertura_padrao_unica_por_instancia():
    c1 = Caixa(id=1, responsavel=novo_usuario())
    time.sleep(0.01)
    c2 = Caixa(id=2, responsavel=novo_usuario())
    assert c1.abertura != c2.abertura


def test_saldo_total_mensal():
    c1 = Caixa(
        id=1,
        responsavel=novo_usuario(),
        entradas=[Entrada(id=1, valor=100, metodo=MetodoPagamento.DINHEIRO)],
    )
    c2 = Caixa(
        id=2,
        responsavel=novo_usuario(),
        entradas=[Entrada(id=2, valor=50, metodo=MetodoPagamento.CREDITO)],
        saidas=[Saida(id=1, valor=20, metodo=MetodoPagamento.DEBITO)],
    )
    fm = FechamentoMensal(id=1, mes=6, ano=2026, caixas=[c1, c2])
    assert fm.saldo_total == 130.0

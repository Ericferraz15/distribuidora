import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../api/client.js'
import { useAuth } from '../auth/AuthContext.jsx'
import { useToast } from '../components/Toast.jsx'
import Modal from '../components/Modal.jsx'
import { SkeletonLinhas } from '../components/Skeleton.jsx'
import { formatBRL, formatData, rotulo } from '../lib/format.js'

const METODOS = ['dinheiro', 'debito', 'credito']
const CATEGORIAS_SAIDA = ['sangria', 'despesa', 'suprimento']

export default function Operacao() {
  const { user } = useAuth()
  const toast = useToast()

  const [caixa, setCaixa] = useState(null)
  const [produtos, setProdutos] = useState([])
  const [transacoes, setTransacoes] = useState([])
  const [carregando, setCarregando] = useState(true)

  const [saldoInicial, setSaldoInicial] = useState('')
  const [abrindo, setAbrindo] = useState(false)

  const [modalVenda, setModalVenda] = useState(false)
  const [modalSaida, setModalSaida] = useState(false)
  const [modalFechar, setModalFechar] = useState(false)

  const aberto = !!caixa?.aberto
  const souDono = aberto && caixa?.funcionario_id === user?.id

  const carregar = useCallback(async () => {
    setCarregando(true)
    try {
      const status = await api.caixaAtual()
      setCaixa(status)
      if (status?.aberto) {
        const [prod, tx] = await Promise.all([api.listarProdutos(), api.listarTransacoes()])
        setProdutos(prod)
        setTransacoes(tx)
      } else {
        setTransacoes([])
      }
    } catch (err) {
      toast.erro(err.message)
    } finally {
      setCarregando(false)
    }
  }, [toast])

  useEffect(() => {
    carregar()
  }, [carregar])

  async function abrirTurno(e) {
    e.preventDefault()
    setAbrindo(true)
    try {
      await api.abrirTurno(Number(saldoInicial))
      toast.sucesso('Turno aberto com sucesso.')
      setSaldoInicial('')
      await carregar()
    } catch (err) {
      toast.erro(err.message)
    } finally {
      setAbrindo(false)
    }
  }

  if (carregando && !caixa) {
    return (
      <div className="pagina">
        <div className="card"><SkeletonLinhas linhas={5} /></div>
      </div>
    )
  }

  return (
    <div className="pagina">
      <header className="pagina__head">
        <div>
          <h2>Operação de caixa</h2>
          <p className="muted">Turno, vendas e movimentações do caixa atual.</p>
        </div>
        <span className={'pill ' + (aberto ? 'pill--ok' : 'pill--neutro')}>
          {aberto ? 'Caixa aberto' : 'Caixa fechado'}
        </span>
      </header>

      {!aberto && (
        <section className="card card--foco">
          <h3>Abrir turno</h3>
          <p className="muted">Informe o saldo inicial em caixa para começar o turno.</p>
          <form className="form-linha" onSubmit={abrirTurno}>
            <label className="campo">
              <span>Saldo inicial (R$)</span>
              <input
                type="number"
                step="0.01"
                min="0"
                value={saldoInicial}
                onChange={(e) => setSaldoInicial(e.target.value)}
                required
              />
            </label>
            <button className="btn btn--primary" disabled={abrindo || saldoInicial === ''}>
              {abrindo ? 'Abrindo…' : 'Abrir turno'}
            </button>
          </form>
        </section>
      )}

      {aberto && (
        <>
          <section className="grid grid--metricas">
            <div className="card metrica metrica--destaque">
              <span className="metrica__titulo">Saldo atual</span>
              <strong className="metrica__valor">{formatBRL(caixa.saldo_atual)}</strong>
            </div>
            <div className="card metrica">
              <span className="metrica__titulo">Saldo inicial</span>
              <strong className="metrica__valor">{formatBRL(caixa.saldo_inicial)}</strong>
            </div>
            <div className="card metrica">
              <span className="metrica__titulo">Entradas</span>
              <strong className="metrica__valor positivo">{formatBRL(caixa.total_entradas)}</strong>
            </div>
            <div className="card metrica">
              <span className="metrica__titulo">Saídas</span>
              <strong className="metrica__valor negativo">{formatBRL(caixa.total_saidas)}</strong>
            </div>
          </section>

          <section className="card">
            <div className="card__head">
              <div>
                <h3>Turno #{caixa.turno_id}</h3>
                <p className="muted">
                  Responsável: Usuário #{caixa.funcionario_id} · Aberto em {formatData(caixa.abertura)}
                </p>
              </div>
              <div className="acoes">
                <button className="btn btn--primary" onClick={() => setModalVenda(true)} disabled={!souDono}>
                  + Venda
                </button>
                <button className="btn" onClick={() => setModalSaida(true)} disabled={!souDono}>
                  Sangria / Despesa
                </button>
                <button className="btn btn--danger" onClick={() => setModalFechar(true)} disabled={!souDono}>
                  Fechar caixa
                </button>
              </div>
            </div>
            {!souDono && (
              <div className="alerta alerta--aviso">
                Este turno pertence a outro funcionário. Apenas o dono do turno pode
                registrar movimentações (RN01).
              </div>
            )}
          </section>

          <section className="card">
            <div className="card__head">
              <h3>Transações do turno</h3>
            </div>
            {transacoes.length === 0 ? (
              <p className="vazio">Nenhuma transação registrada ainda.</p>
            ) : (
              <table className="tabela tabela--responsiva">
                <thead>
                  <tr>
                    <th>Hora</th>
                    <th>Tipo</th>
                    <th>Categoria</th>
                    <th>Pagamento</th>
                    <th className="num">Valor</th>
                  </tr>
                </thead>
                <tbody>
                  {transacoes.map((t) => (
                    <tr key={t.id}>
                      <td data-label="Hora">{formatData(t.data)}</td>
                      <td data-label="Tipo">
                        <span className={'pill ' + (t.tipo === 'entrada' ? 'pill--ok' : 'pill--warn')}>
                          {rotulo(t.tipo)}
                        </span>
                      </td>
                      <td data-label="Categoria">{rotulo(t.categoria)}</td>
                      <td data-label="Pagamento">{rotulo(t.metodo_pagamento)}</td>
                      <td className={'num ' + (t.tipo === 'entrada' ? 'positivo' : 'negativo')} data-label="Valor">
                        {t.tipo === 'entrada' ? '+' : '−'} {formatBRL(t.valor)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </>
      )}

      <ModalVenda
        aberto={modalVenda}
        produtos={produtos}
        onClose={() => setModalVenda(false)}
        onSucesso={async () => {
          setModalVenda(false)
          await carregar()
        }}
      />
      <ModalSaida
        aberto={modalSaida}
        onClose={() => setModalSaida(false)}
        onSucesso={async () => {
          setModalSaida(false)
          await carregar()
        }}
      />
      <ModalFechar
        aberto={modalFechar}
        saldoAtual={caixa?.saldo_atual}
        onClose={() => setModalFechar(false)}
        onSucesso={async () => {
          setModalFechar(false)
          await carregar()
        }}
      />
    </div>
  )
}

// --- Venda -----------------------------------------------------------------
function ModalVenda({ aberto, produtos, onClose, onSucesso }) {
  const toast = useToast()
  const [itens, setItens] = useState([])
  const [produtoId, setProdutoId] = useState('')
  const [quantidade, setQuantidade] = useState(1)
  const [metodo, setMetodo] = useState('dinheiro')
  const [descricao, setDescricao] = useState('')
  const [enviando, setEnviando] = useState(false)

  const disponiveis = useMemo(
    () => produtos.filter((p) => p.ativo !== false),
    [produtos]
  )
  const porId = useMemo(() => Object.fromEntries(produtos.map((p) => [p.id, p])), [produtos])

  const total = itens.reduce(
    (acc, it) => acc + Number(porId[it.produto_id]?.valor || 0) * it.quantidade,
    0
  )

  function limpar() {
    setItens([])
    setProdutoId('')
    setQuantidade(1)
    setMetodo('dinheiro')
    setDescricao('')
  }

  function adicionar() {
    if (!produtoId) return
    const id = Number(produtoId)
    const qtd = Math.max(1, Number(quantidade) || 1)
    setItens((prev) => {
      const existente = prev.find((i) => i.produto_id === id)
      if (existente) {
        return prev.map((i) => (i.produto_id === id ? { ...i, quantidade: i.quantidade + qtd } : i))
      }
      return [...prev, { produto_id: id, quantidade: qtd }]
    })
    setProdutoId('')
    setQuantidade(1)
  }

  function remover(id) {
    setItens((prev) => prev.filter((i) => i.produto_id !== id))
  }

  async function confirmar() {
    if (itens.length === 0) {
      toast.erro('Adicione ao menos um item.')
      return
    }
    setEnviando(true)
    try {
      await api.registrarVenda({
        itens: itens.map((i) => ({ produto_id: i.produto_id, quantidade: i.quantidade })),
        metodo_pagamento: metodo,
        descricao: descricao || null,
      })
      toast.sucesso('Venda registrada.')
      limpar()
      onSucesso()
    } catch (err) {
      toast.erro(err.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Modal
      aberto={aberto}
      titulo="Registrar venda"
      onClose={() => {
        limpar()
        onClose()
      }}
      footer={
        <>
          <span className="modal__total">Total: <strong>{formatBRL(total)}</strong></span>
          <button className="btn" onClick={onClose}>Cancelar</button>
          <button className="btn btn--primary" onClick={confirmar} disabled={enviando}>
            {enviando ? 'Salvando…' : 'Registrar venda'}
          </button>
        </>
      }
    >
      <div className="form-linha form-linha--fim">
        <label className="campo campo--cresce">
          <span>Produto</span>
          <select value={produtoId} onChange={(e) => setProdutoId(e.target.value)}>
            <option value="">Selecione…</option>
            {disponiveis.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nome} — {formatBRL(p.valor)} (estq: {p.quantidade})
              </option>
            ))}
          </select>
        </label>
        <div className="campo" style={{ flex: '0 0 auto' }}>
          <span>Qtd.</span>
          <div className="stepper">
            <button
              type="button"
              className="stepper__btn"
              onClick={() => setQuantidade((q) => Math.max(1, (Number(q) || 1) - 1))}
              aria-label="Diminuir"
            >
              −
            </button>
            <span className="stepper__valor">{Math.max(1, Number(quantidade) || 1)}</span>
            <button
              type="button"
              className="stepper__btn"
              onClick={() => setQuantidade((q) => (Number(q) || 1) + 1)}
              aria-label="Aumentar"
            >
              +
            </button>
          </div>
        </div>
        <button className="btn" onClick={adicionar} disabled={!produtoId}>
          Adicionar
        </button>
      </div>

      {itens.length > 0 && (
        <table className="tabela tabela--compacta">
          <thead>
            <tr>
              <th>Item</th>
              <th className="num">Qtd.</th>
              <th className="num">Subtotal</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {itens.map((it) => {
              const p = porId[it.produto_id]
              return (
                <tr key={it.produto_id}>
                  <td>{p?.nome ?? `#${it.produto_id}`}</td>
                  <td className="num">{it.quantidade}</td>
                  <td className="num">{formatBRL(Number(p?.valor || 0) * it.quantidade)}</td>
                  <td className="num">
                    <button className="icon-btn" onClick={() => remover(it.produto_id)} aria-label="Remover">
                      ✕
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}

      <div className="form-linha">
        <label className="campo">
          <span>Método de pagamento</span>
          <select value={metodo} onChange={(e) => setMetodo(e.target.value)}>
            {METODOS.map((m) => (
              <option key={m} value={m}>{rotulo(m)}</option>
            ))}
          </select>
        </label>
        <label className="campo campo--cresce">
          <span>Descrição (opcional)</span>
          <input type="text" value={descricao} onChange={(e) => setDescricao(e.target.value)} />
        </label>
      </div>
    </Modal>
  )
}

// --- Saída (sangria / despesa / suprimento) --------------------------------
function ModalSaida({ aberto, onClose, onSucesso }) {
  const toast = useToast()
  const [valor, setValor] = useState('')
  const [categoria, setCategoria] = useState('sangria')
  const [metodo, setMetodo] = useState('dinheiro')
  const [descricao, setDescricao] = useState('')
  const [enviando, setEnviando] = useState(false)

  function limpar() {
    setValor('')
    setCategoria('sangria')
    setMetodo('dinheiro')
    setDescricao('')
  }

  async function confirmar(e) {
    e.preventDefault()
    setEnviando(true)
    try {
      await api.registrarSaida({
        valor: Number(valor),
        categoria,
        metodo_pagamento: metodo,
        descricao: descricao || null,
      })
      toast.sucesso('Movimentação registrada.')
      limpar()
      onSucesso()
    } catch (err) {
      toast.erro(err.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Modal
      aberto={aberto}
      titulo="Sangria / Despesa / Suprimento"
      onClose={() => {
        limpar()
        onClose()
      }}
    >
      <form className="form-vertical" onSubmit={confirmar}>
        <p className="muted">
          Sangria e despesa saem do caixa; suprimento entra. O valor sempre é positivo.
        </p>
        <label className="campo">
          <span>Categoria</span>
          <select value={categoria} onChange={(e) => setCategoria(e.target.value)}>
            {CATEGORIAS_SAIDA.map((c) => (
              <option key={c} value={c}>{rotulo(c)}</option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Valor (R$)</span>
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            required
          />
        </label>
        <label className="campo">
          <span>Método de pagamento</span>
          <select value={metodo} onChange={(e) => setMetodo(e.target.value)}>
            {METODOS.map((m) => (
              <option key={m} value={m}>{rotulo(m)}</option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Descrição (opcional)</span>
          <input type="text" value={descricao} onChange={(e) => setDescricao(e.target.value)} />
        </label>
        <div className="form-acoes">
          <button type="button" className="btn" onClick={onClose}>Cancelar</button>
          <button className="btn btn--primary" disabled={enviando || valor === ''}>
            {enviando ? 'Salvando…' : 'Registrar'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

// --- Fechar caixa ----------------------------------------------------------
function ModalFechar({ aberto, saldoAtual, onClose, onSucesso }) {
  const toast = useToast()
  const [saldoFinal, setSaldoFinal] = useState('')
  const [enviando, setEnviando] = useState(false)

  const diferenca = saldoFinal === '' ? null : Number(saldoFinal) - Number(saldoAtual || 0)

  async function confirmar(e) {
    e.preventDefault()
    setEnviando(true)
    try {
      await api.fecharCaixa(Number(saldoFinal))
      toast.sucesso('Caixa fechado e turno encerrado.')
      setSaldoFinal('')
      onSucesso()
    } catch (err) {
      toast.erro(err.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Modal
      aberto={aberto}
      titulo="Fechar caixa"
      onClose={() => {
        setSaldoFinal('')
        onClose()
      }}
    >
      <form className="form-vertical" onSubmit={confirmar}>
        <p className="muted">
          Saldo esperado no sistema: <strong>{formatBRL(saldoAtual)}</strong>. Informe o valor
          efetivamente conferido em caixa para encerrar o turno (RN01).
        </p>
        <label className="campo">
          <span>Saldo final conferido (R$)</span>
          <input
            type="number"
            step="0.01"
            min="0"
            value={saldoFinal}
            onChange={(e) => setSaldoFinal(e.target.value)}
            required
            autoFocus
          />
        </label>
        {diferenca !== null && (
          <div className={'alerta ' + (Math.abs(diferenca) < 0.005 ? 'alerta--ok' : 'alerta--aviso')}>
            {Math.abs(diferenca) < 0.005
              ? 'Saldo confere com o esperado.'
              : `Diferença de ${formatBRL(diferenca)} em relação ao esperado.`}
          </div>
        )}
        <div className="form-acoes">
          <button type="button" className="btn" onClick={onClose}>Cancelar</button>
          <button className="btn btn--danger" disabled={enviando || saldoFinal === ''}>
            {enviando ? 'Fechando…' : 'Fechar caixa'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

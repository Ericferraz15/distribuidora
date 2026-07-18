import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../api/client.js'
import { useAuth } from '../auth/AuthContext.jsx'
import { useToast } from '../components/Toast.jsx'
import Modal from '../components/Modal.jsx'
import { SkeletonLinhas } from '../components/Skeleton.jsx'
import { formatBRL } from '../lib/format.js'

const VAZIO = { nome: '', valor: '', quantidade: '', fornecedor: '', descricao: '' }

export default function Estoque() {
  const { isAdmin } = useAuth()
  const toast = useToast()

  const [produtos, setProdutos] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [busca, setBusca] = useState('')

  const [modalProduto, setModalProduto] = useState(null) // null | {} (novo) | produto (edicao)
  const [modalEntrada, setModalEntrada] = useState(null)

  const carregar = useCallback(async () => {
    setCarregando(true)
    try {
      setProdutos(await api.listarProdutos())
    } catch (err) {
      toast.erro(err.message)
    } finally {
      setCarregando(false)
    }
  }, [toast])

  useEffect(() => {
    carregar()
  }, [carregar])

  const filtrados = useMemo(() => {
    const q = busca.trim().toLowerCase()
    if (!q) return produtos
    return produtos.filter(
      (p) => p.nome.toLowerCase().includes(q) || (p.fornecedor || '').toLowerCase().includes(q)
    )
  }, [produtos, busca])

  return (
    <div className="pagina">
      <header className="pagina__head">
        <div>
          <h2>Estoque</h2>
          <p className="muted">
            {isAdmin ? 'Cadastro, edição e reposição de produtos.' : 'Consulta de produtos disponíveis.'}
          </p>
        </div>
        <div className="acoes">
          <input
            className="input-busca"
            type="search"
            placeholder="Buscar produto…"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
          />
          {isAdmin && (
            <button className="btn btn--primary" onClick={() => setModalProduto({})}>
              + Novo produto
            </button>
          )}
        </div>
      </header>

      <section className="card">
        {carregando ? (
          <SkeletonLinhas linhas={6} />
        ) : filtrados.length === 0 ? (
          <p className="vazio">Nenhum produto encontrado.</p>
        ) : (
          <table className="tabela tabela--responsiva">
            <thead>
              <tr>
                <th>Produto</th>
                <th>Fornecedor</th>
                <th className="num">Preço</th>
                <th className="num">Estoque</th>
                <th>Status</th>
                {isAdmin && <th className="num">Ações</th>}
              </tr>
            </thead>
            <tbody>
              {filtrados.map((p) => (
                <tr key={p.id} className={p.ativo === false ? 'linha--inativa' : ''}>
                  <td data-label="Produto">
                    <div>
                      <strong>{p.nome}</strong>
                      {p.descricao && <div className="muted sub">{p.descricao}</div>}
                    </div>
                  </td>
                  <td data-label="Fornecedor">{p.fornecedor}</td>
                  <td className="num" data-label="Preço">{formatBRL(p.valor)}</td>
                  <td className="num" data-label="Estoque">
                    <span className={'pill ' + (p.quantidade <= 0 ? 'pill--warn' : 'pill--neutro')}>
                      {p.quantidade}
                    </span>
                  </td>
                  <td data-label="Status">
                    <span className={'pill ' + (p.ativo === false ? 'pill--neutro' : 'pill--ok')}>
                      {p.ativo === false ? 'Inativo' : 'Ativo'}
                    </span>
                  </td>
                  {isAdmin && (
                    <td className="num acoes-celula" data-label="Ações">
                      <button className="btn btn--pequeno" onClick={() => setModalEntrada(p)}>
                        Repor
                      </button>
                      <button className="btn btn--pequeno" onClick={() => setModalProduto(p)}>
                        Editar
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {isAdmin && modalProduto && (
        <ModalProduto
          produto={modalProduto.id ? modalProduto : null}
          onClose={() => setModalProduto(null)}
          onSucesso={async () => {
            setModalProduto(null)
            await carregar()
          }}
        />
      )}
      {isAdmin && modalEntrada && (
        <ModalEntrada
          produto={modalEntrada}
          onClose={() => setModalEntrada(null)}
          onSucesso={async () => {
            setModalEntrada(null)
            await carregar()
          }}
        />
      )}
    </div>
  )
}

function ModalProduto({ produto, onClose, onSucesso }) {
  const toast = useToast()
  const edicao = !!produto
  const [form, setForm] = useState(
    produto
      ? {
          nome: produto.nome,
          valor: String(produto.valor),
          quantidade: String(produto.quantidade),
          fornecedor: produto.fornecedor || '',
          descricao: produto.descricao || '',
          ativo: produto.ativo !== false,
        }
      : { ...VAZIO, ativo: true }
  )
  const [enviando, setEnviando] = useState(false)

  const set = (campo) => (e) =>
    setForm((f) => ({ ...f, [campo]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }))

  async function salvar(e) {
    e.preventDefault()
    setEnviando(true)
    try {
      if (edicao) {
        // Estoque nao muda por edicao: use "Repor" (movimento auditado).
        await api.atualizarProduto(produto.id, {
          nome: form.nome,
          valor: Number(form.valor),
          fornecedor: form.fornecedor,
          descricao: form.descricao || null,
          ativo: form.ativo,
        })
        toast.sucesso('Produto atualizado.')
      } else {
        await api.criarProduto({
          nome: form.nome,
          valor: Number(form.valor),
          quantidade: Number(form.quantidade || 0),
          fornecedor: form.fornecedor,
          descricao: form.descricao || null,
        })
        toast.sucesso('Produto criado.')
      }
      onSucesso()
    } catch (err) {
      toast.erro(err.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Modal aberto titulo={edicao ? 'Editar produto' : 'Novo produto'} onClose={onClose}>
      <form className="form-vertical" onSubmit={salvar}>
        <label className="campo">
          <span>Nome</span>
          <input type="text" value={form.nome} onChange={set('nome')} required />
        </label>
        <div className="form-linha">
          <label className="campo">
            <span>Preço (R$)</span>
            <input type="number" step="0.01" min="0" value={form.valor} onChange={set('valor')} required />
          </label>
          {!edicao && (
            <label className="campo">
              <span>Estoque inicial</span>
              <input type="number" min="0" value={form.quantidade} onChange={set('quantidade')} />
            </label>
          )}
        </div>
        <label className="campo">
          <span>Fornecedor</span>
          <input type="text" value={form.fornecedor} onChange={set('fornecedor')} required />
        </label>
        <label className="campo">
          <span>Descrição (opcional)</span>
          <textarea rows="2" value={form.descricao} onChange={set('descricao')} />
        </label>
        {edicao && (
          <label className="campo campo--check">
            <input type="checkbox" checked={form.ativo} onChange={set('ativo')} />
            <span>Produto ativo</span>
          </label>
        )}
        <div className="form-acoes">
          <button type="button" className="btn" onClick={onClose}>Cancelar</button>
          <button className="btn btn--primary" disabled={enviando}>
            {enviando ? 'Salvando…' : 'Salvar'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function ModalEntrada({ produto, onClose, onSucesso }) {
  const toast = useToast()
  const [quantidade, setQuantidade] = useState('')
  const [motivo, setMotivo] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function salvar(e) {
    e.preventDefault()
    setEnviando(true)
    try {
      await api.entradaEstoque(produto.id, { quantidade: Number(quantidade), motivo: motivo || null })
      toast.sucesso('Estoque reposto.')
      onSucesso()
    } catch (err) {
      toast.erro(err.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Modal aberto titulo={`Repor estoque — ${produto.nome}`} onClose={onClose}>
      <form className="form-vertical" onSubmit={salvar}>
        <p className="muted">Estoque atual: <strong>{produto.quantidade}</strong> unidades.</p>
        <label className="campo">
          <span>Quantidade a adicionar</span>
          <input
            type="number"
            min="1"
            value={quantidade}
            onChange={(e) => setQuantidade(e.target.value)}
            required
            autoFocus
          />
        </label>
        <label className="campo">
          <span>Motivo (opcional)</span>
          <input type="text" value={motivo} onChange={(e) => setMotivo(e.target.value)} placeholder="Ex.: compra fornecedor" />
        </label>
        <div className="form-acoes">
          <button type="button" className="btn" onClick={onClose}>Cancelar</button>
          <button className="btn btn--primary" disabled={enviando || quantidade === ''}>
            {enviando ? 'Salvando…' : 'Repor'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

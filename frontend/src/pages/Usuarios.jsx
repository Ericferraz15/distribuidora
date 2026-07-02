import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client.js'
import { useAuth } from '../auth/AuthContext.jsx'
import { useToast } from '../components/Toast.jsx'
import Modal from '../components/Modal.jsx'
import { SkeletonLinhas } from '../components/Skeleton.jsx'
import { rotulo } from '../lib/format.js'

const PERMISSOES = ['funcionario', 'admin']

export default function Usuarios() {
  const { user } = useAuth()
  const toast = useToast()

  const [usuarios, setUsuarios] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [modal, setModal] = useState(null) // null | {} (novo) | usuario (edicao)

  const carregar = useCallback(async () => {
    setCarregando(true)
    try {
      setUsuarios(await api.listarUsuarios())
    } catch (err) {
      toast.erro(err.message)
    } finally {
      setCarregando(false)
    }
  }, [toast])

  useEffect(() => {
    carregar()
  }, [carregar])

  async function alternarAtivo(u) {
    try {
      await api.atualizarUsuario(u.id, { ativo: !u.ativo })
      toast.sucesso(u.ativo ? 'Usuário desativado.' : 'Usuário ativado.')
      await carregar()
    } catch (err) {
      toast.erro(err.message)
    }
  }

  return (
    <div className="pagina">
      <header className="pagina__head">
        <div>
          <h2>Usuários</h2>
          <p className="muted">Gestão de acessos (somente administrador).</p>
        </div>
        <button className="btn btn--primary" onClick={() => setModal({})}>
          + Novo usuário
        </button>
      </header>

      <section className="card">
        {carregando ? (
          <SkeletonLinhas linhas={5} />
        ) : usuarios.length === 0 ? (
          <p className="vazio">Nenhum usuário cadastrado.</p>
        ) : (
          <table className="tabela tabela--responsiva">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Perfil</th>
                <th>Telefone</th>
                <th>Status</th>
                <th className="num">Ações</th>
              </tr>
            </thead>
            <tbody>
              {usuarios.map((u) => (
                <tr key={u.id} className={u.ativo === false ? 'linha--inativa' : ''}>
                  <td data-label="Nome">
                    <span>
                      <strong>{u.nome}</strong>
                      {u.id === user?.id && <span className="tag">você</span>}
                    </span>
                  </td>
                  <td data-label="Perfil">
                    <span className={'pill ' + (u.permissao === 'admin' ? 'pill--info' : 'pill--neutro')}>
                      {rotulo(u.permissao)}
                    </span>
                  </td>
                  <td data-label="Telefone">{u.numero_telefone || '—'}</td>
                  <td data-label="Status">
                    <span className={'pill ' + (u.ativo === false ? 'pill--neutro' : 'pill--ok')}>
                      {u.ativo === false ? 'Inativo' : 'Ativo'}
                    </span>
                  </td>
                  <td className="num acoes-celula" data-label="Ações">
                    <button className="btn btn--pequeno" onClick={() => setModal(u)}>
                      Editar
                    </button>
                    <button
                      className="btn btn--pequeno"
                      onClick={() => alternarAtivo(u)}
                      disabled={u.id === user?.id}
                      title={u.id === user?.id ? 'Você não pode desativar a si mesmo' : ''}
                    >
                      {u.ativo === false ? 'Ativar' : 'Desativar'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {modal && (
        <ModalUsuario
          usuario={modal.id ? modal : null}
          onClose={() => setModal(null)}
          onSucesso={async () => {
            setModal(null)
            await carregar()
          }}
        />
      )}
    </div>
  )
}

function ModalUsuario({ usuario, onClose, onSucesso }) {
  const toast = useToast()
  const edicao = !!usuario
  const [form, setForm] = useState({
    nome: usuario?.nome || '',
    senha: '',
    permissao: usuario?.permissao || 'funcionario',
    numero_telefone: usuario?.numero_telefone || '',
  })
  const [enviando, setEnviando] = useState(false)

  const set = (campo) => (e) => setForm((f) => ({ ...f, [campo]: e.target.value }))

  async function salvar(e) {
    e.preventDefault()
    setEnviando(true)
    try {
      if (edicao) {
        const payload = {
          nome: form.nome,
          permissao: form.permissao,
          numero_telefone: form.numero_telefone || null,
        }
        if (form.senha) payload.senha = form.senha
        await api.atualizarUsuario(usuario.id, payload)
        toast.sucesso('Usuário atualizado.')
      } else {
        await api.criarUsuario({
          nome: form.nome,
          senha: form.senha,
          permissao: form.permissao,
          numero_telefone: form.numero_telefone || null,
        })
        toast.sucesso('Usuário criado.')
      }
      onSucesso()
    } catch (err) {
      toast.erro(err.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Modal aberto titulo={edicao ? 'Editar usuário' : 'Novo usuário'} onClose={onClose}>
      <form className="form-vertical" onSubmit={salvar}>
        <label className="campo">
          <span>Nome de usuário</span>
          <input type="text" value={form.nome} onChange={set('nome')} required autoFocus />
        </label>
        <label className="campo">
          <span>{edicao ? 'Nova senha (deixe em branco para manter)' : 'Senha'}</span>
          <input
            type="password"
            value={form.senha}
            onChange={set('senha')}
            required={!edicao}
            autoComplete="new-password"
          />
        </label>
        <div className="form-linha">
          <label className="campo">
            <span>Perfil</span>
            <select value={form.permissao} onChange={set('permissao')}>
              {PERMISSOES.map((p) => (
                <option key={p} value={p}>{rotulo(p)}</option>
              ))}
            </select>
          </label>
          <label className="campo campo--cresce">
            <span>Telefone (opcional)</span>
            <input type="text" value={form.numero_telefone} onChange={set('numero_telefone')} />
          </label>
        </div>
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

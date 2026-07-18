import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.jsx'
import { useTheme } from '../theme/ThemeContext.jsx'
import Logo from '../components/Logo.jsx'

export default function Login() {
  const { login } = useAuth()
  const { theme, toggle } = useTheme()
  const navigate = useNavigate()
  const location = useLocation()

  const [nome, setNome] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  const destino = location.state?.from?.pathname

  async function onSubmit(e) {
    e.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      const u = await login(nome.trim(), senha)
      const inicio = u?.permissao === 'admin' ? '/dashboard' : '/operacao'
      navigate(destino || inicio, { replace: true })
    } catch (err) {
      setErro(err.message || 'Não foi possível entrar.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="login">
      <button
        className="icon-btn login__tema"
        onClick={toggle}
        aria-label="Alternar tema"
        title="Alternar tema"
      >
        {theme === 'dark' ? '☀' : '☾'}
      </button>

      <form className="login__card" onSubmit={onSubmit}>
        <div className="login__brand">
          <Logo />
          <p className="login__sub">Gestão de caixa e estoque · operação 24h</p>
        </div>

        {erro && <div className="alerta alerta--erro">{erro}</div>}

        <label className="campo">
          <span>Usuário</span>
          <input
            type="text"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            autoComplete="username"
            autoFocus
            required
          />
        </label>

        <label className="campo">
          <span>Senha</span>
          <input
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>

        <button className="btn btn--primary btn--bloco" disabled={enviando}>
          {enviando ? 'Entrando…' : 'Entrar'}
        </button>
      </form>
    </div>
  )
}

import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.jsx'
import { useTheme } from '../theme/ThemeContext.jsx'
import { rotulo } from '../lib/format.js'
import Logo from './Logo.jsx'

const ICONES = {
  dashboard: '▤',
  operacao: '◧',
  estoque: '▦',
  usuarios: '◑',
}

// Operação fica em destaque (é o uso principal do funcionário no celular).
function itensMenu(isAdmin) {
  const operacao = { to: '/operacao', label: 'Operação', icone: ICONES.operacao, destaque: true }
  const estoque = { to: '/estoque', label: 'Estoque', icone: ICONES.estoque }
  if (isAdmin) {
    return [
      { to: '/dashboard', label: 'Dashboard', icone: ICONES.dashboard },
      estoque,
      operacao,
      { to: '/usuarios', label: 'Usuários', icone: ICONES.usuarios },
    ]
  }
  return [operacao, estoque]
}

export default function Layout() {
  const { user, isAdmin, logout } = useAuth()
  const { theme, toggle } = useTheme()
  const navigate = useNavigate()
  const itens = itensMenu(isAdmin)

  const sair = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar__brand">
          <Logo />
        </div>
        <nav className="sidebar__nav">
          {itens.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => 'navlink' + (isActive ? ' navlink--ativo' : '')}
            >
              <span className="navlink__icone" aria-hidden>
                {item.icone}
              </span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar__rodape">
          <div className="perfil">
            {/* Inicial do nome vindo de /auth/me; cai para o id enquanto carrega. */}
            <div className="perfil__avatar">
              {(user?.nome?.[0] || (isAdmin ? 'A' : 'F')).toUpperCase()}
            </div>
            <div className="perfil__info">
              <strong>{user?.nome || `Usuário #${user?.id}`}</strong>
              <span>{rotulo(user?.permissao)}</span>
            </div>
          </div>
        </div>
      </aside>

      <div className="conteudo">
        <header className="topbar">
          <div className="topbar__brand">
            <Logo compacto />
          </div>
          <div className="topbar__spacer" />
          <button className="icon-btn" onClick={toggle} aria-label="Alternar tema" title="Alternar tema">
            {theme === 'dark' ? '☀' : '☾'}
          </button>
          <button className="btn btn--ghost" onClick={sair}>
            Sair
          </button>
        </header>

        <main className="main">
          <Outlet />
        </main>
      </div>

      <nav className="bottomnav" aria-label="Navegação principal">
        {itens.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              'bottomnav__item' +
              (item.destaque ? ' bottomnav__item--destaque' : '') +
              (isActive ? ' bottomnav__item--ativo' : '')
            }
          >
            <span className="bottomnav__icone" aria-hidden>
              {item.icone}
            </span>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}

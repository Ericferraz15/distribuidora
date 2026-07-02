import { createContext, useContext, useEffect, useMemo, useState, useCallback } from 'react'
import { api, getAccessToken, setTokens, clearTokens } from '../api/client.js'
import { decodeJwt, tokenExpirado } from './jwt.js'

const AuthContext = createContext(null)

function usuarioDoToken(token) {
  const payload = decodeJwt(token)
  if (!payload || tokenExpirado(payload)) return null
  return { id: Number(payload.sub), permissao: payload.permissao }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => usuarioDoToken(getAccessToken()))
  const [carregando] = useState(false)

  const logout = useCallback(async () => {
    try {
      if (getAccessToken()) await api.logout()
    } catch {
      /* logout e best-effort: token pode ja estar invalido */
    }
    clearTokens()
    setUser(null)
  }, [])

  const login = useCallback(async (username, password) => {
    const tokens = await api.login(username, password)
    setTokens(tokens)
    const u = usuarioDoToken(tokens.access_token)
    setUser(u)
    return u
  }, [])

  // O cliente HTTP dispara este evento quando a sessao expira sem refresh.
  useEffect(() => {
    const onLogout = () => {
      clearTokens()
      setUser(null)
    }
    window.addEventListener('auth:logout', onLogout)
    return () => window.removeEventListener('auth:logout', onLogout)
  }, [])

  // O token so carrega id + permissao; o nome (e a permissao mais recente)
  // vem de GET /auth/me. Roda apos o login e ao reabrir a app ja logado.
  useEffect(() => {
    if (!user || user.nome) return
    let cancelado = false
    api
      .me()
      .then((perfil) => {
        if (cancelado || !perfil) return
        setUser((u) => (u ? { ...u, nome: perfil.nome, permissao: perfil.permissao } : u))
      })
      .catch(() => {
        /* melhor exibir "Usuario #id" do que quebrar a app se /me falhar */
      })
    return () => {
      cancelado = true
    }
  }, [user])

  const value = useMemo(
    () => ({
      user,
      carregando,
      isAdmin: user?.permissao === 'admin',
      autenticado: !!user,
      login,
      logout,
    }),
    [user, carregando, login, logout]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth precisa estar dentro de <AuthProvider>')
  return ctx
}

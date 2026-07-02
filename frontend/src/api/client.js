// Cliente HTTP unico da aplicacao. Centraliza:
//  - base URL (proxy em dev; VITE_API_URL em producao)
//  - anexo do Bearer token
//  - renovacao automatica via /auth/refresh em respostas 401
//  - normalizacao das mensagens de erro do FastAPI

const BASE = import.meta.env.VITE_API_URL || ''

const ACCESS_KEY = 'dm_access_token'
const REFRESH_KEY = 'dm_refresh_token'

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY)
}
export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY)
}
export function setTokens({ access_token, refresh_token }) {
  if (access_token) localStorage.setItem(ACCESS_KEY, access_token)
  if (refresh_token) localStorage.setItem(REFRESH_KEY, refresh_token)
}
export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// FastAPI retorna detalhes de validacao como lista de objetos {loc, msg}.
function normalizarDetalhe(detail, fallback) {
  if (!detail) return fallback
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
  }
  return fallback
}

async function tentarRenovar() {
  const refresh = getRefreshToken()
  if (!refresh) return false
  const res = await fetch(BASE + '/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refresh }),
  })
  if (!res.ok) return false
  setTokens(await res.json())
  return true
}

export async function apiFetch(path, opts = {}) {
  const { method = 'GET', body, form, auth = true, _retry = false } = opts
  const headers = {}
  let payload

  if (form) {
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    payload = new URLSearchParams(form).toString()
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  if (auth) {
    const token = getAccessToken()
    if (token) headers['Authorization'] = 'Bearer ' + token
  }

  const res = await fetch(BASE + path, { method, headers, body: payload })

  if (res.status === 401 && auth && !_retry) {
    if (await tentarRenovar()) {
      return apiFetch(path, { ...opts, _retry: true })
    }
    clearTokens()
    window.dispatchEvent(new Event('auth:logout'))
    throw new ApiError('Sessao expirada. Faca login novamente.', 401)
  }

  if (!res.ok) {
    let detalhe = res.statusText
    try {
      const corpo = await res.json()
      detalhe = normalizarDetalhe(corpo.detail, res.statusText)
    } catch {
      /* corpo vazio ou nao-JSON */
    }
    throw new ApiError(detalhe || 'Erro na requisicao', res.status)
  }

  if (res.status === 204) return null
  const texto = await res.text()
  return texto ? JSON.parse(texto) : null
}

// --- Endpoints da Distribuidora API ----------------------------------------
export const api = {
  // auth
  login: (username, password) =>
    apiFetch('/auth/login', { method: 'POST', form: { username, password }, auth: false }),
  logout: () => apiFetch('/auth/logout', { method: 'POST' }),

  // turnos
  turnoAtivo: () => apiFetch('/turnos/ativo'),
  abrirTurno: (saldo_inicial) =>
    apiFetch('/turnos/abrir', { method: 'POST', body: { saldo_inicial } }),
  encerrarTurno: (saldo_final_informado) =>
    apiFetch('/turnos/encerrar', { method: 'POST', body: { saldo_final_informado } }),

  // caixa
  caixaAtual: () => apiFetch('/caixa/atual'),
  fecharCaixa: (saldo_final_informado) =>
    apiFetch('/caixa/fechar', { method: 'POST', body: { saldo_final_informado } }),

  // transacoes
  listarTransacoes: () => apiFetch('/transacoes'),
  registrarVenda: (payload) =>
    apiFetch('/transacoes/venda', { method: 'POST', body: payload }),
  registrarSaida: (payload) =>
    apiFetch('/transacoes/saida', { method: 'POST', body: payload }),

  // estoque
  listarProdutos: () => apiFetch('/produtos'),
  criarProduto: (payload) => apiFetch('/produtos', { method: 'POST', body: payload }),
  atualizarProduto: (id, payload) =>
    apiFetch(`/produtos/${id}`, { method: 'PATCH', body: payload }),
  entradaEstoque: (id, payload) =>
    apiFetch(`/produtos/${id}/entrada`, { method: 'POST', body: payload }),

  // usuarios (admin)
  listarUsuarios: () => apiFetch('/usuarios'),
  criarUsuario: (payload) => apiFetch('/usuarios', { method: 'POST', body: payload }),
  atualizarUsuario: (id, payload) =>
    apiFetch(`/usuarios/${id}`, { method: 'PATCH', body: payload }),

  // dashboard (admin)
  dashboardResumo: (dia) =>
    apiFetch('/dashboard/resumo' + (dia ? `?dia=${dia}` : '')),
  dashboardMaisVendidos: (limite = 10) =>
    apiFetch(`/dashboard/mais-vendidos?limite=${limite}`),
  dashboardCaixaStatus: () => apiFetch('/dashboard/caixa-status'),
}

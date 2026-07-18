// Decodifica o payload de um JWT (sem validar assinatura — isso e papel da API).
// A API nao expoe um endpoint /me, entao o perfil (permissao) e o id do usuario
// sao lidos das claims do proprio access token: { sub, permissao, tipo, exp }.
export function decodeJwt(token) {
  if (!token) return null
  try {
    const payload = token.split('.')[1]
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/')
    const json = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + c.charCodeAt(0).toString(16).padStart(2, '0'))
        .join('')
    )
    return JSON.parse(json)
  } catch {
    return null
  }
}

export function tokenExpirado(payload) {
  if (!payload?.exp) return false
  return Date.now() >= payload.exp * 1000
}

// Gera JWTs falsos (assinatura fictícia) só para os testes: o front nunca valida
// a assinatura — apenas decodifica as claims (sub, permissao, tipo, exp).
function b64url(obj) {
  return btoa(JSON.stringify(obj)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_')
}

export function fakeToken({
  sub = 1,
  permissao = 'admin',
  tipo = 'access',
  exp = Math.floor(Date.now() / 1000) + 3600,
} = {}) {
  const header = b64url({ alg: 'HS256', typ: 'JWT' })
  const payload = b64url({ sub: String(sub), permissao, tipo, exp })
  return `${header}.${payload}.assinatura-de-teste`
}

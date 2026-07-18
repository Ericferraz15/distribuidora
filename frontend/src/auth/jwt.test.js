import { describe, it, expect } from 'vitest'
import { decodeJwt, tokenExpirado } from './jwt.js'
import { fakeToken } from '../test/token.js'

describe('decodeJwt', () => {
  it('decodifica as claims de um token válido', () => {
    const payload = decodeJwt(fakeToken({ sub: 7, permissao: 'funcionario' }))
    expect(payload.sub).toBe('7')
    expect(payload.permissao).toBe('funcionario')
    expect(payload.tipo).toBe('access')
  })
  it('devolve null para token inválido ou vazio', () => {
    expect(decodeJwt('lixo')).toBeNull()
    expect(decodeJwt('')).toBeNull()
    expect(decodeJwt(null)).toBeNull()
  })
})

describe('tokenExpirado', () => {
  it('detecta expiração', () => {
    const passado = { exp: Math.floor(Date.now() / 1000) - 10 }
    const futuro = { exp: Math.floor(Date.now() / 1000) + 60 }
    expect(tokenExpirado(passado)).toBe(true)
    expect(tokenExpirado(futuro)).toBe(false)
  })
  it('sem exp não é considerado expirado', () => {
    expect(tokenExpirado({})).toBe(false)
  })
})

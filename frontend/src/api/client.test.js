import { describe, it, expect } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../test/server.js'
import { api, getAccessToken } from './client.js'

describe('apiFetch', () => {
  it('anexa o Bearer token no cabeçalho', async () => {
    localStorage.setItem('dm_access_token', 'TKN')
    server.use(
      http.get('/produtos', ({ request }) =>
        HttpResponse.json({ auth: request.headers.get('authorization') })
      )
    )
    const r = await api.listarProdutos()
    expect(r.auth).toBe('Bearer TKN')
  })

  it('renova o access token e repete a requisição no 401', async () => {
    localStorage.setItem('dm_access_token', 'OLD')
    localStorage.setItem('dm_refresh_token', 'R0')
    server.use(
      http.get('/caixa/atual', ({ request }) =>
        request.headers.get('authorization') === 'Bearer OLD'
          ? new HttpResponse(null, { status: 401 })
          : HttpResponse.json({ aberto: false })
      ),
      http.post('/auth/refresh', () =>
        HttpResponse.json({ access_token: 'NEW', refresh_token: 'R1' })
      )
    )
    const r = await api.caixaAtual()
    expect(r).toEqual({ aberto: false })
    expect(getAccessToken()).toBe('NEW')
  })

  it('faz logout quando o refresh também falha', async () => {
    localStorage.setItem('dm_access_token', 'OLD')
    localStorage.setItem('dm_refresh_token', 'R0')
    server.use(
      http.get('/produtos', () => new HttpResponse(null, { status: 401 })),
      http.post('/auth/refresh', () => new HttpResponse(null, { status: 401 }))
    )
    let deslogou = false
    window.addEventListener('auth:logout', () => (deslogou = true), { once: true })

    await expect(api.listarProdutos()).rejects.toMatchObject({ status: 401 })
    expect(deslogou).toBe(true)
    expect(getAccessToken()).toBeNull()
  })

  it('normaliza erro com detail string', async () => {
    server.use(http.post('/produtos', () => HttpResponse.json({ detail: 'Já existe' }, { status: 409 })))
    await expect(api.criarProduto({})).rejects.toThrowError('Já existe')
  })

  it('normaliza erro de validação (lista de detalhes do FastAPI)', async () => {
    server.use(
      http.post('/produtos', () =>
        HttpResponse.json({ detail: [{ msg: 'campo obrigatório' }] }, { status: 422 })
      )
    )
    await expect(api.criarProduto({})).rejects.toThrowError(/campo obrigatório/)
  })
})

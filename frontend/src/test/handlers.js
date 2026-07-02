import { http, HttpResponse } from 'msw'
import { fakeToken } from './token.js'

// Banco em memória para os testes de fluxo. `resetDb()` restaura o estado inicial
// entre os testes (chamado no setup). Testes podem sobrescrever handlers com
// server.use(...) para cenários específicos (401, dono diferente, erros, etc.).
function seed() {
  return {
    produtos: [
      { id: 1, nome: 'Cerveja Pilsen 600ml', valor: '9.90', quantidade: 48, fornecedor: 'Ambev', descricao: 'Garrafa', ativo: true },
      { id: 2, nome: 'Refrigerante Cola 2L', valor: '8.50', quantidade: 30, fornecedor: 'Coca-Cola', descricao: null, ativo: true },
    ],
    usuarios: [
      { id: 1, nome: 'admin', permissao: 'admin', numero_telefone: null, ativo: true },
      { id: 2, nome: 'joao', permissao: 'funcionario', numero_telefone: '11999998888', ativo: true },
    ],
    turno: null,
    caixa: null,
    transacoes: [],
    seq: 100,
  }
}

export let db = seed()
export function resetDb() {
  db = seed()
}

const agora = () => new Date().toISOString()

function statusCaixa() {
  if (!db.caixa || db.turno?.status !== 'aberto') return { aberto: false }
  const entradas = db.transacoes.filter((t) => t.tipo === 'entrada').reduce((a, t) => a + Number(t.valor), 0)
  const saidas = db.transacoes.filter((t) => t.tipo === 'saida').reduce((a, t) => a + Number(t.valor), 0)
  const inicial = Number(db.caixa.saldo_inicial)
  return {
    aberto: true,
    turno_id: db.turno.id,
    caixa_id: db.caixa.id,
    funcionario_id: db.turno.funcionario_id,
    funcionario_nome: db.usuarios.find((u) => u.id === db.turno.funcionario_id)?.nome || null,
    saldo_inicial: inicial.toFixed(2),
    total_entradas: entradas.toFixed(2),
    total_saidas: saidas.toFixed(2),
    saldo_atual: (inicial + entradas - saidas).toFixed(2),
    abertura: db.caixa.abertura,
  }
}

export const handlers = [
  // --- auth ---
  http.post('/auth/login', async ({ request }) => {
    const body = new URLSearchParams(await request.text())
    const usuario = db.usuarios.find((u) => u.nome === body.get('username'))
    const permissao = usuario?.permissao || 'admin'
    return HttpResponse.json({
      access_token: fakeToken({ sub: usuario?.id || 1, permissao }),
      refresh_token: fakeToken({ sub: usuario?.id || 1, permissao, tipo: 'refresh' }),
      token_type: 'bearer',
    })
  }),
  http.post('/auth/refresh', () =>
    HttpResponse.json({ access_token: fakeToken(), refresh_token: fakeToken({ tipo: 'refresh' }) })
  ),
  http.post('/auth/logout', () => HttpResponse.json({ detail: 'ok' })),
  // Perfil do usuario logado: lemos o id do proprio Bearer token (claim sub).
  http.get('/auth/me', ({ request }) => {
    const token = request.headers.get('authorization')?.replace('Bearer ', '')
    let sub = 1
    try {
      sub = Number(JSON.parse(atob(token.split('.')[1])).sub)
    } catch {
      /* token de teste sempre decodifica; fallback pro admin */
    }
    const u = db.usuarios.find((x) => x.id === sub) || db.usuarios[0]
    return HttpResponse.json(u)
  }),

  // --- turnos ---
  http.get('/turnos/ativo', () => HttpResponse.json(db.turno)),
  http.post('/turnos/abrir', async ({ request }) => {
    const { saldo_inicial } = await request.json()
    db.turno = { id: ++db.seq, funcionario_id: 1, data_abertura: agora(), data_fechamento: null, status: 'aberto' }
    db.caixa = { id: ++db.seq, saldo_inicial: String(saldo_inicial), abertura: agora() }
    return HttpResponse.json(db.turno, { status: 201 })
  }),
  http.post('/turnos/encerrar', () => {
    if (db.turno) db.turno = { ...db.turno, status: 'encerrado', data_fechamento: agora() }
    const t = db.turno
    db.turno = null
    db.caixa = null
    db.transacoes = []
    return HttpResponse.json(t)
  }),

  // --- caixa ---
  http.get('/caixa/atual', () => HttpResponse.json(statusCaixa())),
  http.post('/caixa/fechar', () => {
    const t = db.turno ? { ...db.turno, status: 'encerrado', data_fechamento: agora() } : null
    db.turno = null
    db.caixa = null
    db.transacoes = []
    return HttpResponse.json(t)
  }),

  // --- transacoes ---
  http.get('/transacoes', () => HttpResponse.json(db.transacoes)),
  http.post('/transacoes/venda', async ({ request }) => {
    const { itens, metodo_pagamento, descricao } = await request.json()
    let total = 0
    const linhas = itens.map((it) => {
      const p = db.produtos.find((x) => x.id === it.produto_id)
      if (p) p.quantidade -= it.quantidade
      const unit = Number(p?.valor || 0)
      total += unit * it.quantidade
      return { produto_id: it.produto_id, quantidade: it.quantidade, valor_unitario: unit.toFixed(2) }
    })
    const tx = {
      id: ++db.seq, caixa_id: db.caixa?.id || 1, funcionario_id: 1, tipo: 'entrada',
      categoria: 'venda', valor: total.toFixed(2), metodo_pagamento, data: agora(),
      descricao: descricao || null, itens: linhas,
    }
    db.transacoes.push(tx)
    return HttpResponse.json(tx, { status: 201 })
  }),
  http.post('/transacoes/saida', async ({ request }) => {
    const { valor, categoria, metodo_pagamento, descricao } = await request.json()
    const tipo = categoria === 'suprimento' ? 'entrada' : 'saida'
    const tx = {
      id: ++db.seq, caixa_id: db.caixa?.id || 1, funcionario_id: 1, tipo,
      categoria, valor: Number(valor).toFixed(2), metodo_pagamento, data: agora(),
      descricao: descricao || null, itens: [],
    }
    db.transacoes.push(tx)
    return HttpResponse.json(tx, { status: 201 })
  }),

  // --- produtos ---
  http.get('/produtos', () => HttpResponse.json(db.produtos)),
  http.post('/produtos', async ({ request }) => {
    const body = await request.json()
    const novo = { id: ++db.seq, quantidade: 0, descricao: null, ativo: true, ...body, valor: String(body.valor) }
    db.produtos.push(novo)
    return HttpResponse.json(novo, { status: 201 })
  }),
  http.patch('/produtos/:id', async ({ request, params }) => {
    const p = db.produtos.find((x) => x.id === Number(params.id))
    if (!p) return new HttpResponse(null, { status: 404 })
    Object.assign(p, await request.json())
    return HttpResponse.json(p)
  }),
  http.post('/produtos/:id/entrada', async ({ request, params }) => {
    const p = db.produtos.find((x) => x.id === Number(params.id))
    if (!p) return new HttpResponse(null, { status: 404 })
    const { quantidade } = await request.json()
    p.quantidade += quantidade
    return HttpResponse.json(p)
  }),

  // --- usuarios ---
  http.get('/usuarios', () => HttpResponse.json(db.usuarios)),
  http.post('/usuarios', async ({ request }) => {
    const body = await request.json()
    const novo = { id: ++db.seq, ativo: true, numero_telefone: null, ...body }
    delete novo.senha
    db.usuarios.push(novo)
    return HttpResponse.json(novo, { status: 201 })
  }),
  http.patch('/usuarios/:id', async ({ request, params }) => {
    const u = db.usuarios.find((x) => x.id === Number(params.id))
    if (!u) return new HttpResponse(null, { status: 404 })
    const body = await request.json()
    delete body.senha
    Object.assign(u, body)
    return HttpResponse.json(u)
  }),

  // --- dashboard ---
  http.get('/dashboard/resumo', () =>
    HttpResponse.json({ data: '2026-07-02', faturamento: '1240.00', num_vendas: 12, total_saidas: '150.00', num_transacoes: 15 })
  ),
  http.get('/dashboard/mais-vendidos', () =>
    HttpResponse.json([
      { produto_id: 1, nome: 'Cerveja Pilsen 600ml', quantidade_total: 40, receita_total: '396.00' },
      { produto_id: 2, nome: 'Refrigerante Cola 2L', quantidade_total: 18, receita_total: '153.00' },
    ])
  ),
  http.get('/dashboard/caixa-status', () => HttpResponse.json(statusCaixa())),
]

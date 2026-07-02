// Helpers de formatacao para exibicao (a API trabalha com Decimal/ISO).

export function formatBRL(valor) {
  const n = Number(valor ?? 0)
  return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export function formatData(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (isNaN(d)) return '—'
  return d.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function hojeISO() {
  return new Date().toISOString().slice(0, 10)
}

const ROTULO = {
  venda: 'Venda',
  sangria: 'Sangria',
  despesa: 'Despesa',
  suprimento: 'Suprimento',
  entrada: 'Entrada',
  saida: 'Saída',
  dinheiro: 'Dinheiro',
  debito: 'Débito',
  credito: 'Crédito',
  admin: 'Administrador',
  funcionario: 'Funcionário',
}

export function rotulo(valor) {
  return ROTULO[valor] || valor
}

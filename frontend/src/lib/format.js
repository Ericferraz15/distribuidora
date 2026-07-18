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
  // Data LOCAL em YYYY-MM-DD. Cuidado com toISOString(): ela converte para
  // UTC, entao depois das 21h no Brasil (UTC-3) devolveria a data de amanha.
  // O locale 'sv' (sueco) formata exatamente como YYYY-MM-DD.
  return new Date().toLocaleDateString('sv')
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

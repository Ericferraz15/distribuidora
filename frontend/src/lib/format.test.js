import { describe, it, expect } from 'vitest'
import { formatBRL, formatData, hojeISO, rotulo } from './format.js'

describe('formatBRL', () => {
  it('formata número como moeda BRL', () => {
    expect(formatBRL('1240.00')).toMatch(/1\.240,00/)
    expect(formatBRL('1240.00')).toMatch(/R\$/)
  })
  it('trata nulo/indefinido como zero', () => {
    expect(formatBRL(null)).toMatch(/0,00/)
    expect(formatBRL(undefined)).toMatch(/0,00/)
  })
})

describe('formatData', () => {
  it('retorna traço para valor vazio ou inválido', () => {
    expect(formatData(null)).toBe('—')
    expect(formatData('não-é-data')).toBe('—')
  })
  it('formata ISO para data legível', () => {
    expect(formatData('2026-07-02T12:00:00Z')).toMatch(/2026/)
  })
})

describe('hojeISO', () => {
  it('devolve data no formato YYYY-MM-DD', () => {
    expect(hojeISO()).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })
})

describe('rotulo', () => {
  it('traduz códigos conhecidos', () => {
    expect(rotulo('venda')).toBe('Venda')
    expect(rotulo('debito')).toBe('Débito')
    expect(rotulo('admin')).toBe('Administrador')
  })
  it('devolve o próprio valor quando desconhecido', () => {
    expect(rotulo('xyz')).toBe('xyz')
  })
})

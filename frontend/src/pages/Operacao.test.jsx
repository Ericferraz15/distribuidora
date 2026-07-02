import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'
import Operacao from './Operacao.jsx'
import { db } from '../test/handlers.js'
import { renderWithProviders, login as fazerLogin } from '../test/utils.jsx'

function abrirCaixaNoDb(funcionarioId = 1) {
  db.turno = {
    id: 50,
    funcionario_id: funcionarioId,
    data_abertura: new Date().toISOString(),
    data_fechamento: null,
    status: 'aberto',
  }
  db.caixa = { id: 51, saldo_inicial: '100.00', abertura: new Date().toISOString() }
}

describe('Operacao', () => {
  it('abre o turno quando não há caixa aberto', async () => {
    fazerLogin('admin', 1)
    const { user, container } = renderWithProviders(<Operacao />)

    expect(await screen.findByRole('heading', { name: 'Abrir turno' })).toBeInTheDocument()
    await user.type(container.querySelector('input[type="number"]'), '100')
    await user.click(screen.getByRole('button', { name: /abrir turno/i }))

    expect(await screen.findByText(/Turno #/)).toBeInTheDocument()
  })

  it('registra uma venda no caixa aberto', async () => {
    abrirCaixaNoDb(1)
    fazerLogin('admin', 1)
    const { user } = renderWithProviders(<Operacao />)

    await user.click(await screen.findByRole('button', { name: /\+ venda/i }))
    const selects = await screen.findAllByRole('combobox')
    await user.selectOptions(selects[0], '1')
    await user.click(screen.getByRole('button', { name: 'Adicionar' }))
    await user.click(screen.getByRole('button', { name: /registrar venda/i }))

    expect(await screen.findByText('Venda registrada.')).toBeInTheDocument()
  })

  it('bloqueia ações quando o turno é de outro funcionário (RN01)', async () => {
    abrirCaixaNoDb(2) // turno pertence ao usuário 2
    fazerLogin('funcionario', 1) // logado como usuário 1
    renderWithProviders(<Operacao />)

    expect(await screen.findByText(/pertence a outro funcionário/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /\+ venda/i })).toBeDisabled()
  })
})

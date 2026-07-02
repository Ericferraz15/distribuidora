import { describe, it, expect } from 'vitest'
import { screen, within } from '@testing-library/react'
import Estoque from './Estoque.jsx'
import { renderWithProviders, login as fazerLogin } from '../test/utils.jsx'

describe('Estoque', () => {
  it('admin lista e cria produto', async () => {
    fazerLogin('admin')
    const { user } = renderWithProviders(<Estoque />)

    expect(await screen.findByText('Cerveja Pilsen 600ml')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /novo produto/i }))
    const dialog = screen.getByRole('dialog')
    const texts = dialog.querySelectorAll('input[type="text"]') // Nome, Fornecedor
    const nums = dialog.querySelectorAll('input[type="number"]') // Preço, Estoque inicial
    await user.type(texts[0], 'Vinho Tinto')
    await user.type(nums[0], '25')
    await user.type(texts[1], 'Vinícola Sul')
    await user.click(within(dialog).getByRole('button', { name: /salvar/i }))

    expect(await screen.findByText('Produto criado.')).toBeInTheDocument()
    expect(await screen.findByText('Vinho Tinto')).toBeInTheDocument()
  })

  it('funcionário vê o estoque em modo somente leitura', async () => {
    fazerLogin('funcionario')
    renderWithProviders(<Estoque />)

    expect(await screen.findByText('Cerveja Pilsen 600ml')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /novo produto/i })).toBeNull()
    expect(screen.queryByRole('button', { name: /editar/i })).toBeNull()
    expect(screen.queryByRole('button', { name: /repor/i })).toBeNull()
  })
})

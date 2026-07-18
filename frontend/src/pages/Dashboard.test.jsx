import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'
import Dashboard from './Dashboard.jsx'
import { renderWithProviders, login as fazerLogin } from '../test/utils.jsx'

describe('Dashboard', () => {
  it('renderiza faturamento, mais-vendidos e status do caixa', async () => {
    fazerLogin('admin')
    renderWithProviders(<Dashboard />)

    expect(await screen.findByText(/1\.240,00/)).toBeInTheDocument() // faturamento
    expect(await screen.findByText('Cerveja Pilsen 600ml')).toBeInTheDocument() // mais vendidos
    expect(await screen.findByText('Fechado')).toBeInTheDocument() // caixa sem turno aberto
  })
})

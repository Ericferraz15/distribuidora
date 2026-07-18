import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Modal from './Modal.jsx'

describe('Modal', () => {
  it('mostra o conteúdo quando aberto e nada quando fechado', () => {
    const { rerender } = render(
      <Modal aberto titulo="Título" onClose={() => {}}>
        Conteúdo
      </Modal>
    )
    expect(screen.getByText('Conteúdo')).toBeInTheDocument()

    rerender(
      <Modal aberto={false} titulo="Título" onClose={() => {}}>
        Conteúdo
      </Modal>
    )
    expect(screen.queryByText('Conteúdo')).toBeNull()
  })

  it('fecha com a tecla Escape', () => {
    const onClose = vi.fn()
    render(<Modal aberto titulo="x" onClose={onClose}>c</Modal>)
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(onClose).toHaveBeenCalled()
  })

  it('fecha ao clicar no overlay, mas não ao clicar no corpo', () => {
    const onClose = vi.fn()
    const { container } = render(<Modal aberto titulo="x" onClose={onClose}>c</Modal>)

    fireEvent.mouseDown(container.querySelector('.modal'))
    expect(onClose).not.toHaveBeenCalled()

    fireEvent.mouseDown(container.querySelector('.modal-overlay'))
    expect(onClose).toHaveBeenCalledTimes(1)
  })
})

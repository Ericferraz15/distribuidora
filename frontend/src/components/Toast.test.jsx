import { describe, it, expect, vi } from 'vitest'
import { act } from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { ToastProvider, useToast } from './Toast.jsx'

function Sonda() {
  const t = useToast()
  return <button onClick={() => t.sucesso('salvo!')}>go</button>
}

describe('Toast', () => {
  it('exibe e some sozinho após o tempo', () => {
    vi.useFakeTimers()
    try {
      render(
        <ToastProvider>
          <Sonda />
        </ToastProvider>
      )
      fireEvent.click(screen.getByText('go'))
      expect(screen.getByText('salvo!')).toBeInTheDocument()

      act(() => vi.advanceTimersByTime(4100))
      expect(screen.queryByText('salvo!')).toBeNull()
    } finally {
      vi.useRealTimers()
    }
  })

  it('fecha ao clicar', () => {
    render(
      <ToastProvider>
        <Sonda />
      </ToastProvider>
    )
    fireEvent.click(screen.getByText('go'))
    fireEvent.click(screen.getByText('salvo!'))
    expect(screen.queryByText('salvo!')).toBeNull()
  })
})

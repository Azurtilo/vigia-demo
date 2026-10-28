import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

describe('App', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('muestra que la API está conectada cuando /health responde', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ status: 'ok', environment: 'development' }), { status: 200 }),
      ),
    )

    render(<App />)

    expect(await screen.findByText(/API conectada/)).toBeInTheDocument()
  })

  it('muestra un error cuando la API no responde', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Failed to fetch')))

    render(<App />)

    expect(await screen.findByText(/No se pudo conectar con la API/)).toBeInTheDocument()
  })
})

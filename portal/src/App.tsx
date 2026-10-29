import { useEffect, useState } from 'react'
import { getHealth, type HealthResponse } from './api/health'

type ApiState =
  | { kind: 'loading' }
  | { kind: 'ok'; data: HealthResponse }
  | { kind: 'error'; message: string }

function App() {
  const [api, setApi] = useState<ApiState>({ kind: 'loading' })

  useEffect(() => {
    getHealth()
      .then((data) => setApi({ kind: 'ok', data }))
      .catch((error: unknown) =>
        setApi({ kind: 'error', message: error instanceof Error ? error.message : 'Error desconocido' }),
      )
  }, [])

  return (
    <main className="container">
      <h1>VIGIA</h1>
      <p className="subtitle">Portal web · en construcción</p>

      <section className={`status status--${api.kind}`} aria-live="polite">
        {api.kind === 'loading' && <p>Comprobando conexión con la API…</p>}
        {api.kind === 'ok' && (
          <p>
            API conectada (entorno: <strong>{api.data.environment}</strong>)
          </p>
        )}
        {api.kind === 'error' && (
          <p>
            No se pudo conectar con la API: {api.message}. ¿Está el backend en ejecución?
          </p>
        )}
      </section>
    </main>
  )
}

export default App
